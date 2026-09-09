"""K Pro 3 I CARE Quote: standalone deterministic public-observation policy.
Source SHA256: 876866f9775d1b6539eefa115f5b40f284ee68ee5e7d05071c6a1758b52669c6
Profile SHA256: afd87b09666ff94dbef59029816ce4e5a89007662d7b03fcafb7a381ac9cdf2f
No action tape, opponent identity, seed access, network or runtime file reads.
"""
import math
import copy
CROP = {'WHEAT': (10, 2, 4, 0, 6), 'CARROT': (20, 2, 3, 0, 4), 'TOMATO': (50, 8, 8, 1, 4), 'STRAWBERRY': (100, 10, 10, 2, 4), 'MELON': (80, 10, 12, 0, 6)}
ANIMAL = {'COW': (400, 8, 2, 6, 'MILK'), 'SHEEP': (500, 6, 3, 6, 'WOOL'), 'GOOSE': (300, 4, 1, 4, 'EGG')}
PARAMS = {'WHEAT': (25, 400, 'sqrt', 0.8, 'log', 0.2), 'CARROT': (35, 450, 'hinge', 1, 'sqrt', 0.7), 'TOMATO': (60, 200, 'hinge', 0.4, 'sqrt', 0.6), 'STRAWBERRY': (120, 100, 'sqrt', 0.7, 'linear', 1.6), 'MELON': (250, 300, 'log', 0.2, 'sq', 3.6), 'EGG': (50, 332, 'hinge', 0.4, 'log', 0.2), 'MILK': (160, 122, 'sqrt', 0.6, 'linear', 1.6), 'WOOL': (200, 105, 'log', 0.2, 'sq', 3.2), 'FERTILIZER': (100, 200, 'linear', 0.4, 'linear', 0.4)}
SHOP = {'BAKERY': ('EGG', 'WHEAT'), 'PIZZA_SHOP': ('MILK', 'TOMATO', 'WHEAT'), 'BRUNCH_SPOT': ('EGG', 'WHEAT', 'STRAWBERRY'), 'YARN_STORE': ('WOOL', 'WOOL'), 'ICE_CREAM_SHOP': ('STRAWBERRY', 'MILK', 'WHEAT'), 'PET_CAFE': ('CARROT', 'CARROT'), 'SMOOTHIE_SHOP': ('STRAWBERRY', 'MILK'), 'FARMERS_MARKET': ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY')}
SHED = ((4, 4), (5, 4), (4, 5), (5, 5))
_STATE = {}
_SHED_AXIS_DISTANCE = (4, 3, 2, 1, 0, 0, 1, 2, 3, 4)

def shape(kind, x, t):
    if kind == 'sqrt':
        return math.sqrt(x)
    if kind == 'log':
        return math.log1p(x)
    if kind == 'sq':
        return x * x
    if kind == 'hinge':
        u = x / t
        return u + 8 * max(0, u - 1) ** 2
    return x

def price(item, inventory):
    base, t, bf, bt, af, at = PARAMS[item]
    if inventory < 10000:
        v = base + base * bt * shape(bf, 10000 - inventory, t) / shape(bf, t, t)
    else:
        v = base - base * at * shape(af, inventory - 10000, t) / shape(af, t, t)
    return max(1, round(v))

def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def radius(p):
    return _SHED_AXIS_DISTANCE[p[0]] + _SHED_AXIS_DISTANCE[p[1]]

def move(p, q):
    if p[0] != q[0]:
        return ['EAST' if p[0] < q[0] else 'WEST']
    if p[1] != q[1]:
        return ['SOUTH' if p[1] < q[1] else 'NORTH']
    return ['PASS']

def kind(t):
    if t is None:
        return 'EMPTY'
    if t == 'LOCKED':
        return 'LOCKED'
    return t.get('animal') or t.get('crop') or t.get('kind', 'EMPTY')

def demand(town, item):
    return (item != 'FERTILIZER') + 6 * sum((SHOP.get(s, ()).count(item) for s in town.get('unlocked_shops', [])))

def counts(farm):
    out = {}
    for row in farm['tiles']:
        for t in row:
            k = kind(t)
            out[k] = out.get(k, 0) + 1
    return out

def fibonacci(n):
    a, b = (1, 1)
    for _ in range(n):
        a, b = (b, a + b)
    return a

def forecast(obs, item, horizon=5):
    """Conservative public supply estimate, not hidden future-shop prediction."""
    current = obs['market']['inventory'][item]
    supply = 0.0
    for farm in obs['farms']:
        for row in farm['tiles']:
            for t in row:
                if not isinstance(t, dict):
                    continue
                a = t.get('animal')
                if a and ANIMAL[a][4] == item:
                    first = t['placed_day'] + ANIMAL[a][1]
                    start = max(obs['day'], first)
                    supply += max(0, (obs['day'] + horizon - start) / ANIMAL[a][2]) * min(ANIMAL[a][3], 1 + ANIMAL[a][2])
                    supply += t.get('yield_units', 0)
                if t.get('crop') == item:
                    cd = CROP[item]
                    age = obs['day'] - t['planted_day']
                    if age + horizon >= cd[1]:
                        supply += min(cd[4], t.get('yield_units', 0) + horizon / (cd[3] or 4) * 2)
    return price(item, current + int(supply) - demand(obs.get('town', {}), item) * horizon)

def plan(obs, st):
    day = obs['day']
    me = obs['farms'][obs['player']]
    priv = obs['private']
    ct = counts(me)
    p = obs['market']['prices']
    town = obs.get('town', {})
    money = me['money']
    q = len(me['unlocked_quadrants'])
    pending = {a: priv['shed'].get(a, 0) + sum((i.get(a, 0) for i in priv['inventories'])) for a in ANIMAL}
    animal_n = sum((ct.get(a, 0) + pending[a] for a in ANIMAL))
    targets = {a: ct.get(a, 0) + pending[a] for a in ANIMAL}
    if day == 0:
        targets['SHEEP'] = 4
        targets['COW'] = 0
    elif day <= 16:
        limit = min(18, 4 + 0 + max(0, day - 1) * 2)
        if money > 400 and animal_n < limit:
            choices = []
            species_room = {a: limit - animal_n for a in ANIMAL}
            for a, data in ANIMAL.items():
                if a == 'GOOSE' and ct.get(a, 0) + pending[a] >= 2:
                    continue
                if a == 'GOOSE' and demand(town, 'EGG') < 0:
                    continue
                if a == 'GOOSE':
                    species_room[a] = 2 - ct.get(a, 0) - pending[a]
                if a in ('COW', 'SHEEP'):
                    rival = counts(obs['farms'][1 - obs['player']])
                    milk_share = max(0.3, min(0.7, 0.5 + 0.012 * (demand(town, 'MILK') - demand(town, 'WOOL')) + (-0.02 if day >= 1 else -0.02) * (rival.get('COW', 0) - rival.get('SHEEP', 0))))
                    share = milk_share if a == 'COW' else 1 - milk_share
                    species_room[a] = math.ceil(18 * share) - ct.get(a, 0) - pending[a]
                    if species_room[a] <= 0:
                        continue
                cost, first, interval, cap, product = data
                ticks = max(0, (29 - day - first) // interval + 1)
                fw = 0.35
                fp = fw * forecast(obs, product, 8) + (1 - fw) * (0.6 * p[product] + 0.4 * PARAMS[product][0])
                net = ticks * (interval + 1) * fp + (29 - day) * min(15, p['FERTILIZER']) - (29 - day) * p['WHEAT'] - cost
                net -= (29 - day) * (2 + 1 / interval) * 0.0
                if a in ('COW', 'SHEEP'):
                    fullness = (ct.get(a, 0) + pending[a]) / max(1, math.ceil(18 * share))
                    net *= max(0.1, 1 - 0.6 * fullness)
                choices.append((net / max(1, cost), a))
            if choices:
                value, a = max(choices)
                if value > 1.0:
                    targets[a] += min(2, limit - animal_n, species_room[a])
    pending = {a: priv['shed'].get(a, 0) + sum((i.get(a, 0) for i in priv['inventories'])) for a in ANIMAL}
    for a in ANIMAL:
        targets[a] = max(targets[a], ct.get(a, 0) + pending[a])
    herd = sum(targets.values())
    wheat_floor = 7 if day == 0 or None is None else None
    wheat_target = min(24, max(wheat_floor, math.ceil(herd * 0.65))) if day <= 25 else 0
    if st.get('terminal_active', False) and 22 <= day <= 26:
        wheat_target = max(wheat_target, 36)
    straw_target = 0 if day < 3 else min(42, 2 + day * 3)
    if day > 16:
        straw_target = ct.get('STRAWBERRY', 0)
    if day >= 3 and forecast(obs, 'STRAWBERRY', 8) < 20:
        straw_target = min(straw_target, 8)
    melon_target = 8 if day == 0 else ct.get('MELON', 0)
    if 11 <= day <= 18 and forecast(obs, 'MELON', 10) > 100:
        melon_target = max(melon_target, 4)
    carrot_target = 0 if day == 0 else 0
    if 20 <= day <= 26 and p['CARROT'] > 35:
        carrot_target = min(20, 8 + int(demand(town, 'CARROT') / 2))
    if st.get('terminal_active', False) and day >= 22 and True:
        carrot_target = 0
    wanted = {'WHEAT': wheat_target, 'STRAWBERRY': straw_target, 'MELON': melon_target, 'CARROT': carrot_target}
    roles = {}
    for y, row in enumerate(me['tiles']):
        for x, t in enumerate(row):
            k = kind(t)
            if k in ANIMAL or k in CROP:
                roles[x, y] = k
    free = [(x, y) for y, row in enumerate(me['tiles']) for x, t in enumerate(row) if kind(t) in ('EMPTY', 'WEED', 'PASTURE', 'COOP')]
    free.sort(key=lambda pos: (radius(pos), pos[1], pos[0]))
    for a in ('SHEEP', 'COW', 'GOOSE'):
        for _ in range(max(0, targets[a] - ct.get(a, 0))):
            structure = 'COOP' if a == 'GOOSE' else 'PASTURE'
            eligible = [pos for pos in free if kind(me['tiles'][pos[1]][pos[0]]) in ('EMPTY', 'WEED', structure)]
            if a != 'COW':
                central_sheep = any((r == 'SHEEP' and radius(p) == 0 for p, r in roles.items()))
                if a == 'GOOSE' or central_sheep:
                    noncentral = [p for p in eligible if radius(p) > 0]
                    if noncentral:
                        eligible = noncentral
            if not eligible:
                break
            slot = min(eligible, key=lambda pos: (0 if kind(me['tiles'][pos[1]][pos[0]]) == structure else 1, radius(pos), pos))
            roles[slot] = a
            free.remove(slot)
    if day <= 16:
        occupied_animals = [p for p, r in roles.items() if r in ANIMAL]
        future = max(0, 18 - len(occupied_animals))
        reserved_ring = [p for p in free if radius(p) <= 2][:future]
        free = [p for p in free if p not in reserved_ring]
    elif day < 6:
        protected = max(0, 2 - (herd - 4 - 0))
        free = free[protected:]
    for c in ('MELON', 'WHEAT', 'STRAWBERRY', 'TOMATO', 'CARROT'):
        for _ in range(max(0, wanted.get(c, 0) - ct.get(c, 0))):
            allowed = [pos for pos in free if kind(me['tiles'][pos[1]][pos[0]]) not in ('PASTURE', 'COOP') and (q < 3 or radius(pos) <= 6)]
            if not allowed:
                break
            slot = min(allowed, key=lambda pos: (-radius(pos) if c == 'MELON' and day < 2 and True else radius(pos), pos))
            roles[slot] = c
            free.remove(slot)
    workload = sum((4.8 if k in ANIMAL else 1.7 for k in roles.values()))
    hands = min(10, max(3, math.ceil(workload / 13)))
    if day == 0:
        hands = 6
    if day >= 28:
        hands = max(3, min(10, math.ceil(workload / 15)))
    st.update(day=day, roles=roles, herd=targets, hands=hands, targets={}, zones=None, quadrants=q)

def crop_tasks(t, day, prices, rotation_active=False):
    c = t['crop']
    seed, first, maximum, interval, cap = CROP[c]
    age = day - t['planted_day']
    yu = t.get('yield_units', 0)
    acts = []
    dying = t.get('consecutive_unwatered', 0) >= 1
    growing = (maximum + 1) // 2 <= age <= maximum and yu < cap if not interval else age + 1 >= first and (age + 1 - first) % interval == 0 and ((age + 1 - first) // interval < cap)
    expired = t.get('max_lifespan_step', -1) >= 0
    wheat_harvest = min(5, 5) if day <= 4 else 5
    if c == 'WHEAT' and rotation_active and (day >= 28):
        wheat_harvest = min(wheat_harvest, 3)
    ready = age >= first and yu > 0 and (interval and (yu >= 2 or expired or day == 29) or (not interval and (yu >= cap or age >= maximum or (c == 'WHEAT' and yu >= wheat_harvest) or (day == 29))))
    if day < 29 or ready or (not interval and age >= first and (yu > 0)):
        wants_fert = growing and t.get('fertilized_until_day', -1) < day and (interval or (c == 'WHEAT' and True))
        if wants_fert and prices[c] * 2 > max(8, prices['FERTILIZER']):
            acts.append(['FERTILIZE'])
        if not t.get('watered_today') and (growing or (dying and (not ready))):
            acts.append(['WATER'])
    if ready:
        acts.append(['HARVEST'])
    value = (prices[c] * max(1, yu) + seed * 0.5) * (1.0 if c == 'MELON' and age >= first else 1)
    urgent = 1000 if dying and (not ready) and (day < 29) else 0
    return (acts, value + urgent)

def animal_tasks(t, day, prices, town, care_quotes=None):
    a = t['animal']
    _, first, interval, cap, product = ANIMAL[a]
    yu = t.get('yield_units', 0)
    acts = []
    if yu > 0:
        acts.append(['HARVEST'])
    if day == 29:
        return (acts, prices[product] * yu)
    production = day + 1 - t['placed_day'] - first >= 0 and (day + 1 - t['placed_day'] - first) % interval == 0
    skip = not t.get('consecutive_unfed', 0) and prices[product] * 1.5 < prices['WHEAT'] and (demand(town, product) <= 1) and (not production)
    if not t.get('consecutive_unfed', 0) and demand(town, product) <= 1:
        marginal = min(cap - 1, t.get('pending_care_bonus', 0)) if production else 1.5
        if marginal * prices[product] < prices['WHEAT']:
            skip = True
    care_quote = prices[product] if care_quotes is None else care_quotes[product]
    care_quote = max(care_quote, PARAMS[product][0] * 0)
    if day == 28:
        missed = t.get('consecutive_unfed', 0)
        if not production and (not missed or not yu) or (production and (not missed) and (not t.get('pending_care_bonus', 0))):
            skip = True
    if not t.get('fed_today') and (not skip):
        acts.append(['FEED'])
    future_ticks = (29 - t['placed_day'] - first) // interval - (day - t['placed_day'] - first) // interval
    useful_care = production or t.get('pending_care_bonus', 0) < cap - 1
    if useful_care and (not t.get('cared_today')) and (not skip) and (future_ticks > 0) and (care_quote > prices['WHEAT'] * 0.5):
        acts.append(['CARE'])
    if t.get('fertilizer_available') and prices['FERTILIZER'] >= 3:
        acts.append(['COLLECT_FERTILIZER'])
    urgent = 1000 if t.get('consecutive_unfed', 0) and (not t.get('fed_today')) and (not skip) else 0
    return (acts, prices[product] * max(1, yu) + urgent)

def care_payoff_delay(tile, day):
    """Delay to the first production that can consume CARE credited next day."""
    _, first_delay, interval, _, _ = ANIMAL[tile['animal']]
    first = tile['placed_day'] + first_delay
    minimum = day + 2
    next_production = first + max(0, (minimum - first + interval - 1) // interval) * interval
    return next_production - day if next_production <= 29 else None

def incremental_task_value(tile, sequence, day, prices, care_price=None):
    """Approximate immediate marginal goods value; no hidden future state."""
    k = kind(tile)
    if k not in CROP and k not in ANIMAL:
        return None
    ops = {a[0] for a in sequence}
    units = tile.get('yield_units', 0)
    result = 0.0
    if k in CROP:
        _, first, maximum, interval, cap = CROP[k]
        age = day - tile['planted_day']
        growing = (maximum + 1) // 2 <= age <= maximum and units < cap if not interval else age + 1 >= first and (age + 1 - first) % interval == 0 and ((age + 1 - first) // interval < cap)
        if 'HARVEST' in ops:
            result += units * prices[k]
        if 'WATER' in ops and growing:
            result += min(max(0, cap - units), 2 if tile.get('fertilized_until_day', -1) >= day else 1) * prices[k]
        if 'FERTILIZE' in ops and growing:
            result += max(0, prices[k] - prices['FERTILIZER'])
        if tile.get('consecutive_unwatered', 0) and 'WATER' in ops:
            result += 1000
    else:
        _, first, interval, cap, product = ANIMAL[k]
        production = day + 1 - tile['placed_day'] - first >= 0 and (day + 1 - tile['placed_day'] - first) % interval == 0
        if 'HARVEST' in ops:
            result += units * prices[product]
        if 'FEED' in ops:
            bonus = min(max(0, cap - 1), tile.get('pending_care_bonus', 0)) if production else 0
            result += max(0, bonus * prices[product] - prices['WHEAT'])
            if tile.get('consecutive_unfed', 0):
                result += 1000
        if 'CARE' in ops:
            result += prices[product] if care_price is None else care_price
        if 'COLLECT_FERTILIZER' in ops:
            result += prices['FERTILIZER']
    return max(1.0, result)

def tasks(obs, st):
    day = obs['day']
    me = obs['farms'][obs['player']]
    prices = obs['market']['prices']
    result = {}
    task_care_quotes = {}
    care_quotes = None
    for pos, role in st['roles'].items():
        t = me['tiles'][pos[1]][pos[0]]
        k = kind(t)
        if k in CROP:
            acts, value = crop_tasks(t, day, prices, st.get('terminal_active', False))
        elif k in ANIMAL:
            acts, value = animal_tasks(t, day, prices, obs.get('town', {}), care_quotes)
        elif k == 'WEED':
            acts, value = ([['DIG']], 80)
        elif k == 'EMPTY' and role in CROP:
            admissible = len(me['unlocked_quadrants']) < 3 or radius(pos) <= 6
            acts, value = ([['PLANT', role], ['WATER']], 120) if admissible and obs['hour'] < 21 and (day + CROP[role][1] < 30) else ([], 0)
        elif k == 'EMPTY' and role in ANIMAL:
            acts, value = ([['BUILD_COOP' if role == 'GOOSE' else 'BUILD_PASTURE'], ['PLACE', role]], 200)
        elif k in ('PASTURE', 'COOP') and role in ANIMAL:
            acts, value = ([['PLACE', role]], 200)
        else:
            acts, value = ([], 0)
        if acts:
            if day >= 6:
                if k in ANIMAL and ['CARE'] in acts:
                    delay = care_payoff_delay(t, day)
                    if delay is None:
                        care_price = 0.0
                    else:
                        product = ANIMAL[k][4]
                        key = (product, delay)
                        if key not in task_care_quotes:
                            task_care_quotes[key] = forecast(obs, product, delay)
                        care_price = task_care_quotes[key]
                    marginal = incremental_task_value(t, acts, day, prices, care_price)
                else:
                    marginal = incremental_task_value(t, acts, day, prices)
                if marginal is not None:
                    value = (1 - 0.5) * value + 0.5 * marginal
            result[pos] = (acts, value)
    return result

def zone_total(values):
    return math.fsum(values)

def assignment_urgency(value, hour, day):
    divisor = 250 if day < 6 else 500
    return min(8, value / divisor) * (1.8 if hour >= 17 else 1.0)

def zones(st, work, n):
    zone_mode = 'specialized' if st['day'] >= 99 else 'angular'
    order = sorted(work, key=lambda p: (math.atan2(p[1] - 4.5, p[0] - 4.5), radius(p)))
    if zone_mode == 'routing':
        routes = [[] for _ in range(n)]
        duration = [2.0] * n
        out = {}
        for pos in sorted(work, key=lambda p: (-radius(p), -len(work[p][0]), p)):
            service = len(work[pos][0])
            if st['roles'][pos] in ANIMAL and any((a[0] in ('PLACE', 'BUILD_PASTURE', 'BUILD_COOP') for a in work[pos][0])):
                service += 2
            best = None
            for uid, route in enumerate(routes):
                for j in range(len(route) + 1):
                    before = route[j - 1] if j else None
                    after = route[j] if j < len(route) else None
                    first = distance(before, pos) if before else radius(pos)
                    last = distance(pos, after) if after else 0
                    old = (distance(before, after) if before else radius(after)) if after else 0
                    delta = first + last - old + service
                    cost = delta + 0.03 * duration[uid] + 0.8 * max(0, duration[uid] + delta - 21) ** 2
                    choice = (cost, uid, j, delta)
                    if best is None or choice < best:
                        best = choice
            _, uid, j, delta = best
            routes[uid].insert(j, pos)
            duration[uid] += delta
            out[pos] = uid
        st['zones'] = out
        st['zone_count'] = n
        st['planned_routes'] = routes
        return out
    if zone_mode == 'specialized' and n > 1:
        animal = [p for p in order if st['roles'][p] in ANIMAL]
        crops = [p for p in order if st['roles'][p] not in ANIMAL]
        nh = min(n - 1, max(1, math.ceil(len(animal) * 5.0 / 22))) if animal else 0
        if not crops:
            nh = n
        out = {}
        for group, offset, size in ((animal, 0, nh), (crops, nh, n - nh)):
            total = zone_total((len(work[p][0]) + 1.3 for p in group))
            done = 0.0
            for p in group:
                out[p] = offset + min(size - 1, int(done / max(1, total) * size))
                done += len(work[p][0]) + 1.3
        st['zones'] = out
        st['zone_count'] = n
        return out
    if zone_mode == 'strips':
        order = sorted(work, key=lambda p: (p[0] // 2, p[1] if p[0] // 2 % 2 == 0 else -p[1], p[0]))
    total = zone_total((len(work[p][0]) + 1.3 for p in order))
    done = 0.0
    out = {}
    for p in order:
        out[p] = min(n - 1, int(done / max(1, total) * n))
        done += len(work[p][0]) + 1.3
    st['zones'] = out
    st['zone_count'] = n
    return out

def act_units_greedy(obs, st, work):
    me = obs['farms'][obs['player']]
    priv = obs['private']
    hour = obs['hour']
    day = obs['day']
    positions = [tuple(me['farmer'])] + [tuple(p) for p in me['hands']]
    inventories = priv['inventories']
    shed = dict(priv['shed'])
    seeds = dict(priv['seeds'])
    n = len(positions)
    z = st.get('zones')
    planned = max(n, st.get('hands', n - 1) + 1)
    if z is None or st.get('zone_count') != planned:
        z = zones(st, work, planned)
    reserved = set()
    actions = []
    fixed = set()
    st['_fixed_units'] = fixed
    owners = {p: u for u, p in st['targets'].items() if u < n and p in work}
    deadline = 23 if day == 29 else 24
    for uid, pos in enumerate(positions):
        inv = inventories[uid] if uid < len(inventories) else {}
        nearest = min(SHED, key=lambda s: distance(pos, s))
        back = distance(pos, nearest)
        sellable = sum((inv.get(p, 0) for p in PARAMS))
        if day == 29 and sellable and (hour + back + 1 >= deadline):
            action = ['DROP'] if back == 0 else move(pos, nearest)
            if back == 0:
                room = 100 - sum(shed.values())
                for item, count in inv.items():
                    add = max(0, min(count, room))
                    shed[item] = shed.get(item, 0) + add
                    room -= add
            actions.append(action)
            fixed.add(uid)
            continue
        premium = [p for p in PARAMS if p not in ('WHEAT', 'FERTILIZER') and inv.get(p, 0) > 0]
        early_fert = False
        if early_fert and inv.get('FERTILIZER', 0):
            premium.append('FERTILIZER')
        cash_item = max(premium, key=lambda p: inv[p] * obs['market']['prices'][p], default=None)
        cash_value = inv.get(cash_item, 0) * obs['market']['prices'].get(cash_item, 0)
        standing = me['tiles'][pos[1]][pos[0]]
        service_pending = day >= 99 and any((a[0] == 'WATER' and kind(standing) in CROP or (a[0] == 'FEED' and inv.get('WHEAT', 0) > 0) or (a[0] == 'CARE' and isinstance(standing, dict) and standing.get('fed_today')) for a in work.get(pos, ([], 0))[0]))
        central_sale = back == 0 and cash_value >= (min(70, 200) if early_fert else 200 if day >= 12 else 200) and (cash_item is not None)
        capital_due = day <= 12 and me['money'] < 4000 and (hour < 18)
        deliver = central_sale or (capital_due and cash_value >= (min(120, 400) if early_fert else 400) + back * 50 and (back <= 4) and (hour + back + 1 < 24))
        if cash_item and (not service_pending) and deliver:
            if back:
                actions.append(move(pos, nearest))
                fixed.add(uid)
                continue
            amount = min(inv[cash_item], max(0, 100 - sum(shed.values())))
            if amount:
                actions.append(['PLACE', cash_item, amount])
                shed[cash_item] = shed.get(cash_item, 0) + amount
                fixed.add(uid)
                continue
        if back == 0 and sum((inv.get(p, 0) for p in premium)) >= 12 and (hour > 7 or day == 29):
            room = 100 - sum(shed.values())
            if room >= sellable:
                for item, count in inv.items():
                    shed[item] = shed.get(item, 0) + count
                actions.append(['DROP'])
                fixed.add(uid)
                continue
        own = [p for p in work if z.get(p) == uid]
        feed_need = sum((any((a[0] == 'FEED' for a in work[p][0])) for p in own))
        if feed_need:
            feed_need += 0
        fert_need = sum((any((a[0] == 'FERTILIZE' for a in work[p][0])) for p in own))
        if back == 0:
            took = False
            for item, need in [('WHEAT', feed_need), ('FERTILIZER', min(5, fert_need))]:
                if day >= 6 and need:
                    batch = 0 if item == 'WHEAT' else 0
                    if batch:
                        op = 'FEED' if item == 'WHEAT' else 'FERTILIZE'
                        total_need = sum((any((a[0] == op for a in todo)) for todo, _ in work.values()))
                        already_carried = sum((i.get(item, 0) for i in inventories))
                        already_booked = max(0, priv['shed'].get(item, 0) - shed.get(item, 0))
                        available_demand = max(0, total_need - already_carried - already_booked)
                        need = max(need, inv.get(item, 0) + min(batch, available_demand))
                qty = min(max(0, need - inv.get(item, 0)), shed.get(item, 0))
                if qty and hour < 18:
                    actions.append(['PICKUP', item, qty])
                    shed[item] -= qty
                    took = True
                    break
            if took:
                fixed.add(uid)
                continue
            for a in ANIMAL:
                needing = sum((st['roles'][p] == a and kind(me['tiles'][p[1]][p[0]]) not in ANIMAL for p in own))
                if needing > inv.get(a, 0) and shed.get(a, 0):
                    qty = min(needing - inv.get(a, 0), shed[a])
                    actions.append(['PICKUP', a, qty])
                    shed[a] -= qty
                    took = True
                    break
            if took:
                fixed.add(uid)
                continue
        best = None
        for p, (todo, value) in work.items():
            if p in reserved:
                continue
            owner = owners.get(p, uid)
            sequence = []
            requires = None
            for a in todo:
                op = a[0]
                if op == 'FERTILIZE' and inv.get('FERTILIZER', 0) <= 0:
                    continue
                if op == 'FEED' and inv.get('WHEAT', 0) <= 0:
                    requires = 'WHEAT'
                    continue
                if op == 'CARE' and (not inv.get('WHEAT')) and (not me['tiles'][p[1]][p[0]].get('fed_today')):
                    continue
                if op in ('BUILD_PASTURE', 'BUILD_COOP') and inv.get(st['roles'][p], 0) <= 0:
                    requires = st['roles'][p]
                    break
                if op == 'PLACE' and inv.get(a[1], 0) <= 0:
                    requires = a[1]
                    break
                if op == 'PLANT' and seeds.get(a[1], 0) <= 0:
                    break
                sequence.append(a)
            d = distance(pos, p)
            if not sequence:
                if requires and shed.get(requires, 0) > 0 and (hour + back + 2 + radius(p) < deadline):
                    score = back + radius(p) + 4 + 6 * (z.get(p) != uid)
                    candidate = (score, p, ['PICKUP', requires, 1] if back == 0 else move(pos, nearest), True)
                else:
                    continue
            else:
                if day == 29 and (not any((a[0] == 'HARVEST' for a in sequence))):
                    continue
                if day == 29 and True and (hour + d + len(sequence) + radius(p) + 1 > deadline):
                    sequence = [a for a in sequence if a[0] == 'HARVEST']
                if hour + d + 1 + (radius(p) + 1 if day == 29 else 0) > deadline:
                    continue
                score = d + 6 * (z.get(p) != uid) - min(3.0, value / 600)
                if st['targets'].get(uid) == p:
                    score -= 1.0
                if p == pos:
                    score -= 2.0
                candidate = (score, p, sequence[0] if d == 0 else move(pos, p), False)
            if best is None or (candidate[0], candidate[1]) < (best[0], best[1]):
                best = candidate
        if best:
            _, target, action, supply = best
            reserved.add(target)
            st['targets'][uid] = target
            if supply:
                fixed.add(uid)
            if action[0] == 'PLANT':
                seeds[action[1]] -= 1
            if action[0] == 'PICKUP':
                shed[action[1]] -= action[2]
            actions.append(action)
        else:
            actions.append(['PASS'])
    return (actions, shed)

def minimum_assignment(costs):
    """Rectangular Hungarian assignment, deterministic ties, O(n*n*m)."""
    n = len(costs)
    if not n:
        return []
    m = len(costs[0])
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)
    way = [0] * (m + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minimum = [float('inf')] * (m + 1)
        used = [False] * (m + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float('inf')
            j1 = 0
            for j in range(1, m + 1):
                if not used[j]:
                    cur = costs[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minimum[j]:
                        minimum[j] = cur
                        way[j] = j0
                    if minimum[j] < delta:
                        delta = minimum[j]
                        j1 = j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    answer = [-1] * n
    for j in range(1, m + 1):
        if p[j]:
            answer[p[j] - 1] = j - 1
    return answer

def act_units(obs, st, work):
    previous_targets = dict(st['targets'])
    actions, shed = act_units_greedy(obs, st, work)
    me = obs['farms'][obs['player']]
    priv = obs['private']
    hour = obs['hour']
    day = obs['day']
    pos = [tuple(me['farmer'])] + [tuple(p) for p in me['hands']]
    fixed = st['_fixed_units']
    workers = [i for i in range(len(pos)) if i not in fixed]
    fixed_tiles = {pos[i] for i in fixed if actions[i][0] == 'PLACE' and len(actions[i]) > 1 and (actions[i][1] in ANIMAL)}
    tiles = sorted((p for p in work if p not in fixed_tiles))
    costs = []
    commands = []
    seeds = dict(priv['seeds'])
    for uid in workers:
        inv = priv['inventories'][uid] if uid < len(priv['inventories']) else {}
        row = []
        cmd = []
        for p in tiles:
            todo, value = work[p]
            valid = []
            for a in todo:
                op = a[0]
                if op == 'FERTILIZE' and (not inv.get('FERTILIZER')):
                    continue
                if op == 'FEED' and (not inv.get('WHEAT')):
                    continue
                if op == 'CARE':
                    t = me['tiles'][p[1]][p[0]]
                    if not t.get('fed_today') and (not inv.get('WHEAT')):
                        continue
                if op in ('BUILD_PASTURE', 'BUILD_COOP') and (not inv.get(st['roles'][p])):
                    break
                if op == 'PLACE' and (not inv.get(a[1])):
                    break
                if op == 'PLANT' and (not seeds.get(a[1])):
                    break
                valid.append(a)
            d = distance(pos[uid], p)
            deadline = 23 if day == 29 else 24
            if day == 29 and True and (hour + d + len(valid) + radius(p) + 1 > deadline):
                valid = [a for a in valid if a[0] == 'HARVEST']
            if not valid or hour + d + 1 + (radius(p) + 1 if day == 29 else 0) > deadline or (day == 29 and (not any((a[0] == 'HARVEST' for a in valid)))):
                row.append(1000000.0)
                cmd.append(['PASS'])
                continue
            action = valid[0] if d == 0 else move(pos[uid], p)
            urgency = assignment_urgency(value, hour, obs['day'])
            zone_cost = 6
            cost = d + 0.15 * len(valid) - urgency + zone_cost * (st['zones'].get(p) != uid)
            if pos[uid] == p:
                cost -= 2
            if previous_targets.get(uid) == p:
                cost -= 0.4
            row.append(cost)
            cmd.append(action)
        costs.append(row + [50.0] * len(workers))
        commands.append(cmd)
    matched = minimum_assignment(costs)
    for index, uid in enumerate(workers):
        j = matched[index]
        if j >= len(tiles) or costs[index][j] >= 100000.0:
            actions[uid] = ['PASS']
            st['targets'].pop(uid, None)
            continue
        action = commands[index][j]
        if action[0] == 'PLANT':
            crop = action[1]
            if seeds.get(crop, 0) <= 0:
                action = ['PASS']
            else:
                seeds[crop] -= 1
        actions[uid] = action
        st['targets'][uid] = tiles[j]
    return (actions, shed)

def idle_deliveries(obs, actions, shed):
    """Use otherwise idle actions to sell loads before a forecast night overflow.

    Never orders a general return: at most enough idle loads to cover the excess,
    and never steals an action already assigned to a live field task.
    """
    return (actions, shed)

def market_orders(obs, st, shed):
    me = obs['farms'][obs['player']]
    priv = obs['private']
    day = obs['day']
    hour = obs['hour']
    prices = obs['market']['prices']
    mi = obs['market']['inventory']
    money = me['money']
    orders = []
    ct = counts(me)
    herd = sum((ct.get(a, 0) for a in ANIMAL))
    carry = {p: sum((i.get(p, 0) for i in priv['inventories'])) for p in PARAMS}
    final_feeds = None
    if day == 28:
        final_feeds = sum((any((a[0] == 'FEED' for a in todo)) for todo, _ in tasks(obs, st).values()))
    projected = sum(shed.values()) + sum(carry.values())
    items = sorted(PARAMS, key=lambda p: (-prices[p], p))
    for item in items:
        have = shed.get(item, 0)
        keep = 0
        if day < 29:
            if item == 'WHEAT':
                keep = max(0, math.ceil(herd * (1.5 if hour < 16 else 0.8)) - carry[item])
            if item == 'WHEAT' and final_feeds is not None:
                keep = max(0, final_feeds - carry[item])
            if item == 'FERTILIZER':
                willing = prices['FERTILIZER'] < prices['WHEAT'] * 1.5 or day >= 9
                keep = max(0, (12 if willing else 0) - carry[item])
        amount = max(0, have - keep)
        if not amount:
            continue
        floor = max(1, int(PARAMS[item][0] * 0.05))
        if day >= 28 or projected > 85 or money < 300:
            floor = 1
        if day < 28 and hour > 2 and (item in ('MILK', 'WOOL', 'STRAWBERRY')) and (projected < 60) and (money > 1000):
            floor = max(floor, int(forecast(obs, item, 1) * 0.8))
        qty = 0
        revenue = 0
        while qty < amount and price(item, mi[item] + qty) >= floor:
            revenue += price(item, mi[item] + qty)
            qty += 1
        if qty:
            orders.append(['SELL', item, qty])
            money += revenue
            shed[item] -= qty

    def append(order, cost):
        nonlocal money
        if len(orders) < 10 and money >= cost:
            orders.append(order)
            money -= cost
            return True
        return False
    food_reserve = max(0, herd - shed.get('WHEAT', 0) - carry['WHEAT']) * prices['WHEAT'] if day < 29 else 0
    current = len(me['hands'])
    hires = me.get('hires_today', current)
    while current < st['hands'] and hour < 8:
        if money - fibonacci(hires) < food_reserve or not append(['HIRE'], fibonacci(hires)):
            break
        current += 1
        hires += 1
    if day == 29:
        return orders[:10]
    unfed = sum((1 for row in me['tiles'] for t in row if isinstance(t, dict) and t.get('animal') and (not t.get('fed_today'))))
    wheat_need = max(0, (unfed + sum(st['herd'].values()) // 3 if final_feeds is None else final_feeds) - shed.get('WHEAT', 0) - carry['WHEAT'])
    if wheat_need and hour < 19:
        qty = wheat_need
        while qty and sum((price('WHEAT', mi['WHEAT'] - i - 1) for i in range(qty))) > money - 10:
            qty -= 1
        if qty:
            append(['BUY_PRODUCT', 'WHEAT', qty], sum((price('WHEAT', mi['WHEAT'] - i - 1) for i in range(qty))))
    reserve = 50 + max(0, herd - priv['shed'].get('WHEAT', 0) - carry['WHEAT']) * prices['WHEAT']
    q = len(me['unlocked_quadrants'])
    land_day = 6 if q == 1 else 10 if q == 2 else 12
    land_cost = (1000, 2000, 4000)[min(2, q - 1)]

    def acquire_land():
        if q < 4 and (q < 3 or False) and (land_day <= day <= 16) and (money > land_cost + reserve + 100):
            append(['BUY_LAND'], land_cost)
    acquire_land()
    escrow = 0
    for a, data in ANIMAL.items():
        held = priv['shed'].get(a, 0) + sum((i.get(a, 0) for i in priv['inventories']))
        need = st['herd'][a] - ct.get(a, 0) - held
        if need > 0 and hour < 14:
            qty = min(need, max(0, int((money - reserve - escrow) // data[0])))
            if qty:
                append(['BUY_ANIMAL', a, qty], qty * data[0])
    for crop, data in CROP.items():
        if day + data[1] >= 30:
            continue
        needed = sum((role == crop and kind(me['tiles'][p[1]][p[0]]) in ('EMPTY', 'WEED') and (len(me['unlocked_quadrants']) < 3 or radius(p) <= 6) for p, role in st['roles'].items())) - priv['seeds'].get(crop, 0)
        if needed > 0 and hour < 18:
            qty = min(needed, max(0, int((money - 50) // data[0])))
            if qty:
                append(['BUY_SEED', crop, qty], qty * data[0])
    return orders[:10]

def decide(obs, st):
    player = obs['player']
    step = obs.get('step', obs['day'] * 24 + obs['hour'])
    structural = st.get('quadrants') != len(obs['farms'][player]['unlocked_quadrants']) or False
    if st['day'] != obs['day'] or structural or (obs['hour'] in (4, 12) and obs['farms'][player]['money'] > 400):
        keep_routes = st.get('day') == obs['day'] and st.get('quadrants') == len(obs['farms'][player]['unlocked_quadrants']) and structural
        previous = {k: st.get(k) for k in ('zones', 'targets', 'zone_count', 'hands')}
        stable = False
        plan(obs, st)
        if keep_routes:
            st.update(previous)
        elif stable and st['hands'] == previous['hands']:
            z = dict(previous['zones'])
            anchors = list(z)
            for pos in sorted(st['roles']):
                if pos not in z and anchors:
                    z[pos] = z[min(anchors, key=lambda p: (distance(pos, p), p))]
            st.update(zones=z, zone_count=previous['zone_count'], targets=previous['targets'])
        st['rotation_pending'] = False
    work = tasks(obs, st)
    actions, shed = act_units(obs, st, work)
    actions, shed = idle_deliveries(obs, actions, shed)
    orders = market_orders(obs, st, shed)
    st['last_step'] = step
    return {'farmer': actions[0], 'hands': actions[1:], 'market': orders}

def agent(obs, configuration=None):
    player = obs['player']
    step = obs.get('step', obs['day'] * 24 + obs['hour'])
    if player not in _STATE or step <= _STATE[player].get('last_step', -1):
        _STATE[player] = {'day': -1}
    st = _STATE[player]
    return decide(obs, st)
