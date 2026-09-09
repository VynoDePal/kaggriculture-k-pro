"""Bounded same-day maintenance alternatives (two stops by default).

Combines verified feed/water primitives, not arbitrary actions. No market or
night transition is simulated. Bounded enumeration is not a full routing solver.
"""
from collections import deque
from animal_routes_bv import feeding_proposals
from plant_routes_bw import watering_proposals


def _singles(obs, action_value):
    feed=feeding_proposals(obs,action_value=action_value)
    water=watering_proposals(obs,action_value=action_value)
    return dict(projects=feed['projects']+water['projects'],workers=feed['workers'],
                required_groups={**feed['required_groups'],**water['required_groups']})


def project_route_state(obs, project):
    """Project verified feed/water routes; copy only the branches we mutate.

    Other observation branches remain read-only. This is not a general game
    transition: it has no market, decay or night processing.
    """
    state=dict(obs);state['farms']=list(obs['farms'])
    farm=dict(obs['farms'][obs['player']]);state['farms'][obs['player']]=farm
    farm['hands']=list(farm['hands']);farm['tiles']=list(farm['tiles'])
    plots=project.get('plots',[project['plot']])
    session=project['sessions'][0];uid=session['worker']
    x,y=plots[-1]
    if uid==0:farm['farmer']=[x,y]
    else:farm['hands'][uid-1]=[x,y]
    for ty in {y for x,y in plots}:farm['tiles'][ty]=list(farm['tiles'][ty])
    for tx,ty in plots:
        tile=dict(farm['tiles'][ty][tx]);farm['tiles'][ty][tx]=tile
        tile['fed_today' if 'animal' in tile else 'watered_today']=True
    private=dict(obs['private']);state['private']=private
    private['shed']=dict(private['shed'])
    private['inventories']=[dict(inv) for inv in private['inventories']]
    for event in project['stock_events']:
        for account,item,delta in event['changes']:
            stock=private['shed'] if account=='shed' else private['inventories'][int(account.split(':')[1])]
            stock[item]=stock.get(item,0)+delta
    state['step']+=len(session['actions']);state['hour']+=len(session['actions'])
    return state


def maintenance_proposals(obs, *, action_value, max_stops=2, max_projects=10000):
    if type(max_stops) is not int or max_stops<1 or type(max_projects) is not int or max_projects<1:
        raise ValueError('Positive route and proposal budgets required')
    result=_singles(obs,action_value)
    result['truncated']=len(result['projects'])>max_projects
    result['projects']=result['projects'][:max_projects]
    kept={p['id'] for p in result['projects']}
    result['required_groups']={g:[pid for pid in ids if pid in kept] for g,ids in result['required_groups'].items()}
    originals=list(result['projects'])
    membership={p['id']:[g for g,ids in result['required_groups'].items() if p['id'] in ids]
                for p in originals}
    originals.sort(key=lambda p:(-len(membership[p['id']]),-p['net_value'],p['id']))
    queues={}
    for p in originals:queues.setdefault(p['sessions'][0]['worker'],deque()).append(p)
    active=deque(sorted(queues))
    while active:
        worker=active.popleft()
        if not queues[worker]:continue
        first=queues[worker].popleft()
        active.append(worker)
        first_plots=first.get('plots',[first['plot']])
        if len(first_plots)>=max_stops:continue
        session=first['sessions'][0];uid=session['worker'];ops=session['actions']
        if obs['hour']+len(ops)>=24:continue
        state=project_route_state(obs,first)
        later=_singles(state,action_value)
        urgent={pid for ids in later['required_groups'].values() for pid in ids}
        later['projects'].sort(key=lambda p:(p['id'] not in urgent,-p['net_value'],p['id']))
        extensions=[]
        for second in later['projects']:
            if second['sessions'][0]['worker']!=uid or second['plot'] in first_plots:continue
            if len(result['projects'])>=max_projects:
                result['truncated']=True
                return result
            name=f"pair:{first['id']}|{second['id']}"
            combined=dict(id=name,plot=first['plot'],plots=first_plots+[second['plot']],
                net_value=first['net_value']+second['net_value'],
                sessions=[dict(session,actions=ops+second['sessions'][0]['actions'])],
                cashflows=[],stock_events=first['stock_events']+second['stock_events'],market_actions=[])
            result['projects'].append(combined)
            groups=membership[first['id']]+[g for g,ids in later['required_groups'].items() if second['id'] in ids]
            membership[name]=list(set(groups))
            for group in set(groups):result['required_groups'][group].append(name)
            if len(combined['plots'])<max_stops:extensions.append(combined)
        # Reach complete tours before exhausting the budget on all short pairs.
        queues[worker].extendleft(reversed(extensions))
    return result
