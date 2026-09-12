"""Evaluation boundaries: wrong loader, termination, mutated inputs, invalid samples."""
import copy
import json
import platform
import shutil
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from evaluation.engine import load_engine, load_policy, new_game
from evaluation import engine as bridge
from evaluation.campaign import run_match, summarize, validate_rows, run_campaign, _validate_action, publish_results, save_checkpoint, load_checkpoints, source_hashes

ROOT = Path(__file__).resolve().parents[1]


class EvaluationTests(unittest.TestCase):
    def test_checkpoints_verify_checksum_identity_and_exclusivity(self):
        job={'candidate':'a','opponent':'b','seed':123,'seat':0}
        row=dict(job,margin=0,scores=[1,1],decisions_per_player=719,max_seconds=[0,0],
                 total_seconds=[0,0],commands=[{'PASS':719},{'PASS':719}],late_care_commands=[0,0],shops=[])
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);(folder/'checkpoints').mkdir()
            save_checkpoint(folder,0,row)
            self.assertEqual(load_checkpoints(folder,[job]),{0:row})
            with self.assertRaises(FileExistsError):save_checkpoint(folder,0,row)
            with self.assertRaises(ValueError):load_checkpoints(folder,[dict(job,seed=124)])
            path=folder/'checkpoints'/'000000.json'
            envelope=json.loads(path.read_text());envelope['row']['scores']=[2,2]
            path.write_text(json.dumps(envelope))
            with self.assertRaisesRegex(ValueError,'checksum'):load_checkpoints(folder,[job])

    def test_resume_finalizes_durable_results_without_replaying_and_checks_sources(self):
        pairs=[['k_pro/k_pro2.py','k_pro/k_pro6.py']];seeds=list(range(200))
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);(folder/'checkpoints').mkdir()
            manifest=dict(status='RUNNING',seeds=seeds,pairs=pairs,source_sha256=source_hashes(pairs),
                python=platform.python_version(),workers=1,expected_matches=400,checkpoint_format=1,
                configuration=json.loads((bridge.VENDOR/'kaggriculture.json').read_text())['configuration'])
            (folder/'manifest.json').write_text(json.dumps(manifest))
            for s in seeds:
                for seat in (0,1):
                    row=dict(candidate=pairs[0][0],opponent=pairs[0][1],seed=s,seat=seat,margin=0,
                        scores=[1,1],decisions_per_player=719,max_seconds=[0,0],total_seconds=[0,0],
                        commands=[{'PASS':719},{'PASS':719}],late_care_commands=[0,0],shops=[])
                    save_checkpoint(folder,s*2+seat,row)
            with self.assertRaisesRegex(ValueError,'identity'):
                run_campaign(pairs,1,folder,workers=1,resume=True)
            with patch('evaluation.campaign.ProcessPoolExecutor',side_effect=AssertionError('replayed')):
                report=run_campaign(pairs,0,folder,workers=1,resume=True)
            self.assertEqual(next(iter(report.values()))['games'],400)
            self.assertEqual(json.loads((folder/'manifest.json').read_text())['status'],'COMPLETE')
            with self.assertRaisesRegex(ValueError,'COMPLETE'):
                run_campaign(pairs,0,folder,workers=1,resume=True)

    def test_result_publication_is_atomic_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            def interrupted():
                yield {'seed':1}
                raise RuntimeError('interrupted serialization')
            with self.assertRaisesRegex(RuntimeError,'interrupted serialization'):
                publish_results(folder,interrupted())
            self.assertFalse((folder/'matches.jsonl').exists())
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            rows=[{'seed':1},{'seed':2}]
            publish_results(folder,rows)
            before=(folder/'matches.jsonl').read_bytes()
            self.assertEqual([json.loads(l) for l in before.splitlines()],rows)
            with self.assertRaises(FileExistsError):publish_results(folder,[{'seed':3}])
            self.assertEqual((folder/'matches.jsonl').read_bytes(),before)

    def test_policy_network_is_blocked_before_connection(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'network.py'
            p.write_text("import socket\ndef agent(obs,cfg):\n socket.socket()\n return {'farmer':['PASS'],'hands':[],'market':[]}\n")
            with self.assertRaisesRegex(RuntimeError,'Offline policy'):
                run_match({'candidate':str(p),'opponent':str(p),'seed':1,'seat':0})

    def test_imported_helpers_do_not_share_policy_state(self):
        import sys
        with tempfile.TemporaryDirectory() as temp:
            helper=Path(temp)/'kpro_test_helper_unique.py'
            helper.write_text('counter=0\n')
            p=Path(temp)/'policy.py'
            p.write_text('import kpro_test_helper_unique as h\ndef agent(obs,cfg):\n h.counter+=1\n return h.counter\n')
            before=dict(sys.modules)
            one,two=load_policy(p),load_policy(p)
            self.assertEqual((one({},{}),one({},{}),two({},{})),(1,2,1))
            self.assertEqual(set(sys.modules),set(before))

    def test_actions_reject_unknown_ops_and_wrong_arguments_but_keep_empty_order_slots(self):
        good={'farmer':['PASS'],'hands':[],'market':[[],['BUY_SEED','WHEAT',1]]}
        _validate_action(good,0)
        for bad in [dict(good,farmer=['FLY']),dict(good,farmer=['PLANT']),
                    dict(good,market=[['BUY_SEED','WHEAT','all']]),
                    dict(good,hands=[['PASS']])]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):_validate_action(bad,0)

    def test_tampered_vendor_is_rejected(self):
        old = bridge.VENDOR
        try:
            with tempfile.TemporaryDirectory() as temp:
                shutil.copytree(old, Path(temp)/'vendor')
                bridge.VENDOR = Path(temp)/'vendor'
                bridge.verify_vendor()
                file = bridge.VENDOR/'kaggriculture.py'
                file.write_bytes(file.read_bytes()+b'\n# tampered\n')
                with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                    bridge.verify_vendor()
        finally:
            bridge.VENDOR = old

    def test_existing_campaign_directory_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp)/'marker'
            marker.write_text('preserved')
            with self.assertRaises(FileExistsError):
                run_campaign([['k_pro/k_pro2.py','k_pro/k_pro6.py']],123,temp,workers=1)
            self.assertEqual(marker.read_text(),'preserved')

    def test_real_loader_selects_bad_historical_helper_and_corrected_entry(self):
        self.assertEqual(load_policy(ROOT/'k_pro/k_pro4.py').__name__, 'project_unit_phase')
        self.assertEqual(load_policy(ROOT/'k_pro/k_pro4_loader_fixed.py').__name__, 'kaggle_agent')

    def test_engine_hides_seed_and_stops_before_last_night(self):
        engine = load_engine()
        state, env = new_game(123)
        self.assertIsNone(env.configuration.seed)
        self.assertEqual(env.info['seed'], 123)
        for step in range(719):
            for player in state:
                player.observation.step = step
                player.action = {'farmer':['PASS'], 'hands':[], 'market':[]}
            engine.interpreter(state, env)
        self.assertEqual([s.status for s in state], ['DONE', 'DONE'])
        self.assertEqual((state[0].observation.day,state[0].observation.hour), (29,23))
        self.assertEqual([s.reward for s in state], [3000.0,3000.0])

    def test_match_rejects_observation_and_configuration_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            clean=Path(temp)/'clean.py'
            clean.write_text("def agent(obs,cfg):\n return {'farmer':['PASS'],'hands':[],'market':[]}\n")
            for statement in ("obs['day']=99", "cfg['seed']=5"):
                bad=Path(temp)/'bad.py'
                bad.write_text("def agent(obs,cfg):\n "+statement+"\n return {'farmer':['PASS'],'hands':[],'market':[]}\n")
                with self.subTest(statement=statement), self.assertRaisesRegex(ValueError, 'mutation'):
                    run_match({'seed':123,'seat':0,'candidate':str(bad),'opponent':str(clean)})

    def test_match_rejects_observation_shaped_action(self):
        with tempfile.TemporaryDirectory() as temp:
            bad=Path(temp)/'bad.py';bad.write_text('def agent(obs,cfg):\n return obs\n')
            with self.assertRaisesRegex(ValueError,'action'):
                run_match({'seed':123,'seat':0,'candidate':str(bad),'opponent':str(bad)})

    def test_duplicate_or_missing_results_never_form_complete_campaign(self):
        jobs=[{'candidate':'a','opponent':'b','seed':s,'seat':i} for s in range(200) for i in (0,1)]
        rows=[dict(j,margin=0,scores=[1,1],decisions_per_player=719,
                   max_seconds=[.1,.1],total_seconds=[1.,1.],commands=[{'PASS':719},{'PASS':719}],
                   late_care_commands=[0,0],shops=[]) for j in jobs]
        validate_rows(rows,jobs)
        with self.assertRaises(ValueError):validate_rows(rows[:-1],jobs)
        with self.assertRaises(ValueError):validate_rows(rows[:-1]+[rows[0]],jobs)
        bad=copy.deepcopy(rows);del bad[0]['commands']
        with self.assertRaises(ValueError):validate_rows(bad,jobs)

    def test_summary_clusters_two_seats_before_estimating_uncertainty(self):
        rows=[]
        for s in range(200):
            for seat,margin in [(0,10),(1,-10)]:
                rows.append({'candidate':'a','opponent':'b','seed':s,'seat':seat,'margin':margin})
        report=summarize(rows)
        self.assertEqual(report['mean_margin'],0)
        self.assertEqual(report['margin_ci95'],[0,0])
        self.assertEqual(report['win_rate'],.5)
        self.assertEqual(report['win_rate_ci95'],[.5,.5])
        self.assertEqual(report['seats']['0']['margin_ci95'],[10,10])
        self.assertEqual(report['seats']['1']['win_rate_ci95'],[0,0])

    def test_summary_refuses_mixed_pairs_and_nonfinite_margins(self):
        rows=[{'candidate':'a','opponent':'b','seed':s,'seat':seat,'margin':1} for s in range(200) for seat in (0,1)]
        bad=copy.deepcopy(rows);bad[0]['opponent']='c'
        with self.assertRaises(ValueError):summarize(bad)
        bad=copy.deepcopy(rows);bad[0]['margin']=float('nan')
        with self.assertRaises(ValueError):summarize(bad)


if __name__=='__main__':unittest.main()
