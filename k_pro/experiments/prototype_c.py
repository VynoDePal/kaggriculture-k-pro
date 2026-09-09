"""K Pro 1: observation-driven economy, spatial contracts and finite-horizon work.

Standalone stdlib agent. No action tape, opponent identity, seed or future state.
Game constants are transcribed from kaggle_environments Kaggriculture 1.32.7.
"""
import math

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
           delivery_cash_ceiling=4000,central_sale_value=200)
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
                inventory+=total-public-optimism*new_shops*gain
            values.append(cash)
        feed=(29-day)*obs['market']['prices']['WHEAT']
        fertilizer=(29-day)*min(12,obs['market']['prices']['FERTILIZER'])
        candidates.append(values[1]-values[0]-cost-feed+fertilizer)
    return sum(candidates)/len(candidates)-.2*(max(candidates)-min(candidates))

def plan(obs,st):
    day=obs['day'];me=obs['farms'][obs['player']];priv=obs['private']
    ct=counts(me);p=obs['market']['prices'];town=obs.get('town',{})
    money=me['money'];q=len(me['unlocked_quadrants'])
    animal_n=sum(ct.get(a,0) for a in ANIMAL)
    # Herd decisions use public demand/supply. Opening is an explicit capital budget.
    targets={a:ct.get(a,0) for a in ANIMAL}
    if day==0:
        targets['SHEEP']=CFG['open_sheep'];targets['COW']=CFG['open_cows']
    elif day<=16:
        limit=min(CFG['max_animals'],CFG['open_sheep']+CFG['open_cows']+max(0,day-1)*2)
        if money>400 and animal_n<limit:
            choices=[]
            for a,data in ANIMAL.items():
                if a=='GOOSE' and ct.get(a,0)>=CFG['max_geese']:continue
                if CFG['herd_policy']=='balanced' and a in ('COW','SHEEP'):
                    rival=counts(obs['farms'][1-obs['player']])
                    milk_share=max(.3,min(.7,.5+.012*(demand(town,'MILK')-demand(town,'WOOL'))-.02*(rival.get('COW',0)-rival.get('SHEEP',0))))
                    share=milk_share if a=='COW' else 1-milk_share
                    if ct.get(a,0)>=math.ceil(CFG['max_animals']*share):continue
                cost,first,interval,cap,product=data
                ticks=max(0,(29-day-first)//interval+1)
                fw=CFG['animal_forecast_weight']
                fp=fw*forecast(obs,product,8)+(1-fw)*(.6*p[product]+.4*PARAMS[product][0])
                # Includes feed purchase and opportunity cost of daily service.
                net=(herd_value(obs,a) if CFG['herd_policy']=='margin' else
                     ticks*(interval+1)*fp+(29-day)*min(15,p['FERTILIZER'])-(29-day)*p['WHEAT']-cost)
                choices.append((net/max(1,cost),a))
            if choices:
                value,a=max(choices)
                if value>1.0:targets[a]+=min(CFG['herd_batch'],limit-animal_n)
    pending={a:priv['shed'].get(a,0)+sum(i.get(a,0) for i in priv['inventories']) for a in ANIMAL}
    for a in ANIMAL:targets[a]=max(targets[a],ct.get(a,0)+pending[a])
    herd=sum(targets.values())
    # Live crop capacity: planting every available tile is not a free action.
    wheat_target=min(CFG['wheat_max'],max(CFG['open_wheat'],math.ceil(herd*CFG['wheat_ratio']))) if day<=CFG['late_wheat_day'] else 0
    straw_target=0 if day<CFG['straw_start_day'] else min(CFG['max_straw'],2+day*3)
    if day>16:straw_target=ct.get('STRAWBERRY',0)
    if day>=3 and forecast(obs,'STRAWBERRY',8)<20:straw_target=min(straw_target,8)
    melon_target=CFG['open_melons'] if day==0 else ct.get('MELON',0)
    if 11<=day<=18 and forecast(obs,'MELON',10)>100:melon_target=max(melon_target,6)
    carrot_target=0
    if 20<=day<=26 and p['CARROT']>35:carrot_target=min(20,8+int(demand(town,'CARROT')/2))
    wanted={'WHEAT':wheat_target,'STRAWBERRY':straw_target,'MELON':melon_target,'CARROT':carrot_target}
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
            if not eligible:break
            slot=min(eligible,key=lambda pos:(0 if kind(me['tiles'][pos[1]][pos[0]])==structure else 1,radius(pos),pos))
            roles[slot]=a;free.remove(slot)
    if day<6:
        # Preserve the two near-shed sites for early herd expansion. They can
        # be reassigned once the initial expansion window has passed.
        protected=max(0,CFG['reserve_herd_sites']-(herd-CFG['open_sheep']-CFG['open_cows']))
        free=free[protected:]
    for c in ('MELON','WHEAT','STRAWBERRY','CARROT'):
        for _ in range(max(0,wanted[c]-ct.get(c,0))):
            allowed=[pos for pos in free if kind(me['tiles'][pos[1]][pos[0]]) not in ('PASTURE','COOP') and (q<3 or radius(pos)<=CFG['diamond_radius'])]
            if not allowed:break
            # Low-touch melons farther out; frequent crops occupy short routes.
            slot=min(allowed,key=lambda pos:((-radius(pos) if c=='MELON' and day<2 else radius(pos)),pos))
            roles[slot]=c;free.remove(slot)
    workload=sum(CFG['animal_work'] if k in ANIMAL else CFG['crop_work'] for k in roles.values())
    hands=min(CFG['max_hands'],max(3,math.ceil(workload/CFG['work_per_hand'])))
    if day==0:hands=CFG['open_hands']
    if day>=28:hands=max(3,min(CFG['max_hands'],math.ceil(workload/15)))
    st.update(day=day,roles=roles,herd=targets,hands=hands,targets={},zones=None)

def crop_tasks(t,day,prices):
    c=t['crop'];seed,first,maximum,interval,cap=CROP[c]
    age=day-t['planted_day'];yu=t.get('yield_units',0);acts=[]
    dying=t.get('consecutive_unwatered',0)>=1
    growing=((maximum+1)//2<=age<=maximum and yu<cap) if not interval else (age+1>=first and (age+1-first)%interval==0 and (age+1-first)//interval<cap)
    expired=t.get('max_lifespan_step',-1)>=0
    ready=age>=first and yu>0 and (interval and (yu>=2 or expired or day==29) or not interval and (yu>=cap or age>=maximum or c=='WHEAT' and yu>=CFG['harvest_wheat'] or day==29))
    # One-time crops can gain units through WATER immediately, before harvest.
    if day<29 or ready or (not interval and age>=first and yu>0):
        wants_fert=growing and t.get('fertilized_until_day',-1)<day and (interval or c=='WHEAT' and CFG['fert_wheat'])
        if wants_fert and prices[c]*2>max(8,prices['FERTILIZER']):acts.append(['FERTILIZE'])
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
    if not t.get('fed_today') and not skip:acts.append(['FEED'])
    future_ticks=(29-t['placed_day']-first)//interval-(day-t['placed_day']-first)//interval
    if CFG['care'] and not t.get('cared_today') and not skip and future_ticks>0 and prices[product]>prices['WHEAT']*.5:acts.append(['CARE'])
    if t.get('fertilizer_available') and prices['FERTILIZER']>=CFG['fert_collect_floor']:acts.append(['COLLECT_FERTILIZER'])
    urgent=1000 if t.get('consecutive_unfed',0) and not t.get('fed_today') else 0
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
    deadline=22 if day==29 else 23
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
        cash_item=max(premium,key=lambda p:inv[p]*obs['market']['prices'][p],default=None)
        cash_value=inv.get(cash_item,0)*obs['market']['prices'].get(cash_item,0)
        central_sale=(back==0 and cash_value>=CFG['central_sale_value'] and cash_item is not None)
        capital_due=CFG['capital_delivery'] and day<=CFG['delivery_last_day'] and me['money']<CFG['delivery_cash_ceiling'] and hour<18
        if cash_item and (central_sale or capital_due and cash_value>=CFG['capital_value']+back*50 and back<=4):
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
            deadline=22 if day==29 else 23
            if not valid or hour+d+1+(radius(p)+1 if day==29 else 0)>deadline or day==29 and not any(a[0]=='HARVEST' for a in valid):
                row.append(1e6);cmd.append(['PASS']);continue
            action=valid[0] if d==0 else move(pos[uid],p)
            urgency=min(8,value/250)*(1.8 if hour>=17 else 1.)
            cost=d+.15*len(valid)-urgency+CFG['zone_penalty']*(st['zones'].get(p)!=uid)
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

def market_orders(obs,st,shed):
    me=obs['farms'][obs['player']];priv=obs['private'];day=obs['day'];hour=obs['hour']
    prices=obs['market']['prices'];mi=obs['market']['inventory'];money=me['money'];orders=[]
    ct=counts(me);herd=sum(ct.get(a,0) for a in ANIMAL)
    carry={p:sum(i.get(p,0) for i in priv['inventories']) for p in PARAMS}
    projected=sum(shed.values())+sum(carry.values())
    # Sell first so receipts can finance this turn's purchases. Never assume held crops count as score.
    items=sorted(PARAMS,key=lambda p:(-prices[p],p))
    for item in items:
        have=shed.get(item,0)
        keep=0
        if day<29:
            if item=='WHEAT':keep=max(0,math.ceil(herd*(1.5 if hour<16 else .8))-carry[item])
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
    wheat_need=max(0,unfed+sum(st['herd'].values())//3-shed.get('WHEAT',0)-carry['WHEAT'])
    if wheat_need and hour<19:
        qty=wheat_need
        while qty and sum(price('WHEAT',mi['WHEAT']-i-1) for i in range(qty))>money-10:qty-=1
        if qty:append(['BUY_PRODUCT','WHEAT',qty],sum(price('WHEAT',mi['WHEAT']-i-1) for i in range(qty)))
    reserve=CFG['investment_reserve']+max(0,herd-priv['shed'].get('WHEAT',0)-carry['WHEAT'])*prices['WHEAT']
    q=len(me['unlocked_quadrants']);land_day=CFG['land2_day'] if q==1 else CFG['land3_day'] if q==2 else CFG['land4_day']
    land_cost=(1000,2000,4000)[min(2,q-1)]
    if q<4 and (q<3 or CFG['four_quadrants']) and land_day<=day<=16 and money>land_cost+reserve+CFG['land_buffer']:
        append(['BUY_LAND'],land_cost)
    for a,data in ANIMAL.items():
        # Transfers within this turn do not change owned headcount. Using the
        # post-PICKUP shed with pre-PICKUP inventories would buy replacements!
        held=priv['shed'].get(a,0)+sum(i.get(a,0) for i in priv['inventories'])
        need=st['herd'][a]-ct.get(a,0)-held
        if need>0 and hour<14:
            qty=min(need,max(0,int((money-reserve)//data[0])))
            if qty:append(['BUY_ANIMAL',a,qty],qty*data[0])
    for crop,data in CROP.items():
        needed=sum(role==crop and kind(me['tiles'][p[1]][p[0]]) in ('EMPTY','WEED')
                   and (not CFG['strict_diamond'] or len(me['unlocked_quadrants'])<3 or radius(p)<=CFG['diamond_radius'])
                   for p,role in st['roles'].items())-priv['seeds'].get(crop,0)
        if needed>0 and hour<18:
            qty=min(needed,max(0,int((money-50)//data[0])))
            if qty:append(['BUY_SEED',crop,qty],qty*data[0])
    return orders[:10]

def agent(obs,configuration=None):
    player=obs['player'];step=obs.get('step',obs['day']*24+obs['hour'])
    if player not in _STATE or step<=_STATE[player].get('last_step',-1):_STATE[player]={'day':-1}
    st=_STATE[player]
    if st['day']!=obs['day'] or obs['hour'] in CFG['replan_hours'] and obs['farms'][player]['money']>400:
        plan(obs,st)
    work=tasks(obs,st)
    actions,shed=act_units(obs,st,work)
    orders=market_orders(obs,st,shed)
    st['last_step']=step
    return {'farmer':actions[0],'hands':actions[1:],'market':orders}

