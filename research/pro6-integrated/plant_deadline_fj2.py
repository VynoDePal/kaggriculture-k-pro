"""Repair impossible planting routes without displacing current valid work.

Experimental adapter, not a submission. Keeps the reviewed reference's valid
assignments and supply/delivery actions. Rematches only otherwise idle workers
and workers assigned to planting that cannot start before its h21 cutoff.
This prevents a local route repair from taking away an already selected care
action. Future daily outcomes and economic superiority remain unproven.
"""


def install(reference):
    original = reference.act_units

    def act_units(obs, st, work):
        previous = dict(st['targets'])
        actions, shed = original(obs, st, work)
        farm, private = obs['farms'][obs['player']], obs['private']
        positions = [tuple(farm['farmer']),*(tuple(p) for p in farm['hands'])]
        fixed = st['_fixed_units']
        hour, day = obs['hour'], obs['day']

        def too_late(uid, target):
            return (any(a[0] == 'PLANT' for a in work.get(target,([],0))[0])
                    and hour + reference.distance(positions[uid],target) >= 21)

        invalid = {uid for uid,target in st['targets'].items()
                   if uid < len(positions) and uid not in fixed and too_late(uid,target)}
        if not invalid: return actions, shed
        workers = [uid for uid in range(len(positions)) if uid not in fixed
                   and (uid in invalid or actions[uid] == ['PASS'])]
        occupied = {target for uid,target in st['targets'].items()
                    if uid not in workers and uid not in fixed and uid < len(positions)}
        occupied.update(positions[uid] for uid in fixed
            if actions[uid][0] == 'PLACE' and len(actions[uid]) > 1 and actions[uid][1] in reference.ANIMAL)
        tiles = sorted(p for p in work if p not in occupied)
        seeds = dict(private['seeds'])
        for uid,action in enumerate(actions):
            if uid not in workers and action[0] == 'PLANT': seeds[action[1]] -= 1
        costs, commands = [], []
        for uid in workers:
            inv = private['inventories'][uid] if uid < len(private['inventories']) else {}
            row, cmd = [], []
            for target in tiles:
                todo,value = work[target]; valid = []
                for action in todo:
                    op = action[0]
                    if op == 'FERTILIZE' and not inv.get('FERTILIZER'): continue
                    if op == 'FEED' and not inv.get('WHEAT'): continue
                    if op == 'CARE' and not farm['tiles'][target[1]][target[0]].get('fed_today') and not inv.get('WHEAT'): continue
                    if op in ('BUILD_PASTURE','BUILD_COOP') and not inv.get(st['roles'][target]): break
                    if op == 'PLACE' and not inv.get(action[1]): break
                    if op == 'PLANT' and seeds.get(action[1],0) <= 0: break
                    valid.append(action)
                distance = reference.distance(positions[uid],target)
                deadline = 23 if day == 29 else 24
                if day == 29 and hour + distance + len(valid) + reference.radius(target) + 1 > deadline:
                    valid = [a for a in valid if a[0] == 'HARVEST']
                if (not valid or too_late(uid,target)
                        or hour + distance + 1 + (reference.radius(target)+1 if day == 29 else 0) > deadline
                        or (day == 29 and not any(a[0] == 'HARVEST' for a in valid))):
                    row.append(1000000.0);cmd.append(['PASS']);continue
                cost = (distance + 0.15*len(valid) - reference.assignment_urgency(value,hour,day)
                        + 6*(st['zones'].get(target) != uid))
                if positions[uid] == target: cost -= 2
                if previous.get(uid) == target: cost -= 0.4
                row.append(cost)
                cmd.append(valid[0] if distance == 0 else reference.move(positions[uid],target))
            costs.append(row+[50.0]*len(workers));commands.append(cmd)
        matched = reference.minimum_assignment(costs)
        for index,uid in enumerate(workers):
            column = matched[index]
            if column >= len(tiles) or costs[index][column] >= 100000.0:
                actions[uid] = ['PASS'];st['targets'].pop(uid,None);continue
            action = commands[index][column]
            if action[0] == 'PLANT':
                crop = action[1]
                if seeds.get(crop,0) <= 0: action = ['PASS']
                else: seeds[crop] -= 1
            actions[uid] = action;st['targets'][uid] = tiles[column]
        return actions,shed

    reference.act_units = act_units
    return reference.agent
