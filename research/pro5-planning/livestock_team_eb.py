"""Compose a livestock farmer with a daily paid crop hand.

Shift farmer husbandry by one turn on hire days, retain the h0 spawn guard,
and assign disjoint market ordinals. No free labour or duplicated food.
"""
from animal_food_dz import funded_animal_lifecycle
from funded_crop_dn import funded_crop_proposal
from market_quote_ci import quote_sale
from joint_sales_ck import reprice_sales
from portfolio_reservations_bp import check_portfolio
from stock_reservations_bq import check_stock_events
from crop_service_model_bm import CROPS
from itertools import islice,permutations
from paid_team_ef import paid_crop_team
from crop_rotation_eu import paid_crop_rotation
import copy


def livestock_team_candidates(obs,*,limit,action_value,market_scenario,max_hands=1,share_hands=False,rotation_size=0):
    farm=obs['farms'][obs['player']];projects=[];workers={}
    if farm['hands'] or farm['hires_today'] or obs['day']>=29:
        return dict(projects=projects,workers=workers)
    available=set(market_scenario['params']) & set(market_scenario['inventory'])
    if not {'WHEAT','FERTILIZER'}<=available:return dict(projects=projects,workers=workers)
    plots=[(x,y) for y,row in enumerate(farm['tiles']) for x,tile in enumerate(row) if tile is None]
    plots.sort(key=lambda p:(abs(p[0]-4)+abs(p[1]-4),p))
    for animal_plot,crop_plot in islice(permutations(plots,2),limit):
        for animal,product in (('COW','MILK'),('SHEEP','WOOL'),('GOOSE','EGG')):
            if product not in available:continue
            herd=funded_animal_lifecycle(obs,animal=animal,plot=animal_plot,end_day=29,
                                         action_value=action_value,market_scenario=market_scenario)
            if not herd['feasible']:continue
            for crop in sorted(set(CROPS)&available):
                extra=[p for p in plots if p not in (animal_plot,crop_plot)]
                for n in range(1,min(max_hands,len(extra)+1)+1):
                    for hands in ([None]+list(range(1,min(n,5))) if share_hands else [None]):
                        following=[()]
                        if n==rotation_size and not CROPS[crop][3]:
                            following += [(c,) for c in sorted(set(CROPS)&available)]
                        for sequence in following:
                            r=_compose_livestock_team(obs,herd=herd,animal=animal,animal_plot=animal_plot,end_day=29,
                                crop=crop,crop_plot=crop_plot,action_value=action_value,market_scenario=market_scenario,
                                extra_crops=[(crop,p) for p in extra[:n-1]],hand_count=hands,following_crops=sequence)
                            if r['feasible']:projects.append(r['project']);workers.update(r['workers'])
    return dict(projects=projects,workers=workers)


def livestock_team(obs,*,animal,animal_plot,end_day,crop,crop_plot,action_value,market_scenario,extra_crops=(),hand_count=None,following_crops=()):
    crops=[(crop,crop_plot)]+list(extra_crops)
    if len(crops)>8 or any(tuple(animal_plot)==tuple(p) for _,p in crops):return dict(feasible=False,reason='same_plot_or_team_size')
    herd=funded_animal_lifecycle(obs,animal=animal,plot=animal_plot,end_day=end_day,
                                action_value=action_value,market_scenario=market_scenario)
    return _compose_livestock_team(obs,herd=herd,animal=animal,animal_plot=animal_plot,end_day=end_day,
        crop=crop,crop_plot=crop_plot,action_value=action_value,market_scenario=market_scenario,
        extra_crops=extra_crops,hand_count=hand_count,following_crops=following_crops)


