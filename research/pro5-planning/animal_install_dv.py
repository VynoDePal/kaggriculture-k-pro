"""Paid animal setup with physical transport; no future income credited."""
from crop_route_model_bo import SHED
from stock_reservations_bq import check_stock_events

ANIMALS={'COW':(400,'PASTURE'),'SHEEP':(500,'PASTURE'),'GOOSE':(300,'COOP')}


def animal_installation(obs,*,animal,plot,action_value):
    cost,structure=ANIMALS[animal];farm=obs['farms'][obs['player']];private=obs['private']
    x,y=plot
    if not 0<=x<10 or not 0<=y<10:return dict(feasible=False,reason='plot_outside')
    tile=farm['tiles'][y][x]
    if tile is not None and not (isinstance(tile,dict) and tile.get('kind')==structure and 'animal' not in tile):
        return dict(feasible=False,reason='plot_unavailable')
    owned=private['shed'].get(animal,0)>0;cost=0 if owned else cost
    if farm['money']<cost:return dict(feasible=False,reason='insufficient_cash')
    def path(a,b):
        sx,sy=a;tx,ty=b;ops=[]
        while sx!=tx:ops.append(('EAST' if sx<tx else 'WEST',));sx+=1 if sx<tx else -1
        while sy!=ty:ops.append(('SOUTH' if sy<ty else 'NORTH',));sy+=1 if sy<ty else -1
        return ops
    start=tuple(farm['farmer']);step=obs['step'];ops=[];built=False;events=[]
    depot=min(SHED,key=lambda p:(len(path(start,p))+len(path(p,plot)),p))
    if start==tuple(plot) and start in SHED and tile is None:
        ops.append(('BUILD_'+structure,));built=True;depot=start
    else:ops+=path(start,depot)
    if not owned and not ops:ops.append(('PASS',))
    pickup=step+len(ops);ops.append(('PICKUP',animal,1));ops+=path(depot,plot)
    if tile is None and not built:ops.append(('BUILD_'+structure,))
    placement=step+len(ops);ops.append(('PLACE',animal,1))
    if obs['hour']+len(ops)>(23 if obs['day']==29 else 24):return dict(feasible=False,reason='no_installation_window')
    if not owned:events.append(dict(step=step,phase='market',order=0,changes=[('shed',animal,1)]))
    events+=[dict(step=pickup,phase='unit',order=0,changes=[('shed',animal,-1),('hand:0',animal,1)]),
             dict(step=placement,phase='unit',order=0,changes=[('hand:0',animal,-1)])]
    checked=check_stock_events(events,initial_stock={'shed':private['shed'],'hand:0':private['inventories'][0]})
    if not checked['feasible']:return checked
    p=dict(id=f"install:{step}:{plot}:{animal}",plot=tuple(plot),
        sessions=[dict(day=obs['day'],hour=obs['hour'],worker=0,start=start,actions=ops)],
        net_value=-cost-action_value*len(ops),cashflows=[dict(day=obs['day'],cost=cost,receipts=0)],
        cash_events=[] if owned else [dict(step=step,phase='market',order=0,cost=cost)],
        market_actions=[] if owned else [(step,0,('BUY_ANIMAL',animal,1))],stock_events=events)
    return dict(feasible=True,project=p,installed_after_step=placement)
