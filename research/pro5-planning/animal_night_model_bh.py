"""Public-state one-night animal counterfactual, not a feeding policy.

Callers must establish action feasibility and price future service separately.
No sale, harvest, care opportunity or following-day feeding is assumed here.
"""

ANIMAL_CYCLE = {'SHEEP': (6, 3, 6), 'COW': (8, 2, 6), 'GOOSE': (4, 1, 4)}


def animal_after_night(tile, day, *, feed=False, care=False):
    """Outcome if feasible additional feed/care actions precede this night.

    Existing flags are preserved. Day29 has no terminal night. Returns a new
    tile, allowing direct comparison of feed/no-feed without input mutation.
    """
    result = dict(tile)
    if day >= 29:
        return result
    fed = bool(tile.get('fed_today') or feed)
    cared = bool(tile.get('cared_today') or care)
    missed = 0 if fed else tile.get('consecutive_unfed', 0) + 1
    if missed >= 2:
        return {'kind': tile['kind']}
    first, interval, cap = ANIMAL_CYCLE[tile['animal']]
    elapsed = day + 1 - tile['placed_day'] - first
    production = elapsed >= 0 and elapsed % interval == 0
    bonus = tile.get('pending_care_bonus', 0)
    if production:
        result['yield_units'] = min(cap, tile.get('yield_units', 0) + 1 + (bonus if fed else 0))
        bonus = 0
    if fed and cared:
        bonus += 1
    result.update(consecutive_unfed=missed, pending_care_bonus=bonus,
                  fertilizer_available=True, fed_today=False, cared_today=False)
    return result
