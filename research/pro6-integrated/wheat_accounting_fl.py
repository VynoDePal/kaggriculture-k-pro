"""Bound existing wheat purchases using actual post-unit own food inventory.

Does not change crop targets, selling policy, unit tasks, or other market orders.
Keeps the reference's ordinary-day food target (unfed animals plus one third
of planned herd), but counts pickup/harvest/feed exactly once. Never increases
a purchase. Terminal feeding rules are deliberately left to the reference.
An empty order is an ignored slot in the reviewed official market parser; it
preserves simultaneous order indices instead of shifting subsequent orders.
"""


def adjust(obs,action,state,*,project):
    if obs['day']>=28:return action
    orders=action.get('market',[])
    buys=[i for i,o in enumerate(orders) if len(o)>=3 and o[0]=='BUY_PRODUCT'
          and o[1]=='WHEAT' and o[2]>0]
    # The reviewed policy emits one wheat buy. Multiple purchases require a
    # fill-aware cash/market model; do not assume an earlier order succeeds.
    if len(buys)!=1:return action
    after=project(obs,[action['farmer'],*action['hands']])
    private=after['private'];farm=after['farms'][obs['player']]
    food=private['shed'].get('WHEAT',0)+sum(i.get('WHEAT',0) for i in private['inventories'])
    unfed=sum(1 for row in farm['tiles'] for tile in row
              if isinstance(tile,dict) and tile.get('animal') and not tile.get('fed_today'))
    target=unfed+sum(state['herd'].values())//3
    sales=sum(o[2] for o in orders if len(o)>=3 and o[0]=='SELL' and o[1]=='WHEAT' and o[2]>0)
    # Reserve all proposed sales, even if some might fail. No expected future
    # harvest or future purchase from outside this action is credited.
    need=max(0,target-food+sales)
    result=list(orders);changed=False
    for index in buys:
        order=orders[index]
        quantity=min(order[2],need)
        need-=quantity
        if quantity != order[2]:
            result[index]=['BUY_PRODUCT','WHEAT',quantity] if quantity else []
            changed=True
    return dict(action,market=result) if changed else action


def install(reference):
    original=reference.decide

    def decide(obs,state):
        action=original(obs,state)
        return adjust(obs,action,state,project=reference.project_unit_phase)

    reference.decide=decide
    return reference.agent
