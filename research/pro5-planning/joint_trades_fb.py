"""Conditional own buys and sells in one shared market inventory timeline.

Triggered only by explicitly tagged joint-trade portfolios. Opponent trades
remain unknown. Successful full quantities are assumptions checked separately
against stock/cash and then revalidated by the executor on observations.
"""
import copy
from market_quote_ci import quote_sale
from town_scenario_ep import consumed_between


def reprice_trades(projects, scenario):
    # Match CK's read-only structural contract: only money/quote/event scalar
    # fields change here. Routes and stock movements need not be cloned for
    # every candidate valuation. Callers must copy before editing structure.
    result = [copy.copy(p) for p in projects]
    for p in result:
        for key in ('cashflows', 'cash_events', 'sale_quotes', 'opportunity_events'):
            p[key] = [dict(row) for row in p.get(key, [])]
    inventory = dict(scenario['inventory'])
    events = []; seen = set(); demand = scenario.get('known_town_demand'); consumed = {}
    for index, p in enumerate(result):
        for step, order, op in p.get('market_actions', []):
            if op[0] not in ('SELL', 'BUY_PRODUCT'): continue
            if (step, order) in seen: raise ValueError('Duplicate trade slot')
            seen.add((step, order)); events.append((step, order, index, op))
    for step, order, index, op in sorted(events):
        p = result[index]; kind, item, quantity = op
        if demand:
            inventory[item] -= consumed_between(demand, item, consumed.get(item, demand['from_step']), step)
            consumed[item] = step
        rows = [r for r in p['cashflows'] if r['day'] == step // 24]
        if len(rows) != 1: raise ValueError('Trade needs one daily cashflow row')
        if kind == 'SELL':
            matches = [q for q in p.get('sale_quotes', []) if (q['step'], q['order'], q['item'], q['quantity']) == (step, order, item, quantity)]
            if len(matches) != 1: raise ValueError('Missing unique sale quote')
            q = matches[0]; quote = quote_sale(scenario['params'][item], inventory[item], quantity)
            delta = quote['receipts'] - q['receipts']; q['receipts'] = quote['receipts']
            rows[0]['receipts'] += delta; p['net_value'] += delta; inventory[item] = quote['inventory']
        else:
            matches = [e for e in p.get('cash_events', []) if (e['step'], e['phase'], e['order']) == (step, 'market', order)]
            if len(matches) != 1: raise ValueError('Missing unique purchase cost')
            cost = 0
            for _ in range(quantity):
                inventory[item] -= 1
                cost += quote_sale(scenario['params'][item], inventory[item], 1)['unit_prices'][0]
            event = matches[0]; delta = cost - event['cost']; event['cost'] = cost
            rows[0]['cost'] += delta; p['net_value'] -= delta
            held = sorted((e for e in p.get('opportunity_events', [])
                           if e.get('resource') == item and tuple(e.get('purchase_ref', ())) == (step, order)), key=lambda e: e['step'])
            if len(held) > quantity: raise ValueError('Purchase overallocated to future consumption')
            resale = quote_sale(scenario['params'][item], inventory[item], quantity)['unit_prices']
            for e, value in zip(held, resale): e['cost'] = value
    for p in result:
        value = sum(e['cost'] for e in p.get('opportunity_events', []) if e.get('available_after', -1) <= p.get('valuation_step', 0))
        p['net_value'] += p.get('resource_opportunity_cost', 0) - value
        p['resource_opportunity_cost'] = value
    return result
