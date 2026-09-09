"""Compose a funded herd cohort, preserving retained operations.

Only mutable event/session records are copied. Retained action sequences,
stock change payloads and untouched metadata are shared read-only (as in CK).
"""
import copy
from itertools import permutations
from paid_herd_ez import paid_herd
from future_workers_do import future_workers, reserves_center_spawn
from joint_sales_ck import reprice_sales
from portfolio_reservations_bp import check_portfolio
from stock_reservations_bq import check_stock_events


def _delay_farmer_for_spawn(parts, day):
    """Reserve hour0, preserving gaps and shifting only farmer-linked sales."""
    mapping = {}; end = 1
    for s in sorted((s for p in parts for s in p['sessions'] if s['worker'] == 0 and s['day'] == day), key=lambda s: s['hour']):
        old = s['hour']; new = max(old, end); end = new + len(s['actions'])
        if end > (23 if day == 29 else 24): return False
        for i in range(len(s['actions'])): mapping[24 * day + old + i] = 24 * day + new + i
        s['hour'] = new
    for p in parts:
        sales = set()
        for e in p['stock_events']:
            if e['phase'] != 'unit' or e['order'] != 0 or e['step'] not in mapping: continue
            for account, item, qty in e['changes']:
                if account != 'shed' or qty <= 0: continue
                matches = [(step, order) for step, order, op in p['market_actions']
                           if step == e['step'] and tuple(op) == ('SELL', item, qty)]
                if len(matches) > 1: return False
                sales.update(matches)
        for e in p['stock_events']:
            if e['phase'] == 'unit' and e['order'] == 0 or e['phase'] == 'market' and (e['step'], e['order']) in sales:
                e['step'] = mapping.get(e['step'], e['step'])
        for q in p.get('sale_quotes', []):
            if (q['step'], q['order']) in sales: q['step'] = mapping[q['step']]
        p['market_actions'] = [(mapping[step] if (step, order) in sales else step, order, op)
                               for step, order, op in p['market_actions']]
        # Current animal opportunity events refer to their feeder. Preserve
        # events belonging to retained paid cohorts when they share the turn.
        for e in p.get('opportunity_events', []):
            if e.get('worker', 0) == 0: e['step'] = mapping.get(e['step'], e['step'])
    return True


def expansion_candidates(obs, *, pending_projects, max_size, action_value, market_scenario, care=False, flexible_fertilizer=False):
    farm = obs['farms'][obs['player']]
    if obs['hour'] or farm['hands'] or farm['hires_today'] or not pending_projects:
        return []
    uid = 1 + max(s['worker'] for p in pending_projects for s in p['sessions'])
    if uid > 4: return []
    reserved = {tuple(t) for p in pending_projects for t in p.get('plots', [p['plot']])}
    pool = [(x, y) for y, row in enumerate(farm['tiles']) for x, tile in enumerate(row)
            if tile is None and (x, y) not in reserved]
    pool.sort(key=lambda t: (abs(t[0]-4)+abs(t[1]-4), t)); pool = pool[:8]
    spawn = [(5, 4), (4, 5), (5, 5), (4, 4)][uid - 1]
    def distance(a, b): return abs(a[0]-b[0])+abs(a[1]-b[1])
    def route_cost(route): return (distance(spawn, route[0])+sum(distance(a, b) for a, b in zip(route, route[1:]))+
                                   min(distance(route[-1], s) for s in ((4, 4), (5, 4), (4, 5), (5, 5))), route)
    result = []; species = ('COW', 'SHEEP', 'GOOSE')
    for n in range(1, min(max_size, len(pool)) + 1):
        plots = min(permutations(pool, n), key=route_cost)
        kinds = [(a,) * n for a in species]
        if n > 1: kinds += [tuple(species[(i + shift) % 3] for i in range(n)) for shift in range(3)]
        for animals in kinds:
            for with_care in ((False, True) if care else (False,)):
                for flexible in ((False, True) if flexible_fertilizer else (False,)):
                    r = expand_herd(obs, pending_projects=pending_projects, herd=list(zip(animals, plots)), end_day=29,
                                    action_value=action_value, market_scenario=market_scenario, care=with_care,
                                    flexible_fertilizer=flexible)
                    if r['feasible']: result.append(r['project'])
    return result


