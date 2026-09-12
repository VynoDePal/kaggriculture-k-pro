"""Exact passive accounting over recorded K Pro diagnostic replays."""
import argparse
import copy
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .campaign import _atomic_bytes
from .engine import load_engine, new_game
from .replay import snapshot


def _records(path):
    rows = [json.loads(line) for line in gzip.decompress(Path(path).read_bytes()).splitlines()]
    if not rows or rows[0].get('type') != 'identity' or rows[-1].get('type') != 'terminal':
        raise ValueError('Invalid replay framing')
    return rows[0], rows[1:-1], rows[-1]


def analyze_replay(path):
    """Replay recorded actions and account only successful official-engine commits."""
    identity, steps, terminal = _records(path)
    engine = load_engine()
    state, env = new_game(identity['resolved_seed'])
    events = []
    current_step = None
    originals = (engine._commit_unit, engine._do_hire, engine._do_buy_land)

    def player_for(farm):
        farms = state[0].observation.farms
        return next(i for i, candidate in enumerate(farms) if candidate is farm)

    def commit(op, item, price, farm, private, market, shed_capacity=100):
        ok = originals[0](op, item, price, farm, private, market, shed_capacity)
        if ok:
            events.append({'step': current_step, 'player': player_for(farm),
                           'operation': op, 'item': item, 'money': price if op == 'SELL' else -price})
        return ok

    def atomic(original, operation, farm, *args):
        before = farm['money']
        result = original(farm, *args)
        if farm['money'] != before:
            events.append({'step': current_step, 'player': player_for(farm),
                           'operation': operation, 'item': None,
                           'money': farm['money'] - before})
        return result

    engine._commit_unit = commit
    engine._do_hire = lambda farm, *args: atomic(originals[1], 'HIRE', farm, *args)
    engine._do_buy_land = lambda farm, *args: atomic(originals[2], 'BUY_LAND', farm, *args)
    try:
        for expected_step, record in enumerate(steps):
            if record.get('type') != 'step' or record.get('step') != expected_step:
                raise ValueError(f'Invalid step record at index {expected_step}')
            current_step = expected_step
            for player in (0, 1):
                state[player].observation.step = expected_step
                if snapshot(state[player].observation) != record['pre'][player]:
                    raise ValueError(f'prestate mismatch at step {expected_step}, player {player}')
                state[player].action = copy.deepcopy(record['actions'][player])
            engine.interpreter(state, env)
            actual = [snapshot(s.observation) for s in state]
            if actual != record['post']:
                raise ValueError(f'poststate mismatch at step {expected_step}')
    finally:
        engine._commit_unit, engine._do_hire, engine._do_buy_land = originals

    scores = [s.reward for s in state]
    if scores != terminal['scores']:
        raise ValueError(f'terminal score mismatch: expected {terminal["scores"]}, observed {scores}')

    grouped = defaultdict(list)
    totals = defaultdict(lambda: {'units': 0, 'money': 0})
    for event in events:
        key = (event['step'], event['player'], event['operation'], event['item'])
        grouped[key].append(event['money'])
        total_key = (event['player'], event['operation'], event['item'])
        totals[total_key]['units'] += 1
        totals[total_key]['money'] += event['money']

    all_localized = []
    for (step, player, operation, item), money in sorted(grouped.items()):
        all_localized.append({'step': step, 'player': player, 'operation': operation, 'item': item,
                              'units': len(money), 'money': sum(money),
                              'first_unit_price': abs(money[0]),
                              'last_unit_price': abs(money[-1])})
    paired = defaultdict(lambda: [0, 0])
    for row in all_localized:
        paired[(row['step'], row['operation'], row['item'])][row['player']] = row['money']
    notable = set(key for key, _ in sorted(
        paired.items(), key=lambda pair: abs(pair[1][0] - pair[1][1]), reverse=True)[:24])
    localized = [row for row in all_localized
                 if (row['step'], row['operation'], row['item']) in notable]
    transaction_totals = [dict(player=p, operation=op, item=item, **values)
                          for (p, op, item), values in sorted(
                              totals.items(), key=lambda pair: tuple(str(x) for x in pair[0]))]
    divergence = next((record for record in steps
                       if record['actions'][0] != record['actions'][1]), None)
    terminal_stock = []
    for player in (0, 1):
        obs = state[player].observation
        private = obs.private
        terminal_stock.append({
            'shed_goods': sum(private['shed'].values()),
            'carried_goods': sum(sum(inv.values()) for inv in private['inventories']),
            'tile_yield_units': sum(tile.get('yield_units', 0)
                                    for row in obs.farms[player]['tiles'] for tile in row
                                    if isinstance(tile, dict)),
            'seeds': sum(private['seeds'].values()),
        })
    initial_money = [steps[0]['pre'][0]['farms'][p]['money'] for p in (0, 1)]
    realized_net = [sum(event['money'] for event in events if event['player'] == p)
                    for p in (0, 1)]
    reconciliation = [{'player': p, 'initial_money': initial_money[p],
                       'realized_net_commits': realized_net[p], 'terminal_money': scores[p],
                       'difference': scores[p] - initial_money[p] - realized_net[p]}
                      for p in (0, 1)]
    return {
        'file': Path(path).name,
        'trace_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        'job': identity['job'],
        'scores': scores,
        'verified_poststates': len(steps) * 2,
        'first_action_divergence': ({'step': divergence['step'],
                                     'day': divergence['pre'][0]['day'],
                                     'hour': divergence['pre'][0]['hour']}
                                    if divergence else None),
        'terminal_stock': terminal_stock,
        'cash_reconciliation': reconciliation,
        'transaction_totals': transaction_totals,
        'localized_transactions': localized,
        'accounting_note': ('Money records successful official-engine commits only; positive sales '
                            'and negative purchases/hire/land are realized flows.'),
    }


