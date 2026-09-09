"""A new herd appended to an already-funded worker's retained daily routes.

No existing action is removed or rescheduled and no wage is added. Current
unreserved shed stock only may supply the new herd; future purchases and sales
are jointly repriced and checked after composition. This does not merge feed
pickups or retime a previously installed herd, and is not a global optimizer.
"""
from itertools import permutations

from herd_calendar_ex import herd_calendar
from future_workers_do import future_workers
from hiring_cb import hire_scenario
from reuse_paid_hands_fc import SPAWNS, _finish, combine_funded_projects, copy_project_records


def shared_herd_candidates(obs, *, pending_projects, max_size, action_value, market_scenario,
                            care=False, flexible_fertilizer=False):
    farm = obs['farms'][obs['player']]
    if not pending_projects or obs['hour'] or farm['hands'] or farm['hires_today']: return []
    hires = {}
    for p in pending_projects:
        for step, _, op in p['market_actions']:
            if op[0] == 'HIRE': hires[step // 24] = hires.get(step // 24, 0) + 1
    n = hires.get(obs['day'], 0)
    if not 1 <= n <= 4: return []
    loads = {uid: sum(len(s['actions']) for p in pending_projects for s in p['sessions'] if s['worker'] == uid)
             for uid in range(1, n + 1)}
    ids = sorted(loads, key=lambda uid: (loads[uid], uid))[:2]
    reserved = {tuple(t) for p in pending_projects for t in p.get('plots', [p['plot']])}
    def distance(a, b): return abs(a[0]-b[0]) + abs(a[1]-b[1])
    def shed_distance(t): return min(distance(t, s) for s in SPAWNS[:4])
    pool = [(x, y) for y, row in enumerate(farm['tiles']) for x, tile in enumerate(row)
            if tile is None and (x, y) not in reserved]
    pool.sort(key=lambda t: (shed_distance(t), t)); pool = pool[:6]
    def route_cost(route):
        return shed_distance(route[0]) + sum(distance(a, b) for a, b in zip(route, route[1:])) + shed_distance(route[-1]), route
    routes = [min(permutations(pool, count), key=route_cost) for count in range(1, min(max_size, len(pool)) + 1)]
    species = ('COW', 'SHEEP', 'GOOSE'); result = []
    availability = {(d, uid): dict(position=SPAWNS[uid], available_from=1)
                    for d in range(obs['day'], 30) for uid in range(1, min(4, hires.get(d, 0)) + 1)}
    for s in sorted((s for p in pending_projects for s in p['sessions']), key=lambda s: (s['day'], s['hour'])):
        if (s['day'], s['worker']) in availability: availability[s['day'], s['worker']] = _finish(s)
    for uid in ids + [None]:
        end_day = obs['day']
        while end_day < 29 and hires.get(end_day + 1, 0) >= (uid or 1): end_day += 1
        if end_day <= obs['day']: continue
        for route in routes:
            assigned = None
            if uid is None:
                assigned = {}
                for d in range(obs['day'], end_day + 1):
                    def arrival(worker):
                        row = availability[d, worker]; pos = row['position']
                        approach = (min(distance(pos, shed) + distance(shed, route[0]) for shed in SPAWNS[:4])
                                    if d < end_day else distance(pos, route[0]))
                        return row['available_from'] + approach, row['available_from'], worker
                    assigned[d] = min(range(1, min(4, hires[d]) + 1), key=arrival)
                if len(set(assigned.values())) == 1 and assigned[obs['day']] in ids: continue
            kinds = [(animal,) * len(route) for animal in species]
            if len(route) > 1:
                kinds += [tuple(species[(i + shift) % 3] for i in range(len(route))) for shift in range(3)]
            for animals in kinds:
                for with_care in ((False, True) if care else (False,)):
                    for flexible in ((False, True) if flexible_fertilizer else (False,)):
                        r = reuse_herd_hand(obs, pending_projects=pending_projects, herd=list(zip(animals, route)),
                                            worker_id=uid if assigned is None else assigned[obs['day']], end_day=end_day,
                                            daily_workers=assigned, action_value=action_value,
                                            market_scenario=market_scenario, care=with_care, flexible_fertilizer=flexible)
                        if r['feasible']: result.append(r['project'])
    return result


def _unreserved_shed(obs, parts):
    balance = dict(obs['private']['shed']); free = dict(balance)
    phases = {'unit': 0, 'market': 1, 'night': 2}
    for e in sorted((e for p in parts for e in p['stock_events']),
                    key=lambda e: (e['step'], phases[e['phase']], e['order'])):
        for account, item, qty in e['changes']:
            if account == 'shed':
                balance[item] = balance.get(item, 0) + qty
                free[item] = min(free.get(item, 0), balance[item])
    return {item: max(0, qty) for item, qty in free.items()}


def reuse_herd_hand(obs, *, pending_projects, herd, worker_id, end_day,
                    action_value, market_scenario, care=False, flexible_fertilizer=False, daily_workers=None):
    farm = obs['farms'][obs['player']]
    if not pending_projects or obs['hour'] or farm['hands'] or farm['hires_today'] or tuple(farm['farmer']) != (4, 4):
        return dict(feasible=False, reason='requires_funded_day_start')
    if type(worker_id) is not int or not 1 <= worker_id <= 4:
        return dict(feasible=False, reason='unfunded_herd_service')
    if type(end_day) is not int or not obs['day'] < end_day <= 29:
        return dict(feasible=False, reason='collection_date')
    if not future_workers(obs, pending_projects)['feasible']:
        return dict(feasible=False, reason='invalid_retained_funding')
    reserved = {tuple(t) for p in pending_projects for t in p.get('plots', [p['plot']])}
    if any(tuple(tile) in reserved for _, tile in herd):
        return dict(feasible=False, reason='reserved_plot')
    hires = {}
    for p in pending_projects:
        for step, _, op in p['market_actions']:
            if op[0] == 'HIRE': hires[step // 24] = hires.get(step // 24, 0) + 1
    days = range(obs['day'], end_day + 1)
    assigned = dict.fromkeys(days, worker_id) if daily_workers is None else dict(daily_workers)
    if (set(assigned) != set(days) or assigned[obs['day']] != worker_id
            or any(type(uid) is not int or not 1 <= uid <= 4 for uid in assigned.values())):
        return dict(feasible=False, reason='invalid_daily_workers')
    if any(not assigned[d] <= hires.get(d, 0) <= 4 for d in days):
        return dict(feasible=False, reason='unfunded_herd_service')
    calendar = {d: dict(position=SPAWNS[assigned[d]], available_from=1) for d in days}
    for s in sorted((s for p in pending_projects for s in p['sessions'] if s['day'] in calendar and s['worker'] == assigned[s['day']]),
                    key=lambda s: (s['day'], s['hour'])):
        calendar[s['day']] = _finish(s)
    # EX starts from an empty carried inventory. Prove that retained work
    # leaves this hand empty on every service day instead of assuming it.
    for d, row in calendar.items():
        carried = {}
        start = 24*d + row['available_from']
        for e in (e for p in pending_projects for e in p['stock_events'] if 24*d <= e['step'] < start):
            for account, item, qty in e['changes']:
                if account == f'hand:{assigned[d]}': carried[item] = carried.get(item, 0) + qty
        if any(carried.values()): return dict(feasible=False, reason='retained_carried_stock')
    projection = hire_scenario(obs, count=hires[obs['day']])
    if not projection['feasible']: return projection
    projected = projection['observation']
    projected['farms'][obs['player']]['hands'][worker_id - 1] = list(calendar[obs['day']]['position'])
    projected['private']['shed'] = _unreserved_shed(obs, pending_projects)
    fresh = herd_calendar(projected, herd=herd, end_day=end_day, worker_id=worker_id, calendar=calendar,
                           action_value=action_value, market_scenario=market_scenario, care=care,
                           flexible_fertilizer=flexible_fertilizer)
    if not fresh['feasible']: return fresh
    # EX uses one temporary account while building the nightly animal state.
    # Its daily circuit unloads all products and spends all food. Rebind each
    # day's unit events to the actual funded hand, then prove the whole farm
    # from the real spawns/stocks below. No inter-worker cargo transfer exists.
    new = fresh['project']
    for s in new['sessions']: s['worker'] = assigned[s['day']]
    for e in new['stock_events']:
        uid = assigned[e['step'] // 24]
        if e['phase'] == 'unit': e['order'] = uid
        e['changes'] = [(f'hand:{uid}' if account == f'hand:{worker_id}' else account, item, qty)
                        for account, item, qty in e['changes']]
    for e in new['opportunity_events']: e['worker'] = assigned[e['step'] // 24]
    parts = copy_project_records(pending_projects) + [fresh['project']]
    identifier = f'shared-herd:{obs["step"]}:{worker_id}:{herd}:{end_day}:{care}:{flexible_fertilizer}'
    if daily_workers is not None: identifier += ':daily:' + str(sorted(assigned.items()))
    return combine_funded_projects(obs, parts=parts, plots=reserved | {tuple(t) for _, t in herd},
                                    project_id=identifier,
                                    action_value=action_value, market_scenario=market_scenario)
