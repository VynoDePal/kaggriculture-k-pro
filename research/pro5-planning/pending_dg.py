"""Remaining reservations for maintenance, crop and dated-purchase projects.

Cash expenditures require matching dated cash_events; refuse undated costs
instead of guessing which purchases have already been paid.
"""
import copy
import math

MOVES={'EAST':(1,0),'WEST':(-1,0),'SOUTH':(0,1),'NORTH':(0,-1)}


def remaining_projects(projects,*,step,action_value):
    result=[]
    for source in projects:
        opportunity_events=source.get('opportunity_events',[])
        if not math.isclose(sum(e['cost'] for e in opportunity_events
                               if e.get('available_after',-1)<=source.get('valuation_step',0)),
                            source.get('resource_opportunity_cost',0),abs_tol=1e-9):
            raise ValueError('Undated resource opportunity costs')
        daily={}
        for row in source['cashflows']:daily[row['day']]=daily.get(row['day'],0)+row['cost']
        dated={}
        for e in source.get('cash_events',[]):dated[e['step']//24]=dated.get(e['step']//24,0)+e['cost']
        if {d:c for d,c in daily.items() if c}!={d:c for d,c in dated.items() if c}:
            raise ValueError('Undated purchase costs')
        p=copy.deepcopy(source);sessions=[]
        p['plot']=tuple(p['plot'])
        if 'plots' in p:p['plots']=[tuple(plot) for plot in p['plots']]
        deadlines={}
        for e in p.get('plot_releases',[]):
            tile=tuple(e['plot']);deadlines[tile]=max(deadlines.get(tile,0),e['after_step'])
        active=set()
        tile_ops={'PLANT','WATER','FERTILIZE','HARVEST','FEED','CARE','COLLECT_FERTILIZER','BUILD_COOP','BUILD_PASTURE'}
        for s in p['sessions']:
            x,y=s['start']
            for i,op in enumerate(s['actions']):
                at=24*s['day']+s['hour']+i
                if op[0] in MOVES:
                    dx,dy=MOVES[op[0]];nx,ny=x+dx,y+dy
                    if 0<=nx<10 and 0<=ny<10:x,y=nx,ny
                elif at>=step and (op[0] in tile_ops or op[0]=='PLACE' and op[1] in ('COW','SHEEP','GOOSE')):
                    active.add((x,y))
        released={tile for tile,deadline in deadlines.items() if deadline<=step and tile not in active}
        if released and 'plots' in p:
            p['plots']=[plot for plot in p['plots'] if plot not in released or plot==p['plot']]
        if active-set(p.get('plots',[p['plot']])):
            p['plots']=list(dict.fromkeys(p.get('plots',[p['plot']])+sorted(active)))
        for s in p['sessions']:
            begin=24*s['day']+s['hour'];skip=max(0,step-begin)
            if skip>=len(s['actions']):continue
            x,y=s['start']
            for op in s['actions'][:skip]:
                if op[0] in MOVES:
                    dx,dy=MOVES[op[0]];nx,ny=x+dx,y+dy
                    if 0<=nx<10 and 0<=ny<10:x,y=nx,ny
            s.update(start=(x,y),hour=s['hour']+skip,actions=s['actions'][skip:]);sessions.append(s)
        p['sessions']=sessions
        p['stock_events']=[e for e in p['stock_events'] if e['step']>=step]
        p['market_actions']=[o for o in p.get('market_actions',[]) if o[0]>=step]
        p['sale_quotes']=[q for q in p.get('sale_quotes',[]) if q['step']>=step]
        p['cash_events']=[e for e in p.get('cash_events',[]) if e['step']>=step]
        p['opportunity_events']=[e for e in opportunity_events if e['step']>=step]
        p['valuation_step']=step
        p['resource_opportunity_cost']=sum(e['cost'] for e in p['opportunity_events']
            if e.get('available_after',-1)<=step)
        if not sessions and not p['market_actions']:continue
        receipts={}
        for q in p['sale_quotes']:receipts[q['step']//24]=receipts.get(q['step']//24,0)+q['receipts']
        costs={}
        for e in p['cash_events']:costs[e['step']//24]=costs.get(e['step']//24,0)+e['cost']
        p['cashflows']=[dict(day=d,cost=costs.get(d,0),receipts=receipts.get(d,0)) for d in sorted(set(receipts)|set(costs))]
        p['net_value']=sum(receipts.values())-sum(costs.values())-p['resource_opportunity_cost']-action_value*sum(len(s['actions']) for s in sessions)
        result.append(p)
    return result
