"""Bounded public-state economic guards; these are heuristics, not ROI promises."""
import math


def wheat_acreage_target(day, herd, feed_per_day=None, wheat_stock=0,
                         renewal_days=4, yield_per_plot=5):
    """Return desired total wheat plots, including currently planted wheat.

    One feed consumes one wheat. Cover demand across a four-day harvest/renewal
    cycle at the policy's five-unit harvest threshold, less accessible stock.
    ``feed_per_day`` can reflect actual planned feeding; omitted means one per
    target animal. Stock means own shed plus hands, never market inventory.
    Keep K Pro 3's seven-plot floor and baseline, allowing at most three extra
    plots and 24 total. This limited adjustment cannot guarantee self-sufficiency.
    """
    if day > 25:
        return 0
    herd = max(0, herd)
    baseline = min(24, max(7, math.ceil(0.65 * herd)))
    daily_feed = herd if feed_per_day is None else max(0, feed_per_day)
    cycle_demand = daily_feed * max(1, renewal_days)
    shortage = max(0, cycle_demand - max(0, wheat_stock))
    renewal_plots = math.ceil(shortage / max(1, yield_per_plot))
    return min(24, baseline + 3, max(baseline, renewal_plots))


def late_melon_plant_count(day, forecast_price, money, reserve, *,
                          seed_cost=80, labor_cost=120, available_actions=0,
                          actions_per_plot=16, maximum=4):
    """Return an upper bound on NEW melon plots; never removes existing plants.

    Caller supplies the public forecast at first harvest (ten days ahead), not
    today's quote, and spare worker actions over that growing period after
    existing commitments. Reserve includes feed/hiring and other commitments.
    Require a day for sale after first harvest and restrict the late wave to
    days 11..18. Value four units at 80% of the forecast and require revenue to
    exceed seed plus labor opportunity cost by 25%. Cash covers both costs;
    this intentionally conservative budget is not an estimated realized profit.
    """
    if day < 11 or day + 10 + 1 > 29:
        return 0
    cost = max(0, seed_cost) + max(0, labor_cost)
    conservative_revenue = 4 * 0.8 * max(0, forecast_price)
    if cost <= 0 or conservative_revenue <= cost * 1.25:
        return 0
    cash_plots = int(max(0, money - max(0, reserve)) // cost)
    labor_plots = int(max(0, available_actions) // max(1, actions_per_plot))
    return max(0, min(4, int(maximum), cash_plots, labor_plots))


def fourth_quadrant_eligible(day, quadrants, money, reserve, land_cost,
                             occupied_diamond, diamond_capacity, *,
                             expansion_budget=1000):
    """Permit considering the fourth quadrant, never blindly force its purchase.

    Count productive crop/animal tiles within radius six on currently unlocked
    land against all usable radius-six tiles there (exclude shed and locked
    tiles). Require 85% saturation, fourteen days left, and cash for land plus
    current operating reserve plus an additional planting/worker allowance.
    This checks resource feasibility; it is not proof expansion will pay back.
    """
    if quadrants != 3 or 29 - day < 14 or diamond_capacity <= 0:
        return False
    if max(0, occupied_diamond) < 0.85 * diamond_capacity:
        return False
    budget = max(0, land_cost) + max(0, reserve) + max(0, expansion_budget)
    return money >= budget
