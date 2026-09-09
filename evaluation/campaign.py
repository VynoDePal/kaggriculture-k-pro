"""Immutable campaigns: exactly 200 seeds and both seats for every policy pair."""
import argparse
import copy
import hashlib
import json
import math
import platform
import statistics
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from .engine import ROOT, VENDOR, load_engine, load_policy, new_game, verify_vendor, offline_policy

SEED_COUNT = 200
# Student t(.975,199), since campaigns always cluster 200 paired seed results.
T_CRITICAL_199 = 1.971956544


def result_key(row):
    return row['candidate'], row['opponent'], row['seed'], row['seat']


def _validate_action(action, hand_count):
    if not isinstance(action, dict) or set(action) != {'farmer', 'hands', 'market'}:
        raise ValueError('Invalid action fields')
    if not all(isinstance(action[k], list) for k in ('farmer', 'hands', 'market')):
        raise ValueError('Invalid action containers')
    if not all(isinstance(a, list) and a and isinstance(a[0], str)
               for a in [action['farmer'], *action['hands']]):
        raise ValueError('Invalid unit action')
    if not all(isinstance(order, list) for order in action['market']):
        raise ValueError('Invalid market action')
    if len(action['hands']) > hand_count or len(action['market']) > 10:
        raise ValueError('Invalid action count')
    engine = load_engine()
    goods = set(engine.PRODUCTS) | set(engine.ANIMALS)
    simple = {'NORTH','SOUTH','EAST','WEST','PASS','DROP','WATER','HARVEST',
              'FERTILIZE','BUILD_COOP','BUILD_PASTURE','DIG','FEED','COLLECT_FERTILIZER','CARE'}
    for command in [action['farmer'], *action['hands']]:
        op = command[0]
        valid = op in simple and len(command) == 1
        if op == 'PLANT':
            valid = len(command) == 2 and isinstance(command[1],str) and command[1] in engine.CROPS
        if op in ('PICKUP','PLACE'):
            valid = (len(command) in (2,3) and isinstance(command[1],str) and command[1] in goods
                     and (len(command) == 2 or type(command[2]) is int and command[2] > 0))
        if not valid:
            raise ValueError('Invalid unit action arguments')
    allowed = {'SELL':set(engine.PRODUCTS),'BUY_PRODUCT':{'WHEAT','FERTILIZER'},
               'BUY_ANIMAL':set(engine.ANIMALS),'BUY_SEED':set(engine.CROPS)}
    for order in action['market']:
        if not order:
            continue  # FL/FM deliberately preserve ignored simultaneous-order slots.
        op = order[0]
        if not isinstance(op,str):
            raise ValueError('Invalid market action operation')
        valid = op in ('HIRE','BUY_LAND') and len(order) == 1
        if op in allowed:
            valid = (len(order) == 3 and isinstance(order[1],str) and order[1] in allowed[op]
                     and type(order[2]) is int and order[2] > 0)
        if not valid:
            raise ValueError('Invalid market action arguments')


def _late_care(engine, obs, action):
    farm = obs['farms'][obs['player']]
    positions = [farm['farmer'], *farm['hands']]
    count = 0
    for pos, command in zip(positions, [action['farmer'], *action['hands']]):
        if command != ['CARE']:
            continue
        tile = farm['tiles'][pos[1]][pos[0]]
        if not isinstance(tile, dict) or not tile.get('animal'):
            continue
        data = engine.ANIMALS[tile['animal']]
        first = tile['placed_day'] + data['first_yield_day']
        interval = data['interval']
        # Diagnostic classification of issued commands, not realized lost money.
        next_yield = first + max(0, math.ceil((obs['day'] + 2 - first) / interval)) * interval
        count += next_yield > 29
    return count


