"""Verify a supported daily team of up to four hands before reserving labour.

Does not authorize arbitrary future worker IDs or assume a previous day's hand
survives the night. Portfolio collision and cash checks still apply afterwards.
"""

STATIONARY={'PASS','PICKUP','PLACE','FEED','CARE','WATER','HARVEST',
            'COLLECT_FERTILIZER','PLANT','FERTILIZE','BUILD_PASTURE','BUILD_COOP'}


def reserves_center_spawn(session,day):
    return (session['day']==day and session['hour']==0 and session['worker']==0
            and tuple(session['start'])==(4,4) and bool(session['actions'])
            and session['actions'][0][0] in STATIONARY)


def future_workers(obs,projects):
    workers={}
    for p in projects:
        for s in p['sessions']:
            if s['day']<obs['day'] or s['worker']==0:continue
            if s['day']==obs['day']:
                if s['worker']<=len(obs['farms'][obs['player']]['hands']):continue
                if obs['hour']!=0:return dict(feasible=False)
            d=s['day'];step=24*d
            if not 1<=s['worker']<=4 or s['hour']<1:return dict(feasible=False)
            orders=sorted(o for o in p.get('market_actions',[]) if o[0]//24==d and o[2][0]=='HIRE')
            n=len(orders)
            if not s['worker']<=n<=4 or any(o[0]!=step or o[1]!=i for i,o in enumerate(orders)):
                return dict(feasible=False)
            wages=sorted((e['order'],e['cost']) for e in p.get('cash_events',[])
                         if e['step']==step and e['phase']=='market' and e['order']<n)
            if wages!=list(enumerate([1,1,2,3][:n])):return dict(feasible=False)
            cash_cost=sum(e['cost'] for e in p.get('cash_events',[]) if e['step']//24==d)
            if sum(e['cost'] for e in p['cashflows'] if e['day']==d)!=cash_cost:return dict(feasible=False)
            spawn_reserved=any(reserves_center_spawn(t,d) for t in p['sessions'])
            if not spawn_reserved:return dict(feasible=False)
            workers[d,s['worker']]=dict(position=[(5,4),(4,5),(5,5),(4,4)][s['worker']-1],available_from=1)
    return dict(feasible=True,workers=workers)
