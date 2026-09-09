"""Daily accounting of a supplied service/sale scenario, not a price oracle.

Sale feasibility within a day and travel must be established by the caller.
Costs precede receipts within each day, a conservative funding convention.
Action opportunity value is not cash and does not fund subsequent purchases.
"""
import math


def quote_crop_plan(plan, *, sales, fertilizer_cost, action_value, extra_actions):
    def day_index(day):
        if type(day) is not int or not 0<=day<=29:
            raise ValueError('Activity outside playable days')
        return day

    def amount(value):
        if not math.isfinite(value) or value<0:
            raise ValueError('Amounts must be finite and nonnegative')
        return value

    fertilizer_cost=amount(fertilizer_cost)
    action_value=amount(action_value)
    daily=[dict(actions=0,cost=0,receipts=0,harvested=0,sold=0) for _ in range(30)]
    seed_charged=False
    for day,op in plan['actions']:
        row=daily[day_index(day)]
        row['actions']+=1
        if op[0]=='PLANT':
            if seed_charged:raise ValueError('Expected a single planting cycle')
            row['cost']+=amount(plan['seed_cost']);seed_charged=True
        elif op[0]=='FERTILIZE':
            row['cost']+=fertilizer_cost
    for day,count in extra_actions.items():
        if type(count) is not int:raise ValueError('Action counts must be integers')
        daily[day_index(day)]['actions']+=amount(count)
    for day,units in plan['harvests']:
        daily[day_index(day)]['harvested']+=amount(units)
    for day,units,price in sales:
        row=daily[day_index(day)];units=amount(units);price=amount(price)
        row['sold']+=units;row['receipts']+=units*price
    balance=0
    capital=0
    inventory=0
    for row in daily:
        inventory+=row['harvested']
        if row['sold']>inventory:raise ValueError('Sale exceeds harvested inventory')
        inventory-=row['sold']
        balance-=row['cost']
        capital=max(capital,-balance)
        balance+=row['receipts']
    actions=sum(row['actions'] for row in daily)
    return dict(daily=daily,cash_profit=balance,capital_required=capital,
                action_count=actions,net_value=balance-actions*action_value,
                unsold_units=inventory)
