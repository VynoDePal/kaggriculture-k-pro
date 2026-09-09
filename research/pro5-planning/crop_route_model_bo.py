"""Single-plot daily routes under explicit worker start positions and hours.

Caller must supply an owned, available plot, reserve a worker every service day,
buy seeds beforehand and reserve fertilizer/room in the shared shed. Each
harvest returns for deposit that day. No free night delivery is assumed.
"""

SHED=((4,4),(5,4),(4,5),(5,5))


def route_crop_service(plan, *, plot, start_positions, start_hours):
    def distance(a,b):return abs(a[0]-b[0])+abs(a[1]-b[1])

    def path(a,b):
        x,y=a;tx,ty=b;ops=[]
        while x!=tx:
            ops.append(('EAST' if x<tx else 'WEST',));x+=1 if x<tx else -1
        while y!=ty:
            ops.append(('SOUTH' if y<ty else 'NORTH',));y+=1 if y<ty else -1
        return ops

    daily={}
    crop=None
    for day,op in plan['actions']:
        daily.setdefault(day,[]).append(op)
        if op[0]=='PLANT':crop=op[1]
    harvests=dict(plan['harvests'])
    routes={};extra={};deliveries=[]
    for day,service in sorted(daily.items()):
        start=start_positions[day];hour=start_hours[day]
        if type(hour) is not int or not 0<=hour<24:
            raise ValueError('Invalid worker start hour')
        if not all(type(v) is int and 0<=v<10 for v in (*start,*plot)):
            raise ValueError('Position outside standard board')
        ops=[];current=start
        fertilizer=sum(op[0]=='FERTILIZE' for op in service)
        if fertilizer:
            depot=min(SHED,key=lambda s:(distance(current,s)+distance(s,plot),distance(current,s),s))
            ops.extend(path(current,depot));ops.append(('PICKUP','FERTILIZER',fertilizer));current=depot
        ops.extend(path(current,plot));ops.extend(service)
        if harvests.get(day,0):
            depot=min(SHED,key=lambda s:(distance(plot,s),s))
            ops.extend(path(plot,depot));ops.append(('PLACE',crop,harvests[day]))
        available=(23 if day==29 else 24)-hour
        if len(ops)>available:
            return dict(feasible=False,failed_day=day,required_actions=len(ops),available_actions=available)
        routes[day]=ops;extra[day]=len(ops)-len(service)
        if harvests.get(day,0):deliveries.append((day,harvests[day]))
    return dict(feasible=True,routes=routes,extra_actions=extra,deliveries=deliveries,
                plot=tuple(plot),start_positions={d:tuple(start_positions[d]) for d in routes},
                start_hours={d:start_hours[d] for d in routes})
