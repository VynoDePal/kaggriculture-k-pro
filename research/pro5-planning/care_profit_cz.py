"""Compare selling all delivered output with/without care under fixed scenario.

Caller supplies the marginal action/opportunity cost of the compared schedules.
This does not reserve market slots or predict future market inventory.
"""
from market_quote_ci import quote_sale


def quote_care_profit(delivery,*,product,params,inventory,marginal_action_cost):
    if not delivery['feasible']:raise ValueError('Delivery must be feasible')
    if marginal_action_cost<0:raise ValueError('Negative marginal action cost')
    care_inventory=base_inventory=inventory;care_receipts=base_receipts=0
    for event in sorted(delivery['stock_events'],key=lambda e:(e['step'],e['order'])):
        qty=sum(n for account,item,n in event['changes'] if account=='shed' and item==product and n>0)
        if not qty:continue
        delta=delivery['collection_deltas'].get(event['step']//24,0)
        if not 0<=delta<=qty:raise ValueError('Unsupported negative or inconsistent surplus')
        care=quote_sale(params,care_inventory,qty);base=quote_sale(params,base_inventory,qty-delta)
        care_receipts+=care['receipts'];base_receipts+=base['receipts']
        care_inventory=care['inventory'];base_inventory=base['inventory']
    increment=care_receipts-base_receipts
    return dict(care_receipts=care_receipts,baseline_receipts=base_receipts,
                extra_receipts=increment,net_increment=increment-marginal_action_cost)
