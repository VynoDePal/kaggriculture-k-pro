"""Animal lifecycle funded by owned wheat plus an explicit immediate purchase.

Buy prices assume no concurrent opponent order. Execution must revalidate the
observed delivered stock; this is not a guarantee of the opponent's actions.
"""
import copy
from animal_lifecycle_dw import animal_lifecycle
from market_quote_ci import quote_sale
from stock_reservations_bq import check_stock_events
from portfolio_reservations_bp import check_portfolio


def funded_animal_lifecycle(obs,*,animal,plot,end_day,action_value,market_scenario):
    if not obs['day']<end_day<=29:return dict(feasible=False,reason='collection_date')
    needed=end_day-obs['day'];owned=min(needed,obs['private']['shed'].get('WHEAT',0))
    missing=needed-owned;inventory=market_scenario['inventory']['WHEAT'];cost=0
    for _ in range(missing):
        inventory-=1
        cost+=quote_sale(market_scenario['params']['WHEAT'],inventory,1)['unit_prices'][0]
    projected=copy.deepcopy(obs)
    projected['private']['shed']['WHEAT']=obs['private']['shed'].get('WHEAT',0)+missing
    r=animal_lifecycle(projected,animal=animal,plot=plot,end_day=end_day,
                       action_value=action_value,market_scenario=market_scenario)
    if not r['feasible']:return r
    p=r['project'];p['id']='funded-'+p['id']
    old_opportunity=p['resource_opportunity_cost']
    resale=quote_sale(market_scenario['params']['WHEAT'],inventory,missing)['unit_prices']
    p['valuation_step']=obs['step']
    for event,price in zip(p['opportunity_events'][owned:],resale):
        event.update(cost=price,available_after=obs['step']+1)
    p['resource_opportunity_cost']=sum(e['cost'] for e in p['opportunity_events']
        if e.get('available_after',-1)<=p['valuation_step'])
    if missing:
        step=obs['step']
        p['market_actions'].append((step,1,('BUY_PRODUCT','WHEAT',missing)))
        p['cash_events'].append(dict(step=step,phase='market',order=1,cost=cost))
        p['cashflows'][0]['cost']+=cost
        p['stock_events'].append(dict(step=step,phase='market',order=1,changes=[('shed','WHEAT',missing)]))
    p['net_value']+=old_opportunity-p['resource_opportunity_cost']-cost
    check=check_portfolio([p],workers=r['workers'],initial_cash=obs['farms'][obs['player']]['money'])
    if not check['feasible']:return check
    check=check_stock_events(p['stock_events'],initial_stock={
        'shed':obs['private']['shed'],'hand:0':obs['private']['inventories'][0]})
    if not check['feasible']:return check
    return r
