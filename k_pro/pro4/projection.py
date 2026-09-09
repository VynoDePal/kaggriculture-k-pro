"""Deterministic own-unit projection for the standard 24-turn/100-capacity game.

This is the state immediately before market processing, not the next observation:
time, market, opponents, decay, night refresh and randomness are not advanced.
"""
import copy


_PRO4_CROPS = {
    # first harvest age, last yield age, maximum yield, ongoing
    'WHEAT': (2, 4, 6, False), 'CARROT': (2, 3, 4, False),
    'TOMATO': (8, 8, 4, True), 'STRAWBERRY': (10, 10, 4, True),
    'MELON': (10, 12, 6, False),
}
_PRO4_ANIMALS = {'GOOSE': ('COOP', 'EGG'), 'COW': ('PASTURE', 'MILK'),
                 'SHEEP': ('PASTURE', 'WOOL')}


def project_unit_phase(obs, actions):
    """Copy and apply selected [farmer, *hands] actions in canonical order.

    Only public state and this player's private state are needed. As in the
    interpreter, oversubscribed seed requests all fail atomically. Inputs are
    engine-valid observations and action lists; configuration is the standard
    KPro game (24 turns/day, shed capacity 100).
    """
    result = dict(obs)
    result['private'] = copy.deepcopy(obs['private'])
    result['farms'] = list(obs['farms'])
    farm = copy.deepcopy(obs['farms'][obs['player']])
    result['farms'][obs['player']] = farm
    private = result['private']
    shed, seeds = private['shed'], private['seeds']
    # Nonzero seats can receive only day/hour, without the framework's step.
    step = obs.get('step')
    if step is None:
        step = obs['day'] * 24 + obs.get('hour', 0)
    day = step // 24
    size = len(farm['tiles'])
    half = size // 2
    access = {(half - 1, half - 1), (half, half - 1),
              (half - 1, half), (half, half)}
    moves = {'NORTH': (0, -1), 'SOUTH': (0, 1),
             'WEST': (-1, 0), 'EAST': (1, 0)}
    demand = {}
    for action in actions:
        if isinstance(action, list) and len(action) >= 2 and action[0] == 'PLANT':
            demand[action[1]] = demand.get(action[1], 0) + 1
    blocked = {crop for crop, n in demand.items() if n > seeds.get(crop, 0)}
    for index, action in enumerate(actions):
        if index > len(farm['hands']):
            break
        if not isinstance(action, list) or not action:
            continue
        op = action[0]
        pos = farm['farmer'] if index == 0 else farm['hands'][index - 1]
        x, y = pos
        while len(private['inventories']) <= index:
            private['inventories'].append({})
        inv = private['inventories'][index]

        def add(item, n=1):
            inv[item] = inv.get(item, 0) + n

        def take(item):
            if inv.get(item, 0) < 1:
                return False
            inv[item] -= 1
            if inv[item] == 0:
                del inv[item]
            return True

        if op in moves:
            dx, dy = moves[op]
            new_pos = [x + dx, y + dy]
            if 0 <= new_pos[0] < size and 0 <= new_pos[1] < size:
                if index == 0:
                    farm['farmer'] = new_pos
                else:
                    farm['hands'][index - 1] = new_pos
            continue
        tile = farm['tiles'][y][x]
        at_shed = (x, y) in access
        if op == 'DROP':
            if at_shed:
                for item, n in list(inv.items()):
                    moved = min(n, max(0, 100 - sum(shed.values())))
                    if moved > 0:
                        shed[item] = shed.get(item, 0) + moved
                    del inv[item]
            continue
        if op == 'PICKUP':
            if at_shed and len(action) >= 2:
                item = action[1]
                n = min(int(action[2]) if len(action) >= 3 else 1, shed.get(item, 0))
                if n > 0:
                    shed[item] -= n
                    add(item, n)
            continue
        if op == 'PLACE':
            if len(action) < 2:
                continue
            item = action[1]
            if (item in _PRO4_ANIMALS and isinstance(tile, dict)
                    and tile.get('kind') == _PRO4_ANIMALS[item][0]
                    and 'animal' not in tile):
                if take(item):
                    farm['tiles'][y][x] = {
                        'kind': _PRO4_ANIMALS[item][0], 'animal': item,
                        'placed_day': day, 'yield_units': 0, 'consecutive_unfed': 0,
                        'fed_today': False, 'cared_today': False,
                        'fertilizer_available': False, 'pending_care_bonus': 0,
                    }
            elif at_shed:
                n = min(int(action[2]) if len(action) >= 3 else 1,
                        inv.get(item, 0), max(0, 100 - sum(shed.values())))
                if n > 0:
                    inv[item] -= n
                    if inv[item] == 0:
                        del inv[item]
                    shed[item] = shed.get(item, 0) + n
            continue
        if tile == 'LOCKED':
            continue
        is_plant = isinstance(tile, dict) and tile.get('kind') == 'PLANT'
        is_animal = isinstance(tile, dict) and 'animal' in tile
        if op == 'PLANT' and len(action) >= 2:
            crop = action[1]
            if (tile is None and crop in _PRO4_CROPS and crop not in blocked
                    and seeds.get(crop, 0) > 0):
                _, max_age, _, ongoing = _PRO4_CROPS[crop]
                seeds[crop] -= 1
                farm['tiles'][y][x] = {
                    'kind': 'PLANT', 'crop': crop, 'planted_day': day,
                    'watered_today': False, 'consecutive_unwatered': 1,
                    'yield_units': 0 if ongoing else 1,
                    'max_lifespan_step': -1 if ongoing else (day + max_age + 1) * 24,
                    'fertilized_until_day': -1,
                }
        elif op == 'WATER' and is_plant and not tile['watered_today']:
            tile['watered_today'] = True
            _, max_age, max_yield, ongoing = _PRO4_CROPS[tile['crop']]
            age = day - tile['planted_day']
            if not ongoing and (max_age + 1) // 2 <= age <= max_age:
                bonus = 2 if tile['fertilized_until_day'] >= day else 1
                tile['yield_units'] = min(max_yield, tile['yield_units'] + bonus)
        elif op == 'HARVEST' and isinstance(tile, dict) and tile.get('yield_units', 0) > 0:
            if is_plant:
                first_age, _, _, ongoing = _PRO4_CROPS[tile['crop']]
                if day - tile['planted_day'] >= first_age:
                    add(tile['crop'], tile['yield_units'])
                    tile['yield_units'] = 0
                    if not ongoing:
                        farm['tiles'][y][x] = None
            elif is_animal:
                add(_PRO4_ANIMALS[tile['animal']][1], tile['yield_units'])
                tile['yield_units'] = 0
        elif op == 'FERTILIZE' and is_plant and take('FERTILIZER'):
            tile['fertilized_until_day'] = max(tile.get('fertilized_until_day', -1), day + 2)
        elif op == 'DIG' and tile is not None and not is_animal:
            farm['tiles'][y][x] = None
        elif op in ('BUILD_COOP', 'BUILD_PASTURE') and tile is None:
            farm['tiles'][y][x] = {'kind': op[6:]}
        elif op == 'FEED' and is_animal and not tile['fed_today'] and take('WHEAT'):
            tile['fed_today'] = True
        elif op == 'COLLECT_FERTILIZER' and is_animal and tile['fertilizer_available']:
            tile['fertilizer_available'] = False
            add('FERTILIZER')
        elif op == 'CARE' and is_animal and not tile['cared_today']:
            tile['cared_today'] = True
    return result
