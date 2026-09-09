"""Crop blocks appended to retained, already financed daily hand calendars.

No hire or retained unit action is added/removed/moved. Only owned empty plots
at canonical day start are supported. Routes follow all retained work on their
worker/day; all days of service must have their own funded canonical hire.
This is a bounded service constructor, not an optimal whole-farm schedule.
"""
import copy

from crop_service_model_bm import CROPS, crop_service_plan
from public_crop_proposals_bt import make_crop_proposal
from future_workers_do import future_workers
from hiring_cb import hire_scenario
from pending_dg import MOVES
from market_quote_ci import quote_sale
from joint_sales_ck import reprice_sales
from portfolio_reservations_bp import check_portfolio
from stock_reservations_bq import check_stock_events

SPAWNS = ((4, 4), (5, 4), (4, 5), (5, 5), (4, 4))
FIELDS = ('sessions', 'market_actions', 'cash_events', 'stock_events',
          'sale_quotes', 'opportunity_events', 'plot_releases', 'land_purchases')


def copy_project_records(projects):
    """Own editable records, sharing unchanged routes/stock payloads read-only.

As with FA/CK/FB, callers must copy a route before changing its actions. The
constructors below only edit event ordinals and append newly built sessions.
"""
    result = []
    for source in projects:
        p = dict(source)
        for field in FIELDS:
            p[field] = list(source.get(field, [])) if field == 'market_actions' else [dict(e) for e in source.get(field, [])]
        p['cashflows'] = [dict(e) for e in source['cashflows']]
        result.append(p)
    return result


def reuse_candidates(obs, *, pending_projects, limit, action_value, market_scenario):
    """Bounded homogeneous blocks, sharing the least occupied paid workers.

The constructor can append to busy workers too. This generator compares one
and two least-loaded hands, not every assignment/permutation or crop mixture.
"""
    farm = obs['farms'][obs['player']]
    if obs['hour'] or farm['hands'] or not pending_projects: return []
    n = sum(op[0] == 'HIRE' and step == obs['step'] for p in pending_projects for step, _, op in p['market_actions'])
    if not 1 <= n <= 4: return []
    load = {uid: sum(len(s['actions']) for p in pending_projects for s in p['sessions'] if s['worker'] == uid)
            for uid in range(1, n + 1)}
    ids = sorted(load, key=lambda uid: (load[uid], uid))
    reserved = {tuple(t) for p in pending_projects for t in p.get('plots', [p['plot']])}
    plots = [(x, y) for y, row in enumerate(farm['tiles']) for x, tile in enumerate(row) if tile is None and (x, y) not in reserved]
    plots.sort(key=lambda t: (abs(t[0]-4) + abs(t[1]-4), t))
    result = []
    for crop in sorted(set(CROPS) & set(market_scenario['params']) & set(market_scenario['inventory'])):
        for size in sorted({1, min(2, limit), min(limit, len(plots))}):
            if size < 1 or size > len(plots): continue
            for count in range(1, min(2, n, size) + 1):
                crops = [(crop, plot, ids[i % count]) for i, plot in enumerate(plots[:size])]
                r = reuse_paid_hands(obs, pending_projects=pending_projects, crops=crops,
                                    action_value=action_value, market_scenario=market_scenario)
                if r['feasible']: result.append(r['project'])
    return result


def _finish(session):
    x, y = session['start']
    for op in session['actions']:
        if op[0] in MOVES:
            dx, dy = MOVES[op[0]]; nx, ny = x + dx, y + dy
            if 0 <= nx < 10 and 0 <= ny < 10: x, y = nx, ny
    return dict(position=(x, y), available_from=session['hour'] + len(session['actions']))


def _free_seeds(obs, parts):
    balance = dict(obs['private']['seeds']); free = dict(balance)
    phases = {'unit': 0, 'market': 1, 'night': 2}
    for e in sorted((e for p in parts for e in p['stock_events']),
                    key=lambda e: (e['step'], phases[e['phase']], e['order'])):
        for account, item, n in e['changes']:
            if account == 'seeds':
                balance[item] = balance.get(item, 0) + n
                free[item] = min(free.get(item, 0), balance[item])
    return {item: max(0, n) for item, n in free.items()}


