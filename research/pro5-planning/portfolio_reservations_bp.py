"""Check time, position, plot and cash compatibility of proposed projects.

Not an optimizer or complete game-state validator. Seed/fertilizer availability,
shed capacity, ownership, market execution and service legality remain separate
requirements. Plot exclusivity is conservative across the entire portfolio;
reuse after retirement is not yet scheduled. Daily cash costs precede receipts.
"""


def check_portfolio(projects, *, workers, initial_cash):
    moves={'EAST':(1,0),'WEST':(-1,0),'SOUTH':(0,1),'NORTH':(0,-1)}
    plots=set();sessions={};cashflows={}
    for project in projects:
        reserved=set(project.get('plots',[project['plot']]))
        reserved.add(project['plot'])
        if plots.intersection(reserved):return dict(feasible=False,reason='plot_overlap',project=project['id'])
        plots.update(reserved)
        for session in project['sessions']:
            key=(session['day'],session['worker'])
            sessions.setdefault(key,[]).append((session,project['id']))
        for event in project['cashflows']:
            row=cashflows.setdefault(event['day'],[0,0])
            row[0]+=event['cost'];row[1]+=event['receipts']
    for key,items in sorted(sessions.items()):
        if key not in workers:return dict(feasible=False,reason='missing_worker',key=key)
        worker=workers[key];position=tuple(worker['position']);end=worker['available_from']
        for session,pid in sorted(items,key=lambda pair:(pair[0]['hour'],pair[1])):
            hour=session['hour'];ops=session['actions'];limit=23 if key[0]==29 else 24
            if hour<worker['available_from'] or hour+len(ops)>limit:
                return dict(feasible=False,reason='outside_worker_window',project=pid,key=key)
            if hour<end:return dict(feasible=False,reason='worker_overlap',project=pid,key=key)
            if tuple(session['start'])!=position:
                return dict(feasible=False,reason='start_position_mismatch',project=pid,key=key)
            for op in ops:
                if op[0] in moves:
                    dx,dy=moves[op[0]];nx,ny=position[0]+dx,position[1]+dy
                    # Match official silent no-op on movement outside the board.
                    if 0<=nx<10 and 0<=ny<10:position=(nx,ny)
            end=hour+len(ops)
    cash=initial_cash
    for day,(cost,receipts) in sorted(cashflows.items()):
        cash-=cost
        if cash<0:return dict(feasible=False,reason='insufficient_cash',day=day,shortfall=-cash)
        cash+=receipts
    return dict(feasible=True,final_cash=cash)
