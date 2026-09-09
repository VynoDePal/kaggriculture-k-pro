"""Observation-driven maintenance controller, not a complete farming strategy.

One baseline search, optionally followed by bounded day-start hand-renewal
comparisons. Valid portfolios persist across nights. Missing production or
investment proposals are not supplied by a fallback.
"""
from workforce_cc import choose_maintenance_workforce
from plan_execution_dd import start_plan,next_action
from pending_dg import remaining_projects
from renew_hand_ed import renewal_candidates
from rotation_review_ev import release_unstarted_rotations
from herd_expansion_fa import expansion_candidates
from reuse_paid_hands_fc import reuse_candidates
from town_scenario_ep import with_known_town_demand
from funded_land_fg import land_candidates
from shared_herd_fh import shared_herd_candidates


def decide_turn(obs,memory=None,*,market_scenario,renew_hand_limit=0,renew_max_hands=1,fill_spare_farmer=False,
                reconsider_rotations=False,herd_expansion_size=0,reuse_paid_crop_limit=0,land_crop_limit=0,shared_herd_size=0,
                use_known_town_demand=False,wait_for_first_shop=False,**options):
    if type(renew_hand_limit) is not int or not 0<=renew_hand_limit<=100:raise ValueError('Invalid hand renewal limit')
    if type(renew_max_hands) is not int or not 1<=renew_max_hands<=6 or renew_max_hands>4 and not options.get('share_crop_hands',False):
        raise ValueError('Invalid renewal crop block size')
    if type(fill_spare_farmer) is not bool:raise ValueError('Invalid spare farmer option')
    if type(reconsider_rotations) is not bool:raise ValueError('Invalid rotation review option')
    if type(herd_expansion_size) is not int or not 0<=herd_expansion_size<=4:raise ValueError('Invalid herd expansion size')
    if type(reuse_paid_crop_limit) is not int or not 0<=reuse_paid_crop_limit<=10:raise ValueError('Invalid paid crop reuse limit')
    if type(land_crop_limit) is not int or not 0<=land_crop_limit<=10:raise ValueError('Invalid land crop limit')
    if type(shared_herd_size) is not int or not 0<=shared_herd_size<=4:raise ValueError('Invalid shared herd size')
    if type(use_known_town_demand) is not bool or type(wait_for_first_shop) is not bool:
        raise ValueError('Invalid public market option')
    if use_known_town_demand:
        if market_scenario is None:raise ValueError('Known demand needs a market scenario')
        market_scenario=with_known_town_demand(obs,market_scenario)
    reason='initial';pending=();fallback=None
    review=None
    farm=obs['farms'][obs['player']]
    if (reconsider_rotations and memory is not None and not memory.get('cancelled')
            and memory.get('last_step') in (None,obs['step']-1) and not farm['hands'] and not farm['hires_today']):
        review=release_unstarted_rotations(memory.get('projects',[]),step=obs['step'],action_value=options['action_value'])
    if memory is not None:
        execution=next_action(obs,memory)
        if not execution['replan']:
            fallback=dict(action=execution['action'],memory=execution['state'],replanned=False)
            action=execution['action']
            idle=action['farmer']==['PASS'] and all(op==['PASS'] for op in action['hands']) and not action['market']
            spare_farmer=fill_spare_farmer and options.get('new_crop_limit',0)>0 and action['farmer']==['PASS'] and not any(
                s['worker']==0 and 24*s['day']+s['hour']<=obs['step']<24*s['day']+s['hour']+len(s['actions'])
                for p in memory.get('projects',[]) for s in p['sessions'])
            renew=renew_hand_limit and obs['hour']==0 and market_scenario is not None and not any(
                s['worker']!=0 and 24*s['day']+s['hour']+len(s['actions'])>obs['step']
                for p in memory.get('projects',[]) for s in p['sessions'])
            renew=renew or (herd_expansion_size or reuse_paid_crop_limit or land_crop_limit or shared_herd_size) and obs['hour']==0
            if (not idle and not spare_farmer and not memory.get('replan_after_hire') and not renew and review is None) or 'projects' not in memory:return fallback
            pending=remaining_projects(memory['projects'],step=obs['step'],action_value=options['action_value'])
            reason='fill_idle_time'
        else:reason=execution['reason']
    if review is not None:
        pending=remaining_projects(memory['projects'],step=obs['step'],action_value=options['action_value'])
    groups=[pending]
    search_options=dict(options)
    if review is not None:
        budget=options.get('max_subsets',5000)
        if type(budget) is not int or budget<1:raise ValueError('Invalid shared search budget')
        if budget>=2:
            groups.append(review);search_options['max_subsets']=budget//2
    selected=None
    for index,required in enumerate(groups):
        if herd_expansion_size or reuse_paid_crop_limit or land_crop_limit or shared_herd_size:
            # Retaining and expanding must use the same current own-trade
            # accounting, rather than stale food costs for the baseline only.
            required=[dict(p,joint_product_trades=True) for p in required]
        candidate,why=_select_portfolio(obs,required,market_scenario=market_scenario,options=search_options,
                                        renew_hand_limit=renew_hand_limit,renew_max_hands=renew_max_hands,reason=reason,
                                        herd_expansion_size=herd_expansion_size,reuse_paid_crop_limit=reuse_paid_crop_limit,
                                        wait_for_first_shop=wait_for_first_shop,land_crop_limit=land_crop_limit,shared_herd_size=shared_herd_size)
        if selected is None or candidate['feasible'] and (not selected['feasible'] or candidate['net_value']>selected['net_value']):
            selected=candidate;pending=required
            reason='rotation_reconsidered' if index else why
    if not selected['feasible'] and fallback is not None:return fallback
    if selected['feasible'] and selected['initial_action'] is not None:
        # Keep prior commitments only, never the projected new worker plan.
        retained=None
        if pending:
            retained=start_plan(pending)
            retained.update(last_step=obs['step'],replan_after_hire=True)
        return dict(action=selected['initial_action'],memory=retained,replanned=True,reason='hire_reobserve')
    if selected['feasible']:
        execution=next_action(obs,start_plan(selected['selected_projects']))
        if not execution['replan']:
            return dict(action=execution['action'],memory=execution['state'],replanned=True,reason=reason)
        reason=execution['reason']
    else:reason='no_feasible_portfolio'
    farm=obs['farms'][obs['player']]
    return dict(action=dict(farmer=['PASS'],hands=[['PASS'] for _ in farm['hands']],market=[]),
                memory=None,replanned=True,reason=reason)


