"""Fund consecutive paid crop blocks on the same already-owned plots.

Each new block starts the morning after the preceding block has delivered and
sold all its harvests. This is a conditional, explicit calendar, not a forecast
of future observations. Own sales are repriced together from today's market;
unknown opponent trades and future town openings are not invented. Temporary
hands are hired again, seeds carry over only through physical stock events.
"""
import copy
from crop_service_model_bm import CROPS
from paid_team_ef import paid_crop_team
from market_quote_ci import quote_sale
from joint_sales_ck import reprice_sales
from portfolio_reservations_bp import check_portfolio
from stock_reservations_bq import check_stock_events
from rotation_review_ev import rotation_reviews


def rotation_candidates(obs,*,plot_count,action_value,market_scenario,share_hands=False):
    """Bounded two-cycle alternatives on one nearest-plot block.

    First crops must retire on harvest. A perennial can be the final crop.
    This does not assume free farmer/hand slots alongside another project.
    """
    farm=obs['farms'][obs['player']];projects=[];workers={}
    if farm['hands'] or farm['hires_today']:
        return dict(projects=projects,workers=workers)
    plots=sorted(((x,y) for y,row in enumerate(farm['tiles']) for x,t in enumerate(row) if t is None),
                 key=lambda p:(abs(p[0]-4)+abs(p[1]-4),p))[:plot_count]
    if len(plots)<plot_count:return dict(projects=projects,workers=workers)
    available=sorted(set(CROPS)&set(market_scenario['params'])&set(market_scenario['inventory']))
    for first in available:
        if CROPS[first][3]:continue
        for second in available:
            for hands in (range(1,min(plot_count,4)+1) if share_hands else [plot_count]):
                r=paid_crop_rotation(obs,plots=plots,rotation=(first,second),hand_count=hands,
                                     action_value=action_value,market_scenario=market_scenario)
                if r['feasible']:projects.append(r['project']);workers.update(r['workers'])
    return dict(projects=projects,workers=workers)


def paid_crop_rotation(obs,*,plots,rotation,hand_count,action_value,market_scenario):
    if not 1<=len(rotation)<=8 or any(c not in CROPS for c in rotation):
        return dict(feasible=False,reason='unsupported_rotation')
    if any(CROPS[c][3] for c in rotation[:-1]):
        return dict(feasible=False,reason='perennial_plot_not_released')
    # There is no background-transport projection in this crop-only builder.
    # Do not silently erase carried goods at the first night boundary.
    if any(any(items.values()) for items in obs['private']['inventories']):
        return dict(feasible=False,reason='unreserved_carried_inventory')
    available=set(market_scenario['params'])&set(market_scenario['inventory'])
    if any(c not in available for c in rotation):
        return dict(feasible=False,reason='missing_market_scenario')
    initial_stock={'shed':obs['private']['shed'],'seeds':obs['private']['seeds'],
                   **{f'hand:{i}':items for i,items in enumerate(obs['private']['inventories'])}}
    projected=copy.deepcopy(obs);parts=[];workers={};starts=[]
    prices={c:dict.fromkeys(range(obs['day'],30),quote_sale(
        market_scenario['params'][c],market_scenario['inventory'][c],1)['receipts']) for c in rotation}
    for index,crop in enumerate(rotation):
        if projected['day']>29:return dict(feasible=False,reason='rotation_after_terminal')
        block=paid_crop_team(projected,crops=[(crop,p) for p in plots],hand_count=hand_count,
                             sale_prices=prices,action_value=action_value,clear_before_plant=index>0)
        if not block['feasible']:return block
        parts.append(block['project']);workers.update(block['workers']);starts.append(projected['day'])
        merged=dict(id=f"paid-rotation:{obs['step']}:{plots}:{rotation}:hands:{hand_count}",
                    plot=parts[0]['plot'],plots=parts[0]['plots'],
                    rotation=list(rotation[:index+1]),cycle_days=starts[:],
                    net_value=sum(p['net_value'] for p in parts))
        for key in ('sessions','cash_events','stock_events','sale_quotes','market_actions','plot_releases'):
            merged[key]=[e for p in parts for e in p.get(key,[])]
        rows={}
        for p in parts:
            for row in p['cashflows']:
                total=rows.setdefault(row['day'],dict(cost=0,receipts=0))
                total['cost']+=row['cost'];total['receipts']+=row['receipts']
        merged['cashflows']=[dict(day=d,**row) for d,row in sorted(rows.items())]
        merged=reprice_sales([merged],market_scenario)[0]
        finance=check_portfolio([merged],workers=workers,initial_cash=obs['farms'][obs['player']]['money'])
        if not finance['feasible']:return finance
        physical=check_stock_events(merged['stock_events'],initial_stock=initial_stock)
        if not physical['feasible']:return physical
        if index==len(rotation)-1:
            merged['rotation_reconsiderations']=rotation_reviews(parts,starts)
            return dict(feasible=True,project=merged,workers=workers)
        # Only consumed annual crops can be cleared; each block deposits/sells
        # its output explicitly before its last service day ends.
        next_day=1+max(s['day'] for s in block['project']['sessions'])
        projected=copy.deepcopy(obs)
        projected.update(day=next_day,hour=0,step=24*next_day)
        farm=projected['farms'][obs['player']]
        farm.update(money=finance['final_cash'],farmer=[4,4],hands=[],hires_today=0)
        for x,y in plots:farm['tiles'][y][x]=None
        projected['private']['seeds']=dict(physical['stock'].get('seeds',{}))
        projected['private']['shed']=dict(physical['stock'].get('shed',{}))
        projected['private']['inventories']=[{}]
