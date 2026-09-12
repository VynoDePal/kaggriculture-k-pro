"""Deterministic, non-intrusive diagnostic replays for K Pro matches."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

from .campaign import _atomic_bytes, _validate_action, source_hashes
from .engine import ROOT, VENDOR, load_engine, load_policy, new_game, offline_policy


DEFAULT_CANDIDATE = 'candidates/k_pro6_care_fp.py'
DEFAULT_OPPONENT = 'k_pro/k_pro6.py'
DEFAULT_SEEDS = (930053, 930132, 930051)
CAMPAIGN_B = ROOT / 'results/measure-care-b'


def snapshot(value):
    """Return a JSON-compatible deep snapshot without retaining live references."""
    return json.loads(json.dumps(copy.deepcopy(value), sort_keys=True))


def _campaign_rows(folder=CAMPAIGN_B):
    folder = Path(folder)
    manifest = json.loads((folder / 'manifest.json').read_text())
    raw = gzip.decompress((folder / 'matches.jsonl.gz').read_bytes())
    actual = hashlib.sha256(raw).hexdigest()
    if actual != manifest.get('results_sha256'):
        raise ValueError('Campaign B decompressed results hash mismatch')
    return manifest, [json.loads(line) for line in raw.splitlines()]


def expected_scores(jobs, folder=CAMPAIGN_B):
    manifest, rows = _campaign_rows(folder)
    wanted = {(j['candidate'], j['opponent'], j['seed'], j['seat']) for j in jobs}
    found = {}
    for row in rows:
        key = (row['candidate'], row['opponent'], row['seed'], row['seat'])
        if key in wanted:
            if key in found:
                raise ValueError('Duplicate campaign B result')
            found[key] = row['scores']
    if set(found) != wanted:
        raise ValueError('Missing campaign B result')
    return manifest, found


def _money(observations):
    # Either player's observation contains both public farm balances.
    return [farm['money'] for farm in observations[0]['farms']]


def _summary(steps, terminal_observations):
    deltas = [[], []]
    for event in steps:
        before, after = _money(event['pre']), _money(event['post'])
        for player in (0, 1):
            deltas[player].append(after[player] - before[player])
    players = []
    for player in (0, 1):
        own = terminal_observations[player]
        players.append({
            'player': player,
            'terminal_money': own['farms'][player]['money'],
            'observed_positive_money_delta': sum(x for x in deltas[player] if x > 0),
            'observed_negative_money_delta': sum(x for x in deltas[player] if x < 0),
            'steps_with_money_change': sum(x != 0 for x in deltas[player]),
            'terminal_shed': own['private']['shed'],
            'terminal_seeds': own['private']['seeds'],
            'terminal_carried_inventories': own['private']['inventories'],
        })
    return {
        'players': players,
        'interpretation': ('Money values are observed net pre/post-step changes. Simultaneous engine '
                           'effects mean they are not evidence that any particular command succeeded.'),
    }


def replay_match(job, expected):
    """Replay one real match, returning a detached trace only if scores agree."""
    engine = load_engine()
    seat = job['seat']
    if seat not in (0, 1):
        raise ValueError('Invalid seat')
    names = [job['opponent'], job['opponent']]
    names[seat] = job['candidate']
    policies = [load_policy(ROOT / name) for name in names]
    state, env = new_game(job['seed'])
    configuration = snapshot(env.configuration)
    steps = []
    for step in range(env.configuration.episodeSteps - 1):
        pre = []
        actions = []
        for player in (0, 1):
            state[player].observation.step = step
            obs = copy.deepcopy(state[player].observation)
            cfg = copy.deepcopy(env.configuration)
            pre.append(snapshot(obs))
            with offline_policy():
                action = policies[player](obs, cfg)
            _validate_action(action, len(state[player].observation.farms[player]['hands']))
            if obs != state[player].observation or cfg != env.configuration:
                raise ValueError(f'Input mutation at step {step}, player {player}')
            state[player].action = action
            actions.append(snapshot(action))
        engine.interpreter(state, env)
        post = [snapshot(s.observation) for s in state]
        steps.append({'type': 'step', 'step': step, 'pre': pre,
                      'actions': actions, 'post': post})
        if all(s.status == 'DONE' for s in state):
            break
    if step != 718 or not all(s.status == 'DONE' for s in state):
        raise ValueError('Unexpected terminal boundary')
    scores = [s.reward for s in state]
    if scores != expected:
        raise ValueError(f'Campaign B score mismatch: expected {expected}, observed {scores}')
    terminal_observations = [snapshot(s.observation) for s in state]
    identity = {
        'type': 'identity',
        'job': snapshot(job),
        'resolved_seed': env.info['seed'],
        'configuration': configuration,
        'source_sha256': source_hashes([[job['candidate'], job['opponent']]]),
        'vendor_provenance_sha256': hashlib.sha256(
            (VENDOR / 'provenance.json').read_bytes()).hexdigest(),
    }
    terminal = {
        'type': 'terminal',
        'scores': scores,
        'statuses': [s.status for s in state],
        'decisions_per_player': step + 1,
        'states': snapshot(state),
        'summary': _summary(steps, terminal_observations),
    }
    return {'identity': identity, 'steps': steps, 'terminal': terminal}


def replay_bytes(replay):
    records = [replay['identity'], *replay['steps'], replay['terminal']]
    raw = ''.join(json.dumps(record, sort_keys=True, separators=(',', ':')) + '\n'
                  for record in records).encode()
    return gzip.compress(raw, compresslevel=9, mtime=0)


def write_replay(path, replay):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_bytes(path, replay_bytes(replay))


def run_replays(output, candidate=DEFAULT_CANDIDATE, opponent=DEFAULT_OPPONENT,
                seeds=DEFAULT_SEEDS, campaign=CAMPAIGN_B):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    jobs = [dict(candidate=candidate, opponent=opponent, seed=seed, seat=seat)
            for seed in seeds for seat in (0, 1)]
    manifest, expected = expected_scores(jobs, campaign)
    summaries = []
    for job in jobs:
        key = (candidate, opponent, job['seed'], job['seat'])
        replay = replay_match(job, expected[key])
        name = f"seed-{job['seed']}-seat-{job['seat']}.jsonl.gz"
        write_replay(output / name, replay)
        summaries.append({'file': name, 'job': job, 'scores': replay['terminal']['scores'],
                          'summary': replay['terminal']['summary']})
    report = {
        'diagnostic_only': True,
        'campaign_b_results_sha256': manifest['results_sha256'],
        'matches': summaries,
    }
    _atomic_bytes(output / 'summary.json', (json.dumps(report, indent=2, sort_keys=True)+'\n').encode())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--candidate', default=DEFAULT_CANDIDATE)
    parser.add_argument('--opponent', default=DEFAULT_OPPONENT)
    parser.add_argument('--campaign-b', default=str(CAMPAIGN_B))
    parser.add_argument('--seed', action='append', type=int, dest='seeds')
    args = parser.parse_args()
    report = run_replays(args.output, args.candidate, args.opponent,
                         tuple(args.seeds) if args.seeds else DEFAULT_SEEDS,
                         Path(args.campaign_b))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
