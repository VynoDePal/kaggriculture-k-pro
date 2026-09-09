"""Bounded animal investments with explicitly reserved owned food and service.

All candidate horizons are scenarios, not future price predictions. The common
selector decides against crops and maintenance; no purchase is compulsory.
"""
from animal_lifecycle_dw import animal_lifecycle
from animal_food_dz import funded_animal_lifecycle


def animal_candidates(obs,*,limit,action_value,market_scenario,buy_food=False):
    farm=obs['farms'][obs['player']];projects=[];workers={}
    last=29 if buy_food else min(29,obs['day']+int(obs['private']['shed'].get('WHEAT',0)))
    if last<=obs['day']:return dict(projects=projects,workers=workers)
    available=set(market_scenario['params']) & set(market_scenario['inventory'])
    if not {'WHEAT','FERTILIZER'}<=available:return dict(projects=projects,workers=workers)
    plots=[(x,y) for y,row in enumerate(farm['tiles']) for x,tile in enumerate(row)
           if tile is None or isinstance(tile,dict) and tile.get('kind') in ('COOP','PASTURE') and 'animal' not in tile]
    plots.sort(key=lambda p:(abs(p[0]-4)+abs(p[1]-4),p))
    for plot in plots[:limit]:
        for animal,product in (('COW','MILK'),('SHEEP','WOOL'),('GOOSE','EGG')):
            if product not in available:continue
            for end in range(obs['day']+1,last+1):
                builder=funded_animal_lifecycle if buy_food else animal_lifecycle
                r=builder(obs,animal=animal,plot=plot,end_day=end,
                                   action_value=action_value,market_scenario=market_scenario)
                if r['feasible']:
                    projects.append(r['project']);workers.update(r['workers'])
    return dict(projects=projects,workers=workers)
