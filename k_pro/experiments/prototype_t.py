"""K Pro 1: observation-driven economy, spatial contracts and finite-horizon work.

Standalone stdlib agent. No action tape, opponent identity, seed or future state.
Game constants are transcribed from kaggle_environments Kaggriculture 1.32.7.
"""
import math
import copy

CROP = {  # seed, first, maximum-yield age, interval (0 = one harvest), yield cap
    'WHEAT': (10, 2, 4, 0, 6), 'CARROT': (20, 2, 3, 0, 4),
    'TOMATO': (50, 8, 8, 1, 4), 'STRAWBERRY': (100, 10, 10, 2, 4),
    'MELON': (80, 10, 12, 0, 6),
}
ANIMAL = {'COW': (400, 8, 2, 6, 'MILK'), 'SHEEP': (500, 6, 3, 6, 'WOOL'),
          'GOOSE': (300, 4, 1, 4, 'EGG')}
PARAMS = {
    'WHEAT': (25,400,'sqrt',.8,'log',.2), 'CARROT': (35,450,'hinge',1,'sqrt',.7),
    'TOMATO': (60,200,'hinge',.4,'sqrt',.6), 'STRAWBERRY': (120,100,'sqrt',.7,'linear',1.6),
    'MELON': (250,300,'log',.2,'sq',3.6), 'EGG': (50,332,'hinge',.4,'log',.2),
    'MILK': (160,122,'sqrt',.6,'linear',1.6), 'WOOL': (200,105,'log',.2,'sq',3.2),
    'FERTILIZER': (100,200,'linear',.4,'linear',.4),
}
SHOP = {'BAKERY': ('EGG','WHEAT'), 'PIZZA_SHOP': ('MILK','TOMATO','WHEAT'),
        'BRUNCH_SPOT': ('EGG','WHEAT','STRAWBERRY'), 'YARN_STORE': ('WOOL','WOOL'),
        'ICE_CREAM_SHOP': ('STRAWBERRY','MILK','WHEAT'), 'PET_CAFE': ('CARROT','CARROT'),
        'SMOOTHIE_SHOP': ('STRAWBERRY','MILK'), 'FARMERS_MARKET': ('WHEAT','CARROT','TOMATO','STRAWBERRY')}
SHED = ((4,4),(5,4),(4,5),(5,5))
CFG = dict(open_melons=12,open_sheep=2,open_cows=2,open_wheat=7,open_hands=5,max_hands=12,
           max_animals=14,max_straw=32,wheat_ratio=.75,land2_day=5,land3_day=9,
           land4_day=12,four_quadrants=False,diamond_radius=5,animal_radius=2,
           fert_wheat=True,feed_roi=True,care=True,fert_collect_floor=3,
           premium_floor=.2,forecast_days=5,zone_penalty=3.,fert_stock=12,
           crop_work=1.7,animal_work=4.8,work_per_hand=13,late_wheat_day=25,
           opportunistic_drop=12,zone_mode='angular',harvest_wheat=5,max_geese=2,
           animal_forecast_weight=.35,land_buffer=100,straw_start_day=3,
           herd_policy='margin',rival_value=1.,replan_hours=(4,12),herd_batch=3,
           capital_delivery=True,capital_value=400,wheat_max=24,planned_zones=True,
           protect_targets=True,reserve_herd_sites=2,investment_reserve=50,
           strict_diamond=True,scheduler='auction',delivery_last_day=12,
           delivery_cash_ceiling=4000,central_sale_value=200,early_fert_delivery=True,
           finish_service=True,delivery_radius=8,delivery_distance_cost=150,
           crop_policy='legacy',crop_risk=.35,tomato_max=24,carrot_max=24,land_first=True,
           force_early_fert=False,hire_policy='legacy',route_hire_margin=2,
           reserve_animal_ring=True,straw_forecast_floor=20,full_day=True,
           pickup_extra_food=0,herd_worker_effort=5.,herd_growth_rate=2,
           feed_supply_fix=True,second_melons=6,rotate_crops=False,
           react_land=True,straw_latest_day=16,strict_species_cap=True,
           quota_balance_weight=0.,milk_share_floor=.3,milk_share_ceiling=.7,
           liquid_capital=True,idle_delivery=False,overflow_target=90,
           economic_tasks=False,early_wheat_yield=5,early_wheat_until=4,
           open_carrots=0,smart_fertilizer=False,buy_fertilizer=False,
           fertilizer_buy_ceiling=20,final_bundle_fix=True,
           route_capacity=21,route_balance=.03,route_future_service=True,
           late_zone_decay=False,capital_discount=.98,market_risk=.2,
           forecast_model='legacy',forecast_production=1.7,future_shop_weight=.7,
           lookahead=False,lookahead_choices=4,lookahead_field_weight=.4,
           seed_horizon_fix=True,care_cap=True,terminal_feed_roi=True,
           milk_shed_slots=False,market_delivery=False,market_delivery_value=250,
           market_delivery_radius=2,wheat_floor=None,rotation_scope='all',
           hybrid_weight=.5,feed_collapse_production=False,feed_task_budget=False,
           retire_unprofitable=False,retire_after=24,market_rank='quote',bounded_market=False)
_STATE = {}

def shape(kind,x,t):
    if kind=='sqrt':return math.sqrt(x)
    if kind=='log':return math.log1p(x)
    if kind=='sq':return x*x
    if kind=='hinge':
        u=x/t
        return u+8*max(0,u-1)**2
    return x

def price(item,inventory):
    base,t,bf,bt,af,at=PARAMS[item]
    if inventory<10000:
        v=base+base*bt*shape(bf,10000-inventory,t)/shape(bf,t,t)
    else:v=base-base*at*shape(af,inventory-10000,t)/shape(af,t,t)
    return max(1,round(v))

def bounded_inventory(item,inventory):
    """Sales at the price floor do not add market inventory in the engine."""
    if not CFG['bounded_market'] or price(item,inventory)>1:return inventory
    lo,hi=10000,max(10001,int(math.ceil(inventory)))
    while lo<hi:
        mid=(lo+hi)//2
        if price(item,mid)<=1:hi=mid
        else:lo=mid+1
    return lo

def distance(a,b):return abs(a[0]-b[0])+abs(a[1]-b[1])
def radius(p):return min(distance(p,s) for s in SHED)
def move(p,q):
    if p[0]!=q[0]:return ['EAST' if p[0]<q[0] else 'WEST']
    if p[1]!=q[1]:return ['SOUTH' if p[1]<q[1] else 'NORTH']
    return ['PASS']
def kind(t):
    if t is None:return 'EMPTY'
    if t=='LOCKED':return 'LOCKED'
    return t.get('animal') or t.get('crop') or t.get('kind','EMPTY')
def demand(town,item):return (item!='FERTILIZER')+6*sum(SHOP.get(s,()).count(item) for s in town.get('unlocked_shops',[]))
def counts(farm):
    out={}
    for row in farm['tiles']:
        for t in row:
            k=kind(t);out[k]=out.get(k,0)+1
    return out
def fibonacci(n):
    a,b=1,1
    for _ in range(n):a,b=b,a+b
    return a

def forecast(obs,item,horizon=5):
    """Conservative public supply estimate, not hidden future-shop prediction."""
    current=obs['market']['inventory'][item]
    if CFG['forecast_model']=='discrete':
        supply=0.;day=obs['day']
        for farm in obs['farms']:
            for row in farm['tiles']:
                for t in row:
                    if not isinstance(t,dict):continue
                    a=t.get('animal')
                    if a and ANIMAL[a][4]==item:
                        _,first,interval,cap,_=ANIMAL[a];bonus=t.get('pending_care_bonus',0)
                        supply+=t.get('yield_units',0)
                        for offset in range(1,horizon+1):
                            d=day+offset
                            if d>=t['placed_day']+first and (d-t['placed_day']-first)%interval==0:
                                supply+=min(cap,1+bonus);bonus=0
                            bonus+=1
                    if t.get('crop')==item:
                        _,first,maximum,interval,cap=CROP[item]
                        if interval:
                            supply+=t.get('yield_units',0)
                            supply+=CFG['forecast_production']*sum(day<t['planted_day']+first+i*interval<=day+horizon for i in range(cap))
                        elif t['planted_day']+first<=day+horizon:
                            supply+=max(t.get('yield_units',0),cap*.85)
        drain=demand(obs.get('town',{}),item)*horizon
        expected_shop=sum(6*items.count(item) for items in SHOP.values())/len(SHOP)
        drain+=CFG['future_shop_weight']*expected_shop*sum(max(0,day+horizon-d) for d in (3,6,9,12,15,18,21,24) if d>day)
        return price(item,int(current+supply-drain))
    supply=0.
    for farm in obs['farms']:
        for row in farm['tiles']:
            for t in row:
                if not isinstance(t,dict):continue
                a=t.get('animal')
                if a and ANIMAL[a][4]==item:
                    first=t['placed_day']+ANIMAL[a][1]
                    start=max(obs['day'],first)
                    supply+=max(0,(obs['day']+horizon-start)/ANIMAL[a][2])*min(ANIMAL[a][3],1+ANIMAL[a][2])
                    supply+=t.get('yield_units',0)
                if t.get('crop')==item:
                    cd=CROP[item];age=obs['day']-t['planted_day']
                    if age+horizon>=cd[1]:
                        supply+=min(cd[4],t.get('yield_units',0)+horizon/(cd[3] or 4)*2)
    return price(item,current+int(supply)-demand(obs.get('town',{}),item)*horizon)

