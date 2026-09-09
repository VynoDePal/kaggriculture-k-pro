"""Same-day feeding alternatives from own observation, without implicit purchases.

Required groups implement an explicit preserve-at-risk-animals policy, not a
proof that every animal is worth preserving. Optional feeds have only action
cost here: callers must supply marginal production value before choosing them.
Routes reserve one worker from now; no care, collection or multi-stop tour yet.
"""
from crop_route_model_bo import SHED


def feeding_proposals(obs, *, action_value):
    farm=obs['farms'][obs['player']];private=obs['private']
    day=obs['day'];hour=obs['hour'];step=obs['step']
    positions=[farm['farmer']]+farm['hands']
    workers={(day,i):dict(position=tuple(pos),available_from=hour) for i,pos in enumerate(positions)}
    projects=[];groups={}
    if day>=29:return dict(projects=projects,required_groups=groups,workers=workers)

    def distance(a,b):return abs(a[0]-b[0])+abs(a[1]-b[1])

    def path(a,b):
        x,y=a;tx,ty=b;ops=[]
        while x!=tx:
            ops.append(('EAST' if x<tx else 'WEST',));x+=1 if x<tx else -1
        while y!=ty:
            ops.append(('SOUTH' if y<ty else 'NORTH',));y+=1 if y<ty else -1
        return ops

    for y,row in enumerate(farm['tiles']):
        for x,tile in enumerate(row):
            if not isinstance(tile,dict) or 'animal' not in tile or tile['fed_today']:continue
            plot=(x,y);alternatives=[]
            for uid,start in enumerate(positions):
                ops=[];events=[];hand=f'hand:{uid}'
                if private['inventories'][uid].get('WHEAT',0)>0:
                    ops.extend(path(start,plot))
                elif private['shed'].get('WHEAT',0)>0:
                    depot=min(SHED,key=lambda s:(distance(start,s)+distance(s,plot),s))
                    ops.extend(path(start,depot))
                    events.append(dict(step=step+len(ops),phase='unit',order=uid,
                                       changes=[('shed','WHEAT',-1),(hand,'WHEAT',1)]))
                    ops.append(('PICKUP','WHEAT',1));ops.extend(path(depot,plot))
                else:continue
                events.append(dict(step=step+len(ops),phase='unit',order=uid,changes=[(hand,'WHEAT',-1)]))
                ops.append(('FEED',))
                if len(ops)>24-hour:continue
                name=f'feed:{step}:{x}:{y}:{uid}';alternatives.append(name)
                projects.append(dict(id=name,plot=plot,net_value=-action_value*len(ops),
                    sessions=[dict(day=day,hour=hour,worker=uid,start=tuple(start),actions=ops)],
                    cashflows=[],stock_events=events,market_actions=[]))
            if tile['consecutive_unfed']>=1:groups[f'feed:{x}:{y}']=alternatives
    return dict(projects=projects,required_groups=groups,workers=workers)