def run_match(job):
    engine = load_engine()
    seat = job['seat']
    if seat not in (0, 1):
        raise ValueError('Invalid seat')
    names = [job['opponent'], job['opponent']]
    names[seat] = job['candidate']
    policies = [load_policy(ROOT / name) for name in names]
    state, env = new_game(job['seed'])
    maximum = [0.0, 0.0]
    total = [0.0, 0.0]
    commands = [Counter(), Counter()]
    late_care = [0, 0]
    for step in range(env.configuration.episodeSteps - 1):
        for player in range(2):
            state[player].observation.step = step
            obs = copy.deepcopy(state[player].observation)
            cfg = copy.deepcopy(env.configuration)
            start = time.perf_counter()
            with offline_policy():
                action = policies[player](obs, cfg)
            elapsed = time.perf_counter() - start
            maximum[player] = max(maximum[player], elapsed)
            total[player] += elapsed
            _validate_action(action, len(state[player].observation.farms[player]['hands']))
            if obs != state[player].observation or cfg != env.configuration:
                raise ValueError(f'Input mutation at step {step}, player {player}')
            state[player].action = action
            commands[player].update(a[0] for a in [action['farmer'], *action['hands']])
            late_care[player] += _late_care(engine, obs, action)
        engine.interpreter(state, env)
        if all(s.status == 'DONE' for s in state):
            break
    if step != 718 or not all(s.status == 'DONE' for s in state):
        raise ValueError('Unexpected terminal boundary')
    scores = [s.reward for s in state]
    return dict(job, scores=scores, margin=scores[seat] - scores[1-seat],
                decisions_per_player=step + 1, max_seconds=maximum, total_seconds=total,
                commands=commands, late_care_commands=late_care,
                shops=state[0].observation.town['unlocked_shops'])


def validate_rows(rows, jobs):
    required = {'candidate','opponent','seed','seat','scores','margin','decisions_per_player',
                'max_seconds','total_seconds','commands','late_care_commands','shops'}
    for row in rows:
        if not isinstance(row,dict) or set(row) != required:
            raise ValueError('Invalid result fields')
        if type(row['seed']) is not int or type(row['seat']) is not int or row['seat'] not in (0,1):
            raise ValueError('Invalid result seed or seat')
        if not all(isinstance(row[k],str) for k in ('candidate','opponent')) or row['decisions_per_player'] != 719:
            raise ValueError('Invalid result identity or terminal count')
        for field in ('scores','max_seconds','total_seconds'):
            values=row[field]
            if (not isinstance(values,list) or len(values)!=2
                    or any(type(v) not in (int,float) or not math.isfinite(v) or v < 0 for v in values)):
                raise ValueError('Invalid result numeric telemetry')
        if any(t < m for t,m in zip(row['total_seconds'],row['max_seconds'])):
            raise ValueError('Inconsistent timing telemetry')
        counts=row['commands']
        if (not isinstance(counts,list) or len(counts)!=2
                or any(not isinstance(c,dict)
                       or any(not isinstance(k,str) or type(v) is not int or v<0 for k,v in c.items())
                       or sum(c.values()) < 719 for c in counts)):
            raise ValueError('Invalid command telemetry')
        if (not isinstance(row['late_care_commands'],list) or len(row['late_care_commands'])!=2
                or any(type(v) is not int or v<0 for v in row['late_care_commands'])):
            raise ValueError('Invalid care telemetry')
        if (not isinstance(row['shops'],list) or len(row['shops'])>8
                or any(not isinstance(s,str) or s not in load_engine().SHOPS for s in row['shops'])):
            raise ValueError('Invalid public context')
    expected = {result_key(job) for job in jobs}
    actual = [result_key(row) for row in rows]
    if len(expected) != len(jobs) or len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError('Missing, duplicate or unexpected match results')
    for row in rows:
        scores = row['scores']
        if len(scores) != 2 or not all(math.isfinite(s) for s in scores):
            raise ValueError('Invalid scores')
        if type(row['margin']) not in (int,float) or not math.isfinite(row['margin']) or row['margin'] != scores[row['seat']] - scores[1-row['seat']]:
            raise ValueError('Invalid margin')


def _interval(values):
    mean = statistics.mean(values)
    half = T_CRITICAL_199 * statistics.stdev(values) / math.sqrt(SEED_COUNT)
    return [mean - half, mean + half]


