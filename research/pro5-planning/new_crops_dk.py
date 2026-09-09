"""Bounded crop alternatives on owned empty plots, permanent farmer only.

Current market is a conditional price scenario, not a forecast. A common
calendar and shared seed suppliers make alternatives compete for resources.
"""
from crop_service_model_bm import CROPS
from public_crop_proposals_bt import make_crop_proposal
from market_quote_ci import quote_sale
from pending_dg import MOVES


def new_crop_proposals(obs,*,limit,action_value,market_scenario,pending_projects=()):
    farm=obs['farms'][obs['player']]
    plots=[(x,y) for y,row in enumerate(farm['tiles']) for x,tile in enumerate(row) if tile is None]
    plots.sort(key=lambda p:(abs(p[0]-4)+abs(p[1]-4),p))
    calendar={d:dict(position=(4,4),available_from=0) for d in range(obs['day'],30)}
    calendar[obs['day']]=dict(position=tuple(farm['farmer']),available_from=obs['hour'])
    reserved=[s for p in pending_projects for s in p['sessions'] if s['worker']==0]
    # New work may follow today's reserved round trip. Its starting position
    # must still agree with the observed position accepted by the constructor.
    for s in sorted(reserved,key=lambda s:(s['day'],s['hour'])):
        if s['day']<obs['day']:continue
        x,y=s['start']
        for op in s['actions']:
            if op[0] in MOVES:
                dx,dy=MOVES[op[0]];nx,ny=x+dx,y+dy
                if 0<=nx<10 and 0<=ny<10:x,y=nx,ny
        calendar[s['day']]=dict(position=(x,y),available_from=s['hour']+len(s['actions']))
    if tuple(calendar[obs['day']]['position'])!=tuple(farm['farmer']):
        return dict(projects=[],workers={})
    # Reserve the minimum seed balance over the existing commitments. Future
    # purchases only release stock if they arrive before the reserved usage.
    # The common validator still checks real stocks and all new suppliers.
    balance=dict(obs['private']['seeds']);free=dict(balance)
    phases={'unit':0,'market':1,'night':2}
    events=[e for p in pending_projects for e in p.get('stock_events',[]) if e['step']>=obs['step']]
    for event in sorted(events,key=lambda e:(e['step'],phases[e['phase']],e['order'])):
        changes={}
        for account,item,delta in event['changes']:
            if account=='seeds':changes[item]=changes.get(item,0)+delta
        for item,delta in changes.items():
            balance[item]=balance.get(item,0)+delta
            free[item]=min(free.get(item,0),balance[item])
    seed_obs=dict(obs,private=dict(obs['private'],seeds={item:max(0,n) for item,n in free.items()}))
    projects={};workers={}
    for plot in plots[:limit]:
        for crop in sorted(CROPS):
            if crop not in market_scenario['params'] or crop not in market_scenario['inventory']:continue
            price=quote_sale(market_scenario['params'][crop],market_scenario['inventory'][crop],1)['receipts']
            proposal=make_crop_proposal(seed_obs,crop=crop,plot=plot,worker_id=0,calendar=calendar,
                sale_quotes={d:price for d in calendar},action_value=action_value)
            if not proposal['feasible']:continue
            # Availability of the worker is distinct from the start of this
            # new session: earlier reserved sessions remain part of the day.
            for d,uid in proposal['workers']:
                workers[d,uid]=dict(position=tuple(farm['farmer']) if d==obs['day'] else (4,4),
                                    available_from=obs['hour'] if d==obs['day'] else 0)
            for p in proposal['projects']:projects[p['id']]=p
    return dict(projects=list(projects.values()),workers=workers)
