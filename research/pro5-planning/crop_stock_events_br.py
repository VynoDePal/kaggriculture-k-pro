"""Translate a BM/BO crop scenario into BQ's physical reservations.

Requires the modeled plot to remain owned/available and the service yield model
to remain valid. Does not invent purchases, background flows or price receipts.
Sales are scheduled in the market phase of the complete crop deposit's turn.
"""


def compile_crop_stock_events(plan, route, *, start_hours, worker_id, sale_order):
    if not route['feasible']:raise ValueError('Cannot compile an infeasible route')
    if type(worker_id) is not int or worker_id<0:raise ValueError('Invalid worker')
    if type(sale_order) is not int or not 0<=sale_order<10:raise ValueError('Invalid market slot')
    moves={'EAST':(1,0),'WEST':(-1,0),'SOUTH':(0,1),'NORTH':(0,-1)}
    service_ops={'PLANT','WATER','FERTILIZE','HARVEST','DIG'}
    shed={(4,4),(4,5),(5,4),(5,5)}
    expected={}
    for day,op in plan['actions']:expected.setdefault(day,[]).append(tuple(op))
    if set(expected)!=set(route['routes']):raise ValueError('Missing service days')
    crops={op[1] for _,op in plan['actions'] if op[0]=='PLANT'}
    if not expected:return []
    if len(crops)!=1:raise ValueError('Expected one crop')
    crop=next(iter(crops));harvests=dict(plan['harvests']);events=[];hand=f'hand:{worker_id}';delivered=[]
    for day,ops in sorted(route['routes'].items()):
        if [tuple(op) for op in ops if op[0] in service_ops]!=expected[day]:
            raise ValueError('Route differs from projected service')
        hour=start_hours[day]
        if hour!=route['start_hours'][day] or hour+len(ops)>(23 if day==29 else 24):
            raise ValueError('Route timing mismatch')
        position=tuple(route['start_positions'][day])
        for offset,op in enumerate(ops):
            step=day*24+hour+offset;name=op[0];changes=[]
            if name in moves:
                dx,dy=moves[name];nx,ny=position[0]+dx,position[1]+dy
                if 0<=nx<10 and 0<=ny<10:position=(nx,ny)
                continue
            if name in service_ops and position!=tuple(route['plot']):
                raise ValueError('Service position mismatch')
            if name in ('PICKUP','PLACE') and position not in shed:
                raise ValueError('Shed position mismatch')
            if name=='PLANT':changes=[('seeds',crop,-1)]
            elif name=='FERTILIZE':changes=[(hand,'FERTILIZER',-1)]
            elif name=='HARVEST':changes=[(hand,crop,harvests[day])]
            elif name=='PICKUP':
                if op[1]!='FERTILIZER':raise ValueError('Unexpected pickup item')
                changes=[('shed',op[1],-op[2]),(hand,op[1],op[2])]
            elif name=='PLACE':
                if op[1]!=crop or op[2]!=harvests.get(day):raise ValueError('Deposit does not match harvest')
                changes=[(hand,crop,-op[2]),('shed',crop,op[2])]
            elif name not in ('WATER','DIG'):raise ValueError('Unsupported route action')
            if changes:events.append(dict(step=step,phase='unit',order=worker_id,changes=changes))
            if name=='PLACE':
                delivered.append((day,op[2]))
                events.append(dict(step=step,phase='market',order=sale_order,changes=[('shed',crop,-op[2])]))
    if delivered!=sorted(plan['harvests']) or delivered!=sorted(route['deliveries']):
        raise ValueError('Reported delivery differs from route deposits')
    return events