def herd_value(obs,species):
    """Counterfactual cash margin on public-state market scenarios.

    This estimates the price effect on BOTH farms, not just the purchased animal.
    Future shops are expectations over the eight official types, never seed reads.
    """
    day=obs['day'];item=ANIMAL[species][4];cost,first,interval,cap,_=ANIMAL[species]
    town=obs.get('town',{});public=demand(town,item)
    gain=sum(6*items.count(item) for items in SHOP.values())/len(SHOP)
    seat=obs['player'];counts_by_seat=[counts(f) for f in obs['farms']]
    own_n=counts_by_seat[seat].get(species,0);rival_n=counts_by_seat[1-seat].get(species,0)
    candidates=[]
    for optimism in (.3,1.,1.7):
        values=[]
        for added in (0,1):
            inventory=float(obs['market']['inventory'][item]);cash=0.
            for d in range(day,30):
                own=0.;rival=0.
                for s,farm in enumerate(obs['farms']):
                    quantity=0.
                    for row in farm['tiles']:
                        for tile in row:
                            if not isinstance(tile,dict) or tile.get('animal')!=species:continue
                            if d>=tile['placed_day']+first:
                                quantity+=(interval+1)/interval
                    if s==seat:own=quantity
                    else:rival=quantity
                if added and d>=day+first:own+=(interval+1)/interval
                # A modest population-growth prior prevents an early monopoly illusion.
                growth=min(max(0,d-day),max(0,10-day))*.18
                if d>=day+first:rival+=growth*(interval+1)/interval
                total=own+rival
                avg=(price(item,int(inventory))+4*price(item,int(inventory+total/2))+price(item,int(inventory+total)))/6
                cash+=avg*(own-CFG['rival_value']*rival)
                new_shops=sum(day<u<=d for u in (3,6,9,12,15,18,21,24))
                inventory=bounded_inventory(item,inventory+total)-public-optimism*new_shops*gain
            values.append(cash)
        feed=(29-day)*obs['market']['prices']['WHEAT']
        fertilizer=(29-day)*min(12,obs['market']['prices']['FERTILIZER'])
        candidates.append(values[1]-values[0]-cost-feed+fertilizer)
    return sum(candidates)/len(candidates)-.2*(max(candidates)-min(candidates))

