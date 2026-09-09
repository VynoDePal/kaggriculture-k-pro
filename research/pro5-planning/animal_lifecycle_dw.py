"""Installation plus a reserved daily-feed/collection calendar.

Scenario values, not price forecasts. Uses owned shed wheat, a permanent farmer,
and explicit daily deposits/sales. No income for the animal left at the horizon.
Not yet an autonomous purchase policy or an optimal feeding schedule.
"""
from animal_install_dv import animal_installation, ANIMALS
from animal_night_model_bh import animal_after_night
from portfolio_reservations_bp import check_portfolio
from stock_reservations_bq import check_stock_events
from market_quote_ci import quote_sale
from joint_sales_ck import reprice_sales


def animal_lifecycle(obs, *, animal, plot, end_day, action_value, market_scenario):
    day=obs['day'];farm=obs['farms'][obs['player']];private=obs['private']
    if not day < end_day <= 29:
        return dict(feasible=False, reason='collection_date')
    wheat=end_day-day
    if private['shed'].get('WHEAT',0)<wheat:
        return dict(feasible=False, reason='unfunded_feed_stock')
    result=animal_installation(obs,animal=animal,plot=plot,action_value=action_value)
    if not result['feasible']:return result
    p=result['project'];p['id']=f"lifecycle:{obs['step']}:{plot}:{animal}:{end_day}"
    product={'COW':'MILK','SHEEP':'WOOL','GOOSE':'EGG'}[animal]
    state=dict(kind=ANIMALS[animal][1],animal=animal,placed_day=day,yield_units=0,
               consecutive_unfed=0,fed_today=False,cared_today=False,
               fertilizer_available=False,pending_care_bonus=0)
    workers={};p['sale_quotes']=[];p['opportunity_events']=[]
    wheat_inventory=market_scenario['inventory']['WHEAT']
    for d in range(day,end_day+1):
        if d==day:
            session=p['sessions'][0];position=tuple(plot)
        else:
            session=dict(day=d,hour=0,worker=0,start=(4,4),actions=[])
            p['sessions'].append(session);position=(4,4)
            p['cashflows'].append(dict(day=d,cost=0,receipts=0))
        workers[d,0]=dict(position=tuple(session['start']),available_from=session['hour'])
        def action(op, changes=None):
            step=24*d+session['hour']+len(session['actions'])
            session['actions'].append(op)
            if changes:p['stock_events'].append(dict(step=step,phase='unit',order=0,changes=changes))
            return step
        def move(target):
            nonlocal position
            x,y=position;tx,ty=target
            while x!=tx:
                action(('EAST' if x<tx else 'WEST',));x+=1 if x<tx else -1
            while y!=ty:
                action(('SOUTH' if y<ty else 'NORTH',));y+=1 if y<ty else -1
            position=(x,y)
        if d<end_day:
            move((4,4))
            action(('PICKUP','WHEAT',1),[('shed','WHEAT',-1),('hand:0','WHEAT',1)])
            move(plot)
            feed_step=action(('FEED',),[('hand:0','WHEAT',-1)])
            foregone=quote_sale(market_scenario['params']['WHEAT'],wheat_inventory,1)
            wheat_inventory=foregone['inventory']
            p['opportunity_events'].append(dict(step=feed_step,cost=foregone['receipts']))
        else:move(plot)
        collected=[]
        if state['yield_units']:
            qty=state['yield_units']
            action(('HARVEST',),[('hand:0',product,qty)])
            collected.append((product,qty));state['yield_units']=0
        if state['fertilizer_available']:
            action(('COLLECT_FERTILIZER',),[('hand:0','FERTILIZER',1)])
            collected.append(('FERTILIZER',1));state['fertilizer_available']=False
        if collected:move((4,4))
        for item,qty in collected:
            step=action(('PLACE',item,qty),[('hand:0',item,-qty),('shed',item,qty)])
            p['market_actions'].append((step,0,('SELL',item,qty)))
            p['stock_events'].append(dict(step=step,phase='market',order=0,changes=[('shed',item,-qty)]))
            p['sale_quotes'].append(dict(step=step,order=0,item=item,quantity=qty,receipts=0))
        if d<end_day:state=animal_after_night(state,d,feed=True)
    check=check_portfolio([p],workers=workers,initial_cash=farm['money'])
    if not check['feasible']:return check
    check=check_stock_events(p['stock_events'],initial_stock={
        'shed':private['shed'],'hand:0':private['inventories'][0]})
    if not check['feasible']:return check
    opportunity=sum(e['cost'] for e in p['opportunity_events'])
    p['resource_opportunity_cost']=opportunity
    p['net_value']=-sum(row['cost'] for row in p['cashflows'])-opportunity-action_value*sum(
        len(s['actions']) for s in p['sessions'])
    p=reprice_sales([p],market_scenario)[0]
    return dict(feasible=True,project=p,workers=workers)
