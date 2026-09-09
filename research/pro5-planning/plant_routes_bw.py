"""Immediate single-plant watering routes under a preserve-existing-plants policy.

Only action cost is valued. Survival obligations are not an economic claim:
harvest/removal may ultimately be better and must be offered by the portfolio.
Future decay can invalidate a route; this initial generator excludes crops whose
decay has started rather than projecting an unsupported survival guarantee.
"""


def watering_proposals(obs, *, action_value):
    farm=obs['farms'][obs['player']];day=obs['day'];hour=obs['hour'];step=obs['step']
    positions=[farm['farmer']]+farm['hands']
    workers={(day,i):dict(position=tuple(pos),available_from=hour) for i,pos in enumerate(positions)}
    projects=[];groups={}
    for y,row in enumerate(farm['tiles']):
        for x,tile in enumerate(row):
            if not isinstance(tile,dict) or tile.get('kind')!='PLANT' or tile['watered_today']:continue
            alternatives=[]
            for uid,start in enumerate(positions):
                sx,sy=start;ops=[]
                while sx!=x:
                    ops.append(('EAST' if sx<x else 'WEST',));sx+=1 if sx<x else -1
                while sy!=y:
                    ops.append(('SOUTH' if sy<y else 'NORTH',));sy+=1 if sy<y else -1
                ops.append(('WATER',))
                if len(ops)>(23 if day==29 else 24)-hour:continue
                decay=tile['max_lifespan_step']
                if decay>=0 and step+len(ops)-1>=decay:continue
                name=f'water:{step}:{x}:{y}:{uid}';alternatives.append(name)
                projects.append(dict(id=name,plot=(x,y),net_value=-action_value*len(ops),
                    sessions=[dict(day=day,hour=hour,worker=uid,start=tuple(start),actions=ops)],
                    cashflows=[],stock_events=[],market_actions=[]))
            if day<29 and tile['consecutive_unwatered']>=1:
                groups[f'water:{x}:{y}']=alternatives
    return dict(projects=projects,required_groups=groups,workers=workers)
