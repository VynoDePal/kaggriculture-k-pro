"""A funded block of crops served by up to four daily temporary hands.

All hands are hired on the union of service days. This conservative schedule
prices idle capacity explicitly; it does not yet share it with other projects.
"""
import copy
from hiring_cb import hire_scenario
from public_crop_proposals_bt import make_crop_proposal
from portfolio_reservations_bp import check_portfolio
from stock_reservations_bq import check_stock_events
from crop_service_model_bm import CROPS
from market_quote_ci import quote_sale
from pending_dg import MOVES


def paid_team_candidates(obs,*,max_size,sale_scenario,action_value,share_hands=False):
    farm=obs['farms'][obs['player']];projects=[];workers={}
    if farm['hands'] or farm['hires_today']:return dict(projects=projects,workers=workers)
    plots=[(x,y) for y,row in enumerate(farm['tiles']) for x,tile in enumerate(row) if tile is None]
    plots.sort(key=lambda p:(abs(p[0]-4)+abs(p[1]-4),p))
    available=set(CROPS)&set(sale_scenario['params'])&set(sale_scenario['inventory'])
    for n in range(2,min(max_size,len(plots))+1):
        for crop in sorted(available):
            price=quote_sale(sale_scenario['params'][crop],sale_scenario['inventory'][crop],1)['receipts']
            for hands in ([None]+list(range(1,min(n,5))) if share_hands else [None]):
                r=paid_crop_team(obs,crops=[(crop,plot) for plot in plots[:n]],hand_count=hands,
                    sale_prices={crop:{d:price for d in range(obs['day'],30)}},action_value=action_value)
                if r['feasible']:projects.append(r['project']);workers.update(r['workers'])
    return dict(projects=projects,workers=workers)


def paid_crop_team(obs,*,crops,sale_prices,action_value,hand_count=None,clear_before_plant=False):
    n=len(crops) if hand_count is None else hand_count;farm=obs['farms'][obs['player']]
    # Sales keep one ordinal per crop; seed purchases share an ordinal per
    # species. Both sets must fit the actual market limit, not n + plot count.
    if type(n) is not int or not 1<=n<=4 or not n<=len(crops)<=10 or farm['hands'] or farm['hires_today']:
        return dict(feasible=False,reason='unsupported_team')
    seed_slots={crop:n+i for i,crop in enumerate(dict.fromkeys(crop for crop,_ in crops))}
    if n+len(seed_slots)>10:return dict(feasible=False,reason='market_capacity')
    plots=[tuple(plot) for crop,plot in crops]
    if len(set(plots))!=len(crops):return dict(feasible=False,reason='duplicate_plot')
    hire=hire_scenario(obs,count=n)
    if not hire['feasible']:return hire
    projected=copy.deepcopy(hire['observation']);parts=[];workers={};releases=[]
    future_spawns=[(5,4),(4,5),(5,5),(4,4)]
    calendars={};seed_suppliers={}
    for index,(crop,plot) in enumerate(crops):
        uid=index%n+1
        if uid not in calendars:
            calendars[uid]={d:dict(position=future_spawns[uid-1],available_from=1) for d in range(obs['day'],30)}
            calendars[uid][obs['day']]=dict(position=tuple(projected['farms'][obs['player']]['hands'][uid-1]),available_from=projected['hour'])
        calendar=calendars[uid]
        projected['farms'][obs['player']]['hands'][uid-1]=list(calendar[obs['day']]['position'])
        r=make_crop_proposal(projected,crop=crop,plot=plot,worker_id=uid,calendar=calendar,
            sale_quotes=sale_prices[crop],action_value=action_value,seed_order=seed_slots[crop],sale_order=index,
            clear_before_plant=clear_before_plant)
        if not r['feasible']:return r
        parts.append(r['projects'][0])
        for supplier in r['projects'][1:]:
            step,order,op=supplier['market_actions'][0]
            key=(step,order,op[1])
            if key not in seed_suppliers:
                seed_suppliers[key]=supplier
            else:
                merged=seed_suppliers[key]
                count=merged['market_actions'][0][2][2]+op[2]
                merged['market_actions']=[(step,order,('BUY_SEED',op[1],count))]
                merged['stock_events'][0]['changes']=[('seeds',op[1],count)]
                merged['cash_events'][0]['cost']+=supplier['cash_events'][0]['cost']
                merged['cashflows'][0]['cost']+=supplier['cashflows'][0]['cost']
                merged['net_value']+=supplier['net_value']
        for key,value in r['workers'].items():workers.setdefault(key,value)
        for s in r['projects'][0]['sessions']:
            x,y=s['start']
            for op in s['actions']:
                if op[0] in MOVES:
                    dx,dy=MOVES[op[0]];x,y=x+dx,y+dy
            calendar[s['day']]=dict(position=(x,y),available_from=s['hour']+len(s['actions']))
        if projected['private']['seeds'].get(crop,0):projected['private']['seeds'][crop]-=1
        if CROPS[crop][3]==0:
            releases.append(dict(plot=tuple(plot),after_step=max(24*s['day']+s['hour']+len(s['actions']) for s in r['projects'][0]['sessions'])))
    parts.extend(seed_suppliers.values())
    p=dict(id=f"paid-team:{obs['step']}:{crops}",plot=plots[0],plots=plots,plot_releases=releases)
    if hand_count is not None:p['id']+=f":hands:{n}"
    if clear_before_plant:p['id']+=':clear'
    for key in ('sessions','cash_events','stock_events','sale_quotes','market_actions'):
        p[key]=[e for part in parts for e in part.get(key,[])]
    days=sorted({s['day'] for s in p['sessions']})
    costs=[1,1,2,3]
    for d in days:
        hour=obs['hour'] if d==obs['day'] else 0;step=24*d+hour
        start=tuple(farm['farmer']) if d==obs['day'] else (4,4)
        p['sessions'].append(dict(day=d,hour=hour,worker=0,start=start,actions=[('PASS',)]))
        workers[d,0]=dict(position=start,available_from=hour)
        for index in range(n):
            p['market_actions'].append((step,index,('HIRE',)))
            p['cash_events'].append(dict(step=step,phase='market',order=index,cost=costs[index]))
    rows={}
    for e in p['cash_events']:rows.setdefault(e['step']//24,dict(cost=0,receipts=0))['cost']+=e['cost']
    for q in p['sale_quotes']:rows.setdefault(q['step']//24,dict(cost=0,receipts=0))['receipts']+=q['receipts']
    p['cashflows']=[dict(day=d,**row) for d,row in sorted(rows.items())]
    p['net_value']=sum(row['receipts']-row['cost'] for row in rows.values())-action_value*sum(len(s['actions']) for s in p['sessions'])
    checked=check_portfolio([p],workers=workers,initial_cash=farm['money'])
    if not checked['feasible']:return checked
    checked=check_stock_events(p['stock_events'],initial_stock={'shed':obs['private']['shed'],'seeds':obs['private']['seeds'],
        **{f'hand:{i}':v for i,v in enumerate(obs['private']['inventories'])}})
    if not checked['feasible']:return checked
    return dict(feasible=True,project=p,workers=workers)
