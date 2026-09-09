"""Complete same-service portfolios differing only in today's care excursion.

Future daily feeding and one collection date are fixed, not globally optimal.
Owned wheat consumes stock; no second cash acquisition cost is invented.
"""
import copy
from public_care_da import care_proposal
from market_quote_ci import quote_sale


def care_project_pair(obs,*,plot,collection_day,action_value,market_scenario):
    proposal=care_proposal(obs,plot=plot,collection_day=collection_day,action_value=action_value,market_scenario=market_scenario)
    if not proposal['feasible']:return proposal
    product={'COW':'MILK','SHEEP':'WOOL','GOOSE':'EGG'}[obs['farms'][obs['player']]['tiles'][plot[1]][plot[0]]['animal']]
    projects=[]
    for care in (False,True):
        sessions=copy.deepcopy(proposal['sessions'] if care else proposal['sessions'][1:])
        events=copy.deepcopy(proposal['delivery']['stock_events'])
        delta=0 if care else proposal['delivery']['extra_delivered']
        for s in sessions:
            s['actions']=[(op[0],op[1],op[2]-delta) if op[0]=='PLACE' else op for op in s['actions']]
        for e in events:
            e['changes']=[(account,item,n-(delta if n>0 else -delta)) if item==product else (account,item,n)
                          for account,item,n in e['changes']]
        last=sessions[-1];sale_step=24*last['day']+last['hour']+len(last['actions'])-1
        quantity=last['actions'][-1][2]
        receipts=quote_sale(market_scenario['params'][product],market_scenario['inventory'][product],quantity)['receipts']
        events.append(dict(step=sale_step,phase='market',order=0,changes=[('shed',product,-quantity)]))
        projects.append(dict(id=f"care-pair:{obs['step']}:{plot}:{collection_day}:{int(care)}",plot=tuple(plot),sessions=sessions,
            net_value=receipts-action_value*sum(len(s['actions']) for s in sessions),
            cashflows=[dict(day=collection_day,cost=0,receipts=receipts)],stock_events=events,
            sale_quotes=[dict(step=sale_step,order=0,item=product,quantity=quantity,receipts=receipts)],
            market_actions=[(sale_step,0,('SELL',product,quantity))]))
    return dict(feasible=True,projects=projects,workers=proposal['workers'])
