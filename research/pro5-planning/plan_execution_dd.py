"""Persistent executor for prevalidated portfolios, not an autonomous agent.

Checks dated positions and current stock reservations before emitting a turn.
Checks care/feed/water eligibility and exact reserved harvest yield. Does not
yet certify every operation, future prices or unreserved activities.
Caller must replan when requested; the cancelled portfolio cannot be resumed.
"""
import copy
from stock_reservations_bq import check_stock_events
from crop_service_model_bm import CROPS
from animal_install_dv import ANIMALS

MOVES={'EAST':(1,0),'WEST':(-1,0),'SOUTH':(0,1),'NORTH':(0,-1)}


def start_plan(projects):
    turns={};events={};costs={};end=-1
    for project in projects:
        for session in project['sessions']:
            pos=list(session['start'])
            for i,op in enumerate(session['actions']):
                step=24*session['day']+session['hour']+i
                row=turns.setdefault(str(step),dict(units={},market={}))
                uid=str(session['worker'])
                if uid in row['units']:raise ValueError('Overlapping unit actions')
                row['units'][uid]=dict(position=pos[:],action=list(op))
                if op[0] in MOVES:
                    dx,dy=MOVES[op[0]];pos=[pos[0]+dx,pos[1]+dy]
                end=max(end,step)
        for step,ordinal,op in project.get('market_actions',[]):
            row=turns.setdefault(str(step),dict(units={},market={}))
            if str(ordinal) in row['market']:raise ValueError('Overlapping market orders')
            row['market'][str(ordinal)]=list(op);end=max(end,step)
        for event in project['stock_events']:
            events.setdefault(str(event['step']),[]).append(copy.deepcopy(event))
        for event in project.get('cash_events',[]):
            key=str(event['step']);costs[key]=costs.get(key,0)+event['cost']
    return dict(turns=turns,events=events,costs=costs,projects=copy.deepcopy(projects),last_step=None,end=end,cancelled=False)


def next_action(obs,state,*,shed_capacity=100):
    step=obs['step'];farm=obs['farms'][obs['player']]
    idle=dict(farmer=['PASS'],hands=[['PASS'] for _ in farm['hands']],market=[])
    def reject(reason):
        return dict(action=idle,replan=True,reason=reason,state=dict(state,cancelled=True))
    if state['cancelled']:return reject('cancelled')
    if step>state['end']:return reject('finished')
    if state['last_step'] is not None and step!=state['last_step']+1:return reject('nonconsecutive_observation')
    # Conservative: do not prefinance purchases with same-turn expected sales.
    if state.get('costs',{}).get(str(step),0)>farm['money']:return reject('insufficient_cash')
    for project in state.get('projects', []):
        for purchase in project.get('land_purchases', []):
            if purchase['step'] == step and list(farm['unlocked_quadrants']) != list(purchase['owned_before']):
                return reject('land_ownership_changed')
    row=state['turns'].get(str(step),dict(units={},market={}))
    positions=[farm['farmer']]+farm['hands']
    for uid,entry in row['units'].items():
        if int(uid)>=len(positions) or list(positions[int(uid)])!=entry['position']:
            return reject('position_changed')
        op=entry['action'][0]
        if op=='DIG':
            x,y=entry['position'];tile=farm['tiles'][y][x]
            # Current planners use DIG only to insure a vacant future plot
            # against weeds, never to retire a crop, animal or building.
            if tile is not None and not(isinstance(tile,dict) and tile.get('kind')=='WEED'):
                return reject('clearing_state_changed')
        if op in ('BUILD_COOP','BUILD_PASTURE'):
            x,y=entry['position']
            if farm['tiles'][y][x] is not None:return reject('building_state_changed')
        if op=='PLACE' and entry['action'][1] in ANIMALS:
            x,y=entry['position'];tile=farm['tiles'][y][x]
            if not isinstance(tile,dict) or tile.get('kind')!=ANIMALS[entry['action'][1]][1] or 'animal' in tile:
                return reject('animal_structure_changed')
        if op=='COLLECT_FERTILIZER':
            x,y=entry['position'];tile=farm['tiles'][y][x]
            if not isinstance(tile,dict) or 'animal' not in tile or not tile.get('fertilizer_available'):
                return reject('fertilizer_state_changed')
        if op=='PLANT':
            x,y=entry['position']
            if farm['tiles'][y][x] is not None or entry['action'][1] not in CROPS:
                return reject('planting_state_changed')
        if op in ('CARE','FEED','WATER','HARVEST'):
            x,y=entry['position'];tile=farm['tiles'][y][x]
            if not isinstance(tile,dict):return reject('tile_changed')
            if op in ('CARE','FEED'):
                flag='cared_today' if op=='CARE' else 'fed_today'
                if 'animal' not in tile or tile[flag]:return reject('animal_service_changed')
            elif op=='WATER':
                if tile.get('kind')!='PLANT' or tile['watered_today']:return reject('watering_state_changed')
            else:
                if 'animal' in tile:
                    product={'COW':'MILK','SHEEP':'WOOL','GOOSE':'EGG'}[tile['animal']]
                elif tile.get('kind')=='PLANT':
                    product=tile['crop']
                    if obs['day']-tile['planted_day']<CROPS[product][1]:return reject('immature_crop')
                else:return reject('unharvestable_tile')
                expected=[(account,item,n) for e in state['events'].get(str(step),[])
                    if e['phase']=='unit' and e['order']==int(uid)
                    for account,item,n in e['changes']]
                if expected!=[(f'hand:{uid}',product,tile.get('yield_units',0))] or tile.get('yield_units',0)<=0:
                    return reject('harvest_changed')
    private=obs['private']
    stock={'shed':private['shed'],'seeds':private['seeds'],
           **{f'hand:{i}':hand for i,hand in enumerate(private['inventories'])}}
    checked=check_stock_events(state['events'].get(str(step),[]),initial_stock=stock,shed_capacity=shed_capacity)
    if not checked['feasible']:return reject(checked['reason'])
    action=dict(farmer=row['units'].get('0',{}).get('action',['PASS']),
        hands=[row['units'].get(str(i+1),{}).get('action',['PASS']) for i in range(len(farm['hands']))],
        market=[op for _,op in sorted(row['market'].items(),key=lambda pair:int(pair[0]))])
    return dict(action=action,replan=False,state=dict(state,last_step=step))