def summarize(rows):
    if len({(r['candidate'], r['opponent']) for r in rows}) != 1:
        raise ValueError('One policy pair required')
    grouped = defaultdict(dict)
    for row in rows:
        if row['seat'] not in (0, 1) or row['seat'] in grouped[row['seed']] or not math.isfinite(row['margin']):
            raise ValueError('Invalid paired result')
        grouped[row['seed']][row['seat']] = row
    if len(grouped) != SEED_COUNT or any(set(v) != {0, 1} for v in grouped.values()):
        raise ValueError('Exactly 200 complete paired seeds required')
    margins = [statistics.mean(r['margin'] for r in v.values()) for v in grouped.values()]
    wins = [statistics.mean(1 if r['margin'] > 0 else .5 if r['margin'] == 0 else 0 for r in v.values())
            for v in grouped.values()]
    return dict(seeds=SEED_COUNT, games=len(rows), wins=sum(r['margin'] > 0 for r in rows),
                losses=sum(r['margin'] < 0 for r in rows), ties=sum(r['margin'] == 0 for r in rows),
                mean_margin=statistics.mean(margins), margin_ci95=_interval(margins),
                win_rate=statistics.mean(wins), win_rate_ci95=_interval(wins),
                seats={str(s): dict(wins=sum(r['margin'] > 0 for r in rows if r['seat'] == s),
                                   mean_margin=statistics.mean(r['margin'] for r in rows if r['seat'] == s),
                                   margin_ci95=_interval([r['margin'] for r in rows if r['seat']==s]),
                                   win_rate_ci95=_interval([1 if r['margin']>0 else .5 if r['margin']==0 else 0
                                                          for r in rows if r['seat']==s])) for s in (0, 1)},
                ci_method='Student t199 on 200 seed clusters; one opponent per summary')


def source_hashes(pairs):
    files = {name for pair in pairs for name in pair}
    files.update(str(p.relative_to(ROOT)) for p in (ROOT/'evaluation').glob('*.py'))
    files.update(str(p.relative_to(ROOT)) for p in VENDOR.iterdir() if p.is_file())
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(files)}


def run_campaign(pairs, start_seed, output, workers=8):
    if not pairs or len({tuple(p) for p in pairs}) != len(pairs) or any(a == b for a, b in pairs):
        raise ValueError('Unique non-self pairs required')
    if type(start_seed) is not int or not 1 <= workers <= 8:
        raise ValueError('Invalid seed or worker count')
    verify_vendor()
    seeds = list(range(start_seed, start_seed + SEED_COUNT))
    jobs = [dict(candidate=a, opponent=b, seed=seed, seat=seat)
            for a, b in pairs for seed in seeds for seat in (0, 1)]
    output = Path(output)
    hashes = source_hashes(pairs)
    output.mkdir(parents=True, exist_ok=False)
    manifest = dict(status='RUNNING', seeds=seeds, pairs=pairs, source_sha256=hashes,
                    python=platform.python_version(), workers=workers, expected_matches=len(jobs),
                    configuration=json.loads((VENDOR/'kaggriculture.json').read_text())['configuration'],
                    limitation='Official interpreter and loader, local orchestration without Kaggle sandbox/time enforcement')
    def save_manifest():
        temp=output/'manifest.tmp'
        temp.write_text(json.dumps(manifest, indent=2)+'\n')
        temp.replace(output/'manifest.json')
    save_manifest()
    rows=[]
    try:
        with ProcessPoolExecutor(max_workers=workers, max_tasks_per_child=1) as pool, (output/'matches.jsonl').open('x') as stream:
            for row in pool.map(run_match, jobs):
                stream.write(json.dumps(row, sort_keys=True)+'\n');stream.flush()
                rows.append(row)
                if len(rows)%100 == 0:
                    print(f'{len(rows)}/{len(jobs)} matches complete', flush=True)
        validate_rows(rows, jobs)
        persisted = [json.loads(line) for line in (output/'matches.jsonl').read_text().splitlines()]
        validate_rows(persisted, jobs)
        if persisted != rows:
            raise ValueError('Persisted results differ from computed results')
        if source_hashes(pairs) != hashes:
            raise ValueError('Sources changed during campaign')
        summary = {a+' vs '+b: summarize([r for r in rows if (r['candidate'],r['opponent'])==(a,b)]) for a,b in pairs}
        (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        manifest.update(status='COMPLETE',completed_matches=len(rows),
                        results_sha256=hashlib.sha256((output/'matches.jsonl').read_bytes()).hexdigest(),
                        summary_sha256=hashlib.sha256((output/'summary.json').read_bytes()).hexdigest())
    except BaseException as error:
        manifest.update(status='FAILED',completed_matches=len(rows),error=type(error).__name__+': '+str(error))
        save_manifest()
        raise
    save_manifest()
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pair',action='append',nargs=2,required=True,metavar=('CANDIDATE','OPPONENT'))
    parser.add_argument('--seed-start',type=int,required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--workers',type=int,default=8)
    args=parser.parse_args()
    run_campaign(args.pair,args.seed_start,args.output,args.workers)


if __name__=='__main__':main()