def reuse_paid_hands(obs, *, pending_projects, crops, action_value, market_scenario):
    farm = obs['farms'][obs['player']]
    if not pending_projects or obs['hour'] or farm['hands'] or farm['hires_today'] or tuple(farm['farmer']) != (4, 4):
        return dict(feasible=False, reason='requires_funded_day_start')
    if not crops or len(crops) > 10: return dict(feasible=False, reason='unsupported_crop_count')
    if not future_workers(obs, pending_projects)['feasible']:
        return dict(feasible=False, reason='invalid_retained_funding')
    parts = copy_project_records(pending_projects)
    reserved = {tuple(t) for p in parts for t in p.get('plots', [p['plot']])}
    hires = {}
    for p in parts:
        for step, order, op in p['market_actions']:
            if op[0] == 'HIRE': hires[step // 24] = hires.get(step // 24, 0) + 1
    n = hires.get(obs['day'], 0)
    if not 1 <= n <= 4: return dict(feasible=False, reason='unfunded_crop_service')
    projection = hire_scenario(obs, count=n)
    if not projection['feasible']: return projection
    for crop, tile, uid in crops:
        tile = tuple(tile)
        if type(uid) is not int or not 1 <= uid <= n: return dict(feasible=False, reason='unfunded_crop_service')
        if crop not in CROPS: return dict(feasible=False, reason='unsupported_crop')
        if tile in reserved: return dict(feasible=False, reason='reserved_plot')
        plan = crop_service_plan(crop, obs['day'])
        days = sorted({d for d, _ in plan['actions']})
        if any(hires.get(d, 0) < uid for d in days):
            return dict(feasible=False, reason='unfunded_crop_service')
        calendar = {d: dict(position=SPAWNS[uid], available_from=1) for d in days}
        for s in sorted((s for p in parts for s in p['sessions'] if s['worker'] == uid and s['day'] in calendar),
                        key=lambda s: (s['day'], s['hour'])):
            calendar[s['day']] = _finish(s)
        if not days: return dict(feasible=False, reason='no_harvest_before_end')
        projected = copy.deepcopy(projection['observation'])
        # Only a route-constructor input: this position is reached by retained
        # actions, which are kept and checked from the real spawn below.
        projected['farms'][obs['player']]['hands'][uid - 1] = list(calendar[obs['day']]['position'])
        projected['private']['seeds'] = _free_seeds(obs, parts)
        price = quote_sale(market_scenario['params'][crop], market_scenario['inventory'][crop], 1)['receipts']
        r = make_crop_proposal(projected, crop=crop, plot=tile, worker_id=uid, calendar=calendar,
                               sale_quotes=dict.fromkeys(days, price), action_value=action_value)
        if not r['feasible']: return r
        if CROPS[crop][3] == 0:
            consumer = r['projects'][0]
            consumer['plot_releases'] = [dict(plot=tile, after_step=max(24*s['day'] + s['hour'] + len(s['actions']) for s in consumer['sessions']))]
        parts.extend(r['projects']); reserved.add(tile)
    return combine_funded_projects(obs, parts=parts, plots=reserved,
                                    project_id=f"reused-paid-hands:{obs['step']}:{crops}",
                                    action_value=action_value, market_scenario=market_scenario)


def combine_funded_projects(obs, *, parts, plots, project_id, action_value, market_scenario):
    """Compose owned mutable copies; no unit task or wage is removed or moved.

Callers must own the event records passed here. They may share action sequences
read-only. This common composition keeps livestock/crop purchases, quotes,
funding proofs and retained ownership guards on the same canonical timeline.
"""
    farm = obs['farms'][obs['player']]
    # Unique market ordinals, preserving retained order and canonical HIRE
    # prefix. Purchase references refer to actual orders, not stale ordinals.
    slots = {}
    for index, p in enumerate(parts):
        for step, order, op in p['market_actions']:
            slots.setdefault(step, []).append((op[0] != 'HIRE', index, order))
    ranks = {}
    for step, items in slots.items():
        if len(items) > 10: return dict(feasible=False, reason='market_capacity')
        for rank, (_, index, old) in enumerate(sorted(items)): ranks[index, step, old] = rank
    for index, p in enumerate(parts):
        for field in ('stock_events', 'cash_events', 'sale_quotes'):
            for e in p.get(field, []):
                if field == 'sale_quotes' or e['phase'] == 'market': e['order'] = ranks[index, e['step'], e['order']]
        for e in p.get('opportunity_events', []):
            if e.get('purchase_ref') is not None:
                step, order = e['purchase_ref']; e['purchase_ref'] = (step, ranks.get((index, step, order), order))
        p['market_actions'] = [(step, ranks[index, step, order], op) for step, order, op in p['market_actions']]
    p = dict(id=project_id, plot=tuple(parts[0]['plot']),
             plots=sorted(plots), valuation_step=obs['step'], joint_product_trades=True)
    for field in FIELDS: p[field] = [e for part in parts for e in part.get(field, [])]
    p['market_actions'].sort(key=lambda x: x[:2])
    rows = {}
    for e in p['cash_events']: rows.setdefault(e['step']//24, dict(cost=0, receipts=0))['cost'] += e['cost']
    for q in p['sale_quotes']: rows.setdefault(q['step']//24, dict(cost=0, receipts=0))['receipts'] += q['receipts']
    p['cashflows'] = [dict(day=d, **r) for d, r in sorted(rows.items())]
    p['resource_opportunity_cost'] = sum(e['cost'] for e in p['opportunity_events'] if e.get('available_after', -1) <= obs['step'])
    p['net_value'] = sum(r['receipts'] - r['cost'] for r in rows.values()) - p['resource_opportunity_cost'] - action_value * sum(len(s['actions']) for s in p['sessions'])
    proof = future_workers(obs, [p])
    if not proof['feasible']: return dict(feasible=False, reason='invalid_combined_funding')
    workers = dict(proof['workers'])
    for s in p['sessions']:
        if s['worker'] == 0: workers[s['day'], 0] = dict(position=(4, 4), available_from=0)
    p = reprice_sales([p], market_scenario)[0]
    checked = check_portfolio([p], workers=workers, initial_cash=farm['money'])
    if not checked['feasible']: return checked
    checked = check_stock_events(p['stock_events'], initial_stock={'shed': obs['private']['shed'], 'seeds': obs['private']['seeds'],
                                 **{f'hand:{i}': v for i, v in enumerate(obs['private']['inventories'])}})
    if not checked['feasible']: return checked
    return dict(feasible=True, project=p, workers=workers)
