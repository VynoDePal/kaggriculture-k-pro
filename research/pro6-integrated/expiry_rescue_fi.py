"""Experimental local expiry rescue derived from a recorded K Pro 4 loss.

No opponent, seed or replay identifier enters the policy. This is not a
standalone submission and does not change the frozen submitted source.
"""


def rescue(obs, action, *, project):
    """Use an idle, already-present worker after planned local service.

Only the last action before an ordinary night is considered. The plant must
already be at its decay deadline for the next day. Reserve the entire carried
stock and all proposed purchases before accepting a harvest; do not rely on a
sale, free storage, or a final night after the game. The injected projection
implements the standard K Pro 24-turn/100-capacity own-unit phase.
"""
    day = obs['day']
    if day >= 29 or obs['hour'] != 23:
        return action
    commands = [action.get('farmer', ['PASS']), *action.get('hands', [])]
    farm = obs['farms'][obs['player']]
    positions = [farm['farmer'], *farm['hands']]
    next_step = (day + 1) * 24
    candidates = []
    for uid, command in enumerate(commands[:len(positions)]):
        if command != ['PASS']:
            continue
        x, y = positions[uid]
        tile = farm['tiles'][y][x]
        if (not isinstance(tile, dict) or 'crop' not in tile
                or not 0 <= tile.get('max_lifespan_step', -1) <= next_step):
            continue
        # Earlier service can be followed by harvest. Later service cannot:
        # it would act on the cleared tile and invalidate the existing plan.
        if any(positions[j] == positions[uid] and commands[j][0] not in
               ('PASS', 'NORTH', 'SOUTH', 'EAST', 'WEST')
               for j in range(uid + 1, min(len(commands), len(positions)))):
            continue
        candidates.append(uid)
    if not candidates:
        return action
    purchases = sum(max(0, int(order[2] if len(order) >= 3 else 1)) for order in action.get('market', [])
                    if isinstance(order, list) and len(order) >= 2
                    and order[0] in ('BUY_PRODUCT', 'BUY_ANIMAL'))
    result = dict(action)
    commands = [list(command) for command in commands]
    for uid in candidates:
        baseline = project(obs, commands)
        trial_commands = [list(command) for command in commands]
        trial_commands[uid] = ['HARVEST']
        trial = project(obs, trial_commands)
        old = baseline['private']['inventories'][uid]
        new = trial['private']['inventories'][uid]
        if sum(new.values()) <= sum(old.values()):
            continue  # Already harvested, not mature, or otherwise no effect.
        private = trial['private']
        total = sum(private['shed'].values()) + sum(sum(inv.values()) for inv in private['inventories'])
        if total + purchases > 100:
            continue
        commands = trial_commands
    result['farmer'], result['hands'] = commands[0], commands[1:]
    return result


def make_agent(reference):
    """Wrap a freshly loaded reference; leave its source and helpers intact."""
    def agent(observation, configuration=None):
        action = reference.agent(observation, configuration)
        if configuration is not None and (
                configuration.get('turnsPerDay', 24) != 24
                or configuration.get('shedCapacity', 100) != 100
                or configuration.get('episodeSteps', 720) != 720):
            return action
        return rescue(observation, action, project=reference.project_unit_phase)
    return agent
