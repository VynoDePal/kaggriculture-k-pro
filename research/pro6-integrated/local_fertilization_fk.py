"""Complete an existing fertilizer job locally instead of waiting for travel.

Experimental adapter for the standard reviewed K Pro reference. Only an idle
worker carrying fertilizer may take over an existing FERTILIZE task reserved
to another worker who is moving. The moving worker's current action and all
other actions remain intact. No target-memory rewrite or price forecast.
"""
import copy

MOVES={'NORTH','SOUTH','EAST','WEST'}


def complete(obs,actions,st,work,*,project):
    farm=obs['farms'][obs['player']]
    positions=[tuple(farm['farmer']),*(tuple(p) for p in farm['hands'])]
    owners={p:uid for uid,p in st['targets'].items() if uid < len(actions)}
    revised=list(actions)
    baseline=None
    for uid,(pos,action) in enumerate(zip(positions,revised)):
        if action != ['PASS'] or uid in st.get('_fixed_units',set()):continue
        owner=owners.get(pos)
        if owner is None or owner==uid or revised[owner][0] not in MOVES:continue
        if owner in st.get('_fixed_units',set()):continue
        if not any(a[0]=='FERTILIZE' for a in work.get(pos,([],0))[0]):continue
        if baseline is None:baseline=project(obs,revised)
        tile=baseline['farms'][obs['player']]['tiles'][pos[1]][pos[0]]
        if not isinstance(tile,dict) or tile.get('kind')!='PLANT':continue
        if tile.get('fertilized_until_day',-1)>=obs['day']:continue
        inventory=baseline['private']['inventories'][uid]
        if inventory.get('FERTILIZER',0)<=0:continue
        trial=list(revised);trial[uid]=['FERTILIZE']
        after=project(obs,trial)
        expected=copy.deepcopy(baseline)
        expected['farms'][obs['player']]['tiles'][pos[1]][pos[0]]['fertilized_until_day']=obs['day']+2
        inv=expected['private']['inventories'][uid]
        inv['FERTILIZER']-=1
        if inv['FERTILIZER']==0:del inv['FERTILIZER']
        # Exact own-phase check guards canonical interactions and duplicated
        # service, not just the final flag on the target plant.
        if after != expected:continue
        revised=trial;baseline=after
    return revised


def install(reference):
    original=reference.act_units

    def act_units(obs,st,work):
        actions,shed=original(obs,st,work)
        return complete(obs,actions,st,work,project=reference.project_unit_phase),shed

    reference.act_units=act_units
    return reference.agent
