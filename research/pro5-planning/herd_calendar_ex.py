"""One collective installation/feed/collection route for a specified herd.

Food is purchased only for the next daily circuit; earlier delivered output
may fund later days. Prices are a conditional own-trade scenario, never a
promise about future adversary orders. All productive nights are fed, without
terminal animal value. Optional marginal CARE uses otherwise free slots.
This is a proposal builder, not an adaptive herd-growth policy.
"""
from collections import Counter
from itertools import permutations

from animal_install_dv import ANIMALS
from animal_night_model_bh import animal_after_night
from crop_route_model_bo import SHED
from joint_sales_ck import reprice_sales
from market_quote_ci import quote_sale
from portfolio_reservations_bp import check_portfolio
from stock_reservations_bq import check_stock_events
from town_scenario_ep import consumed_between

PRODUCT = {'COW': 'MILK', 'SHEEP': 'WOOL', 'GOOSE': 'EGG'}


def herd_candidates(obs, *, max_size, action_value, market_scenario, care=False, flexible_fertilizer=False):
    """Bounded herd alternatives on compact currently vacant plots.

    At most eight nearby tiles form the geometry pool. For each size use the
    shortest Manhattan circuit, then compare homogeneous and balanced herds.
    No claim of exhaustive species/geometry search or adaptive growth yet.
    """
    farm = obs['farms'][obs['player']]
    pool = [(x, y) for y, row in enumerate(farm['tiles']) for x, tile in enumerate(row) if tile is None]
    pool.sort(key=lambda p: (abs(p[0]-4)+abs(p[1]-4), p))
    pool = pool[:8]; projects = []; workers = {}
    if obs['day'] >= 29: return dict(projects=projects, workers=workers)
    def distance(a, b): return abs(a[0]-b[0])+abs(a[1]-b[1])
    def route_cost(route):
        return (distance((4, 4), route[0]) + sum(distance(a, b) for a, b in zip(route, route[1:]))
                + min(distance(route[-1], depot) for depot in SHED), route)
    species = ('COW', 'SHEEP', 'GOOSE')
    for n in range(1, min(max_size, len(pool)) + 1):
        plots = min(permutations(pool, n), key=route_cost)
        kinds = [(animal,) * n for animal in species]
        if n > 1: kinds += [tuple(species[(i + shift) % 3] for i in range(n)) for shift in range(3)]
        for animals in kinds:
            for with_care in ((False, True) if care else (False,)):
                for flexible in ((False, True) if flexible_fertilizer else (False,)):
                    result = herd_calendar(obs, herd=list(zip(animals, plots)), end_day=29, care=with_care,
                                           action_value=action_value, market_scenario=market_scenario,
                                           flexible_fertilizer=flexible)
                    if result['feasible']:
                        projects.append(result['project']); workers.update(result['workers'])
    return dict(projects=projects, workers=workers)


def _care_gain(state, day, end_day):
    """Extra units collected by end_day with one care today, future feed only."""
    totals = []
    for with_care in (False, True):
        current = dict(state, yield_units=0); total = 0
        for d in range(day, end_day):
            current = animal_after_night(current, d, feed=True, care=with_care and d == day)
            total += current['yield_units']; current['yield_units'] = 0
        totals.append(total)
    return totals[1] - totals[0]


def _care_candidates(states, herd, day, end_day, scenario, action_value):
    result = []
    for i, (animal, _) in enumerate(herd):
        gain = _care_gain(states[i], day, end_day); product = PRODUCT[animal]
        value = quote_sale(scenario['params'][product], scenario['inventory'][product], gain)['receipts']
        if gain > 0 and value > action_value: result.append((-value, i))
    return result


