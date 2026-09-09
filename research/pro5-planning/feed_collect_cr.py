"""Compose feeding then collection on the same animal before the same night."""
import copy
from animal_routes_bv import feeding_proposals
from harvest_cg import harvest_proposals
from dual_collect_du import dual_collect_proposals


def feed_collect_proposals(obs, *, action_value,sale_prices=None,market_scenario=None,fertilizer_only=False):
    result=[]
    for feed in feeding_proposals(obs,action_value=action_value)['projects']:
        session=feed['sessions'][0];ops=session['actions'];uid=session['worker'];x,y=feed['plot']
        if obs['hour']+len(ops)>=24:continue
        state=copy.deepcopy(obs);farm=state['farms'][state['player']]
        tile=farm['tiles'][y][x]
        if fertilizer_only:
            if not tile.get('fertilizer_available'):continue
        elif tile['yield_units']<=0:continue
        farm['tiles'][y][x]['fed_today']=True
        if uid==0:farm['farmer']=[x,y]
        else:farm['hands'][uid-1]=[x,y]
        for event in feed['stock_events']:
            for account,item,delta in event['changes']:
                stock=state['private']['shed'] if account=='shed' else state['private']['inventories'][int(account.split(':')[1])]
                stock[item]=stock.get(item,0)+delta
        state['hour']+=len(ops);state['step']+=len(ops)
        collections=harvest_proposals(state,action_value=action_value,sale_prices=sale_prices,market_scenario=market_scenario,fertilizer_only=fertilizer_only)
        if not fertilizer_only:collections+=dual_collect_proposals(state,action_value=action_value,sale_prices=sale_prices,market_scenario=market_scenario)
        for harvest in collections:
            if harvest['plot']!=(x,y) or harvest['sessions'][0]['worker']!=uid:continue
            prefix='feed-fertilizer' if fertilizer_only else ('feed-dual' if harvest['id'].startswith('dual-') else 'feed-collect')
            result.append(dict(harvest,id=f"{prefix}:{obs['step']}:{x}:{y}:{uid}",
                net_value=feed['net_value']+harvest['net_value'],satisfies=[f'feed:{x}:{y}'],
                sessions=[dict(session,actions=ops+harvest['sessions'][0]['actions'])],
                stock_events=feed['stock_events']+harvest['stock_events']))
    return result
