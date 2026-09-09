"""Bounded deterministic selection over supplied, scored project proposals.

Optimal means optimal for this finite proposal set and its additive values,
NOT optimal play or correct future prices. No infeasible-prefix pruning: a
supplier project may enable another project that cannot run independently.
"""
import itertools
import math
from portfolio_reservations_bp import check_portfolio
from stock_reservations_bq import check_stock_events
from joint_sales_ck import reprice_sales


def select_projects(projects, *, workers, initial_cash, initial_stock,
                    required_ids=(), required_groups=None, shed_capacity=100, max_subsets=10000,market_scenario=None):
    if type(max_subsets) is not int or max_subsets<1:
        raise ValueError('Positive subset budget required')
    ordered=sorted(projects,key=lambda p:p['id'])
    ids=[p['id'] for p in ordered]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate project id')
    required=set(required_ids)
    if not required.issubset(ids):raise ValueError('Unknown required project')
    # Each obligation needs at least one alternative, not every alternative.
    groups=[set(members) for members in (required_groups or {}).values()]
    if any(not group.issubset(ids) for group in groups):
        raise ValueError('Unknown required group alternative')
    if any(not math.isfinite(p['net_value']) for p in ordered):
        raise ValueError('Non-finite project value')
    fixed=[p for p in ordered if p['id'] in required]
    optional=[p for p in ordered if p['id'] not in required]
    upper=sum(p['net_value'] for p in fixed)+sum(max(0,p['net_value']) for p in optional)
    if market_scenario is not None:upper=math.inf
    reserved_plots={p['id']:set(p.get('plots',[p['plot']]))|{p['plot']} for p in ordered}
    def price(chosen):
        # Reject only an already complete, physically conflicting subset.
        # A later supplier can repair cash/stock, but cannot repair two
        # simultaneous project reservations of the same plot.
        occupied=set()
        for p in chosen:
            reserved=reserved_plots[p['id']]
            if occupied.intersection(reserved):return None
            occupied.update(reserved)
        commands=[(step,order) for p in chosen for step,order,_ in p.get('market_actions',[])]
        if len(set(commands))!=len(commands):return None
        if market_scenario is None:return chosen
        slots=[(q['step'],q['order']) for p in chosen for q in p.get('sale_quotes',[])]
        if len(set(slots))!=len(slots):return None
        return reprice_sales(chosen,market_scenario)
    best=None;best_value=None;examined=0;exhausted=False
    # Heuristic warm start for several obligations. This is not an optimality
    # proof: prefix position checks may omit plans enabled by later suppliers.
    # The exhaustive fallback below remains responsible for proofs.
    if len(groups)>1 and max_subsets>1:
        warm_budget=max_subsets//2
        seen=set()
        def cover(chosen):
            nonlocal examined,best,best_value
            key=frozenset(p['id'] for p in chosen)
            if key in seen or examined>=warm_budget:return False
            seen.add(key);examined+=1
            structural=[dict(p,cashflows=[]) for p in chosen]
            if not check_portfolio(structural,workers=workers,initial_cash=0)['feasible']:return False
            missing=[g for g in groups if not g.intersection(key)]
            if not missing:
                chosen=price(chosen)
                if chosen is None:return False
                if not check_portfolio(chosen,workers=workers,initial_cash=initial_cash)['feasible']:return False
                events=[e for p in chosen for e in p['stock_events']]
                if not check_stock_events(events,initial_stock=initial_stock,shed_capacity=shed_capacity)['feasible']:return False
                best=sorted(chosen,key=lambda p:p['id']);best_value=sum(p['net_value'] for p in best)
                return True
            group=min(missing,key=lambda g:(len(g),sorted(g)))
            candidates=[p for p in ordered if p['id'] in group]
            candidates.sort(key=lambda p:(-sum(p['id'] in g for g in missing),-p['net_value'],p['id']))
            for p in candidates:
                if cover(chosen+[p]):return True
            return False
        cover(fixed)
    # Improve a feasible coverage before enumerating small subsets again.
    # Reserve budget for the exhaustive fallback; this is not an optimum proof.
    if best is not None:
        improve_limit=examined+(max_subsets-examined)//2
        candidates=sorted(ordered,key=lambda p:(-p['net_value'],p['id']))
        for candidate in candidates:
            if examined>=improve_limit:break
            if any(p['id']==candidate['id'] for p in best):continue
            examined+=1
            trial=price(sorted(best+[candidate],key=lambda p:p['id']))
            if trial is None:continue
            value=sum(p['net_value'] for p in trial)
            if value<=best_value:continue
            if not check_portfolio(trial,workers=workers,initial_cash=initial_cash)['feasible']:continue
            if not check_stock_events([e for p in trial for e in p['stock_events']],initial_stock=initial_stock,shed_capacity=shed_capacity)['feasible']:continue
            best=trial;best_value=value
    for count in range(len(optional)+1):
        for subset in itertools.combinations(optional,count):
            if examined>=max_subsets:
                exhausted=True;break
            examined+=1
            chosen=sorted(fixed+list(subset),key=lambda p:p['id'])
            chosen_ids={p['id'] for p in chosen}
            if any(not group.intersection(chosen_ids) for group in groups):continue
            chosen=price(chosen)
            if chosen is None:continue
            value=sum(p['net_value'] for p in chosen)
            if best_value is not None and value<=best_value:continue
            physical=check_portfolio(chosen,workers=workers,initial_cash=initial_cash)
            if not physical['feasible']:continue
            events=[e for p in chosen for e in p['stock_events']]
            resources=check_stock_events(events,initial_stock=initial_stock,shed_capacity=shed_capacity)
            if not resources['feasible']:continue
            best=chosen;best_value=value
            if value>=upper:
                return dict(feasible=True,selected_ids=[p['id'] for p in best],net_value=best_value,
                            optimal=True,examined_subsets=examined)
        if exhausted:break
    return dict(feasible=best is not None,selected_ids=None if best is None else [p['id'] for p in best],
                net_value=best_value,optimal=not exhausted,examined_subsets=examined)
