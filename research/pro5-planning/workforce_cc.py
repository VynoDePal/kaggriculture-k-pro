"""Compare bounded maintenance plans with zero or more funded hires.

Preservation policy only, not total farm profit. Hiring projections require a
fresh observation and replanning after the initial action; no predicted market
or plant-decay state may be blindly used for subsequent execution.
"""
from hiring_cb import hire_scenario
from combined_maintenance_bx import maintenance_proposals
from project_selection_bs import select_projects
from cooperative_maintenance_ce import complementary_proposals
from harvest_cg import harvest_proposals
from joint_sales_ck import reprice_sales
from feed_collect_cr import feed_collect_proposals
from care_pair_db import care_project_pair
from pending_dg import MOVES
from new_crops_dk import new_crop_proposals
from future_workers_do import future_workers
from funded_candidates_dp import funded_candidates
from team_candidates_dr import team_candidates
from dual_collect_du import dual_collect_proposals
from animal_candidates_dy import animal_candidates
from livestock_team_eb import livestock_team_candidates
from paid_team_ef import paid_team_candidates
from crop_rotation_eu import rotation_candidates
from herd_calendar_ex import herd_candidates


def choose_maintenance_workforce(obs, *, max_hires, action_value, reserve_cash=0,
                                 max_stops=6,max_projects=2000,max_subsets=5000,sale_prices=None,market_scenario=None,
                                 care_horizon=3,pending_projects=(),new_crop_limit=0,funded_crop_limit=0,team_pair_limit=0,
                                 animal_plot_limit=0,animal_buy_food=False,livestock_team_limit=0,paid_team_size=0,
                                 livestock_max_hands=1,share_crop_hands=False,paid_rotation_size=0,herd_size_limit=0,herd_care=False,
                                 herd_flexible_fertilizer=False):
    if type(max_hires) is not int or not 0<=max_hires<=10:raise ValueError('Invalid hire limit')
    if type(care_horizon) is not int or not 0<=care_horizon<=29:raise ValueError('Invalid care horizon')
    if type(new_crop_limit) is not int or not 0<=new_crop_limit<=100:raise ValueError('Invalid crop plot limit')
    if type(funded_crop_limit) is not int or not 0<=funded_crop_limit<=100:raise ValueError('Invalid funded crop limit')
    if type(team_pair_limit) is not int or not 0<=team_pair_limit<=100:raise ValueError('Invalid team pair limit')
    if type(animal_plot_limit) is not int or not 0<=animal_plot_limit<=100:raise ValueError('Invalid animal plot limit')
    if type(animal_buy_food) is not bool:raise ValueError('Invalid animal food funding option')
    if type(livestock_team_limit) is not int or not 0<=livestock_team_limit<=100:raise ValueError('Invalid livestock team limit')
    if type(paid_team_size) is not int or not 0<=paid_team_size<=6 or paid_team_size>4 and not share_crop_hands:
        raise ValueError('Invalid paid crop block size')
    # Legacy option name: with sharing enabled this bounds crop count;
    # paid_crop_team still limits the actual workforce to four hands.
    if type(livestock_max_hands) is not int or not 1<=livestock_max_hands<=6 or livestock_max_hands>4 and not share_crop_hands:
        raise ValueError('Invalid mixed crop block size')
    if type(share_crop_hands) is not bool:raise ValueError('Invalid shared crop hands option')
    if type(paid_rotation_size) is not int or not 0<=paid_rotation_size<=6 or paid_rotation_size>4 and not share_crop_hands:
        raise ValueError('Invalid rotation crop block size')
    if type(herd_size_limit) is not int or not 0<=herd_size_limit<=4:
        raise ValueError('Invalid herd size limit')
    if type(herd_care) is not bool:raise ValueError('Invalid herd care option')
    if type(herd_flexible_fertilizer) is not bool:raise ValueError('Invalid flexible fertilizer option')
    funding=future_workers(obs,pending_projects)
    if not funding['feasible']:return dict(feasible=False,attempts=[],optimal=False,reason='unfunded_future_worker')
    best=None;attempts=[]
    for count in range(max_hires+1):
        if count and pending_projects:
            # Do not skip any reserved operation in the hiring turn. Future
            # sessions keep their absolute dates; no retiming is necessary.
            now=obs['step']
            if any(24*s['day']+s['hour']<=now<24*s['day']+s['hour']+len(s['actions'])
                   for p in pending_projects for s in p['sessions']):continue
            if any(o[0]==now for p in pending_projects for o in p.get('market_actions',[])):continue
        state=obs;cost=0;initial=None
        if count:
            hired=hire_scenario(obs,count=count,reserve_cash=reserve_cash)
            if not hired['feasible']:
                attempts.append(dict(hire_count=count,feasible=False,reason=hired['reason']));continue
            state=hired['observation'];cost=hired['cost'];initial=hired['action']
        proposals=maintenance_proposals(state,action_value=action_value,max_stops=max_stops,max_projects=max_projects)
        complementary=complementary_proposals(state,action_value=action_value,max_stops=max_stops)
        proposals['projects']+=complementary['projects']
        for group,ids in complementary['required_groups'].items():
            proposals['required_groups'][group].extend(ids)
        if sale_prices is not None or market_scenario is not None:
            harvests=harvest_proposals(state,sale_prices=sale_prices,action_value=action_value,market_scenario=market_scenario)
            harvests+=dual_collect_proposals(state,sale_prices=sale_prices,action_value=action_value,market_scenario=market_scenario)
            harvests+=harvest_proposals(state,sale_prices=sale_prices,action_value=action_value,market_scenario=market_scenario,fertilizer_only=True)
            harvests+=feed_collect_proposals(state,sale_prices=sale_prices,action_value=action_value,market_scenario=market_scenario)
            harvests+=feed_collect_proposals(state,sale_prices=sale_prices,action_value=action_value,market_scenario=market_scenario,fertilizer_only=True)
            proposals['projects']+=harvests
            for project in harvests:
                for group in project['satisfies']:
                    if group in proposals['required_groups']:
                        proposals['required_groups'][group].append(project['id'])
        if market_scenario is not None and care_horizon:
            # Only the permanent farmer is reserved on future days. These are
            # conditional plans, not a guarantee of future market prices.
            for y,row in enumerate(state['farms'][state['player']]['tiles']):
                for x,tile in enumerate(row):
                    if not isinstance(tile,dict) or 'animal' not in tile:continue
                    product={'COW':'MILK','SHEEP':'WOOL','GOOSE':'EGG'}[tile['animal']]
                    if product not in market_scenario['params'] or product not in market_scenario['inventory']:continue
                    for day in range(state['day']+1,min(29,state['day']+care_horizon)+1):
                        pair=care_project_pair(state,plot=(x,y),collection_day=day,
                            action_value=action_value,market_scenario=market_scenario)
                        if pair['feasible']:
                            proposals['projects']+=pair['projects']
                            proposals['workers'].update(pair['workers'])
        if market_scenario is not None and new_crop_limit:
            crops=new_crop_proposals(state,limit=new_crop_limit,action_value=action_value,market_scenario=market_scenario,
                                     pending_projects=pending_projects)
            proposals['projects']+=crops['projects'];proposals['workers'].update(crops['workers'])
        if market_scenario is not None and funded_crop_limit:
            funded=funded_candidates(state,limit=funded_crop_limit,action_value=action_value,market_scenario=market_scenario)
            proposals['projects']+=funded['projects'];proposals['workers'].update(funded['workers'])
        if market_scenario is not None and team_pair_limit:
            teams=team_candidates(state,pair_limit=team_pair_limit,action_value=action_value,market_scenario=market_scenario)
            proposals['projects']+=teams['projects'];proposals['workers'].update(teams['workers'])
        if market_scenario is not None and animal_plot_limit:
            animals=animal_candidates(state,limit=animal_plot_limit,action_value=action_value,
                                      market_scenario=market_scenario,buy_food=animal_buy_food)
            proposals['projects']+=animals['projects'];proposals['workers'].update(animals['workers'])
        herd_start_reserved=any(s['worker']==0 and 24*s['day']+s['hour']<=state['step']<24*s['day']+s['hour']+len(s['actions'])
                                for p in pending_projects for s in p['sessions'])
        # Every standalone herd starts its farmer session now. It cannot be
        # selected beside a mandatory operation on that same unit/turn.
        # Paid cohorts composed with the retained plan are handled separately.
        if market_scenario is not None and herd_size_limit and not herd_start_reserved:
            animals=herd_candidates(state,max_size=herd_size_limit,action_value=action_value,market_scenario=market_scenario,
                                    care=herd_care,flexible_fertilizer=herd_flexible_fertilizer)
            proposals['projects']+=animals['projects'];proposals['workers'].update(animals['workers'])
        # Every supported mixed investment hires now and starts its animal
        # installation with the farmer next turn. A mandatory operation in
        # that exact slot makes every such candidate incompatible, regardless
        # of its crop, species or market value. Retained livestock and crop-only
        # renewals remain eligible; this is not a general ban on investment.
        mixed_start=state['step']+1
        mixed_start_reserved=any(s['worker']==0 and 24*s['day']+s['hour']<=mixed_start<24*s['day']+s['hour']+len(s['actions'])
                                 for p in pending_projects for s in p['sessions'])
        if market_scenario is not None and livestock_team_limit and not mixed_start_reserved:
            teams=livestock_team_candidates(state,limit=livestock_team_limit,action_value=action_value,
                                            market_scenario=market_scenario,max_hands=livestock_max_hands,share_hands=share_crop_hands,
                                            rotation_size=paid_rotation_size)
            proposals['projects']+=teams['projects'];proposals['workers'].update(teams['workers'])
        if market_scenario is not None and paid_team_size>=2:
            teams=paid_team_candidates(state,max_size=paid_team_size,sale_scenario=market_scenario,action_value=action_value,
                                      share_hands=share_crop_hands)
            proposals['projects']+=teams['projects'];proposals['workers'].update(teams['workers'])
        if market_scenario is not None and paid_rotation_size:
            rotations=rotation_candidates(state,plot_count=paid_rotation_size,action_value=action_value,
                                           market_scenario=market_scenario,share_hands=share_crop_hands)
            proposals['projects']+=rotations['projects'];proposals['workers'].update(rotations['workers'])
        proposals['projects']+=list(pending_projects)
        proposals['workers'].update(funding['workers'])
        for p in pending_projects:
            for s in p['sessions']:
                if s['day']>state['day']:
                    if s['worker']==0:proposals['workers'].setdefault((s['day'],0),dict(position=(4,4),available_from=0))
                if s['day']==state['day']:
                    x,y=s['start']
                    for op in s['actions']:
                        if op[0] in MOVES:
                            dx,dy=MOVES[op[0]];x,y=x+dx,y+dy
                        elif op[0] in ('FEED','WATER'):
                            group=f"{'feed' if op[0]=='FEED' else 'water'}:{x}:{y}"
                            if group in proposals['required_groups']:
                                proposals['required_groups'][group].append(p['id'])
        private=state['private']
        stock={'shed':private['shed'],'seeds':private['seeds'],**{f'hand:{i}':v for i,v in enumerate(private['inventories'])}}
        result=select_projects(proposals['projects'],workers=proposals['workers'],
            initial_cash=state['farms'][state['player']]['money'],initial_stock=stock,
            required_groups=proposals['required_groups'],required_ids=[p['id'] for p in pending_projects],
            max_subsets=max_subsets,market_scenario=market_scenario)
        attempts.append(dict(hire_count=count,feasible=result['feasible'],search_optimal=result['optimal'],
                             proposals_truncated=proposals['truncated']))
        if not result['feasible']:continue
        # Hiring action forces every already present unit to PASS for one turn.
        idle_cost=action_value*(1+len(obs['farms'][obs['player']]['hands'])) if count else 0
        value=result['net_value']-cost-idle_cost
        if best is not None and value<=best['net_value']:continue
        best=dict(feasible=True,hire_count=count,hire_cost=cost,net_value=value,
            initial_action=initial,replan_after_hire=bool(count),
            selected_projects=[p for p in proposals['projects'] if p['id'] in result['selected_ids']])
        if market_scenario is not None:
            best['selected_projects']=reprice_sales(best['selected_projects'],market_scenario)
    return dict(best or dict(feasible=False),attempts=attempts,optimal=False)
