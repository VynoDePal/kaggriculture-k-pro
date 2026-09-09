"""Farmer care proposal conditional on a fixed future daily-feed/collection plan.

Not an autonomous policy: future sessions must be reserved against all other
projects. The counterfactual keeps future service identical except today's care.
"""
from animal_night_model_bh import animal_after_night
from care_delivery_cy import validate_care_delivery
from care_profit_cz import quote_care_profit


def care_proposal(obs,*,plot,collection_day,action_value,market_scenario):
    day=obs['day'];hour=obs['hour'];farm=obs['farms'][obs['player']];x,y=plot
    if not day<collection_day<=29:return dict(feasible=False,reason='collection_date')
    tile=farm['tiles'][y][x]
    if not isinstance(tile,dict) or 'animal' not in tile or not tile['fed_today'] or tile['cared_today']:
        return dict(feasible=False,reason='animal_not_ready_for_care')
    def path(a,b):
        sx,sy=a;tx,ty=b;ops=[]
        while sx!=tx:ops.append(('EAST' if sx<tx else 'WEST',));sx+=1 if sx<tx else -1
        while sy!=ty:ops.append(('SOUTH' if sy<ty else 'NORTH',));sy+=1 if sy<ty else -1
        return ops
    sessions=[];workers={}
    def add(d,start,h,ops):
        sessions.append(dict(day=d,hour=h,worker=0,start=tuple(start),actions=ops))
        workers[d,0]=dict(position=tuple(start),available_from=h)
    today_ops=path(farm['farmer'],plot)+[('CARE',)]
    add(day,farm['farmer'],hour,today_ops)
    state=animal_after_night(tile,day,care=True)
    for d in range(day+1,collection_day):
        add(d,(4,4),0,[('PICKUP','WHEAT',1)]+path((4,4),plot)+[('FEED',)])
        state=animal_after_night(state,d,feed=True)
    qty=state['yield_units'];product={'COW':'MILK','SHEEP':'WOOL','GOOSE':'EGG'}[tile['animal']]
    if qty<=0:return dict(feasible=False,reason='no_collection')
    add(collection_day,(4,4),0,path((4,4),plot)+[('HARVEST',)]+path(plot,(4,4))+[('PLACE',product,qty)])
    checked=validate_care_delivery(tile,day,plot=plot,sessions=sessions,workers=workers,
        initial_stock={'shed':obs['private']['shed']})
    if not checked['feasible']:return checked
    quote=quote_care_profit(checked,product=product,params=market_scenario['params'][product],
        inventory=market_scenario['inventory'][product],marginal_action_cost=action_value*len(today_ops))
    return dict(feasible=True,sessions=sessions,workers=workers,delivery=checked,**quote)
