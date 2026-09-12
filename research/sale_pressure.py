"""Prioritize planned sales by receipts threatened by one equal rival sale.

The pricing functions are a minimal copy of the pinned official Kaggriculture
engine's public market formula. The scenario is a stress calculation, not a
prediction of an opponent's inventory or action.
"""

import math


PRICE_FLOOR = 1
HINGE_GAIN = 8.0
DEFAULT_MARKET_PARAMS = {
    "WHEAT":      {"base": 25, "I0": 10000, "T": 400, "below_func": "sqrt", "below_target": .80, "above_func": "log", "above_target": .20},
    "CARROT":     {"base": 35, "I0": 10000, "T": 450, "below_func": "hinge", "below_target": 1.00, "above_func": "sqrt", "above_target": .70},
    "TOMATO":     {"base": 60, "I0": 10000, "T": 200, "below_func": "hinge", "below_target": .40, "above_func": "sqrt", "above_target": .60},
    "STRAWBERRY": {"base": 120, "I0": 10000, "T": 100, "below_func": "sqrt", "below_target": .70, "above_func": "linear", "above_target": 1.60},
    "MELON":      {"base": 250, "I0": 10000, "T": 300, "below_func": "log", "below_target": .20, "above_func": "sq", "above_target": 3.60},
    "EGG":        {"base": 50, "I0": 10000, "T": 332, "below_func": "hinge", "below_target": .40, "above_func": "log", "above_target": .20},
    "MILK":       {"base": 160, "I0": 10000, "T": 122, "below_func": "sqrt", "below_target": .60, "above_func": "linear", "above_target": 1.60},
    "WOOL":       {"base": 200, "I0": 10000, "T": 105, "below_func": "log", "below_target": .20, "above_func": "sq", "above_target": 3.20},
    "FERTILIZER": {"base": 100, "I0": 10000, "T": 200, "below_func": "linear", "below_target": .40, "above_func": "linear", "above_target": .40},
}


def _shape(kind, x, threshold=None):
    x = max(0.0, x)
    if kind == "linear":
        return x
    if kind == "sq":
        return x * x
    if kind == "sqrt":
        return math.sqrt(x)
    if kind == "log":
        return math.log(1.0 + x)
    if kind == "log10":
        return math.log10(1.0 + x)
    if kind == "hinge":
        if not threshold or threshold <= 0:
            return x
        u = x / threshold
        return u + HINGE_GAIN * max(0.0, u - 1.0) ** 2
    raise ValueError("unsupported market-price shape")


def market_price(item, inventory, params=DEFAULT_MARKET_PARAMS):
    """Return the official integer quote for public *inventory* and *params*."""
    p = params[item]
    base, center, threshold = p["base"], p["I0"], p["T"]
    if inventory < center:
        kind, target, distance = p["below_func"], p["below_target"], center - inventory
        price = base + target * base / _shape(kind, threshold, threshold) * _shape(kind, distance, threshold)
    else:
        kind, target, distance = p["above_func"], p["above_target"], inventory - center
        price = base - target * base / _shape(kind, threshold, threshold) * _shape(kind, distance, threshold)
    return max(PRICE_FLOOR, int(round(price)))


def sale_pressure(item, inventory, quantity, params=DEFAULT_MARKET_PARAMS):
    """Compare receipts now with receipts after an equal successful sale."""
    receipts = []
    for _ in range(2 * quantity):
        price = market_price(item, inventory, params)
        receipts.append(price)
        if price > PRICE_FLOOR:
            inventory += 1
    return sum(receipts[:quantity]) - sum(receipts[quantity:])


def _scored_sales(observation, action):
    market = observation["market"]
    inventory = market["inventory"]
    params = market.get("params", DEFAULT_MARKET_PARAMS)
    scored = []
    for index, order in enumerate(action.get("market", [])):
        if not (isinstance(order, list) and len(order) >= 3 and order[0] == "SELL"):
            continue
        item, quantity = order[1], order[2]
        if type(quantity) is not int or quantity <= 0:
            raise ValueError("unsupported sale quantity")
        current = inventory[item]
        if type(current) not in (int, float) or not math.isfinite(current):
            raise ValueError("unsupported inventory")
        scored.append((index, sale_pressure(item, current, quantity, params), order))
    return scored


def adjust(observation, action):
    """Stable-sort valid SELL orders in place; otherwise return parent action."""
    try:
        scored = _scored_sales(observation, action)
    except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError):
        return action
    if len(scored) <= 1:
        return action
    ordered = sorted(scored, key=lambda row: -row[1])
    if [row[2] for row in ordered] == [row[2] for row in scored]:
        return action
    result = dict(action)
    result["market"] = list(action["market"])
    for destination, source in zip((row[0] for row in scored), ordered):
        result["market"][destination] = source[2]
    return result


def make_agent(parent):
    """Wrap a complete parent decision without sharing additional state."""
    def agent(observation, configuration=None):
        return adjust(observation, parent(observation, configuration))
    return agent
