"""Bounded ordered plot pairs and crop combinations; first paid hand only."""
import itertools
from crop_service_model_bm import CROPS
from market_quote_ci import quote_sale
from team_crop_dq import team_crop_proposal


def team_candidates(obs,*,pair_limit,action_value,market_scenario):
    farm=obs['farms'][obs['player']]
    if farm['hands'] or farm['hires_today']:return dict(projects=[],workers={})
    plots=[(x,y) for y,row in enumerate(farm['tiles']) for x,tile in enumerate(row) if tile is None]
    plots.sort(key=lambda p:(abs(p[0]-4)+abs(p[1]-4),p))
    crops=sorted(set(CROPS)&set(market_scenario['params'])&set(market_scenario['inventory']))
    prices={c:{d:quote_sale(market_scenario['params'][c],market_scenario['inventory'][c],1)['receipts']
               for d in range(obs['day'],30)} for c in crops}
    projects=[];workers={}
    for a,b in itertools.islice(itertools.permutations(plots,2),pair_limit):
        for ca,cb in itertools.product(crops,repeat=2):
            r=team_crop_proposal(obs,farmer_crop=ca,farmer_plot=a,hand_crop=cb,hand_plot=b,
                                 sale_prices=prices,action_value=action_value)
            if r['feasible']:projects.append(r['project']);workers.update(r['workers'])
    return dict(projects=projects,workers=workers)