def analyze_order_swap(path, player, step, slots):
    """Isolate one recorded market-slot swap without continuing the policy."""
    _, steps, _ = _records(path)
    if player not in (0, 1) or step < 0 or step >= len(steps):
        raise ValueError('Invalid player or step')
    left, right = slots
    target_record = steps[step]
    recorded_market = target_record['actions'][player]['market']
    if any(type(slot) is not int or not 0 <= slot < len(recorded_market)
           for slot in (left, right)):
        raise ValueError('Swap slot outside recorded market orders')
    engine = load_engine()
    identity, _, _ = _records(path)
    state, env = new_game(identity['resolved_seed'])
    for index in range(step):
        record = steps[index]
        for seat in (0, 1):
            state[seat].observation.step = index
            if snapshot(state[seat].observation) != record['pre'][seat]:
                raise ValueError(f'prestate mismatch at step {index}, player {seat}')
            state[seat].action = copy.deepcopy(record['actions'][seat])
        engine.interpreter(state, env)
        if [snapshot(s.observation) for s in state] != record['post']:
            raise ValueError(f'poststate mismatch at step {index}')

    original_state, original_env = copy.deepcopy(state), copy.deepcopy(env)
    swapped_state, swapped_env = copy.deepcopy(state), copy.deepcopy(env)
    for seat in (0, 1):
        original_state[seat].observation.step = step
        swapped_state[seat].observation.step = step
        original_state[seat].action = copy.deepcopy(target_record['actions'][seat])
        swapped_state[seat].action = copy.deepcopy(target_record['actions'][seat])
    market = swapped_state[player].action['market']
    market[left], market[right] = market[right], market[left]
    engine.interpreter(original_state, original_env)
    if [snapshot(s.observation) for s in original_state] != target_record['post']:
        raise ValueError(f'original poststate mismatch at step {step}')
    engine.interpreter(swapped_state, swapped_env)

    original_money = [original_state[0].observation.farms[p]['money'] for p in (0, 1)]
    swapped_money = [swapped_state[0].observation.farms[p]['money'] for p in (0, 1)]
    def farms_without_money(branch):
        farms = copy.deepcopy(branch[0].observation.farms)
        for farm in farms:
            farm.pop('money')
        return farms
    return {
        'file': Path(path).name, 'step': step, 'player': player, 'slots': list(slots),
        'original_market': target_record['actions'][player]['market'],
        'swapped_market': swapped_state[player].action['market'],
        'original_money': original_money, 'swapped_money': swapped_money,
        'money_effect': [after - before for after, before in zip(swapped_money, original_money)],
        'relative_margin_effect': ((swapped_money[player] - swapped_money[1-player])
                                   - (original_money[player] - original_money[1-player])),
        'same_farms_except_money': (farms_without_money(original_state)
                                    == farms_without_money(swapped_state)),
        'same_private_sheds': all(original_state[p].observation.private['shed']
                                  == swapped_state[p].observation.private['shed']
                                  for p in (0, 1)),
        'scope_note': ('One official-engine step with recorded actions; this isolates execution '
                       'timing but is not a full-game policy or performance result.'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('replays', nargs='+')
    parser.add_argument('--output', required=True)
    parser.add_argument('--swap-replay')
    parser.add_argument('--swap-player', type=int, default=0)
    parser.add_argument('--swap-step', type=int)
    parser.add_argument('--swap-slots', nargs=2, type=int)
    args = parser.parse_args()
    report = {'diagnostic_only': True,
              'matches': [analyze_replay(path) for path in sorted(args.replays)]}
    if args.swap_replay:
        if args.swap_step is None or args.swap_slots is None:
            parser.error('--swap-replay requires --swap-step and --swap-slots')
        report['isolated_order_swap'] = analyze_order_swap(
            args.swap_replay, args.swap_player, args.swap_step, tuple(args.swap_slots))
    _atomic_bytes(Path(args.output),
                  (json.dumps(report, indent=2, sort_keys=True) + '\n').encode())
    print(json.dumps({'output': args.output, 'matches': len(report['matches'])}, sort_keys=True))


if __name__ == '__main__':
    main()