def crop_value(obs,crop,extra):
    """Marginal return per service action, including delayed and shared-market sales."""
    day=obs['day'];seed,first,maximum,interval,cap=CROP[crop]
    finish=maximum if not interval else first+(cap-1)*interval
    if day+first>29:return -1e6
    ticks=min(cap,1+(29-day-first)//interval) if interval else 1
    amount=ticks*1.7 if interval else min(cap,1+max(0,min(maximum,29-day)-(maximum+1)//2+1)*1.6)
    horizon=min(29-day,finish)
    town=obs.get('town',{});drain=demand(town,crop)*horizon
    gain=sum(6*items.count(crop) for items in SHOP.values())/len(SHOP)
    drain+=sum(max(0,day+horizon-u)*gain*.7 for u in (3,6,9,12,15,18,21,24) if u>day)
    pending=0.
    for farm in obs['farms']:
        for row in farm['tiles']:
            for t in row:
                if not isinstance(t,dict) or t.get('crop')!=crop:continue
                age=day-t['planted_day']
                if interval:
                    pending+=1.7*sum(day< t['planted_day']+first+i*interval <= day+horizon for i in range(cap))
                    pending+=t.get('yield_units',0)
                elif age+horizon>=first:pending+=max(t.get('yield_units',0),cap*.8)
    expected=obs['market']['inventory'][crop]+pending+extra*amount-drain
    pessimistic=price(crop,int(expected+amount))
    optimistic=price(crop,int(expected+amount/2-drain*.3))
    effective=(1-CFG['crop_risk'])*optimistic+CFG['crop_risk']*pessimistic
    service=horizon*.55+3+ticks+(2 if interval else 1)+horizon*.25
    return (effective*amount-seed)/(service*(1+.025*first))

def herd_value_exact(obs,species):
    """Discrete public-state production scenarios, including the first CARE burst.

    Optimize score margin, not market price alone. No opponent-private inventory
    or future town is observed; unknown shops are integrated as explicit scenarios.
    """
    day=obs['day'];seat=obs['player'];cost,first,interval,cap,item=ANIMAL[species]
    horizon=30-day;flows=[[0.]*horizon for _ in (0,1)]
    for owner,farm in enumerate(obs['farms']):
        for row in farm['tiles']:
            for t in row:
                if not isinstance(t,dict) or t.get('animal')!=species:continue
                flows[owner][0]+=t.get('yield_units',0)
                care=t.get('pending_care_bonus',0)
                for offset in range(1,horizon):
                    d=day+offset
                    if d>=t['placed_day']+first and (d-t['placed_day']-first)%interval==0:
                        flows[owner][offset]+=min(cap,1+care);care=0
                    care+=1
    new=[0.]*horizon;care=0
    for offset in range(1,horizon):
        if offset>=first and (offset-first)%interval==0:
            new[offset]=min(cap,1+care);care=0
        care+=1
    public=demand(obs.get('town',{}),item)
    average_shop=sum(6*items.count(item) for items in SHOP.values())/len(SHOP)
    all_animals=sum(sum(counts(f).get(a,0) for a in ANIMAL) for f in obs['farms'])
    fertilizer_sales=max(0,all_animals*.7-2)
    wheat_price=.6*obs['market']['prices']['WHEAT']+.4*PARAMS['WHEAT'][0]
    scenarios=[]
    for optimism in (.3,1.,1.7):
        values=[]
        for added in (0,1):
            inventory=float(obs['market']['inventory'][item]);value=0.
            for offset in range(horizon):
                d=day+offset;own=flows[seat][offset]+added*new[offset];rival=flows[1-seat][offset]
                total=own+rival
                quote=(price(item,int(inventory))+4*price(item,int(inventory+total/2))+price(item,int(inventory+total)))/6
                value+=CFG['capital_discount']**offset*quote*(own-CFG['rival_value']*rival)
                new_shops=sum(day<u<=d for u in (3,6,9,12,15,18,21,24))
                inventory=bounded_inventory(item,inventory+total)-public-optimism*new_shops*average_shop
            values.append(value)
        operating=0.
        for offset in range(horizon-1):
            fert=price('FERTILIZER',int(obs['market']['inventory']['FERTILIZER']+fertilizer_sales*offset))
            operating+=CFG['capital_discount']**offset*(.7*fert-wheat_price)
        scenarios.append(values[1]-values[0]+operating-cost)
    return sum(scenarios)/len(scenarios)-CFG['market_risk']*(max(scenarios)-min(scenarios))

def route_hands(obs,roles):
    """Hire for today's service routes, not for the number of occupied fields."""
    work=tasks(obs,{'roles':roles});day=obs['day'];me=obs['farms'][obs['player']]
    effort={}
    for pos,(todo,_) in work.items():
        amount=len(todo)
        tile=me['tiles'][pos[1]][pos[0]];k=kind(tile)
        if k=='EMPTY' and roles[pos] in ANIMAL:amount+=2
        if k in CROP and not CROP[k][3] and ['HARVEST'] in todo and day+CROP[k][1]<29:amount+=2
        effort[pos]=amount
    if not effort:return 1
    ordered=sorted(effort,key=lambda p:(math.atan2(p[1]-4.5,p[0]-4.5),radius(p)))
    total=sum(effort[p]+1 for p in ordered)
    for hands in range(2,CFG['max_hands']+1):
        units=hands+1;clusters=[[] for _ in range(units)];done=0
        for pos in ordered:
            index=min(units-1,int(done/total*units));clusters[index].append(pos);done+=effort[pos]+1
        times=[]
        for points in clusters:
            here=(4,4);duration=3 # arrival and provisions
            remaining=list(points)
            while remaining:
                next_pos=min(remaining,key=lambda p:(distance(here,p),p))
                duration+=distance(here,next_pos)+effort[next_pos]
                here=next_pos;remaining.remove(next_pos)
            if day==29:duration+=radius(here)+1
            times.append(duration)
        if max(times)<=24-CFG['route_hire_margin'] and sum(times)<=units*21:
            return hands
    return CFG['max_hands']

def plan(obs,st):
    day=obs['day'];me=obs['farms'][obs['player']];priv=obs['private']
    ct=counts(me);p=obs['market']['prices'];town=obs.get('town',{})
    money=me['money'];q=len(me['unlocked_quadrants'])
    if CFG['liquid_capital']:
        # Market SELL orders execute before investment in the same turn. The
        # planner must see that realizable capital, not only the pre-sale wallet.
        for item in PARAMS:
            if item=='WHEAT':continue
            if item=='FERTILIZER' and (day>=9 or p[item]<p['WHEAT']*1.5):continue
            floor=max(1,int(PARAMS[item][0]*CFG['premium_floor']))
            if p[item]>=floor:
                money+=sum(max(0,price(item,obs['market']['inventory'][item]+i))
                           for i in range(priv['shed'].get(item,0)))
    pending={a:priv['shed'].get(a,0)+sum(i.get(a,0) for i in priv['inventories']) for a in ANIMAL}
    animal_n=sum(ct.get(a,0)+pending[a] for a in ANIMAL)
    # Herd decisions use public demand/supply. Opening is an explicit capital budget.
    targets={a:ct.get(a,0)+pending[a] for a in ANIMAL}
    if day==0:
        targets['SHEEP']=CFG['open_sheep'];targets['COW']=CFG['open_cows']
    elif day<=16:
        limit=min(CFG['max_animals'],CFG['open_sheep']+CFG['open_cows']+max(0,day-1)*CFG['herd_growth_rate'])
        if money>400 and animal_n<limit:
            choices=[];species_room={a:limit-animal_n for a in ANIMAL}
            for a,data in ANIMAL.items():
                if a=='GOOSE' and ct.get(a,0)+pending[a]>=CFG['max_geese']:continue
                if a=='GOOSE':species_room[a]=CFG['max_geese']-ct.get(a,0)-pending[a]
                if CFG['herd_policy'] in ('balanced','hybrid') and a in ('COW','SHEEP'):
                    rival=counts(obs['farms'][1-obs['player']])
                    milk_share=max(CFG['milk_share_floor'],min(CFG['milk_share_ceiling'],.5+.012*(demand(town,'MILK')-demand(town,'WOOL'))-.02*(rival.get('COW',0)-rival.get('SHEEP',0))))
                    share=milk_share if a=='COW' else 1-milk_share
                    species_room[a]=math.ceil(CFG['max_animals']*share)-ct.get(a,0)-pending[a]
                    if species_room[a]<=0:continue
                cost,first,interval,cap,product=data
                ticks=max(0,(29-day-first)//interval+1)
                fw=CFG['animal_forecast_weight']
                fp=fw*forecast(obs,product,8)+(1-fw)*(.6*p[product]+.4*PARAMS[product][0])
                # Includes feed purchase and opportunity cost of daily service.
                net=(herd_value_exact(obs,a) if CFG['herd_policy']=='margin_exact' else herd_value(obs,a) if CFG['herd_policy']=='margin' else
                     ticks*(interval+1)*fp+(29-day)*min(15,p['FERTILIZER'])-(29-day)*p['WHEAT']-cost)
                if CFG['herd_policy']=='hybrid':net=(1-CFG['hybrid_weight'])*net+CFG['hybrid_weight']*herd_value_exact(obs,a)
                if CFG['herd_policy'] in ('balanced','hybrid') and a in ('COW','SHEEP'):
                    fullness=(ct.get(a,0)+pending[a])/max(1,math.ceil(CFG['max_animals']*share))
                    net*=max(.1,1-CFG['quota_balance_weight']*fullness)
                choices.append((net/max(1,cost),a))
            if choices:
                value,a=max(choices)
                if value>1.0:targets[a]+=min(CFG['herd_batch'],limit-animal_n,species_room[a] if CFG['strict_species_cap'] else limit-animal_n)
    pending={a:priv['shed'].get(a,0)+sum(i.get(a,0) for i in priv['inventories']) for a in ANIMAL}
    for a in ANIMAL:targets[a]=max(targets[a],ct.get(a,0)+pending[a])
    herd=sum(targets.values())
    # Live crop capacity: planting every available tile is not a free action.
    wheat_floor=CFG['open_wheat'] if day==0 or CFG['wheat_floor'] is None else CFG['wheat_floor']
    wheat_target=min(CFG['wheat_max'],max(wheat_floor,math.ceil(herd*CFG['wheat_ratio']))) if day<=CFG['late_wheat_day'] else 0
    straw_target=0 if day<CFG['straw_start_day'] else min(CFG['max_straw'],2+day*3)
    if day>CFG['straw_latest_day']:straw_target=ct.get('STRAWBERRY',0)
    if day>=3 and forecast(obs,'STRAWBERRY',8)<CFG['straw_forecast_floor']:straw_target=min(straw_target,8)
    melon_target=CFG['open_melons'] if day==0 else ct.get('MELON',0)
    if 11<=day<=18 and forecast(obs,'MELON',10)>100:melon_target=max(melon_target,CFG['second_melons'])
    carrot_target=CFG['open_carrots'] if day==0 else 0
    if 20<=day<=26 and p['CARROT']>35:carrot_target=min(20,8+int(demand(town,'CARROT')/2))
    wanted={'WHEAT':wheat_target,'STRAWBERRY':straw_target,'MELON':melon_target,'CARROT':carrot_target}
    if CFG['crop_policy']=='marginal' and day>0:
        wanted={c:ct.get(c,0) for c in CROP}
        wanted['WHEAT']=max(wanted['WHEAT'],wheat_target)
        cap_by_crop={'WHEAT':CFG['wheat_max'],'STRAWBERRY':CFG['max_straw'],
                     'TOMATO':CFG['tomato_max'],'CARROT':CFG['carrot_max'],'MELON':18}
        total_cap=min(q*25-herd, max(0,int(((CFG['max_hands']+1)*CFG['work_per_hand']-herd*CFG['animal_work'])/CFG['crop_work'])))
        for _ in range(max(0,total_cap-sum(wanted.values()))):
            options=[]
            for c in CROP:
                if wanted[c]>=cap_by_crop[c]:continue
                if c=='WHEAT' and day>CFG['late_wheat_day']:continue
                score=crop_value(obs,c,max(0,wanted[c]-ct.get(c,0)))
                options.append((score,c))
            if not options:break
            value,c=max(options)
            if value<8:break
            wanted[c]+=1
    roles={}
    for y,row in enumerate(me['tiles']):
        for x,t in enumerate(row):
            k=kind(t)
            if k in ANIMAL or k in CROP:roles[(x,y)]=k
    free=[(x,y) for y,row in enumerate(me['tiles']) for x,t in enumerate(row) if kind(t) in ('EMPTY','WEED','PASTURE','COOP')]
    free.sort(key=lambda pos:(radius(pos),pos[1],pos[0]))
    for a in ('SHEEP','COW','GOOSE'):
        for _ in range(max(0,targets[a]-ct.get(a,0))):
            structure='COOP' if a=='GOOSE' else 'PASTURE'
            eligible=[pos for pos in free if kind(me['tiles'][pos[1]][pos[0]]) in ('EMPTY','WEED',structure)]
            if CFG['milk_shed_slots'] and a!='COW':
                central_sheep=any(r=='SHEEP' and radius(p)==0 for p,r in roles.items())
                if a=='GOOSE' or central_sheep:
                    noncentral=[p for p in eligible if radius(p)>0]
                    if noncentral:eligible=noncentral
            if not eligible:break
            slot=min(eligible,key=lambda pos:(0 if kind(me['tiles'][pos[1]][pos[0]])==structure else 1,radius(pos),pos))
            roles[slot]=a;free.remove(slot)
    if CFG['reserve_animal_ring'] and day<=16:
        occupied_animals=[p for p,r in roles.items() if r in ANIMAL]
        future=max(0,CFG['max_animals']-len(occupied_animals))
        reserved_ring=[p for p in free if radius(p)<=CFG['animal_radius']][:future]
        free=[p for p in free if p not in reserved_ring]
    elif day<6:
        # Preserve the two near-shed sites for early herd expansion. They can
        # be reassigned once the initial expansion window has passed.
        protected=max(0,CFG['reserve_herd_sites']-(herd-CFG['open_sheep']-CFG['open_cows']))
        free=free[protected:]
    for c in ('MELON','WHEAT','STRAWBERRY','TOMATO','CARROT'):
        for _ in range(max(0,wanted.get(c,0)-ct.get(c,0))):
            allowed=[pos for pos in free if kind(me['tiles'][pos[1]][pos[0]]) not in ('PASTURE','COOP') and (q<3 or radius(pos)<=CFG['diamond_radius'])]
            if not allowed:break
            # Low-touch melons farther out; frequent crops occupy short routes.
            slot=min(allowed,key=lambda pos:((-radius(pos) if c=='MELON' and day<2 else radius(pos)),pos))
            roles[slot]=c;free.remove(slot)
    workload=sum(CFG['animal_work'] if k in ANIMAL else CFG['crop_work'] for k in roles.values())
    hands=min(CFG['max_hands'],max(3,math.ceil(workload/CFG['work_per_hand'])))
    if day==0:hands=CFG['open_hands']
    if day>=28:hands=max(3,min(CFG['max_hands'],math.ceil(workload/15)))
    if CFG['hire_policy']=='routing' and obs['hour']==0:
        hands=route_hands(obs,roles)
    elif CFG['hire_policy']=='routing' and st.get('day')==day:
        hands=max(len(me['hands']),st.get('hands',hands))
    st.update(day=day,roles=roles,herd=targets,hands=hands,targets={},zones=None,quadrants=q)

def crop_tasks(t,day,prices):
    c=t['crop'];seed,first,maximum,interval,cap=CROP[c]
    age=day-t['planted_day'];yu=t.get('yield_units',0);acts=[]
    dying=t.get('consecutive_unwatered',0)>=1
    growing=((maximum+1)//2<=age<=maximum and yu<cap) if not interval else (age+1>=first and (age+1-first)%interval==0 and (age+1-first)//interval<cap)
    expired=t.get('max_lifespan_step',-1)>=0
    wheat_harvest=min(CFG['harvest_wheat'],CFG['early_wheat_yield']) if day<=CFG['early_wheat_until'] else CFG['harvest_wheat']
    ready=age>=first and yu>0 and (interval and (yu>=2 or expired or day==29) or not interval and (yu>=cap or age>=maximum or c=='WHEAT' and yu>=wheat_harvest or day==29))
    # One-time crops can gain units through WATER immediately, before harvest.
    if day<29 or ready or (not interval and age>=first and yu>0):
        wants_fert=growing and t.get('fertilized_until_day',-1)<day and (interval or c=='WHEAT' and CFG['fert_wheat'])
        if CFG['smart_fertilizer']:
            windows=max(0,maximum-max(age,(maximum+1)//2)+1)
            extra=(min(cap,yu+windows+min(3,windows))-min(cap,yu+windows)) if not interval else 2
            wants_fert=growing and t.get('fertilized_until_day',-1)<day and (c!='WHEAT' or CFG['fert_wheat'])
            if wants_fert and extra*prices[c]>max(5,prices['FERTILIZER']):acts.append(['FERTILIZE'])
        elif wants_fert and prices[c]*2>max(8,prices['FERTILIZER']):acts.append(['FERTILIZE'])
        if not t.get('watered_today') and (growing or dying and not ready):acts.append(['WATER'])
    if ready:acts.append(['HARVEST'])
    value=prices[c]*max(1,yu)+seed*.5
    urgent=1000 if dying and not ready and day<29 else 0
    return acts,value+urgent

def animal_tasks(t,day,prices,town):
    a=t['animal'];_,first,interval,cap,product=ANIMAL[a]
    yu=t.get('yield_units',0);acts=[]
    if yu>0:acts.append(['HARVEST'])
    if day==29:return acts,prices[product]*yu
    production=(day+1-t['placed_day']-first)>=0 and (day+1-t['placed_day']-first)%interval==0
    skip=CFG['feed_roi'] and not t.get('consecutive_unfed',0) and prices[product]*1.5<prices['WHEAT'] and demand(town,product)<=1 and not production
    if CFG['feed_collapse_production'] and not t.get('consecutive_unfed',0) and demand(town,product)<=1:
        marginal=min(cap-1,t.get('pending_care_bonus',0)) if production else 1.5
        if marginal*prices[product]<prices['WHEAT']:skip=True
    if CFG['retire_unprofitable'] and day>=CFG['retire_after'] and demand(town,product)<=1 and prices[product]<=2 and prices['FERTILIZER']<=3:
        # No shop draw remains after day 24. An unproductive animal can be
        # deliberately retired instead of buying wheat solely to keep it alive.
        skip=True
    if CFG['terminal_feed_roi'] and day==28:
        missed=t.get('consecutive_unfed',0)
        if not production and (not missed or not yu) or production and not missed and not t.get('pending_care_bonus',0):skip=True
    if not t.get('fed_today') and not skip:acts.append(['FEED'])
    future_ticks=(29-t['placed_day']-first)//interval-(day-t['placed_day']-first)//interval
    useful_care=not CFG['care_cap'] or production or t.get('pending_care_bonus',0)<cap-1
    if CFG['care'] and useful_care and not t.get('cared_today') and not skip and future_ticks>0 and prices[product]>prices['WHEAT']*.5:acts.append(['CARE'])
    if t.get('fertilizer_available') and prices['FERTILIZER']>=CFG['fert_collect_floor']:acts.append(['COLLECT_FERTILIZER'])
    urgent=1000 if t.get('consecutive_unfed',0) and not t.get('fed_today') and not skip else 0
    return acts,prices[product]*max(1,yu)+urgent

def tasks(obs,st):
    day=obs['day'];me=obs['farms'][obs['player']];prices=obs['market']['prices']
    result={}
    for pos,role in st['roles'].items():
        t=me['tiles'][pos[1]][pos[0]];k=kind(t)
        if k in CROP:acts,value=crop_tasks(t,day,prices)
        elif k in ANIMAL:acts,value=animal_tasks(t,day,prices,obs.get('town',{}))
        elif k=='WEED':acts,value=[['DIG']],80
        elif k=='EMPTY' and role in CROP:
            admissible=not CFG['strict_diamond'] or len(me['unlocked_quadrants'])<3 or radius(pos)<=CFG['diamond_radius']
            acts,value=([['PLANT',role],['WATER']],120) if admissible and obs['hour']<21 and day+CROP[role][1]<30 else ([],0)
        elif k=='EMPTY' and role in ANIMAL:acts,value=[['BUILD_COOP' if role=='GOOSE' else 'BUILD_PASTURE'],['PLACE',role]],200
        elif k in ('PASTURE','COOP') and role in ANIMAL:acts,value=[['PLACE',role]],200
        else:acts,value=[],0
        if acts:result[pos]=(acts,value)
    return result

def zones(st,work,n):
    # Contiguous angular sectors keep adjacent daily services on one worker's route.
    order=sorted(work,key=lambda p:(math.atan2(p[1]-4.5,p[0]-4.5),radius(p)))
    if CFG['zone_mode']=='routing':
        routes=[[] for _ in range(n)];duration=[2.]*n;out={}
        # Greedy cheapest insertion with a soft per-worker daily deadline.
        # Far jobs are placed first; nearby jobs can be inserted along their route.
        for pos in sorted(work,key=lambda p:(-radius(p),-len(work[p][0]),p)):
            service=len(work[pos][0])
            if CFG['route_future_service'] and st['roles'][pos] in ANIMAL and any(a[0] in ('PLACE','BUILD_PASTURE','BUILD_COOP') for a in work[pos][0]):service+=2
            best=None
            for uid,route in enumerate(routes):
                for j in range(len(route)+1):
                    before=route[j-1] if j else None;after=route[j] if j<len(route) else None
                    first=distance(before,pos) if before else radius(pos)
                    last=distance(pos,after) if after else 0
                    old=(distance(before,after) if before else radius(after)) if after else 0
                    delta=first+last-old+service
                    cost=delta+CFG['route_balance']*duration[uid]+.8*max(0,duration[uid]+delta-CFG['route_capacity'])**2
                    choice=(cost,uid,j,delta)
                    if best is None or choice<best:best=choice
            _,uid,j,delta=best;routes[uid].insert(j,pos);duration[uid]+=delta;out[pos]=uid
        st['zones']=out;st['zone_count']=n;st['planned_routes']=routes
        return out
    if CFG['zone_mode']=='specialized' and n>1:
        animal=[p for p in order if st['roles'][p] in ANIMAL]
        crops=[p for p in order if st['roles'][p] not in ANIMAL]
        nh=min(n-1,max(1,math.ceil(len(animal)*CFG['herd_worker_effort']/22))) if animal else 0
        if not crops:nh=n
        out={}
        for group,offset,size in ((animal,0,nh),(crops,nh,n-nh)):
            total=sum(len(work[p][0])+1.3 for p in group);done=0.
            for p in group:
                out[p]=offset+min(size-1,int(done/max(1,total)*size));done+=len(work[p][0])+1.3
        st['zones']=out;st['zone_count']=n
        return out
    if CFG['zone_mode']=='strips':order=sorted(work,key=lambda p:(p[0]//2,p[1] if p[0]//2%2==0 else -p[1],p[0]))
    total=sum(len(work[p][0])+1.3 for p in order)
    done=0.;out={}
    for p in order:
        out[p]=min(n-1,int(done/max(1,total)*n));done+=len(work[p][0])+1.3
    st['zones']=out;st['zone_count']=n
    return out

def act_units_greedy(obs,st,work):
    me=obs['farms'][obs['player']];priv=obs['private'];hour=obs['hour'];day=obs['day']
    positions=[tuple(me['farmer'])]+[tuple(p) for p in me['hands']]
    inventories=priv['inventories'];shed=dict(priv['shed']);seeds=dict(priv['seeds'])
    n=len(positions);z=st.get('zones')
    planned=max(n,st.get('hands',n-1)+1) if CFG['planned_zones'] else n
    if z is None or st.get('zone_count')!=planned:z=zones(st,work,planned)
    reserved=set();actions=[]
    fixed=set();st['_fixed_units']=fixed
    owners={p:u for u,p in st['targets'].items() if u<n and p in work}
    deadline=(23 if day==29 else 24) if CFG['full_day'] else (22 if day==29 else 23)
    for uid,pos in enumerate(positions):
        inv=inventories[uid] if uid<len(inventories) else {}
        nearest=min(SHED,key=lambda s:distance(pos,s));back=distance(pos,nearest)
        sellable=sum(inv.get(p,0) for p in PARAMS)
        if day==29 and sellable and hour+back+1>=deadline:
            action=['DROP'] if back==0 else move(pos,nearest)
            if back==0:
                room=100-sum(shed.values())
                for item,count in inv.items():
                    add=max(0,min(count,room));shed[item]=shed.get(item,0)+add;room-=add
            actions.append(action);fixed.add(uid);continue
        # Capital has a deadline too: the first wool/milk harvest can finance
        # expansion TODAY. A free night deposit may be economically too late.
        premium=[p for p in PARAMS if p not in ('WHEAT','FERTILIZER') and inv.get(p,0)>0]
        early_fert=CFG['early_fert_delivery'] and day<=5 and obs['market']['prices']['FERTILIZER']>=30
        if early_fert and inv.get('FERTILIZER',0):premium.append('FERTILIZER')
        cash_item=max(premium,key=lambda p:inv[p]*obs['market']['prices'][p],default=None)
        cash_value=inv.get(cash_item,0)*obs['market']['prices'].get(cash_item,0)
        standing=me['tiles'][pos[1]][pos[0]]
        service_pending=(CFG['finish_service'] or CFG['market_delivery']) and any(
            a[0]=='WATER' and kind(standing) in CROP or
            a[0]=='FEED' and inv.get('WHEAT',0)>0 or
            a[0]=='CARE' and isinstance(standing,dict) and standing.get('fed_today')
            for a in work.get(pos,([],0))[0])
        central_sale=(back==0 and cash_value>=(min(70,CFG['central_sale_value']) if early_fert else CFG['central_sale_value']) and cash_item is not None)
        capital_due=CFG['capital_delivery'] and day<=CFG['delivery_last_day'] and me['money']<CFG['delivery_cash_ceiling'] and hour<18
        deliver=(central_sale or capital_due and cash_value>=(min(120,CFG['capital_value']) if early_fert else CFG['capital_value'])+back*CFG['delivery_distance_cost'] and back<=CFG['delivery_radius'] and hour+back+1<24)
        if CFG['market_delivery'] and cash_item and hour<21 and back<=CFG['market_delivery_radius'] and cash_value/(back+1)>=CFG['market_delivery_value'] and obs['market']['prices'][cash_item]>=PARAMS[cash_item][0]*.5:
            deliver=True
        if CFG['force_early_fert'] and early_fert and cash_item=='FERTILIZER':
            deliver=back<=2 and hour+back+1<24
        if cash_item and not service_pending and deliver:
            if back:
                actions.append(move(pos,nearest));fixed.add(uid);continue
            amount=min(inv[cash_item],max(0,100-sum(shed.values())))
            if amount:
                actions.append(['PLACE',cash_item,amount]);shed[cash_item]=shed.get(cash_item,0)+amount;fixed.add(uid);continue
        if back==0 and sum(inv.get(p,0) for p in premium)>=CFG['opportunistic_drop'] and (hour>7 or day==29):
            room=100-sum(shed.values())
            if room>=sellable:
                for item,count in inv.items():shed[item]=shed.get(item,0)+count
                actions.append(['DROP']);fixed.add(uid);continue
        # Reserve starting supplies for this worker's sector, not arbitrary full stock.
        own=[p for p in work if z.get(p)==uid]
        feed_need=sum(any(a[0]=='FEED' for a in work[p][0]) for p in own)
        if feed_need:feed_need+=CFG['pickup_extra_food']
        fert_need=sum(any(a[0]=='FERTILIZE' for a in work[p][0]) for p in own)
        if back==0:
            took=False
            for item,need in [('WHEAT',feed_need),('FERTILIZER',min(5,fert_need))]:
                qty=min(max(0,need-inv.get(item,0)),shed.get(item,0))
                if qty and hour<18:
                    actions.append(['PICKUP',item,qty]);shed[item]-=qty;took=True;break
            if took:fixed.add(uid);continue
            for a in ANIMAL:
                needing=sum(st['roles'][p]==a and kind(me['tiles'][p[1]][p[0]]) not in ANIMAL for p in own)
                if needing>inv.get(a,0) and shed.get(a,0):
                    qty=min(needing-inv.get(a,0),shed[a]);actions.append(['PICKUP',a,qty]);shed[a]-=qty;took=True;break
            if took:fixed.add(uid);continue
        best=None
        for p,(todo,value) in work.items():
            if p in reserved:continue
            owner=owners.get(p,uid)
            if CFG['protect_targets'] and owner!=uid and distance(positions[owner],p)<distance(pos,p):
                continue
            sequence=[];requires=None
            for a in todo:
                op=a[0]
                if op=='FERTILIZE' and inv.get('FERTILIZER',0)<=0:continue
                if op=='FEED' and inv.get('WHEAT',0)<=0:
                    requires='WHEAT';continue
                if CFG['feed_supply_fix'] and op=='CARE' and not inv.get('WHEAT') and not me['tiles'][p[1]][p[0]].get('fed_today'):
                    continue
                if op in ('BUILD_PASTURE','BUILD_COOP') and inv.get(st['roles'][p],0)<=0:
                    requires=st['roles'][p];break
                if op=='PLACE' and inv.get(a[1],0)<=0:requires=a[1];break
                if op=='PLANT' and seeds.get(a[1],0)<=0:break
                sequence.append(a)
            d=distance(pos,p)
            if not sequence:
                if requires and shed.get(requires,0)>0 and hour+back+2+radius(p)<deadline:
                    score=back+radius(p)+4+CFG['zone_penalty']*(z.get(p)!=uid)
                    candidate=(score,p,['PICKUP',requires,1] if back==0 else move(pos,nearest),True)
                else:continue
            else:
                if day==29 and not any(a[0]=='HARVEST' for a in sequence):continue
                if day==29 and CFG['final_bundle_fix'] and hour+d+len(sequence)+radius(p)+1>deadline:
                    sequence=[a for a in sequence if a[0]=='HARVEST']
                if hour+d+1+(radius(p)+1 if day==29 else 0)>deadline:continue
                # Finish bundles locally, but emergency survival can pull nearby helpers.
                score=d+CFG['zone_penalty']*(z.get(p)!=uid)-min(3.,value/600)
                if st['targets'].get(uid)==p:score-=1.0
                if p==pos:score-=2.
                candidate=(score,p,sequence[0] if d==0 else move(pos,p),False)
            if best is None or (candidate[0],candidate[1])<(best[0],best[1]):best=candidate
        if best:
            _,target,action,supply=best;reserved.add(target);st['targets'][uid]=target
            if supply:fixed.add(uid)
            if action[0]=='PLANT':seeds[action[1]]-=1
            if action[0]=='PICKUP':shed[action[1]]-=action[2]
            actions.append(action)
        else:actions.append(['PASS'])
    return actions,shed

def minimum_assignment(costs):
    """Rectangular Hungarian assignment, deterministic ties, O(n*n*m)."""
    n=len(costs)
    if not n:return []
    m=len(costs[0]);u=[0.]*(n+1);v=[0.]*(m+1);p=[0]*(m+1);way=[0]*(m+1)
    for i in range(1,n+1):
        p[0]=i;j0=0;minimum=[float('inf')]*(m+1);used=[False]*(m+1)
        while True:
            used[j0]=True;i0=p[j0];delta=float('inf');j1=0
            for j in range(1,m+1):
                if not used[j]:
                    cur=costs[i0-1][j-1]-u[i0]-v[j]
                    if cur<minimum[j]:minimum[j]=cur;way[j]=j0
                    if minimum[j]<delta:delta=minimum[j];j1=j
            for j in range(m+1):
                if used[j]:u[p[j]]+=delta;v[j]-=delta
                else:minimum[j]-=delta
            j0=j1
            if p[j0]==0:break
        while True:
            j1=way[j0];p[j0]=p[j1];j0=j1
            if j0==0:break
    answer=[-1]*n
    for j in range(1,m+1):
        if p[j]:answer[p[j]-1]=j-1
    return answer

def act_units(obs,st,work):
    previous_targets=dict(st['targets'])
    actions,shed=act_units_greedy(obs,st,work)
    if CFG['scheduler']!='auction':return actions,shed
    me=obs['farms'][obs['player']];priv=obs['private'];hour=obs['hour'];day=obs['day']
    pos=[tuple(me['farmer'])]+[tuple(p) for p in me['hands']]
    fixed=st['_fixed_units']
    workers=[i for i in range(len(pos)) if i not in fixed]
    fixed_tiles={pos[i] for i in fixed if actions[i][0]=='PLACE' and len(actions[i])>1 and actions[i][1] in ANIMAL}
    tiles=sorted(p for p in work if p not in fixed_tiles)
    costs=[];commands=[]
    seeds=dict(priv['seeds'])
    for uid in workers:
        inv=priv['inventories'][uid] if uid<len(priv['inventories']) else {}
        row=[];cmd=[]
        for p in tiles:
            todo,value=work[p];valid=[]
            for a in todo:
                op=a[0]
                if op=='FERTILIZE' and not inv.get('FERTILIZER'):continue
                if op=='FEED' and not inv.get('WHEAT'):continue
                if op=='CARE':
                    t=me['tiles'][p[1]][p[0]]
                    if not t.get('fed_today') and not inv.get('WHEAT'):continue
                if op in ('BUILD_PASTURE','BUILD_COOP') and not inv.get(st['roles'][p]):break
                if op=='PLACE' and not inv.get(a[1]):break
                if op=='PLANT' and not seeds.get(a[1]):break
                valid.append(a)
            d=distance(pos[uid],p)
            deadline=(23 if day==29 else 24) if CFG['full_day'] else (22 if day==29 else 23)
            if day==29 and CFG['final_bundle_fix'] and hour+d+len(valid)+radius(p)+1>deadline:
                valid=[a for a in valid if a[0]=='HARVEST']
            if not valid or hour+d+1+(radius(p)+1 if day==29 else 0)>deadline or day==29 and not any(a[0]=='HARVEST' for a in valid):
                row.append(1e6);cmd.append(['PASS']);continue
            action=valid[0] if d==0 else move(pos[uid],p)
            urgency=min(8,value/250)*(1.8 if hour>=17 else 1.)
            zone_cost=CFG['zone_penalty']
            if CFG['late_zone_decay']:zone_cost*=max(0.,1-max(0,hour-10)/13)
            cost=d+.15*len(valid)-urgency+zone_cost*(st['zones'].get(p)!=uid)
            if pos[uid]==p:cost-=2
            if previous_targets.get(uid)==p:cost-=.4
            row.append(cost);cmd.append(action)
        costs.append(row+[50.]*len(workers));commands.append(cmd)
    matched=minimum_assignment(costs)
    for index,uid in enumerate(workers):
        j=matched[index]
        if j>=len(tiles) or costs[index][j]>=1e5:
            actions[uid]=['PASS'];st['targets'].pop(uid,None);continue
        action=commands[index][j]
        if action[0]=='PLANT':
            crop=action[1]
            if seeds.get(crop,0)<=0:action=['PASS']
            else:seeds[crop]-=1
        actions[uid]=action;st['targets'][uid]=tiles[j]
    return actions,shed

def idle_deliveries(obs,actions,shed):
    """Use otherwise idle actions to sell loads before a forecast night overflow.

    Never orders a general return: at most enough idle loads to cover the excess,
    and never steals an action already assigned to a live field task.
    """
    if not CFG['idle_delivery'] or obs['day']==29 or obs['hour']<12:return actions,shed
    me=obs['farms'][obs['player']];invs=obs['private']['inventories'];hour=obs['hour']
    excess=sum(shed.values())+sum(sum(i.values()) for i in invs)-CFG['overflow_target']
    if CFG['idle_delivery']=='all':excess=10000
    if excess<=0:return actions,shed
    positions=[tuple(me['farmer'])]+[tuple(p) for p in me['hands']]
    choices=[]
    for uid,pos in enumerate(positions):
        if actions[uid]!=['PASS']:continue
        nearest=min(SHED,key=lambda p:distance(pos,p));back=distance(pos,nearest)
        if hour+back+1>24:continue
        inv=invs[uid]
        options=[p for p in PARAMS if inv.get(p,0) and (p!='WHEAT' or hour>=20)]
        if not options:continue
        item=max(options,key=lambda p:inv[p]*obs['market']['prices'][p])
        qty=inv[item]
        if obs['market']['prices'][item]*qty<30:continue
        choices.append(((back+1)/qty,uid,item,qty,nearest,back))
    for _,uid,item,qty,nearest,back in sorted(choices):
        if excess<=0:break
        if back:actions[uid]=move(positions[uid],nearest)
        else:
            qty=min(qty,max(0,100-sum(shed.values())))
            if not qty:continue
            actions[uid]=['PLACE',item,qty];shed[item]=shed.get(item,0)+qty
        excess-=qty
    return actions,shed

def market_orders(obs,st,shed):
    me=obs['farms'][obs['player']];priv=obs['private'];day=obs['day'];hour=obs['hour']
    prices=obs['market']['prices'];mi=obs['market']['inventory'];money=me['money'];orders=[]
    ct=counts(me);herd=sum(ct.get(a,0) for a in ANIMAL)
    carry={p:sum(i.get(p,0) for i in priv['inventories']) for p in PARAMS}
    final_feeds=None
    if CFG['feed_task_budget'] or CFG['terminal_feed_roi'] and day==28:
        final_feeds=sum(any(a[0]=='FEED' for a in todo) for todo,_ in tasks(obs,st).values())
    projected=sum(shed.values())+sum(carry.values())
    # Sell first so receipts can finance this turn's purchases. Never assume held crops count as score.
    items=sorted(PARAMS,key=lambda p:(-prices[p],p))
    if CFG['market_rank']=='impact':
        items=sorted(PARAMS,key=lambda p:(-(prices[p]-price(p,mi[p]+max(1,shed.get(p,0))))*shed.get(p,0),-prices[p],p))
    elif CFG['market_rank']=='revenue':items=sorted(PARAMS,key=lambda p:(-prices[p]*shed.get(p,0),p))
    for item in items:
        have=shed.get(item,0)
        keep=0
        if day<29:
            if item=='WHEAT':keep=max(0,math.ceil(herd*(1.5 if hour<16 else .8))-carry[item])
            if item=='WHEAT' and final_feeds is not None:keep=max(0,final_feeds-carry[item])
            if item=='FERTILIZER':
                # Fertilizer is opening liquidity until there are valuable targets.
                willing=prices['FERTILIZER']<prices['WHEAT']*1.5 or day>=9
                keep=max(0,(CFG['fert_stock'] if willing else 0)-carry[item])
        amount=max(0,have-keep)
        if not amount:continue
        floor=max(1,int(PARAMS[item][0]*CFG['premium_floor']))
        if day>=28 or projected>85 or money<300:floor=1
        # Wait for a known next-night recovery only when it is worth inventory exposure.
        if day<28 and hour>2 and item in ('MILK','WOOL','STRAWBERRY') and projected<60 and money>1000:
            floor=max(floor,int(forecast(obs,item,1)*.8))
        qty=0;revenue=0
        while qty<amount and price(item,mi[item]+qty)>=floor:
            revenue+=price(item,mi[item]+qty);qty+=1
        if qty:
            orders.append(['SELL',item,qty]);money+=revenue;shed[item]-=qty
    def append(order,cost):
        nonlocal money
        if len(orders)<10 and money>=cost:
            orders.append(order);money-=cost;return True
        return False
    # Provision survival before discretionary labour and investment.
    food_reserve=max(0,herd-shed.get('WHEAT',0)-carry['WHEAT'])*prices['WHEAT'] if day<29 else 0
    current=len(me['hands']);hires=me.get('hires_today',current)
    while current<st['hands'] and hour<8:
        if money-fibonacci(hires)<food_reserve or not append(['HIRE'],fibonacci(hires)):break
        current+=1;hires+=1
    if day==29:return orders[:10]
    # Midday purchases are justified by observed shortages, not by a blind order queue.
    unfed=sum(1 for row in me['tiles'] for t in row if isinstance(t,dict) and t.get('animal') and not t.get('fed_today'))
    wheat_need=max(0,(unfed+sum(st['herd'].values())//3 if final_feeds is None else final_feeds)-shed.get('WHEAT',0)-carry['WHEAT'])
    if wheat_need and hour<19:
        qty=wheat_need
        while qty and sum(price('WHEAT',mi['WHEAT']-i-1) for i in range(qty))>money-10:qty-=1
        if qty:append(['BUY_PRODUCT','WHEAT',qty],sum(price('WHEAT',mi['WHEAT']-i-1) for i in range(qty)))
    if CFG['buy_fertilizer'] and hour<19 and prices['FERTILIZER']<=CFG['fertilizer_buy_ceiling']:
        wanted=sum(any(a[0]=='FERTILIZE' for a in todo) for todo,_ in tasks(obs,st).values())
        available=priv['shed'].get('FERTILIZER',0)+carry['FERTILIZER']
        qty=min(12,max(0,wanted-available))
        while qty and (sum(price('FERTILIZER',mi['FERTILIZER']-i-1) for i in range(qty))>money-100 or sum(shed.values())+qty>90):qty-=1
        if qty:append(['BUY_PRODUCT','FERTILIZER',qty],sum(price('FERTILIZER',mi['FERTILIZER']-i-1) for i in range(qty)))
    reserve=CFG['investment_reserve']+max(0,herd-priv['shed'].get('WHEAT',0)-carry['WHEAT'])*prices['WHEAT']
    q=len(me['unlocked_quadrants']);land_day=CFG['land2_day'] if q==1 else CFG['land3_day'] if q==2 else CFG['land4_day']
    land_cost=(1000,2000,4000)[min(2,q-1)]
    def acquire_land():
        if q<4 and (q<3 or CFG['four_quadrants']) and land_day<=day<=16 and money>land_cost+reserve+CFG['land_buffer']:
            append(['BUY_LAND'],land_cost)
    if CFG['land_first']:acquire_land()
    for a,data in ANIMAL.items():
        # Transfers within this turn do not change owned headcount. Using the
        # post-PICKUP shed with pre-PICKUP inventories would buy replacements!
        held=priv['shed'].get(a,0)+sum(i.get(a,0) for i in priv['inventories'])
        need=st['herd'][a]-ct.get(a,0)-held
        if need>0 and hour<14:
            qty=min(need,max(0,int((money-reserve)//data[0])))
            if qty:append(['BUY_ANIMAL',a,qty],qty*data[0])
    if not CFG['land_first']:acquire_land()
    for crop,data in CROP.items():
        if CFG['seed_horizon_fix'] and day+data[1]>=30:continue
        needed=sum(role==crop and kind(me['tiles'][p[1]][p[0]]) in ('EMPTY','WEED')
                   and (not CFG['strict_diamond'] or len(me['unlocked_quadrants'])<3 or radius(p)<=CFG['diamond_radius'])
                   for p,role in st['roles'].items())-priv['seeds'].get(crop,0)
        if needed>0 and hour<18:
            qty=min(needed,max(0,int((money-50)//data[0])))
            if qty:append(['BUY_SEED',crop,qty],qty*data[0])
    return orders[:10]

def decide(obs,st):
    player=obs['player'];step=obs.get('step',obs['day']*24+obs['hour'])
    structural=(CFG['react_land'] and st.get('quadrants')!=len(obs['farms'][player]['unlocked_quadrants']) or CFG['rotate_crops'] and st.get('rotation_pending'))
    if st['day']!=obs['day'] or structural or obs['hour'] in CFG['replan_hours'] and obs['farms'][player]['money']>400:
        keep_routes=(st.get('day')==obs['day'] and st.get('quadrants')==len(obs['farms'][player]['unlocked_quadrants']) and structural)
        previous={k:st.get(k) for k in ('zones','targets','zone_count','hands')}
        plan(obs,st)
        if keep_routes:st.update(previous)
        st['rotation_pending']=False
    work=tasks(obs,st)
    actions,shed=act_units(obs,st,work)
    actions,shed=idle_deliveries(obs,actions,shed)
    orders=market_orders(obs,st,shed)
    if CFG['rotate_crops']:
        positions=[obs['farms'][player]['farmer']]+obs['farms'][player]['hands']
        for pos,action in zip(positions,actions):
            tile=obs['farms'][player]['tiles'][pos[1]][pos[0]]
            if action[0]=='HARVEST' and kind(tile) in CROP and not CROP[kind(tile)][3] and (CFG['rotation_scope']=='all' or kind(tile)==CFG['rotation_scope']):st['rotation_pending']=True
    st['last_step']=step
    return {'farmer':actions[0],'hands':actions[1:],'market':orders}

def shadow_step(obs,action):
    """Own-farm transition for short lookahead, assuming no rival market orders.

    Predicts deterministic local mechanics only. Does not generate unknown weeds
    or shops, and never reconstructs a seed or an opponent's private inventory.
    """
    farm=obs['farms'][obs['player']];priv=obs['private'];day=obs['day'];step=obs['step']
    tiles=farm['tiles'];shed=priv['shed'];seeds=priv['seeds'];market=obs['market']['inventory']
    positions=[farm['farmer']]+farm['hands'];inventories=priv['inventories']
    acts=[action.get('farmer',['PASS'])]+action.get('hands',[])
    planting={}
    for a in acts:
        if a[0]=='PLANT':planting[a[1]]=planting.get(a[1],0)+1
    blocked={c for c,n in planting.items() if n>seeds.get(c,0)}
    moves={'NORTH':(0,-1),'SOUTH':(0,1),'WEST':(-1,0),'EAST':(1,0)}
    for uid,(pos,inv,a) in enumerate(zip(positions,inventories,acts)):
        op=a[0];x,y=pos;tile=tiles[y][x]
        def add(item,n):inv[item]=inv.get(item,0)+n
        def take(item,n=1):
            if inv.get(item,0)<n:return False
            inv[item]-=n
            if inv[item]==0:del inv[item]
            return True
        if op in moves:
            dx,dy=moves[op];nx=x+dx;ny=y+dy
            if 0<=nx<10 and 0<=ny<10:
                if uid==0:farm['farmer']=[nx,ny]
                else:farm['hands'][uid-1]=[nx,ny]
            continue
        at_shed=(x,y) in SHED
        if op=='DROP' and at_shed:
            for item,n in list(inv.items()):shed[item]=shed.get(item,0)+min(n,max(0,100-sum(shed.values())))
            inv.clear();continue
        if op=='PICKUP' and at_shed:
            item=a[1];n=min(a[2] if len(a)>2 else 1,shed.get(item,0))
            if n>0:shed[item]-=n;add(item,n)
            continue
        if op=='PLACE':
            item=a[1]
            structure='COOP' if item=='GOOSE' else 'PASTURE'
            if item in ANIMAL and kind(tile)==structure:
                if take(item):tiles[y][x]={'kind':structure,'animal':item,'placed_day':day,'yield_units':0,'consecutive_unfed':0,'fed_today':False,'cared_today':False,'fertilizer_available':False,'pending_care_bonus':0}
            elif at_shed:
                n=min(a[2] if len(a)>2 else 1,inv.get(item,0),max(0,100-sum(shed.values())))
                if n>0:take(item,n);shed[item]=shed.get(item,0)+n
            continue
        if tile=='LOCKED':continue
        if op=='DIG' and kind(tile) not in ANIMAL:tiles[y][x]=None
        elif op in ('BUILD_COOP','BUILD_PASTURE') and tile is None:tiles[y][x]={'kind':op[6:]}
        elif op=='PLANT' and tile is None and a[1] not in blocked and seeds.get(a[1],0)>0:
            c=a[1];seeds[c]-=1;interval=CROP[c][3]
            tiles[y][x]={'kind':'PLANT','crop':c,'planted_day':day,'watered_today':False,'consecutive_unwatered':1,'yield_units':0 if interval else 1,'max_lifespan_step':-1 if interval else (day+CROP[c][2]+1)*24,'fertilized_until_day':-1}
        elif op=='WATER' and kind(tile) in CROP and not tile['watered_today']:
            tile['watered_today']=True;c=tile['crop'];_,_,maximum,interval,cap=CROP[c];age=day-tile['planted_day']
            if not interval and (maximum+1)//2<=age<=maximum:tile['yield_units']=min(cap,tile['yield_units']+(2 if tile['fertilized_until_day']>=day else 1))
        elif op=='FERTILIZE' and kind(tile) in CROP and take('FERTILIZER'):tile['fertilized_until_day']=max(tile['fertilized_until_day'],day+2)
        elif op=='HARVEST' and isinstance(tile,dict) and tile.get('yield_units',0)>0:
            c=tile.get('crop');a_kind=tile.get('animal')
            if c and day-tile['planted_day']>=CROP[c][1]:
                add(c,tile['yield_units']);tile['yield_units']=0
                if not CROP[c][3]:tiles[y][x]=None
            elif a_kind:add(ANIMAL[a_kind][4],tile['yield_units']);tile['yield_units']=0
        elif kind(tile) in ANIMAL:
            if op=='FEED' and not tile['fed_today'] and take('WHEAT'):tile['fed_today']=True
            elif op=='CARE':tile['cared_today']=True
            elif op=='COLLECT_FERTILIZER' and tile['fertilizer_available']:tile['fertilizer_available']=False;add('FERTILIZER',1)
    for order in action.get('market',[])[:10]:
        op=order[0]
        if op=='HIRE':
            cost=fibonacci(farm['hires_today'])
            if farm['money']>=cost:
                farm['money']-=cost;farm['hires_today']+=1
                present=[tuple(farm['farmer'])]+[tuple(p) for p in farm['hands']]
                spawn=min(SHED,key=lambda p:(present.count(p),SHED.index(p)))
                farm['hands'].append(list(spawn));inventories.append({})
        elif op=='BUY_LAND':
            q=len(farm['unlocked_quadrants'])
            if q<4 and farm['money']>=(1000,2000,4000)[q-1]:
                farm['money']-=(1000,2000,4000)[q-1];quadrant=('NE','SW','SE')[q-1]
                farm['unlocked_quadrants'].append(quadrant)
                for y in range(10):
                    for x in range(10):
                        if ('N' if y<5 else 'S')+('W' if x<5 else 'E')==quadrant and tiles[y][x]=='LOCKED':tiles[y][x]=None
        elif len(order)>=3:
            item=order[1]
            for _ in range(order[2]):
                if op=='SELL' and item in PARAMS and shed.get(item,0):
                    quote=price(item,market[item]);farm['money']+=quote;shed[item]-=1
                    if quote>1:market[item]+=1
                elif op in ('BUY_PRODUCT','BUY_ANIMAL','BUY_SEED'):
                    quote=price(item,market[item]-1) if op=='BUY_PRODUCT' else ANIMAL[item][0] if op=='BUY_ANIMAL' else CROP[item][0]
                    if farm['money']<quote or op!='BUY_SEED' and sum(shed.values())>=100:break
                    farm['money']-=quote
                    if op=='BUY_SEED':seeds[item]=seeds.get(item,0)+1
                    else:shed[item]=shed.get(item,0)+1
                    if op=='BUY_PRODUCT':market[item]-=1
                else:break
    if step%4==0:
        for shop in obs.get('town',{}).get('unlocked_shops',[]):
            for item in SHOP.get(shop,()):market[item]-=1
    if step%24==0:
        for item in PARAMS:
            if item!='FERTILIZER':market[item]-=1
    obs['market']['prices']={item:price(item,n) for item,n in market.items()}
    for y,row in enumerate(tiles):
        for x,t in enumerate(row):
            if kind(t) not in CROP:continue
            end=t['max_lifespan_step']
            if end>=0 and step>=end and (step-end)%2==0:
                t['yield_units']-=1
                if t['yield_units']<=0:tiles[y][x]={'kind':'WEED'}
    if (step+1)%24==0:
        for y,row in enumerate(tiles):
            for x,t in enumerate(row):
                k=kind(t)
                if k in CROP:
                    watered=t['watered_today'];t['watered_today']=False;t['consecutive_unwatered']=0 if watered else t['consecutive_unwatered']+1
                    if t['consecutive_unwatered']>=2:tiles[y][x]={'kind':'WEED'};continue
                    _,first,_,interval,cap=CROP[k];elapsed=day+1-t['planted_day']-first
                    if interval and elapsed>=0 and elapsed%interval==0 and elapsed//interval<cap:
                        t['yield_units']=min(cap,t['yield_units']+(2 if watered and t['fertilized_until_day']>=day else 1))
                        if elapsed//interval==cap-1:t['max_lifespan_step']=(day+2)*24
                elif k in ANIMAL:
                    t['consecutive_unfed']=0 if t['fed_today'] else t['consecutive_unfed']+1
                    if t['consecutive_unfed']>=2:tiles[y][x]={'kind':'COOP' if k=='GOOSE' else 'PASTURE'};continue
                    _,first,interval,cap,_=ANIMAL[k];elapsed=day+1-t['placed_day']-first
                    if elapsed>=0 and elapsed%interval==0:
                        t['yield_units']=min(cap,t['yield_units']+1+(t.get('pending_care_bonus',0) if t['fed_today'] else 0));t['pending_care_bonus']=0
                    if t['cared_today'] and t['fed_today']:t['pending_care_bonus']=t.get('pending_care_bonus',0)+1
                    t['fed_today']=False;t['cared_today']=False;t['fertilizer_available']=True
        for inv in inventories:
            for item,n in inv.items():shed[item]=shed.get(item,0)+min(n,max(0,100-sum(shed.values())))
        priv['inventories']=[{}];farm['farmer']=[4,4];farm['hands']=[];farm['hires_today']=0
    obs['step']=step+1;obs['day']=(step+1)//24;obs['hour']=(step+1)%24

def shadow_value(obs):
    farm=obs['farms'][obs['player']];priv=obs['private'];day=obs['day']
    if obs['step']>=719:return farm['money']
    prices=obs['market']['prices'];value=farm['money']
    goods=dict(priv['shed'])
    for inv in priv['inventories']:
        for item,n in inv.items():goods[item]=goods.get(item,0)+n
    for item,n in goods.items():
        if item in PARAMS:value+=sum(price(item,obs['market']['inventory'][item]+j) for j in range(n))
        elif item in ANIMAL:value+=n*ANIMAL[item][0]
    value+=sum(priv['seeds'].get(c,0)*CROP[c][0] for c in CROP)
    if day<19:value+=(0,1000,3000,7000)[len(farm['unlocked_quadrants'])-1]
    for row in farm['tiles']:
        for tile in row:
            k=kind(tile)
            if k in ANIMAL:
                cost,first,interval,cap,product=ANIMAL[k]
                quote=.6*prices[product]+.4*PARAMS[product][0]
                ticks=max(0,(29-tile['placed_day']-first)//interval-(day-tile['placed_day']-first)//interval)
                value+=tile.get('yield_units',0)*quote+min(cap-1,tile.get('pending_care_bonus',0))*quote*.85
                value+=CFG['lookahead_field_weight']*(cost*.5+ticks*(interval+1)*quote)
            elif k in CROP:
                seed,first,maximum,interval,cap=CROP[k];quote=.6*prices[k]+.4*PARAMS[k][0]
                value+=tile.get('yield_units',0)*quote
                if interval:
                    ticks=sum(day<tile['planted_day']+first+i*interval<=29 for i in range(cap))
                    value+=CFG['lookahead_field_weight']*ticks*1.7*quote
                elif tile['planted_day']+first<=29:
                    value+=CFG['lookahead_field_weight']*max(0,cap-tile.get('yield_units',0))*quote
    return value

def choose_tactics(obs,st):
    choices=[{}, {'zone_penalty':3.}, {'zone_penalty':9.}, {'pickup_extra_food':1},
             {'zone_mode':'routing'}, {'zone_penalty':0.}, {'pickup_extra_food':2}][:CFG['lookahead_choices']]
    original=dict(CFG);results=[]
    try:
        for patch in choices:
            CFG.clear();CFG.update(original);CFG.update(patch)
            world=copy.deepcopy(obs);memory=copy.deepcopy(st)
            remaining=min(24-obs['hour'],719-obs['step'])
            for _ in range(remaining):shadow_step(world,decide(world,memory))
            results.append(shadow_value(world))
    finally:CFG.clear();CFG.update(original)
    chosen=max(range(len(choices)),key=lambda i:(results[i],-i))
    st['lookahead_scores']=results
    return choices[chosen]

def agent(obs,configuration=None):
    player=obs['player'];step=obs.get('step',obs['day']*24+obs['hour'])
    if player not in _STATE or step<=_STATE[player].get('last_step',-1):_STATE[player]={'day':-1}
    st=_STATE[player]
    if not CFG['lookahead']:return decide(obs,st)
    if st.get('tactics_day')!=obs['day']:
        st['tactics']=choose_tactics(obs,st);st['tactics_day']=obs['day']
    original=dict(CFG)
    try:
        CFG.update(st.get('tactics',{}));return decide(obs,st)
    finally:CFG.clear();CFG.update(original)