def _compose_livestock_team(obs,*,herd,animal,animal_plot,end_day,crop,crop_plot,action_value,market_scenario,
                            extra_crops=(),hand_count=None,following_crops=()):
    # The generator shares an immutable animal calendar only within this one
    # observation. Each composition owns its shifts and market renumbering.
    crops=[(crop,crop_plot)]+list(extra_crops)
    if len(crops)>8 or any(tuple(animal_plot)==tuple(p) for _,p in crops):return dict(feasible=False,reason='same_plot_or_team_size')
    if not herd['feasible']:return herd
    price=quote_sale(market_scenario['params'][crop],market_scenario['inventory'][crop],1)['receipts']
    if following_crops:
        if any(name!=crop for name,_ in crops):return dict(feasible=False,reason='mixed_rotation_block')
        plant=paid_crop_rotation(obs,plots=[p for _,p in crops],rotation=(crop,*following_crops),
                                hand_count=len(crops) if hand_count is None else hand_count,
                                action_value=action_value,market_scenario=market_scenario)
    elif extra_crops:
        unit_prices={name:quote_sale(market_scenario['params'][name],market_scenario['inventory'][name],1)['receipts']
                     for name in {name for name,_ in crops}}
        quotes={name:dict.fromkeys(range(obs['day'],30),price) for name,price in unit_prices.items()}
        plant=paid_crop_team(obs,crops=crops,sale_prices=quotes,action_value=action_value,hand_count=hand_count)
    else:
        plant=funded_crop_proposal(obs,crop=crop,plot=crop_plot,
            sale_prices={d:price for d in range(obs['day'],30)},action_value=action_value)
    if not plant['feasible']:return plant
    a=copy.deepcopy(herd['project']);c=plant['project']
    hires={s['day'] for s in c['sessions'] if s['worker']==0}
    for s in a['sessions']:
        if s['day'] in hires:s['hour']+=1
    def shifted(step):return step+int(step//24 in hires)
    offset=1+max(order for _,order,_ in c['market_actions'])
    if offset+max(order for _,order,_ in a['market_actions'])>=10:return dict(feasible=False,reason='market_capacity')
    a['market_actions']=[(shifted(step) if op[0]=='SELL' else step,order+offset,op)
                         for step,order,op in a['market_actions']]
    for e in a['stock_events']:
        if e['phase']=='unit' or any(n<0 for account,item,n in e['changes']):
            e['step']=shifted(e['step'])
        if e['phase']=='market':e['order']+=offset
    for e in a['cash_events']:e['order']+=offset
    for e in a['opportunity_events']:e['step']=shifted(e['step'])
    for q in a['sale_quotes']:q.update(step=shifted(q['step']),order=q['order']+offset)
    rows={}
    for p in (a,c):
        for row in p['cashflows']:
            total=rows.setdefault(row['day'],dict(cost=0,receipts=0))
            total['cost']+=row['cost'];total['receipts']+=row['receipts']
    p=dict(id=f"livestock-team:{obs['step']}:{animal_plot}:{animal}:{end_day}:{crop_plot}:{crop}",
        plot=tuple(animal_plot),plots=[tuple(animal_plot)]+[tuple(pos) for _,pos in crops],
        cashflows=[dict(day=d,**row) for d,row in sorted(rows.items())],net_value=a['net_value']+c['net_value'],
        resource_opportunity_cost=a['resource_opportunity_cost'],valuation_step=obs['step'],
        opportunity_events=a['opportunity_events'])
    for key in ('sessions','stock_events','cash_events','sale_quotes','market_actions'):
        p[key]=a[key]+c[key]
    if extra_crops or following_crops:
        p['id']+=f":extra:{extra_crops}"
        if hand_count is not None:p['id']+=f":hands:{hand_count}"
        p['plot_releases']=c.get('plot_releases',[])
    elif CROPS[crop][3]==0:
        last=max(24*s['day']+s['hour']+len(s['actions']) for s in c['sessions'])
        p['plot_releases']=[dict(plot=tuple(crop_plot),after_step=last)]
    if following_crops:
        p['id']+=f":rotation:{following_crops}"
        p['rotation']=c['rotation'];p['cycle_days']=c['cycle_days']
        p['rotation_reconsiderations']=c['rotation_reconsiderations']
    workers=dict(herd['workers']);workers.update(plant['workers'])
    checked=check_portfolio([p],workers=workers,initial_cash=obs['farms'][obs['player']]['money'])
    if not checked['feasible']:return checked
    checked=check_stock_events(p['stock_events'],initial_stock={'shed':obs['private']['shed'],
        'seeds':obs['private']['seeds'],**{f'hand:{i}':v for i,v in enumerate(obs['private']['inventories'])}})
    if not checked['feasible']:return checked
    return dict(feasible=True,project=reprice_sales([p],market_scenario)[0],workers=workers)
