"""Add a paid crop hand to remaining permanent-farmer commitments.

Only farmer-only suffixes at day start are supported. All old work is retained;
hire conflicts shift sessions only until existing slack absorbs the delay.
Impossible windows or financing are refused.
"""
import copy
from funded_crop_dn import funded_crop_proposal
from market_quote_ci import quote_sale
from joint_sales_ck import reprice_sales
from portfolio_reservations_bp import check_portfolio
from stock_reservations_bq import check_stock_events
from crop_service_model_bm import CROPS
from paid_team_ef import paid_crop_team
from future_workers_do import reserves_center_spawn


def renewal_candidates(obs,*,pending_projects,limit,action_value,market_scenario,max_hands=1,share_hands=False):
    if any(s['worker']!=0 for p in pending_projects for s in p['sessions']):return []
    farm=obs['farms'][obs['player']]
    if farm['hands'] or farm['hires_today']:return []
    reserved={tuple(t) for p in pending_projects for t in p.get('plots',[p['plot']])}
    plots=[(x,y) for y,row in enumerate(farm['tiles']) for x,tile in enumerate(row)
           if tile is None and (x,y) not in reserved]
    plots.sort(key=lambda p:(abs(p[0]-4)+abs(p[1]-4),p))
    available=set(CROPS)&set(market_scenario['params'])&set(market_scenario['inventory'])
    result=[]
    for plot in plots[:limit]:
        for crop in sorted(available):
            other=[p for p in plots if p!=plot]
            for n in range(1,min(max_hands,len(plots))+1):
                for hands in ([None]+list(range(1,min(n,5))) if share_hands else [None]):
                    r=renew_hand(obs,pending_projects=pending_projects,crop=crop,plot=plot,
                                 extra_crops=[(crop,p) for p in other[:n-1]],hand_count=hands,
                                 action_value=action_value,market_scenario=market_scenario)
                    if r['feasible']:result.append(r['project'])
    return result