def _fertilizer_choice(states, herd, *, day, first_day, farm, position, prefix_length,
                       food, available, care_candidates, scenario, action_value):
    """Exact route-length comparison, conditional marginal care/fertilizer value.

Every animal is already visited for the retained daily herd circuit. Available
fertilizer units have the same resource value and per-visit pickup cost; compare
their count, including the shared deposit and any otherwise unnecessary return.
No feed or product harvest is optional here. This is not a full price forecast.
"""
    def distance(a, b): return abs(a[0]-b[0]) + abs(a[1]-b[1])
    length = prefix_length; products = set(); at = position
    eligible = [i for i, state in enumerate(states) if state['fertilizer_available']]
    for state, (animal, plot) in zip(states, herd):
        length += distance(at, plot); at = plot
        if day == first_day: length += 1 + int(farm['tiles'][plot[1]][plot[0]] is None)
        length += int(bool(food))
        if state['yield_units']: length += 1; products.add(PRODUCT[animal])
    candidates = sorted(care_candidates); best = None
    for n in range(len(eligible) + 1):
        used = length + n
        if products or n: used += min(distance(at, depot) for depot in SHED) + len(products) + int(n > 0)
        if used > available: continue
        chosen_care = candidates[:available-used]
        value = quote_sale(scenario['params']['FERTILIZER'], scenario['inventory']['FERTILIZER'], n)['receipts']
        value -= sum(v for v, _ in chosen_care)
        value -= action_value * (used + len(chosen_care))
        rank = (value, -(used + len(chosen_care)), -n)
        if best is None or rank > best[0]: best = (rank, set(eligible[:n]))
    return None if best is None else best[1]


