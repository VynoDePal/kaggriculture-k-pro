"""Collect ready animal product and fertilizer on a single transport route."""
import copy
from harvest_cg import harvest_proposals
from market_quote_ci import quote_sale


def dual_collect_proposals(obs,*,action_value,sale_prices=None,market_scenario=None):
    priced=sale_prices if market_scenario is None else market_scenario['params']
    if 'FERTILIZER' not in priced:return []
    result=[]
    for original in harvest_proposals(obs,action_value=action_value,sale_prices=sale_prices,market_scenario=market_scenario):
        x,y=original['plot'];tile=obs['farms'][obs['player']]['tiles'][y][x]
        if 'animal' not in tile or not tile.get('fertilizer_available'):continue
        p=copy.deepcopy(original);s=p['sessions'][0];ops=s['actions'];uid=s['worker']
        if s['hour']+len(ops)+2>(23 if obs['day']==29 else 24):continue
        index=next(i for i,op in enumerate(ops) if op[0]=='HARVEST')
        harvest_step=24*s['day']+s['hour']+index
        ops.insert(index+1,('COLLECT_FERTILIZER',));ops.append(('PLACE','FERTILIZER',1))
        for event in p['stock_events']:
            if event['step']>harvest_step:event['step']+=1
        p['market_actions']=[(step+1,order,op) for step,order,op in p['market_actions']]
        for q in p['sale_quotes']:q['step']+=1
        end=24*s['day']+s['hour']+len(ops)-1
        p['stock_events']+= [dict(step=harvest_step+1,phase='unit',order=uid,changes=[(f'hand:{uid}','FERTILIZER',1)]),
            dict(step=end,phase='unit',order=uid,changes=[(f'hand:{uid}','FERTILIZER',-1),('shed','FERTILIZER',1)]),
            dict(step=end,phase='market',order=0,changes=[('shed','FERTILIZER',-1)])]
        receipts=(sale_prices['FERTILIZER'] if market_scenario is None else
            quote_sale(market_scenario['params']['FERTILIZER'],market_scenario['inventory']['FERTILIZER'],1)['receipts'])
        p['market_actions'].append((end,0,('SELL','FERTILIZER',1)))
        p['sale_quotes'].append(dict(step=end,order=0,item='FERTILIZER',quantity=1,receipts=receipts))
        p['cashflows'][0]['receipts']+=receipts;p['net_value']+=receipts-2*action_value
        p['id']='dual-'+p['id'];result.append(p)
    return result
