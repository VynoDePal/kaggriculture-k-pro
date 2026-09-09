"""Reprice explicit own-sale quotes jointly, optionally with known town demand.

Only annotated sales are supported; future adversary trades are not predicted.
Cashflow updates require a unique daily
row as in crop proposals. Returned values remain conditional scenario values.
"""
from market_quote_ci import quote_sale
from town_scenario_ep import consumed_between


def reprice_sales(projects, market_scenario):
    if any(p.get('joint_product_trades') for p in projects):
        from joint_trades_fb import reprice_trades
        return reprice_trades(projects, market_scenario)
    # Routes and stock events are read-only here; copy only modified fields.
    # Returned structural fields remain shared and must be treated as immutable.
    result=[dict(p,cashflows=[dict(row) for row in p['cashflows']],
                 sale_quotes=[dict(q) for q in p.get('sale_quotes',[])]) for p in projects]
    inventory=dict(market_scenario['inventory'])
    demand=market_scenario.get('known_town_demand');last_consumed={}
    action_keys=[{(s,o,tuple(op)) for s,o,op in p.get('market_actions',[])} for p in result]
    events=[];slots=set()
    for index,p in enumerate(result):
        for q in p.get('sale_quotes',[]):
            slot=(q['step'],q['order'])
            if slot in slots:raise ValueError('Duplicate sale slot')
            slots.add(slot);events.append((*slot,index,q))
    for step,order,index,q in sorted(events,key=lambda e:e[:3]):
        p=result[index];item=q['item']
        expected=(step,order,('SELL',item,q['quantity']))
        if expected not in action_keys[index]:
            raise ValueError('Quote without matching sale')
        if demand is not None:
            inventory[item]-=consumed_between(demand,item,last_consumed.get(item,demand['from_step']),step)
            last_consumed[item]=step
        quote=quote_sale(market_scenario['params'][item],inventory[item],q['quantity'])
        rows=[row for row in p['cashflows'] if row['day']==step//24]
        if len(rows)!=1:raise ValueError('Sale needs one daily cashflow row')
        delta=quote['receipts']-q['receipts']
        rows[0]['receipts']+=delta;p['net_value']+=delta
        q['receipts']=quote['receipts'];inventory[item]=quote['inventory']
    return result
