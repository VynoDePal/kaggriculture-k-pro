"""Release only authenticated-by-content reservations of unstarted cycles.

This is provenance inside a local plan, not a cryptographic trust boundary.
Unknown/modified reservations are never removed. Normal portfolio, stock and
live execution checks remain required after selecting a replacement.
"""
import copy
import hashlib
import json
from collections import Counter
from pending_dg import remaining_projects

FIELDS=('sessions','market_actions','cash_events','stock_events','sale_quotes','plot_releases')


def _key(field,value):
    if field=='sessions':
        data=[value[k] for k in ('day','hour','worker','start','actions')]
    elif field=='sale_quotes':
        # Receipts are deliberately refreshed during market repricing.
        data=[value[k] for k in ('step','order','item','quantity')]
    else:data=value
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _step(field,value):
    if field=='sessions':return 24*value['day']+value['hour']
    if field=='market_actions':return value[0]
    if field=='plot_releases':return value['after_step']-1
    return value['step']


def rotation_reviews(parts,starts):
    return [dict(step=24*starts[i],drop={field:[_key(field,e) for p in parts[i:] for e in p.get(field,[])]
                                         for field in FIELDS}) for i in range(1,len(parts))]


def release_unstarted_rotations(projects,*,step,action_value):
    """None means no valid review point; [] means nothing remains committed."""
    if step%24:return None
    result=[];changed=False
    for source in projects:
        reviews=[r for r in source.get('rotation_reconsiderations',[]) if r['step']==step]
        if not reviews:
            result.append(source);continue
        if len(reviews)!=1:return None
        drop=reviews[0]['drop'];p=copy.deepcopy(source)
        for field in FIELDS:
            wanted=Counter(drop[field]);entries=p.get(field,[])
            matched=[e for e in entries if _key(field,e) in wanted]
            if Counter(_key(field,e) for e in matched)!=wanted:return None
            if any(_step(field,e)<step for e in matched):return None
            p[field]=[e for e in entries if _key(field,e) not in wanted]
        # Rebuild dated accounting before the normal suffix validator. Keep
        # every non-crop opportunity cost and every unrelated animal operation.
        rows={}
        for e in p['cash_events']:rows.setdefault(e['step']//24,dict(cost=0,receipts=0))['cost']+=e['cost']
        for q in p['sale_quotes']:rows.setdefault(q['step']//24,dict(cost=0,receipts=0))['receipts']+=q['receipts']
        p['cashflows']=[dict(day=d,**row) for d,row in sorted(rows.items())]
        p['id']+=f':reviewed:{step}'
        for field in ('rotation_reconsiderations','rotation','cycle_days'):p.pop(field,None)
        result.append(p);changed=True
    return remaining_projects(result,step=step,action_value=action_value) if changed else None
