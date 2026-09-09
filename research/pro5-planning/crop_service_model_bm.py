"""One planted crop, feasible full-service schedule without travel or prices.

Water daily, fertilize only productive windows, harvest recurring output each
event. This is a service scenario, not an optimal route or guaranteed revenue.
No renewals, digging, fertilizer pickup, transport or final sale are included.
"""

CROPS = {
    'WHEAT': (10,2,4,0,6), 'CARROT': (20,2,3,0,4),
    'TOMATO': (50,8,8,1,4), 'STRAWBERRY': (100,10,10,2,4),
    'MELON': (80,10,12,0,6),
}


def crop_service_plan(crop, planted_day, *, fertilized=False):
    seed,first,maximum,interval,cap=CROPS[crop]
    actions=[]
    harvests=[]
    if planted_day+first>29:
        return dict(actions=actions,harvests=harvests,seed_cost=0)
    actions.append((planted_day,('PLANT',crop)))
    stock=0 if interval else 1
    fertile_until=-1
    for day in range(planted_day,30):
        age=day-planted_day
        if interval and stock:
            actions.append((day,('HARVEST',)))
            harvests.append((day,stock))
            stock=0
            if age>=first+(cap-1)*interval:
                break
        if interval and day==29:
            break
        if interval:
            next_age=age+1
            productive=(next_age>=first and (next_age-first)%interval==0
                        and (next_age-first)//interval<cap)
        else:
            productive=(maximum+1)//2<=age<=maximum and stock<cap
        if fertilized and productive and fertile_until<day:
            actions.append((day,('FERTILIZE',)))
            fertile_until=day+2
        actions.append((day,('WATER',)))
        if not interval:
            if productive:
                stock=min(cap,stock+(2 if fertile_until>=day else 1))
            if age>=first and (stock>=cap or age>=maximum or day==29):
                actions.append((day,('HARVEST',)))
                harvests.append((day,stock))
                break
        elif productive:
            stock=min(cap,stock+(2 if fertile_until>=day else 1))
    return dict(actions=actions,harvests=harvests,seed_cost=seed)
