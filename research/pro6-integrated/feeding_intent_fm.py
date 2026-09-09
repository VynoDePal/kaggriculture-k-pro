"""Align ordinary-day wheat purchases with the existing feeding policy.

Experimental extension after FL. No new fasting decision is introduced.
Counts intended feeds after own unit actions and keeps a reserve of at least
one wheat per currently fasting animal for the next feeding opportunity.
This is an inventory budget, not proof of future delivery or price profit.
"""


def food_budget(obs, action, state, *, reference):
    after = reference.project_unit_phase(obs, [action['farmer'], *action['hands']])
    private = after['private']
    food = private['shed'].get('WHEAT', 0) + sum(i.get('WHEAT', 0) for i in private['inventories'])
    intended = fasting = 0
    for row in after['farms'][obs['player']]['tiles']:
        for tile in row:
            if not isinstance(tile, dict) or not tile.get('animal') or tile['fed_today']:
                continue
            tasks, _ = reference.animal_tasks(tile, obs['day'], obs['market']['prices'], obs.get('town', {}))
            # Never reinterpret an already missed feeding as optional, even if
            # a later policy changes its intent helper.
            if ['FEED'] in tasks or tile.get('consecutive_unfed', 0):
                intended += 1
            else:
                fasting += 1
    reserve = max(sum(state['herd'].values())//3, fasting)
    sales = sum(o[2] for o in action['market'] if len(o) >= 3 and o[:2] == ['SELL','WHEAT'] and o[2] > 0)
    return dict(intended=intended, fasting=fasting, reserve=reserve, food=food,
                target=intended+reserve, needed=max(0, intended+reserve+sales-food))


def adjust(obs, action, state, *, reference):
    if obs['day'] >= 28:
        return action
    orders = action['market']
    buys = [i for i, o in enumerate(orders) if len(o) >= 3 and o[:2] == ['BUY_PRODUCT','WHEAT'] and o[2] > 0]
    if len(buys) != 1:
        return action
    budget = food_budget(obs, action, state, reference=reference)
    if not budget['fasting']:
        return action
    index = buys[0]
    quantity = min(orders[index][2], budget['needed'])
    if quantity == orders[index][2]:
        return action
    revised = list(orders)
    revised[index] = ['BUY_PRODUCT','WHEAT',quantity] if quantity else []
    return dict(action, market=revised)


def install(reference):
    original = reference.decide

    def decide(obs, state):
        return adjust(obs, original(obs, state), state, reference=reference)

    reference.decide = decide
    return reference.agent
