import copy
import gzip
import json
import tempfile
import unittest
from pathlib import Path

from evaluation.campaign import run_match
from evaluation.engine import new_game
from evaluation.replay import replay_match, snapshot, write_replay


ROOT = Path(__file__).resolve().parents[1]
JOB = {
    'candidate': 'candidates/k_pro6_care_fp.py',
    'opponent': 'k_pro/k_pro6.py',
    'seed': 930053,
    'seat': 0,
}


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = run_match(JOB)
        cls.replay = replay_match(JOB, cls.expected['scores'])

    def test_real_replay_is_faithful_to_run_match(self):
        self.assertEqual(self.replay['terminal']['scores'], self.expected['scores'])
        self.assertEqual(self.replay['terminal']['decisions_per_player'],
                         self.expected['decisions_per_player'])
        self.assertEqual(len(self.replay['steps']), 719)
        self.assertEqual(self.replay['steps'][0]['pre'][0]['step'], 0)
        self.assertEqual(self.replay['steps'][-1]['post'][0]['step'], 718)

    def test_snapshot_is_detached_and_does_not_mutate_engine_state(self):
        state, env = new_game(930053)
        before = copy.deepcopy(state)
        captured = snapshot(state)
        captured[0]['observation']['day'] = -1
        self.assertEqual(state, before)
        self.assertNotEqual(captured[0]['observation'], state[0].observation)
        self.assertEqual(env.info['seed'], 930053)

    def test_trace_publication_is_compressed_atomic_and_exclusive(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'match.jsonl.gz'
            write_replay(path, self.replay)
            before = path.read_bytes()
            lines = gzip.decompress(before).splitlines()
            self.assertEqual(json.loads(lines[0])['type'], 'identity')
            self.assertEqual(json.loads(lines[-1])['type'], 'terminal')
            with self.assertRaises(FileExistsError):
                write_replay(path, self.replay)
            self.assertEqual(path.read_bytes(), before)

    def test_expected_score_mismatch_is_rejected_before_publication(self):
        with self.assertRaisesRegex(ValueError, 'score mismatch'):
            replay_match(JOB, [0, 0])


if __name__ == '__main__':
    unittest.main()
