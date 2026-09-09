"""One crop serviced by a freshly paid first hand on each service day.

Restricted to no existing hands/hires. Farmer PASS at each hire reserves the
spawn position. This is a complete funded alternative, not free future labour;
other portfolios must validate market slots, sessions and worker assumptions.
"""
from hiring_cb import hire_scenario
from public_crop_proposals_bt import make_crop_proposal
from portfolio_reservations_bp import check_portfolio


def funded_crop_proposal(obs,*,crop,plot,sale_prices,action_value):
    farm=obs['farms'][obs['player']]
    if farm['hands'] or farm['hires_today']:
        return dict(feasible=False,reason='requires_first_hand')
    hire=hire_scenario(obs,count=1)
    if not hire['feasible']:return hire
    projected=hire['observation'];day=obs['day']
    calendar={d:dict(position=(5,4),available_from=1) for d in range(day,30)}
    calendar[day]=dict(position=tuple(projected['farms'][obs['player']]['hands'][0]),available_from=projected['hour'])
    proposal=make_crop_proposal(projected,crop=crop,plot=plot,worker_id=1,calendar=calendar,
                               sale_quotes=sale_prices,action_value=action_value,seed_order=1)
    if not proposal['feasible']:return proposal
    parts=proposal['projects'];consumer=parts[0]
    days=sorted({s['day'] for s in consumer['sessions']})
    sessions=list(consumer['sessions']);orders=[o for p in parts for o in p['market_actions']]
    events=[e for p in parts for e in p['stock_events']]
    costs=[e for p in parts for e in p.get('cash_events',[])]
    workers=dict(proposal['workers'])
    for d in days:
        hour=obs['hour'] if d==day else 0;step=24*d+hour
        sessions.append(dict(day=d,hour=hour,worker=0,start=tuple(farm['farmer']) if d==day else (4,4),actions=[('PASS',)]))
        workers[d,0]=dict(position=tuple(farm['farmer']) if d==day else (4,4),available_from=hour)
        orders.append((step,0,('HIRE',)))
        costs.append(dict(step=step,phase='market',order=0,cost=1))
    rows={}
    for e in costs:rows.setdefault(e['step']//24,dict(cost=0,receipts=0))['cost']+=e['cost']
    for q in consumer['sale_quotes']:rows.setdefault(q['step']//24,dict(cost=0,receipts=0))['receipts']+=q['receipts']
    project=dict(id=f"funded-crop:{obs['step']}:{plot}:{crop}",plot=tuple(plot),sessions=sessions,
        cashflows=[dict(day=d,**row) for d,row in sorted(rows.items())],cash_events=costs,
        stock_events=events,market_actions=sorted(orders),sale_quotes=consumer['sale_quotes'],
        net_value=sum(row['receipts']-row['cost'] for row in rows.values())-action_value*sum(len(s['actions']) for s in sessions))
    checked=check_portfolio([project],workers=workers,initial_cash=farm['money'])
    if not checked['feasible']:return checked
    return dict(feasible=True,project=project,workers=workers)
