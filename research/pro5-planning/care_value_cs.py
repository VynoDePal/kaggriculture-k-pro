"""Marginal collected units from today's care under an explicit future schedule.

Caller must reserve feeding/collection routes and sale opportunities separately.
No cash is credited for pending bonuses or uncollected terminal inventory.
"""
from animal_night_model_bh import animal_after_night


def care_delta(tile,day,*,schedule):
    if any(type(d) is not int or not day<d<=29 for d in schedule):
        raise ValueError('Future schedule must end within the game')
    def simulate(care):
        state=animal_after_night(tile,day,care=care);collected={}
        for d in range(day+1,max(schedule,default=day)+1):
            if 'animal' not in state:break
            actions=schedule.get(d,{})
            if actions.get('collect'):
                collected[d]=state['yield_units'];state=dict(state,yield_units=0)
            state=animal_after_night(state,d,feed=bool(actions.get('feed')),care=bool(actions.get('care')))
        return collected
    baseline=simulate(False);treated=simulate(True)
    deltas={d:treated.get(d,0)-baseline.get(d,0) for d in sorted(set(baseline)|set(treated))}
    return dict(extra_collected=sum(deltas.values()),collection_deltas={d:n for d,n in deltas.items() if n})
