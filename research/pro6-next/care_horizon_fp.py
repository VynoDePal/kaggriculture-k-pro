"""Exclude care bonuses that cannot be consumed before the standard game ends.

Official animal refresh consumes the old bonus before banking today's care.
Today's care cannot affect the dawn at day+1. Keep the original feeding,
harvesting, fertilizer collection, prices and fasting decisions unchanged.
Research adapter for frozen K Pro 6, not a new submission.
"""

def next_care_yield(tile, day, animals):
    first=tile['placed_day']+animals[tile['animal']][1]
    interval=animals[tile['animal']][2]
    earliest=day+2
    offset=max(0, (earliest-first+interval-1)//interval)
    return first+offset*interval

def install(reference):
    original=reference.animal_tasks

    def animal_tasks(tile,day,prices,town,care_quotes=None):
        commands,value=original(tile,day,prices,town,care_quotes)
        if any(action==['CARE'] for action in commands):
            if next_care_yield(tile,day,reference.ANIMAL)>29:
                commands=[action for action in commands if action!=['CARE']]
        return commands,value

    reference.animal_tasks=animal_tasks
    return reference.agent
