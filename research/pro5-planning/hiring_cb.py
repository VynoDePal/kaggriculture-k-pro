"""Funded one-turn hiring scenario with explicit PASS for existing workers.

Returned observation is a planning projection of workforce/cash only. It is not
a full predicted next observation: market, decay and opponent changes must be
read again before executing any subsequent plan. No crossing of night/end.
"""
import copy
from crop_route_model_bo import SHED


def hire_scenario(obs, *, count, reserve_cash=0, available_orders=10, cost_multiplier=1):
    if type(count) is not int or count<1:raise ValueError('Positive hire count required')
    if reserve_cash<0 or cost_multiplier<0:raise ValueError('Negative cost or reserve')
    if count>available_orders or count>10:return dict(feasible=False,reason='market_slots')
    if obs['hour']>=23 or obs['step']>=718:return dict(feasible=False,reason='no_next_service_turn')
    farm=obs['farms'][obs['player']]
    a,b=1,1
    for _ in range(farm['hires_today']):a,b=b,a+b
    cost=0
    for _ in range(count):cost+=cost_multiplier*a;a,b=b,a+b
    if cost+reserve_cash>farm['money']:return dict(feasible=False,reason='insufficient_cash',cost=cost)
    projected=copy.deepcopy(obs);f=projected['farms'][obs['player']]
    for _ in range(count):
        positions=[tuple(f['farmer'])]+[tuple(p) for p in f['hands']]
        spawn=min(SHED,key=lambda p:(positions.count(p),SHED.index(p)))
        f['hands'].append(list(spawn));projected['private']['inventories'].append({})
    f['money']-=cost;f['hires_today']+=count
    projected['step']+=1;projected['hour']+=1
    action=dict(farmer=['PASS'],hands=[['PASS'] for _ in farm['hands']],market=[['HIRE'] for _ in range(count)])
    return dict(feasible=True,cost=cost,observation=projected,action=action)
