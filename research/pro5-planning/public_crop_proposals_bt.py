"""Build one new-crop proposal from own public observation and a reserved calendar.

Calendar availability, renewal of hired hands, background maintenance and sale
quotes are explicit caller responsibilities. Only currently owned empty plots
and currently present workers are considered. Fertilizer purchases are not yet
proposed; fertilized scenarios require enough already-owned fertilizer.
"""
from crop_service_model_bm import crop_service_plan
from crop_route_model_bo import route_crop_service
from crop_cashflow_bn import quote_crop_plan
from crop_stock_events_br import compile_crop_stock_events


def make_crop_proposal(obs, *, crop, plot, worker_id, calendar, sale_quotes,
                       action_value, fertilized=False, seed_order=0, sale_order=0,clear_before_plant=False):
    if type(clear_before_plant) is not bool:raise ValueError('Invalid clearing option')
    player=obs['player'];farm=obs['farms'][player];private=obs['private']
    positions=[farm['farmer']]+farm['hands'];day=obs['day'];hour=obs['hour'];step=obs['step']
    if type(worker_id) is not int or not 0<=worker_id<len(positions):
        return dict(feasible=False,reason='worker_unavailable')
    x,y=plot
    if not 0<=x<10 or not 0<=y<10 or farm['tiles'][y][x] is not None:
        return dict(feasible=False,reason='plot_unavailable')
    plan=crop_service_plan(crop,day,fertilized=fertilized)
    if not plan['harvests']:return dict(feasible=False,reason='no_harvest_before_end')
    if clear_before_plant:
        plan['actions'].insert(0,(day,('DIG',)))
    days=sorted({d for d,op in plan['actions']})
    if any(d not in calendar for d in days):return dict(feasible=False,reason='calendar_unavailable')
    if tuple(calendar[day]['position'])!=tuple(positions[worker_id]):
        return dict(feasible=False,reason='current_position_mismatch')
    fertilizer=sum(op[0]=='FERTILIZE' for _,op in plan['actions'])
    if fertilizer>private['shed'].get('FERTILIZER',0):
        return dict(feasible=False,reason='fertilizer_unavailable')
    buy_seed=private['seeds'].get(crop,0)<1
    hours={d:calendar[d]['available_from'] for d in days}
    hours[day]=max(hours[day],hour+int(buy_seed))
    if hours[day]>=24:return dict(feasible=False,reason='no_planting_slot_after_purchase')
    if any(hours[d]>=(23 if d==29 else 24) for d in days):
        return dict(feasible=False,reason='no_future_service_slot')
    route=route_crop_service(plan,plot=plot,start_positions={d:calendar[d]['position'] for d in days},start_hours=hours)
    if not route['feasible']:return dict(feasible=False,reason='route_infeasible',detail=route)
    # Acquisition costs belong to supplier projects, not to consumption again.
    consumption_plan=dict(plan,seed_cost=0)
    quote=quote_crop_plan(consumption_plan,sales=[(d,n,sale_quotes[d]) for d,n in route['deliveries']],
                          fertilizer_cost=0,action_value=action_value,extra_actions=route['extra_actions'])
    events=compile_crop_stock_events(plan,route,start_hours=hours,worker_id=worker_id,sale_order=sale_order)
    consumer=dict(id=f'crop:{step}:{worker_id}:{x}:{y}:{crop}:{int(fertilized)}',plot=tuple(plot),
        net_value=quote['net_value'],
        sessions=[dict(day=d,hour=hours[d],worker=worker_id,start=route['start_positions'][d],actions=ops)
                  for d,ops in route['routes'].items()],
        cashflows=[dict(day=d,cost=row['cost'],receipts=row['receipts']) for d,row in enumerate(quote['daily'])],
        stock_events=events,
        sale_quotes=[dict(step=e['step'],order=e['order'],item=crop,quantity=-e['changes'][0][2],
                          receipts=-e['changes'][0][2]*sale_quotes[e['step']//24]) for e in events if e['phase']=='market'],
        market_actions=[(e['step'],e['order'],('SELL',crop,-e['changes'][0][2])) for e in events if e['phase']=='market'])
    projects=[consumer]
    if clear_before_plant:consumer['id']+=':clear'
    if buy_seed:
        if type(seed_order) is not int or not 0<=seed_order<10:raise ValueError('Invalid seed market slot')
        cost=plan['seed_cost']
        projects.append(dict(id=f'seed:{step}:{crop}',plot=('seed_purchase',step,crop),net_value=-cost,
            sessions=[],cashflows=[dict(day=day,cost=cost,receipts=0)],
            cash_events=[dict(step=step,phase='market',order=seed_order,cost=cost)],
            stock_events=[dict(step=step,phase='market',order=seed_order,changes=[('seeds',crop,1)])],
            market_actions=[(step,seed_order,('BUY_SEED',crop,1))]))
    workers={(d,worker_id):dict(position=tuple(calendar[d]['position']),available_from=calendar[d]['available_from']) for d in days}
    return dict(feasible=True,projects=projects,workers=workers)