def renew_hand(obs,*,pending_projects,crop,plot,action_value,market_scenario,extra_crops=(),hand_count=None):
    if not pending_projects or obs['hour']!=0:
        return dict(feasible=False,reason='not_day_start')
    if any(s['worker']!=0 for p in pending_projects for s in p['sessions']):
        return dict(feasible=False,reason='existing_hand_commitment')
    if any(op[0]=='HIRE' for p in pending_projects for _,_,op in p.get('market_actions',[])):
        return dict(feasible=False,reason='existing_hire')
    plots={tuple(t) for p in pending_projects for t in p.get('plots',[p['plot']])}
    crops=[(crop,plot)]+list(extra_crops)
    if any(tuple(pos) in plots for _,pos in crops):return dict(feasible=False,reason='reserved_plot')
    price=quote_sale(market_scenario['params'][crop],market_scenario['inventory'][crop],1)['receipts']
    if extra_crops:
        prices={name:quote_sale(market_scenario['params'][name],market_scenario['inventory'][name],1)['receipts']
                for name,_ in crops}
        hand=paid_crop_team(obs,crops=crops,sale_prices={name:dict.fromkeys(range(obs['day'],30),v) for name,v in prices.items()},
                            action_value=action_value,hand_count=hand_count)
    else:
        hand=funded_crop_proposal(obs,crop=crop,plot=plot,sale_prices={d:price for d in range(obs['day'],30)},action_value=action_value)
    if not hand['feasible']:return hand
    parts=copy.deepcopy(list(pending_projects));c=hand['project']
    days={s['day'] for s in c['sessions'] if s['worker']==0}
    shared={d for d in days if any(reserves_center_spawn(s,d) for p in parts for s in p['sessions'])}
    c['sessions']=[s for s in c['sessions'] if not(s['worker']==0 and s['day'] in shared)]
    c['net_value']+=action_value*len(shared)
    days=days-shared
    shifted_steps={};ends={d:1 for d in days}
    for s in sorted((s for part in parts for s in part['sessions']),key=lambda s:(s['day'],s['hour'])):
        if s['day'] not in days:continue
        old=s['hour'];new=max(old,ends[s['day']]);ends[s['day']]=new+len(s['actions'])
        for i in range(len(s['actions'])):shifted_steps[24*s['day']+old+i]=24*s['day']+new+i
        s['hour']=new
    def shift(step):return shifted_steps.get(step,step)
    slots={}
    for part in parts:
        for step,order,op in part.get('market_actions',[]):slots.setdefault(step,set()).add(order)
    offset=1+max(order for _,order,_ in c['market_actions'])
    ranks={(step,old):new+offset for step,orders in slots.items() for new,old in enumerate(sorted(orders))}
    if any(n>=10 for n in ranks.values()):return dict(feasible=False,reason='market_capacity')
    for part in parts:
        for e in part['stock_events']:
            old=e['step']
            if e['phase']=='market':e['order']=ranks[old,e['order']]
            if e['phase']=='unit' or any(n<0 for account,item,n in e['changes']):e['step']=shift(old)
        for e in part.get('cash_events',[]):e['order']=ranks[e['step'],e['order']]
        for e in part.get('opportunity_events',[]):
            e['step']=shift(e['step'])
            if e.get('purchase_ref') is not None:
                step,order=e['purchase_ref'];e['purchase_ref']=(step,ranks[step,order])
        for e in part.get('plot_releases',[]):e['after_step']=shift(e['after_step']-1)+1
        for q in part.get('sale_quotes',[]):q.update(order=ranks[q['step'],q['order']],step=shift(q['step']))
        part['market_actions']=[(shift(step) if op[0]=='SELL' else step,ranks[step,order],op)
                                for step,order,op in part.get('market_actions',[])]
    parts.append(c);rows={}
    for part in parts:
        for row in part['cashflows']:
            total=rows.setdefault(row['day'],dict(cost=0,receipts=0))
            total['cost']+=row['cost'];total['receipts']+=row['receipts']
    p=dict(id=f"renewed-hand:{obs['step']}:{plot}:{crop}",plot=tuple(parts[0]['plot']),
        plots=sorted(plots|{tuple(pos) for _,pos in crops}),cashflows=[dict(day=d,**row) for d,row in sorted(rows.items())],
        net_value=sum(p['net_value'] for p in parts),valuation_step=obs['step'],
        resource_opportunity_cost=sum(p.get('resource_opportunity_cost',0) for p in parts))
    for key in ('sessions','stock_events','market_actions','cash_events','sale_quotes','opportunity_events','plot_releases'):
        p[key]=[e for part in parts for e in part.get(key,[])]
    if any(part.get('joint_product_trades') for part in parts):p['joint_product_trades']=True
    if extra_crops:p['id']+=f":extra:{extra_crops}"
    if extra_crops and hand_count is not None:p['id']+=f":hands:{hand_count}"
    if not extra_crops and CROPS[crop][3]==0:
        p['plot_releases'].append(dict(plot=tuple(plot),after_step=max(24*s['day']+s['hour']+len(s['actions']) for s in c['sessions'])))
    workers=dict(hand['workers'])
    for s in p['sessions']:
        if s['worker']==0:workers.setdefault((s['day'],0),dict(position=tuple(obs['farms'][obs['player']]['farmer']) if s['day']==obs['day'] else (4,4),available_from=0))
    if p.get('joint_product_trades'):p=reprice_sales([p],market_scenario)[0]
    checked=check_portfolio([p],workers=workers,initial_cash=obs['farms'][obs['player']]['money'])
    if not checked['feasible']:return checked
    checked=check_stock_events(p['stock_events'],initial_stock={'shed':obs['private']['shed'],'seeds':obs['private']['seeds'],
        **{f'hand:{i}':v for i,v in enumerate(obs['private']['inventories'])}})
    if not checked['feasible']:return checked
    return dict(feasible=True,project=p if p.get('joint_product_trades') else reprice_sales([p],market_scenario)[0],workers=workers)
