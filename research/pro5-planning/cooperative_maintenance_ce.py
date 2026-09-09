"""Greedy complementary urgent tours; proposals still require joint validation.

Sequential worker allocation reserves only consumable inputs, never future
production. Canonical worker order is a heuristic, not an optimum guarantee.
"""
import copy
from combined_maintenance_bx import _singles


def complementary_proposals(obs, *, action_value, max_stops=6):
    base=_singles(obs,action_value)
    groups={g:[] for g in base['required_groups']};projects=[]
    state=copy.deepcopy(obs);farm=state['farms'][state['player']]
    for uid in range(1+len(farm['hands'])):
        state['step']=obs['step'];state['hour']=obs['hour']
        start=tuple(farm['farmer'] if uid==0 else farm['hands'][uid-1])
        actions=[];events=[];plots=[];covered=[]
        for _ in range(max_stops):
            available=_singles(state,action_value)
            urgent={pid:g for g,ids in available['required_groups'].items() for pid in ids}
            choices=[p for p in available['projects'] if p['sessions'][0]['worker']==uid and p['id'] in urgent]
            if not choices:break
            chosen=min(choices,key=lambda p:(len(p['sessions'][0]['actions']),p['id']))
            ops=chosen['sessions'][0]['actions'];x,y=chosen['plot']
            actions+=ops;events+=chosen['stock_events'];plots.append((x,y));covered.append(urgent[chosen['id']])
            if uid==0:farm['farmer']=[x,y]
            else:farm['hands'][uid-1]=[x,y]
            farm['tiles'][y][x]['fed_today' if ops[-1][0]=='FEED' else 'watered_today']=True
            for event in chosen['stock_events']:
                for account,item,delta in event['changes']:
                    stock=state['private']['shed'] if account=='shed' else state['private']['inventories'][int(account.split(':')[1])]
                    stock[item]=stock.get(item,0)+delta
            state['step']+=len(ops);state['hour']+=len(ops)
            if state['hour']>=24:break
        if not actions:continue
        name=f"cooperative:{obs['step']}:{uid}"
        projects.append(dict(id=name,plot=plots[0],plots=plots,net_value=-action_value*len(actions),
            sessions=[dict(day=obs['day'],hour=obs['hour'],worker=uid,start=start,actions=actions)],
            stock_events=events,cashflows=[],market_actions=[]))
        for g in covered:groups[g].append(name)
    return dict(projects=projects,required_groups=groups,workers=base['workers'],truncated=False)
