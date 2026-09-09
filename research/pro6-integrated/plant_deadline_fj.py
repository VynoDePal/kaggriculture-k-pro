"""Experimental assignment correction, not a standalone Kaggle submission.

Install only on a fresh experimental copy of the reviewed reference module.
Its task generator closes planting at h21. Reject each worker/tile edge whose
arrival is too late, but leave that tile available to closer workers. Other
assignment scores, supplies, unit ordering and market policy are unchanged.
This repairs a planning inconsistency; it does not claim higher final scores.
"""


def install(reference):
    def act_units(obs, st, work):
        previous_targets = dict(st['targets'])
        actions, shed = reference.act_units_greedy(obs, st, work)
        me = obs['farms'][obs['player']]
        priv = obs['private']
        hour, day = obs['hour'], obs['day']
        positions = [tuple(me['farmer'])] + [tuple(p) for p in me['hands']]
        fixed = st['_fixed_units']
        workers = [i for i in range(len(positions)) if i not in fixed]
        fixed_tiles = {positions[i] for i in fixed if actions[i][0] == 'PLACE'
                       and len(actions[i]) > 1 and actions[i][1] in reference.ANIMAL}
        tiles = sorted(p for p in work if p not in fixed_tiles)
        costs, commands = [], []
        seeds = dict(priv['seeds'])
        for uid in workers:
            inv = priv['inventories'][uid] if uid < len(priv['inventories']) else {}
            row, cmd = [], []
            for p in tiles:
                todo, value = work[p]
                valid = []
                for a in todo:
                    op = a[0]
                    if op == 'FERTILIZE' and not inv.get('FERTILIZER'): continue
                    if op == 'FEED' and not inv.get('WHEAT'): continue
                    if op == 'CARE':
                        t = me['tiles'][p[1]][p[0]]
                        if not t.get('fed_today') and not inv.get('WHEAT'): continue
                    if op in ('BUILD_PASTURE', 'BUILD_COOP') and not inv.get(st['roles'][p]): break
                    if op == 'PLACE' and not inv.get(a[1]): break
                    if op == 'PLANT' and not seeds.get(a[1]): break
                    valid.append(a)
                d = reference.distance(positions[uid], p)
                deadline = 23 if day == 29 else 24
                if day == 29 and hour + d + len(valid) + reference.radius(p) + 1 > deadline:
                    valid = [a for a in valid if a[0] == 'HARVEST']
                # The existing task policy removes PLANT at h21. Moving toward
                # such a task cannot execute it at/after that hour, even though
                # the generic daily deadline would allow the movement.
                misses_plant_window = any(a[0] == 'PLANT' for a in valid) and hour + d >= 21
                if (not valid or misses_plant_window
                        or hour + d + 1 + (reference.radius(p) + 1 if day == 29 else 0) > deadline
                        or (day == 29 and not any(a[0] == 'HARVEST' for a in valid))):
                    row.append(1000000.0); cmd.append(['PASS']); continue
                action = valid[0] if d == 0 else reference.move(positions[uid], p)
                urgency = reference.assignment_urgency(value, hour, day)
                cost = d + 0.15 * len(valid) - urgency + 6 * (st['zones'].get(p) != uid)
                if positions[uid] == p: cost -= 2
                if previous_targets.get(uid) == p: cost -= 0.4
                row.append(cost); cmd.append(action)
            costs.append(row + [50.0] * len(workers))
            commands.append(cmd)
        matched = reference.minimum_assignment(costs)
        for index, uid in enumerate(workers):
            j = matched[index]
            if j >= len(tiles) or costs[index][j] >= 100000.0:
                actions[uid] = ['PASS']; st['targets'].pop(uid, None); continue
            action = commands[index][j]
            if action[0] == 'PLANT':
                crop = action[1]
                if seeds.get(crop, 0) <= 0: action = ['PASS']
                else: seeds[crop] -= 1
            actions[uid] = action
            st['targets'][uid] = tiles[j]
        return actions, shed

    reference.act_units = act_units
    return reference.agent