def _select_portfolio(obs,pending,*,market_scenario,options,renew_hand_limit,renew_max_hands,reason,herd_expansion_size=0,reuse_paid_crop_limit=0,wait_for_first_shop=False,land_crop_limit=0,shared_herd_size=0):
    """One mandatory portfolio and its renewals, sharing one subset budget."""
    renewals=[]
    reused_ids=set()
    if pending and renew_hand_limit and obs['hour']==0 and market_scenario is not None:
        renewals=renewal_candidates(obs,pending_projects=pending,limit=renew_hand_limit,
                                    action_value=options['action_value'],market_scenario=market_scenario,max_hands=renew_max_hands,
                                    share_hands=options.get('share_crop_hands',False))
    if pending and reuse_paid_crop_limit and obs['hour']==0 and market_scenario is not None:
        reused=reuse_candidates(obs,pending_projects=pending,limit=reuse_paid_crop_limit,
                                action_value=options['action_value'],market_scenario=market_scenario)
        if reused:
            best=max(reused,key=lambda p:p['net_value'])
            renewals.append(best);reused_ids.add(best['id'])
    growth_id=None
    land_id=None
    if pending and land_crop_limit and obs['hour']==0 and market_scenario is not None:
        sources=[pending]
        if renewals:sources.append([max(renewals,key=lambda p:p['net_value'])])
        lands=[]
        for source in sources:
            lands+=land_candidates(obs,pending_projects=source,limit=land_crop_limit,
                                   action_value=options['action_value'],market_scenario=market_scenario)
        if lands:
            best_land=max(lands,key=lambda p:p['net_value']);land_id=best_land['id']
            renewals.append(best_land)
    shared_id=None
    if (pending and shared_herd_size and obs['hour']==0 and market_scenario is not None
            and (not wait_for_first_shop or obs['town']['unlocked_shops'])):
        sources=[pending]
        if renewals:sources.append([max(renewals,key=lambda p:p['net_value'])])
        shared=[]
        for source in sources:
            shared+=shared_herd_candidates(obs,pending_projects=source,max_size=shared_herd_size,
                                           action_value=options['action_value'],market_scenario=market_scenario,
                                           care=options.get('herd_care',False),
                                           flexible_fertilizer=options.get('herd_flexible_fertilizer',False))
        if shared:
            best_shared=max(shared,key=lambda p:p['net_value']);shared_id=best_shared['id']
            renewals.append(best_shared)
    if (pending and herd_expansion_size and obs['hour']==0 and market_scenario is not None
            and (not wait_for_first_shop or obs['town']['unlocked_shops'])):
        # Deferral affects only new cohorts, never funded crops, food or care.
        # The trigger is the observed shop list, not a predicted future draw.
        sources=[pending]
        if renewals:sources.append([max(renewals,key=lambda p:p['net_value'])])
        growth=[]
        for source in sources:
            growth+=expansion_candidates(obs,pending_projects=source,max_size=herd_expansion_size,
                                          action_value=options['action_value'],market_scenario=market_scenario,
                                          care=options.get('herd_care',False),
                                          flexible_fertilizer=options.get('herd_flexible_fertilizer',False))
        if growth:
            best_growth=max(growth,key=lambda p:p['net_value']);growth_id=best_growth['id']
            renewals=[best_growth]+renewals
    search_options=dict(options)
    if renewals:
        budget=options.get('max_subsets',5000)
        if type(budget) is not int or budget<1:raise ValueError('Invalid shared search budget')
        renewals=renewals[:budget-1]
        search_options['max_subsets']=budget//(len(renewals)+1)
    selected=choose_maintenance_workforce(obs,market_scenario=market_scenario,pending_projects=pending,**search_options)
    if renewals:
        # The baseline already searches unrelated investments. Each renewal
        # compares its complete retained portfolio plus current maintenance;
        # do not regenerate every animal/crop investment for every alternative.
        renewal_options=dict(search_options)
        renewal_options.update(max_hires=0,new_crop_limit=0,funded_crop_limit=0,
                               team_pair_limit=0,animal_plot_limit=0,livestock_team_limit=0,paid_team_size=0,paid_rotation_size=0,herd_size_limit=0)
        for project in renewals:
            alternative=choose_maintenance_workforce(obs,market_scenario=market_scenario,
                                                     pending_projects=[project],**renewal_options)
            if alternative['feasible'] and (not selected['feasible'] or alternative['net_value']>selected['net_value']):
                selected=alternative
                reason=('shared_herd_expansion' if project['id']==shared_id else
                        'productive_land_expansion' if project['id']==land_id else
                        'herd_expanded' if project['id']==growth_id else
                        'reused_paid_hands' if project['id'] in reused_ids else 'funded_hand_renewal')
    return selected,reason
