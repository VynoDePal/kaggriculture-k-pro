"""Verify explicit same-day deposits for a reserved farmer care calendar.

No automatic night deposits, sales, purchases or unrelated production credited.
This proves delivered quantities in the supplied scenario, not cash profit.
"""
from reserved_care_cu import reserved_care_delta
from animal_night_model_bh import animal_after_night
from crop_route_model_bo import SHED
from stock_reservations_bq import check_stock_events


def validate_care_delivery(tile,day,*,plot,sessions,workers,initial_stock,shed_capacity=100):
    stripped=[dict(s,actions=[('PASS',) if op[0]=='PLACE' else op for op in s['actions']]) for s in sessions]
    checked=reserved_care_delta(tile,day,plot=plot,sessions=stripped,workers=workers,
                                shed_wheat=initial_stock.get('shed',{}).get('WHEAT',0))
    if not checked['feasible']:return checked
    product={'COW':'MILK','SHEEP':'WOOL','GOOSE':'EGG'}[tile['animal']]
    state=dict(tile);previous=day;holding=0;events=[]
    moves={'EAST':(1,0),'WEST':(-1,0),'NORTH':(0,-1),'SOUTH':(0,1)}
    for s in sorted(sessions,key=lambda s:(s['day'],s['hour'])):
        if s['day']!=previous and holding:return dict(feasible=False,reason='missing_deposit')
        while previous<s['day']:
            state=animal_after_night(state,previous);previous+=1
            if 'animal' not in state:return dict(feasible=False,reason='animal_escaped')
        pos=tuple(s['start'])
        for i,op in enumerate(s['actions']):
            changes=[];kind=op[0]
            if kind in moves:
                dx,dy=moves[kind];nxt=(pos[0]+dx,pos[1]+dy)
                if all(0<=v<10 for v in nxt):pos=nxt
            elif kind=='PICKUP':changes=[('shed','WHEAT',-1),('hand:0','WHEAT',1)]
            elif kind=='FEED':state['fed_today']=True;changes=[('hand:0','WHEAT',-1)]
            elif kind=='CARE':state['cared_today']=True
            elif kind=='HARVEST':
                qty=state['yield_units'];holding+=qty;state['yield_units']=0
                changes=[('hand:0',product,qty)]
            elif kind=='PLACE':
                if pos not in SHED or len(op)!=3 or op[1]!=product or op[2]!=holding or holding<=0:
                    return dict(feasible=False,reason='invalid_deposit')
                changes=[('hand:0',product,-holding),('shed',product,holding)];holding=0
            if changes:events.append(dict(step=s['day']*24+s['hour']+i,phase='unit',order=0,changes=changes))
    if holding:return dict(feasible=False,reason='missing_deposit')
    stock=check_stock_events(events,initial_stock=initial_stock,shed_capacity=shed_capacity)
    if not stock['feasible']:return stock
    return dict(feasible=True,extra_delivered=checked['extra_collected'],
                collection_deltas=checked['collection_deltas'],stock_events=events)