def herd_calendar(obs, *, herd, end_day, action_value, market_scenario, care=False,
                  worker_id=0, calendar=None, flexible_fertilizer=False):
    day = obs['day']; farm = obs['farms'][obs['player']]; private = obs['private']
    positions = [farm['farmer']] + farm['hands']
    if type(worker_id) is not int or not 0 <= worker_id < len(positions):
        return dict(feasible=False, reason='missing_present_worker')
    if worker_id and calendar is None:
        return dict(feasible=False, reason='missing_worker_calendar')
    if type(care) is not bool: raise ValueError('Invalid herd care option')
    if type(flexible_fertilizer) is not bool: raise ValueError('Invalid fertilizer choice option')
    if type(end_day) is not int or not day < end_day <= 29:
        return dict(feasible=False, reason='collection_date')
    if calendar is None:
        calendar = {d: dict(position=tuple(farm['farmer']) if d == day else (4, 4),
                            available_from=obs['hour'] if d == day else 0) for d in range(day, end_day + 1)}
    if (any(d not in calendar for d in range(day, end_day + 1))
            or tuple(calendar[day]['position']) != tuple(positions[worker_id])
            or calendar[day]['available_from'] < obs['hour']):
        return dict(feasible=False, reason='invalid_worker_calendar')
    account = f'hand:{worker_id}'
    if not 1 <= len(herd) <= 4:
        return dict(feasible=False, reason='herd_size')
    herd = [(animal, tuple(plot)) for animal, plot in herd]
    if len({plot for _, plot in herd}) != len(herd):
        return dict(feasible=False, reason='duplicate_plot')
    if any(n for inventory in private['inventories'] for n in inventory.values()):
        return dict(feasible=False, reason='unreserved_carried_stock')
    for animal, (x, y) in herd:
        if animal not in ANIMALS or not 0 <= x < 10 or not 0 <= y < 10:
            return dict(feasible=False, reason='invalid_animal_plot')
        tile = farm['tiles'][y][x]
        if tile is not None and not (isinstance(tile, dict) and tile.get('kind') == ANIMALS[animal][1] and 'animal' not in tile):
            return dict(feasible=False, reason='plot_unavailable')
    items = {'WHEAT', 'FERTILIZER'} | {PRODUCT[a] for a, _ in herd}
    if any(item not in market_scenario[key] for item in items for key in ('params', 'inventory')):
        return dict(feasible=False, reason='missing_market')

    p = dict(id=f"herd:{obs['step']}:{herd}:{end_day}", plot=herd[0][1],
             plots=[plot for _, plot in herd], sessions=[], cashflows=[], cash_events=[],
             market_actions=[], stock_events=[], sale_quotes=[], opportunity_events=[],
             valuation_step=obs['step'])
    if care: p['id'] += ':care'
    if worker_id: p['id'] += f':worker:{worker_id}'
    if flexible_fertilizer: p['id'] += ':flex-fertilizer'
    states = [dict(kind=ANIMALS[a][1], animal=a, placed_day=day, yield_units=0,
                   consecutive_unfed=0, fed_today=False, cared_today=False,
                   fertilizer_available=False, pending_care_bonus=0) for a, _ in herd]
    counts = Counter(a for a, _ in herd)
    owned_food = private['shed'].get('WHEAT', 0)
    owned_prices = iter(quote_sale(market_scenario['params']['WHEAT'], market_scenario['inventory']['WHEAT'],
                                  min(owned_food, len(herd) * (end_day - day)))['unit_prices'])
    wheat_inventory = market_scenario['inventory']['WHEAT']
    demand = market_scenario.get('known_town_demand')
    last_consumed = demand['from_step'] if demand else obs['step']
    workers = {}
    for d in range(day, end_day + 1):
        start = tuple(calendar[d]['position'])
        session = dict(day=d, hour=calendar[d]['available_from'], worker=worker_id, start=start, actions=[])
        p['sessions'].append(session)
        row = dict(day=d, cost=0, receipts=0); p['cashflows'].append(row)
        workers[d, worker_id] = dict(position=start, available_from=session['hour'])
        position = start; base_step = 24 * d + session['hour']; buy_order = 0

        def market_buy(op, cost):
            nonlocal buy_order
            p['market_actions'].append((base_step, buy_order, op))
            p['cash_events'].append(dict(step=base_step, phase='market', order=buy_order, cost=cost))
            p['stock_events'].append(dict(step=base_step, phase='market', order=buy_order,
                                          changes=[('shed', op[1], op[2])]))
            row['cost'] += cost; buy_order += 1

        if d == day:
            for animal, qty in counts.items():
                missing = max(0, qty - private['shed'].get(animal, 0))
                if missing: market_buy(('BUY_ANIMAL', animal, missing), missing * ANIMALS[animal][0])
        food = len(herd) if d < end_day else 0
        from_owned = min(food, owned_food); owned_food -= from_owned
        missing = food - from_owned
        food_values = [(next(owned_prices), -1) for _ in range(from_owned)]
        food_purchase = None
        if missing:
            if demand:
                wheat_inventory -= consumed_between(demand, 'WHEAT', last_consumed, base_step)
                last_consumed = base_step
            cost = 0
            for _ in range(missing):
                wheat_inventory -= 1
                cost += quote_sale(market_scenario['params']['WHEAT'], wheat_inventory, 1)['unit_prices'][0]
            food_purchase = (base_step, buy_order)
            market_buy(('BUY_PRODUCT', 'WHEAT', missing), cost)
            resale = quote_sale(market_scenario['params']['WHEAT'], wheat_inventory, missing)['unit_prices']
            food_values += [(value, base_step + 1) for value in resale]

        def action(op, changes=None):
            step = base_step + len(session['actions']); session['actions'].append(op)
            if changes:
                p['stock_events'].append(dict(step=step, phase='unit', order=worker_id, changes=changes))
            return step

        def move(target):
            nonlocal position
            x, y = position; tx, ty = target
            while x != tx:
                action(('EAST' if x < tx else 'WEST',)); x += 1 if x < tx else -1
            while y != ty:
                action(('SOUTH' if y < ty else 'NORTH',)); y += 1 if y < ty else -1
            position = (x, y)

        # The market follows unit actions. A purchase cannot supply this very
        # turn's PICKUP, even when that unit stands at a shed access tile.
        if d == day or food:
            depot = min(SHED, key=lambda q: (abs(start[0]-q[0])+abs(start[1]-q[1])+
                                             abs(herd[0][1][0]-q[0])+abs(herd[0][1][1]-q[1]), q))
            move(depot)
            if buy_order and not session['actions']: action(('PASS',))
        if d == day:
            for animal, qty in counts.items():
                action(('PICKUP', animal, qty), [('shed', animal, -qty), (account, animal, qty)])
        if food:
            action(('PICKUP', 'WHEAT', food), [('shed', 'WHEAT', -food), (account, 'WHEAT', food)])
        optional_care = None; fertilizer_selection = None
        if flexible_fertilizer:
            optional_care = _care_candidates(states, herd, d, end_day, market_scenario, action_value) if care and d < end_day else []
            fertilizer_selection = _fertilizer_choice(states, herd, day=d, first_day=day, farm=farm,
                position=position, prefix_length=len(session['actions']), food=food,
                available=(23 if d == 29 else 24)-session['hour'], care_candidates=optional_care,
                scenario=market_scenario, action_value=action_value)
            if fertilizer_selection is None:
                return dict(feasible=False, reason='outside_worker_window', key=(d, worker_id))
        collected = Counter(); care_slots = {}
        for i, (animal, plot) in enumerate(herd):
            move(plot)
            if d == day:
                if farm['tiles'][plot[1]][plot[0]] is None: action(('BUILD_' + ANIMALS[animal][1],))
                action(('PLACE', animal, 1), [(account, animal, -1)])
            if food:
                step = action(('FEED',), [(account, 'WHEAT', -1)])
                value, available_after = food_values[i]
                p['opportunity_events'].append(dict(step=step, cost=value, available_after=available_after, worker=worker_id))
                if available_after >= 0:
                    p['opportunity_events'][-1].update(resource='WHEAT', purchase_ref=food_purchase)
                care_slots[i] = len(session['actions'])
            state = states[i]; product = PRODUCT[animal]
            if state['yield_units']:
                qty = state['yield_units']; state['yield_units'] = 0
                action(('HARVEST',), [(account, product, qty)]); collected[product] += qty
            if state['fertilizer_available'] and (fertilizer_selection is None or i in fertilizer_selection):
                action(('COLLECT_FERTILIZER',), [(account, 'FERTILIZER', 1)])
                collected['FERTILIZER'] += 1; state['fertilizer_available'] = False
        if collected:
            depot = min(SHED, key=lambda q: (abs(position[0]-q[0])+abs(position[1]-q[1]), q))
            move(depot)
            for item, qty in sorted(collected.items()):
                step = action(('PLACE', item, qty), [(account, item, -qty), ('shed', item, qty)])
                p['market_actions'].append((step, 0, ('SELL', item, qty)))
                p['stock_events'].append(dict(step=step, phase='market', order=0, changes=[('shed', item, -qty)]))
                p['sale_quotes'].append(dict(step=step, order=0, item=item, quantity=qty, receipts=0))
        # Reject the route before pricing or simulating further days. Otherwise
        # overlong deposits acquire another day's timestamp (even day30) and
        # can crash the quote layer before the portfolio window check runs.
        if session['hour'] + len(session['actions']) > (23 if d == 29 else 24):
            return dict(feasible=False, reason='outside_worker_window', key=(d, worker_id))
        chosen = set()
        if care and d < end_day:
            candidates = optional_care if optional_care is not None else _care_candidates(states, herd, d, end_day, market_scenario, action_value)
            slack = max(0, (23 if d == 29 else 24) - session['hour'] - len(session['actions']))
            chosen = {i for _, i in sorted(candidates)[:slack]}
            insertions = sorted(care_slots[i] for i in chosen)
            if insertions:
                def shift(step):
                    return step + sum(base_step + index <= step < 24 * (d + 1) for index in insertions)
                original = session['actions']; session['actions'] = []
                for index in range(len(original) + 1):
                    if index in insertions: session['actions'].append(('CARE',))
                    if index < len(original): session['actions'].append(original[index])
                for key in ('stock_events', 'cash_events', 'sale_quotes', 'opportunity_events'):
                    for event in p[key]: event['step'] = shift(event['step'])
                p['market_actions'] = [(shift(step), order, op) for step, order, op in p['market_actions']]
        if d < end_day:
            states = [animal_after_night(state, d, feed=True, care=i in chosen) for i, state in enumerate(states)]
    p['resource_opportunity_cost'] = sum(e['cost'] for e in p['opportunity_events'] if e['available_after'] <= obs['step'])
    p['net_value'] = -sum(row['cost'] for row in p['cashflows']) - p['resource_opportunity_cost'] - action_value * sum(
        len(s['actions']) for s in p['sessions'])
    p = reprice_sales([p], market_scenario)[0]
    checked = check_portfolio([p], workers=workers, initial_cash=farm['money'])
    if not checked['feasible']: return checked
    checked = check_stock_events(p['stock_events'], initial_stock={'shed': private['shed'], account: private['inventories'][worker_id]})
    if not checked['feasible']: return checked
    return dict(feasible=True, project=p, workers=workers)
