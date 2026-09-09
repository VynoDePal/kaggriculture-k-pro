"""One next quadrant financed together with crops on already paid hands.

The ownership projection is only an input to the route constructor: land is
ordered at canonical hour zero, crops start strictly later, and the full land
cost is reserved before composing all old and new commitments. No free future
income, no relocation of retained work, no purchase of unused land.
"""
import copy

from reuse_paid_hands_fc import reuse_paid_hands
from crop_service_model_bm import CROPS

QUADRANTS = ('NW', 'NE', 'SW', 'SE')
LAND_COSTS = (1000, 2000, 4000)


def land_candidates(obs, *, pending_projects, limit, action_value, market_scenario):
    farm = obs['farms'][obs['player']]
    land = _next_land(obs)
    if (not pending_projects or obs['hour'] or farm['hands'] or farm['hires_today']
            or land is None or farm['money'] < land[1]): return []
    n = sum(op[0] == 'HIRE' and step == obs['step']
            for p in pending_projects for step, _, op in p['market_actions'])
    if not 1 <= n <= 4: return []
    load = {uid: sum(len(s['actions']) for p in pending_projects for s in p['sessions'] if s['worker'] == uid)
            for uid in range(1, n + 1)}
    ids = sorted(load, key=lambda uid: (load[uid], uid))
    # Distance from the nearest access tile, not just the NW shed corner.
    def distance(t):
        return min(abs(t[0]-x) + abs(t[1]-y) for x, y in ((4, 4), (5, 4), (4, 5), (5, 5))), t
    plots = sorted(land[2], key=distance)
    result = []
    for crop in sorted(set(CROPS) & set(market_scenario['params']) & set(market_scenario['inventory'])):
        for size in sorted({1, min(2, limit), min(limit, len(plots))}):
            if size < 1: continue
            for count in range(1, min(2, n, size) + 1):
                crops = [(crop, tile, ids[i % count]) for i, tile in enumerate(plots[:size])]
                r = expand_crop_land(obs, pending_projects=pending_projects, crops=crops,
                                     action_value=action_value, market_scenario=market_scenario)
                if r['feasible']: result.append(r['project'])
    return result


def _next_land(obs):
    farm = obs['farms'][obs['player']]
    owned = farm['unlocked_quadrants']
    n = len(owned)
    if not 1 <= n < 4 or tuple(owned) != QUADRANTS[:n]: return None
    quadrant = QUADRANTS[n]
    tiles = [(x, y) for y in range(10) for x in range(10)
             if ('N' if y < 5 else 'S') + ('W' if x < 5 else 'E') == quadrant
             and farm['tiles'][y][x] == 'LOCKED']
    return quadrant, LAND_COSTS[n - 1], tiles


def expand_crop_land(obs, *, pending_projects, crops, action_value, market_scenario):
    if not pending_projects: return dict(feasible=False, reason='missing_retained_farm')
    land = _next_land(obs)
    if land is None: return dict(feasible=False, reason='no_next_quadrant')
    quadrant, cost, plots = land
    if not any(tuple(tile) in plots for _, tile, _ in crops):
        return dict(feasible=False, reason='unused_new_land')
    if any(op[0] == 'BUY_LAND' for p in pending_projects for _, _, op in p['market_actions']):
        return dict(feasible=False, reason='pending_land_purchase')
    projected = copy.deepcopy(obs); farm = projected['farms'][obs['player']]
    if farm['money'] < cost: return dict(feasible=False, reason='insufficient_land_cash')
    farm['money'] -= cost
    farm['unlocked_quadrants'].append(quadrant)
    for x, y in plots: farm['tiles'][y][x] = None
    r = reuse_paid_hands(projected, pending_projects=pending_projects, crops=crops,
                         action_value=action_value, market_scenario=market_scenario)
    if not r['feasible']: return r
    p = r['project']; step = obs['step']
    # The reuse constructor never starts a new crop on hour zero. Assert this
    # contract at the ownership boundary as well, rather than granting the land
    # for unit operations that precede the market purchase in this same turn.
    for s in p['sessions']:
        if 24*s['day'] + s['hour'] <= step:
            for i, op in enumerate(s['actions']):
                if 24*s['day'] + s['hour'] + i <= step and op[0] in ('PLANT', 'BUILD_PASTURE', 'BUILD_COOP'):
                    # Existing Q1 operations are allowed; no new crop session
                    # produced by FC starts before its hand's funded spawn.
                    if s not in [t for old in pending_projects for t in old['sessions']]:
                        return dict(feasible=False, reason='land_not_yet_available')
    current = [(order, op) for at, order, op in p['market_actions'] if at == step]
    ordinal = 1 + max((order for order, _ in current), default=-1)
    if ordinal >= 10: return dict(feasible=False, reason='market_capacity')
    p['market_actions'].append((step, ordinal, ('BUY_LAND',)))
    p['market_actions'].sort(key=lambda row: row[:2])
    p['cash_events'].append(dict(step=step, phase='market', order=ordinal, cost=cost))
    row = next((row for row in p['cashflows'] if row['day'] == obs['day']), None)
    if row is None:
        p['cashflows'].append(dict(day=obs['day'], cost=cost, receipts=0))
        p['cashflows'].sort(key=lambda row: row['day'])
    else: row['cost'] += cost
    p['net_value'] -= cost
    p['land_purchases'] = [dict(step=step, quadrant=quadrant, cost=cost,
                                owned_before=list(obs['farms'][obs['player']]['unlocked_quadrants']))]
    p['id'] = f'funded-land:{quadrant}:' + p['id']
    return r
