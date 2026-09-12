import copy
import gzip
import json
import tempfile
import unittest
from pathlib import Path

from evaluation.diagnose import analyze_order_swap, analyze_replay


ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / 'results/diagnose-care-c/seed-930053-seat-0.jsonl.gz'


class DiagnoseTests(unittest.TestCase):
    def test_successful_commits_give_exact_step_672_strawberry_revenue(self):
        analysis = analyze_replay(TRACE)
        strawberry = [
            row for row in analysis['localized_transactions']
            if row['step'] == 672 and row['operation'] == 'SELL'
            and row['item'] == 'STRAWBERRY'
        ]
        self.assertEqual(strawberry, [
            {'step': 672, 'player': 0, 'operation': 'SELL', 'item': 'STRAWBERRY',
             'units': 29, 'money': 178, 'first_unit_price': 24, 'last_unit_price': 1},
            {'step': 672, 'player': 1, 'operation': 'SELL', 'item': 'STRAWBERRY',
             'units': 30, 'money': 1614, 'first_unit_price': 82, 'last_unit_price': 26},
        ])

    def test_every_recorded_poststate_is_checked(self):
        records = [json.loads(line) for line in gzip.decompress(TRACE.read_bytes()).splitlines()]
        records[673]['post'][0]['farms'][0]['money'] += 1
        with tempfile.TemporaryDirectory() as temp:
            tampered = Path(temp) / 'tampered.jsonl.gz'
            raw = b''.join((json.dumps(row) + '\n').encode() for row in records)
            tampered.write_bytes(gzip.compress(raw))
            with self.assertRaisesRegex(ValueError, 'poststate mismatch at step 672'):
                analyze_replay(tampered)

    def test_step_672_slot_swap_isolated_effect_is_measured(self):
        result = analyze_order_swap(TRACE, player=0, step=672, slots=(1, 2))
        self.assertEqual(result['original_market'][:3], [
            ['SELL', 'WOOL', 12], ['SELL', 'TOMATO', 4], ['SELL', 'STRAWBERRY', 29]])
        self.assertEqual(result['swapped_market'][:3], [
            ['SELL', 'WOOL', 12], ['SELL', 'STRAWBERRY', 29], ['SELL', 'TOMATO', 4]])
        self.assertEqual(result['original_money'], [92289, 93766])
        self.assertEqual(result['swapped_money'], [93027, 93069])
        self.assertEqual(result['money_effect'], [738, -697])
        self.assertEqual(result['relative_margin_effect'], 1435)
        self.assertTrue(result['same_farms_except_money'])
        self.assertTrue(result['same_private_sheds'])

    def test_analysis_localizes_first_action_divergence_and_terminal_stock(self):
        result = analyze_replay(TRACE)
        self.assertEqual(result['first_action_divergence'], {'step': 624, 'day': 26, 'hour': 0})
        self.assertEqual(result['terminal_stock'][0], {
            'shed_goods': 0, 'carried_goods': 0, 'tile_yield_units': 0, 'seeds': 0})


if __name__ == '__main__':
    unittest.main()
