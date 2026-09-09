"""Check physical stock reservations in canonical game phase order.

Events describe intended effects, not arbitrary effects executed in the game.
The caller must derive them from feasible actions and verified harvest amounts.
Rejecting overflow means the intended full transfer cannot be reserved; the
game may instead partially transfer or discard, which requires a revised plan.
"""


def check_stock_events(events, *, initial_stock, shed_capacity=100):
    phases={'unit':0,'market':1,'night':2}
    stock={account:dict(items) for account,items in initial_stock.items()}
    scheduled=[];seen=set()
    for event in events:
        step=event['step'];phase=event['phase'];order=event['order']
        if (type(step) is not int or not 0<=step<=718 or phase not in phases
                or type(order) is not int or order<0
                or (phase=='night' and step%24!=23)):
            return dict(feasible=False,reason='invalid_event_time')
        key=(step,phases[phase],order)
        if key in seen:return dict(feasible=False,reason='duplicate_event',event_key=key)
        seen.add(key);scheduled.append((key,event))
    peak=sum(stock.get('shed',{}).values())
    if peak>shed_capacity:return dict(feasible=False,reason='shed_overflow',event_key=None)
    for key,event in sorted(scheduled,key=lambda pair:pair[0]):
        changes={}
        for account,item,delta in event['changes']:
            if type(delta) is not int:raise ValueError('Stock changes must be integral')
            changes[account,item]=changes.get((account,item),0)+delta
        for (account,item),delta in changes.items():
            if stock.get(account,{}).get(item,0)+delta<0:
                return dict(feasible=False,reason='insufficient_stock',event_key=key,
                            account=account,item=item)
        shed_delta=sum(delta for (account,item),delta in changes.items() if account=='shed')
        size=sum(stock.get('shed',{}).values())+shed_delta
        if size>shed_capacity:return dict(feasible=False,reason='shed_overflow',event_key=key)
        for (account,item),delta in changes.items():
            bucket=stock.setdefault(account,{})
            bucket[item]=bucket.get(item,0)+delta
        peak=max(peak,size)
    return dict(feasible=True,stock=stock,peak_shed_units=peak)
