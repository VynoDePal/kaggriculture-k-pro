"""Existing-crop harvest, delivery and sale proposals with supplied price scenarios.

Future prices are not guaranteed; joint market effects are not priced here.
Shared shed capacity and market slots require the common portfolio validator.
"""
from crop_route_model_bo import SHED
from crop_service_model_bm import CROPS
from market_quote_ci import quote_sale


def harvest_proposals(obs, *, sale_prices=None, action_value, sale_order=0,market_scenario=None,fertilizer_only=False):
    if (sale_prices is None)==(market_scenario is None):
        raise ValueError('Supply exactly one pricing scenario')
    priced=sale_prices if market_scenario is None else market_scenario['params']
    if type(sale_order) is not int or not 0<=sale_order<10:raise ValueError('Invalid market slot')
    farm=obs['farms'][obs['player']];day=obs['day'];hour=obs['hour'];step=obs['step'];result=[]
    def path(a,b):
        x,y=a;tx,ty=b;ops=[]
        while x!=tx:ops.append(('EAST' if x<tx else 'WEST',));x+=1 if x<tx else -1
        while y!=ty:ops.append(('SOUTH' if y<ty else 'NORTH',));y+=1 if y<ty else -1
        return ops
    for y,row in enumerate(farm['tiles']):
        for x,tile in enumerate(row):
            if not isinstance(tile,dict):continue
            if fertilizer_only:
                if 'animal' not in tile or not tile.get('fertilizer_available'):continue
            elif tile.get('yield_units',0)<=0:continue
            animal='animal' in tile
            if fertilizer_only:
                crop='FERTILIZER';first=0;ongoing=True
            elif animal:
                crop={'COW':'MILK','SHEEP':'WOOL','GOOSE':'EGG'}[tile['animal']]
                first=0;ongoing=True
            elif tile.get('kind')=='PLANT':
                crop=tile['crop'];first=CROPS[crop][1];ongoing=CROPS[crop][3]>0
            else:continue
            if (not animal and day-tile['planted_day']<first) or crop not in priced:continue
            for uid,start in enumerate([farm['farmer']]+farm['hands']):
                ops=path(start,(x,y));harvest_step=step+len(ops)
                if not animal and tile['max_lifespan_step']>=0 and harvest_step>=tile['max_lifespan_step']:continue
                qty=1 if fertilizer_only else tile['yield_units']
                ops.append(('COLLECT_FERTILIZER' if fertilizer_only else 'HARVEST',))
                depot=min(SHED,key=lambda p:(abs(p[0]-x)+abs(p[1]-y),p))
                ops+=path((x,y),depot);delivery=step+len(ops);ops.append(('PLACE',crop,qty))
                if len(ops)>(23 if day==29 else 24)-hour:continue
                events=[dict(step=harvest_step,phase='unit',order=uid,changes=[(f'hand:{uid}',crop,qty)]),
                    dict(step=delivery,phase='unit',order=uid,changes=[(f'hand:{uid}',crop,-qty),('shed',crop,qty)]),
                    dict(step=delivery,phase='market',order=sale_order,changes=[('shed',crop,-qty)])]
                receipts=(qty*sale_prices[crop] if market_scenario is None else
                          quote_sale(market_scenario['params'][crop],market_scenario['inventory'][crop],qty)['receipts'])
                result.append(dict(id=f"{'fertilizer' if fertilizer_only else 'harvest'}:{step}:{x}:{y}:{uid}",plot=(x,y),
                    net_value=receipts-action_value*len(ops),satisfies=[] if ongoing else [f'water:{x}:{y}'],
                    sessions=[dict(day=day,hour=hour,worker=uid,start=tuple(start),actions=ops)],
                    cashflows=[dict(day=day,cost=0,receipts=receipts)],stock_events=events,
                    sale_quotes=[dict(step=delivery,order=sale_order,item=crop,quantity=qty,receipts=receipts)],
                    market_actions=[(delivery,sale_order,('SELL',crop,qty))]))
    return result
