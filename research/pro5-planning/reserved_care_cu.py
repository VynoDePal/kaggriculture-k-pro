"""Validate a supplied farmer-only care calendar before crediting collected units.

Worker calendars must be truthful. No purchases, hires, carried initial wheat,
cash proceeds or automatic future production servicing are assumed. End-day
wheat carry is rejected conservatively rather than inventing night transfers.
"""
from portfolio_reservations_bp import check_portfolio
from crop_route_model_bo import SHED
from care_value_cs import care_delta
from stock_reservations_bq import check_stock_events


def reserved_care_delta(tile,day,*,plot,sessions,workers,shed_wheat,background_projects=(),initial_cash=0):
    initial_wheat=shed_wheat;events=[]
    if any(s['worker']!=0 or not day<=s['day']<=29 for s in sessions):
        return dict(feasible=False,reason='unsupported_calendar')
    for d in {s['day'] for s in sessions if s['day']>day}:
        worker=workers.get((d,0))
        if worker is not None and tuple(worker['position'])!=(4,4):
            return dict(feasible=False,reason='unreserved_trip_after_night')
    checked=check_portfolio(list(background_projects)+[dict(id='care-calendar',plot=plot,sessions=sessions,cashflows=[])],workers=workers,initial_cash=initial_cash)
    if not checked['feasible']:return checked
    moves={'EAST':(1,0),'WEST':(-1,0),'NORTH':(0,-1),'SOUTH':(0,1)}
    schedule={};hand=0;previous=None;today_care=False
    for s in sorted(sessions,key=lambda s:(s['day'],s['hour'])):
        d=s['day']
        if previous is not None and d!=previous and hand:return dict(feasible=False,reason='unreserved_night_transfer')
        previous=d;pos=tuple(s['start']);flags=schedule.setdefault(d,{})
        for offset,op in enumerate(s['actions']):
            step=24*d+s['hour']+offset
            if op[0] in moves:
                dx,dy=moves[op[0]];nxt=(pos[0]+dx,pos[1]+dy)
                if all(0<=v<10 for v in nxt):pos=nxt
            elif op[0]=='PICKUP' and tuple(op[1:])==('WHEAT',1):
                if pos not in SHED or shed_wheat<1:return dict(feasible=False,reason='wheat_unavailable')
                shed_wheat-=1;hand+=1
                events.append(dict(step=step,phase='unit',order=0,changes=[('shed','WHEAT',-1),('hand:0','WHEAT',1)]))
            elif op[0] in ('FEED','CARE','HARVEST'):
                if pos!=tuple(plot):return dict(feasible=False,reason='service_position')
                key={'FEED':'feed','CARE':'care','HARVEST':'collect'}[op[0]]
                if flags.get(key):return dict(feasible=False,reason='duplicate_service')
                if op[0]=='FEED':
                    if hand<1:return dict(feasible=False,reason='wheat_unavailable')
                    hand-=1
                    events.append(dict(step=step,phase='unit',order=0,changes=[('hand:0','WHEAT',-1)]))
                if d==day:
                    if op[0]!='CARE':return dict(feasible=False,reason='today_requires_separate_state_update')
                    today_care=True
                flags[key]=True
            elif op[0]!='PASS':return dict(feasible=False,reason='unsupported_action')
    if hand:return dict(feasible=False,reason='unreserved_night_transfer')
    if not today_care:return dict(feasible=False,reason='missing_today_care')
    for p in background_projects:
        for e in p.get('stock_events',[]):
            changes=[c for c in e['changes'] if c[1]=='WHEAT']
            if changes:events.append(dict(e,changes=changes))
    stock=check_stock_events(events,initial_stock={'shed':{'WHEAT':initial_wheat}})
    if not stock['feasible']:return stock
    schedule.pop(day,None)
    return dict(feasible=True,**care_delta(tile,day,schedule=schedule))
