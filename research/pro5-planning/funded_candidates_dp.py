"""Bounded, fully paid first-hand crop alternatives for the common selector."""
from funded_crop_dn import funded_crop_proposal
from crop_service_model_bm import CROPS
from market_quote_ci import quote_sale


def funded_candidates(obs,*,limit,action_value,market_scenario):
    farm=obs['farms'][obs['player']]
    if farm['hands'] or farm['hires_today']:return dict(projects=[],workers={})
    plots=[(x,y) for y,row in enumerate(farm['tiles']) for x,tile in enumerate(row) if tile is None]
    plots.sort(key=lambda p:(abs(p[0]-4)+abs(p[1]-4),p))
    projects=[];workers={}
    for plot in plots[:limit]:
        for crop in sorted(CROPS):
            if crop not in market_scenario['params'] or crop not in market_scenario['inventory']:continue
            price=quote_sale(market_scenario['params'][crop],market_scenario['inventory'][crop],1)['receipts']
            r=funded_crop_proposal(obs,crop=crop,plot=plot,sale_prices={d:price for d in range(obs['day'],30)},action_value=action_value)
            if r['feasible']:
                projects.append(r['project']);workers.update(r['workers'])
    return dict(projects=projects,workers=workers)