def expand_herd(obs, *, pending_projects, herd, end_day, action_value, market_scenario, care=False, flexible_fertilizer=False):
    if not pending_projects: return dict(feasible=False, reason='missing_retained_farm')
    farm = obs['farms'][obs['player']]
    if not future_workers(obs, pending_projects)['feasible']: return dict(feasible=False, reason='invalid_retained_funding')
    reserved = {tuple(tile) for p in pending_projects for tile in p.get('plots', [p['plot']])}
    if any(tuple(tile) in reserved for _, tile in herd): return dict(feasible=False, reason='reserved_plot')
    uid = 1 + max((s['worker'] for p in pending_projects for s in p['sessions']), default=0)
    fresh = paid_herd(obs, herd=herd, end_day=end_day, action_value=action_value,
                      market_scenario=market_scenario, care=care, worker_id=uid, flexible_fertilizer=flexible_fertilizer)
    if not fresh['feasible']: return fresh
    parts = [copy.copy(p) for p in pending_projects]
    for p in parts:
        for field in ('sessions', 'stock_events', 'cash_events', 'sale_quotes', 'opportunity_events'):
            p[field] = [dict(e) for e in p.get(field, [])]
    new = fresh['project']; days = {s['day'] for s in new['sessions']}
    for p in parts:
        old_hires = {(s, o) for s, o, op in p['market_actions'] if s // 24 in days and op[0] == 'HIRE'}
        p['market_actions'] = [(s, o, op) for s, o, op in p['market_actions'] if (s, o) not in old_hires]
        p['cash_events'] = [e for e in p.get('cash_events', []) if (e['step'], e['order']) not in old_hires]
    for s in list(new['sessions']):
        if s['worker'] != 0: continue
        overlaps = [t for p in parts for t in p['sessions'] if t['worker'] == 0 and t['day'] == s['day'] and t['hour'] == 0]
        if overlaps:
            if len(overlaps) != 1:
                return dict(feasible=False, reason='retained_spawn_not_stationary')
            if reserves_center_spawn(overlaps[0], s['day']):
                new['sessions'].remove(s)
            elif not _delay_farmer_for_spawn(parts, s['day']):
                return dict(feasible=False, reason='retained_spawn_window')
    parts.append(new)
    orders = {}
    for index, p in enumerate(parts):
        for step, order, op in p['market_actions']:
            orders.setdefault(step, []).append((op[0] != 'HIRE', index, order))
    ranks = {}
    for step, items in orders.items():
        if len(items) > 10: return dict(feasible=False, reason='market_capacity')
        for rank, (_, index, old) in enumerate(sorted(items)): ranks[index, step, old] = rank
    for index, p in enumerate(parts):
        for key in ('stock_events', 'cash_events', 'sale_quotes'):
            for e in p.get(key, []):
                if key == 'sale_quotes' or e['phase'] == 'market': e['order'] = ranks[index, e['step'], e['order']]
        for e in p.get('opportunity_events', []):
            if e.get('purchase_ref') is not None:
                step, order = e['purchase_ref']; e['purchase_ref'] = (step, ranks[index, step, order])
        p['market_actions'] = [(step, ranks[index, step, order], op) for step, order, op in p['market_actions']]
    p = dict(id=f"herd-expansion:{obs['step']}:{uid}:{herd}:{end_day}:{care}", plot=tuple(parts[0]['plot']),
             plots=sorted(reserved | {tuple(tile) for _, tile in herd}), valuation_step=obs['step'], joint_product_trades=True)
    if flexible_fertilizer: p['id'] += ':flex-fertilizer'
    for key in ('sessions', 'market_actions', 'stock_events', 'cash_events', 'sale_quotes', 'opportunity_events', 'plot_releases', 'land_purchases'):
        p[key] = [e for part in parts for e in part.get(key, [])]
    p['market_actions'].sort(key=lambda x: x[:2])
    rows = {}
    for e in p['cash_events']: rows.setdefault(e['step'] // 24, dict(cost=0, receipts=0))['cost'] += e['cost']
    for q in p['sale_quotes']: rows.setdefault(q['step'] // 24, dict(cost=0, receipts=0))['receipts'] += q['receipts']
    p['cashflows'] = [dict(day=d, **r) for d, r in sorted(rows.items())]
    p['resource_opportunity_cost'] = sum(e['cost'] for e in p['opportunity_events'] if e.get('available_after', -1) <= obs['step'])
    p['net_value'] = sum(r['receipts'] - r['cost'] for r in rows.values()) - p['resource_opportunity_cost'] - action_value * sum(len(s['actions']) for s in p['sessions'])
    p = reprice_sales([p], market_scenario)[0]
    workers = dict(fresh['workers'])
    for part in parts:
        for s in part['sessions']:
            pos = [(4, 4), (5, 4), (4, 5), (5, 5), (4, 4)][s['worker']]
            workers.setdefault((s['day'], s['worker']), dict(position=pos, available_from=0 if s['worker'] == 0 else 1))
    check = check_portfolio([p], workers=workers, initial_cash=farm['money'])
    if not check['feasible']: return check
    check = check_stock_events(p['stock_events'], initial_stock={'shed': obs['private']['shed'], 'seeds': obs['private']['seeds'],
                                    **{f'hand:{i}': v for i, v in enumerate(obs['private']['inventories'])}})
    if not check['feasible']: return check
    if not future_workers(obs, [p])['feasible']: return dict(feasible=False, reason='unfunded_expansion')
    return dict(feasible=True, project=p, workers=workers)
