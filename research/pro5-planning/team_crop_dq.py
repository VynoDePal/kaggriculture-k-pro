"""Joint permanent-farmer and daily-paid-hand crop program.

The farmer starts after the reserved hiring turn. Seed supply and all wages
are shared in one checked portfolio, with no credit for hypothetical capacity.
"""
import copy
from funded_crop_dn import funded_crop_proposal
from public_crop_proposals_bt import make_crop_proposal
from portfolio_reservations_bp import check_portfolio
from stock_reservations_bq import check_stock_events


def team_crop_proposal(obs,*,farmer_crop,farmer_plot,hand_crop,hand_plot,sale_prices,action_value):
    if tuple(farmer_plot)==tuple(hand_plot):return dict(feasible=False,reason='same_plot')
    hand=funded_crop_proposal(obs,crop=hand_crop,plot=hand_plot,sale_prices=sale_prices[hand_crop],action_value=action_value)
    if not hand['feasible']:return hand
    hired_days={s['day'] for s in hand['project']['sessions'] if s['worker']==0}
    calendar={d:dict(position=(4,4),available_from=int(d in hired_days)) for d in range(obs['day'],30)}
    farm=obs['farms'][obs['player']]
    calendar[obs['day']]=dict(position=tuple(farm['farmer']),available_from=obs['hour']+1)
    available=copy.deepcopy(obs)
    # Reserve an owned seed for the hand before deciding if the farmer needs
    # a supplier. Do not count the hand's later purchase as available now.
    if available['private']['seeds'].get(hand_crop,0)>0:available['private']['seeds'][hand_crop]-=1
    farmer=make_crop_proposal(available,crop=farmer_crop,plot=farmer_plot,worker_id=0,calendar=calendar,
        sale_quotes=sale_prices[farmer_crop],action_value=action_value,seed_order=2,sale_order=2)
    if not farmer['feasible']:return farmer
    parts=[hand['project']]+farmer['projects'];rows={}
    for p in parts:
        for row in p['cashflows']:
            daily=rows.setdefault(row['day'],dict(cost=0,receipts=0))
            daily['cost']+=row['cost'];daily['receipts']+=row['receipts']
    project=dict(id=f"team-crop:{obs['step']}:{farmer_plot}:{farmer_crop}:{hand_plot}:{hand_crop}",
        plot=tuple(farmer_plot),plots=[tuple(farmer_plot),tuple(hand_plot)],
        net_value=sum(p['net_value'] for p in parts),cashflows=[dict(day=d,**r) for d,r in sorted(rows.items())])
    for key in ('sessions','stock_events','market_actions','cash_events','sale_quotes'):
        project[key]=[entry for p in parts for entry in p.get(key,[])]
    workers=dict(farmer['workers']);workers.update(hand['workers'])
    checked=check_portfolio([project],workers=workers,initial_cash=farm['money'])
    if not checked['feasible']:return checked
    private=obs['private']
    stock=dict(seeds=private['seeds'],shed=private['shed'],**{f'hand:{i}':v for i,v in enumerate(private['inventories'])})
    checked=check_stock_events(project['stock_events'],initial_stock=stock)
    if not checked['feasible']:return checked
    return dict(feasible=True,project=project,workers=workers)
