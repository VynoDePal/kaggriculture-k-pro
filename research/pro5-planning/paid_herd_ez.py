"""A new herd served by a specified hand, hired on every service day.

Canonical start-of-day only, farmer at the center. The single-action farmer
guards reserve spawn; a compositor may share an existing stationary guard but
must not remove it without proving the resulting spawn remains identical.
All preceding worker IDs are funded too; a compositor deduplicates their
existing wages. Paying unused prefix hands is conservative, not free labour.
"""
from herd_calendar_ex import herd_calendar
from hiring_cb import hire_scenario
from portfolio_reservations_bp import check_portfolio
from stock_reservations_bq import check_stock_events
from future_workers_do import future_workers


def paid_herd(obs, *, herd, end_day, action_value, market_scenario, care=False, worker_id=1, flexible_fertilizer=False):
    farm = obs['farms'][obs['player']]
    if type(worker_id) is not int or not 1 <= worker_id <= 4:
        return dict(feasible=False, reason='unsupported_herd_worker')
    if obs['hour'] != 0 or farm['hands'] or farm['hires_today'] or tuple(farm['farmer']) != (4, 4):
        return dict(feasible=False, reason='requires_canonical_first_hire')
    hire = hire_scenario(obs, count=worker_id)
    if not hire['feasible']: return hire
    projected = hire['observation']
    spawn = [(5, 4), (4, 5), (5, 5), (4, 4)][worker_id - 1]
    calendar = {d: dict(position=spawn, available_from=1) for d in range(obs['day'], end_day + 1)}
    r = herd_calendar(projected, herd=herd, end_day=end_day, action_value=action_value,
                      market_scenario=market_scenario, care=care, worker_id=worker_id, calendar=calendar,
                      flexible_fertilizer=flexible_fertilizer)
    if not r['feasible']: return r
    p = r['project']; p['id'] = 'paid-' + p['id']; p['valuation_step'] = obs['step']
    for row in p['cashflows']:
        d = row['day']; step = 24 * d
        p['sessions'].append(dict(day=d, hour=0, worker=0, start=(4, 4), actions=[('PASS',)]))
        r['workers'][d, 0] = dict(position=(4, 4), available_from=0)
        for order, wage in enumerate([1, 1, 2, 3][:worker_id]):
            p['market_actions'].append((step, order, ('HIRE',)))
            p['cash_events'].append(dict(step=step, phase='market', order=order, cost=wage))
            row['cost'] += wage; p['net_value'] -= wage
        p['net_value'] -= action_value
    check = check_portfolio([p], workers=r['workers'], initial_cash=farm['money'])
    if not check['feasible']: return check
    check = check_stock_events(p['stock_events'], initial_stock={'shed': obs['private']['shed'], f'hand:{worker_id}': {}})
    if not check['feasible']: return check
    if not future_workers(obs, [p])['feasible']: return dict(feasible=False, reason='unfunded_herd_worker')
    return r
