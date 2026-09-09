"""Conditional demand from already visible shops, not a market forecast.

No future shop draws or adversary trades are assumed. Intervals must match
the game configuration; defaults are the official standard configuration.
"""
SHOPS={
    'BAKERY':('EGG','WHEAT'),
    'PIZZA_SHOP':('MILK','TOMATO','WHEAT'),
    'BRUNCH_SPOT':('EGG','WHEAT','STRAWBERRY'),
    'YARN_STORE':('WOOL',),
    'ICE_CREAM_SHOP':('STRAWBERRY','MILK','WHEAT'),
    'PET_CAFE':('CARROT',),
    'SMOOTHIE_SHOP':('STRAWBERRY','MILK'),
    'FARMERS_MARKET':('WHEAT','CARROT','TOMATO','STRAWBERRY'),
}
CENTER_ITEMS=('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL')


def with_known_town_demand(obs,scenario,*,shop_interval=4,center_interval=24):
    if any(type(n) is not int or n<1 for n in (shop_interval,center_interval)):
        raise ValueError('Positive town intervals required')
    rates={}
    for name in obs['town']['unlocked_shops']:
        products=SHOPS[name]
        for item in products:rates[item]=rates.get(item,0)+(2 if len(products)==1 else 1)
    return dict(scenario,known_town_demand=dict(from_step=obs['step'],rates=rates,
        shop_interval=shop_interval,center_interval=center_interval))


def consumed_between(demand,item,start,end):
    """Consumption after trading in turns [start, end), never at end's sale."""
    if start<demand['from_step'] or end<start:raise ValueError('Invalid demand interval')
    def ticks(interval):return (end-1)//interval-(start-1)//interval
    return demand['rates'].get(item,0)*ticks(demand['shop_interval'])+int(item in CENTER_ITEMS)*ticks(demand['center_interval'])
