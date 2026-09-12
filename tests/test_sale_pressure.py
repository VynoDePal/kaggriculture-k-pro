import copy
import json
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from evaluation.engine import load_engine, load_policy, new_game
from evaluation.build_sale_candidate import ADAPTER, PARENT, build, render
from research.sale_pressure import DEFAULT_MARKET_PARAMS, adjust, make_agent, market_price, sale_pressure


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "candidates" / "k_pro6_sale_pressure.py"


def sell_positions(action):
    return [i for i, order in enumerate(action["market"])
            if isinstance(order, list) and len(order) >= 3 and order[0] == "SELL"]


def assert_only_sell_order_changed(case, old, new):
    case.assertEqual(old["farmer"], new["farmer"])
    case.assertEqual(old["hands"], new["hands"])
    case.assertEqual(len(old["market"]), len(new["market"]))
    slots = sell_positions(old)
    case.assertEqual(slots, sell_positions(new))
    case.assertEqual(Counter(tuple(old["market"][i]) for i in slots),
                     Counter(tuple(new["market"][i]) for i in slots))
    for i in set(range(len(old["market"]))) - set(slots):
        case.assertEqual(old["market"][i], new["market"][i])


class SalePressureTests(unittest.TestCase):
    def test_pricing_matches_official_oracle_across_shapes_and_crossings(self):
        engine = load_engine()
        inventories = (0, 9550, 9800, 9999, 10000, 10001, 10100, 10450, 20000)
        for item in engine.PRODUCTS:
            for inventory in inventories:
                with self.subTest(item=item, inventory=inventory):
                    self.assertEqual(market_price(item, inventory, DEFAULT_MARKET_PARAMS),
                                     engine.market_price(item, inventory))

        custom = copy.deepcopy(engine.MARKET_PARAMS)
        custom["WHEAT"].update(base=31, I0=77, T=9, below_func="log10",
                               below_target=.35, above_func="hinge", above_target=.8)
        for inventory in (0, 68, 76, 77, 78, 86, 100):
            with self.subTest(custom_inventory=inventory):
                self.assertEqual(market_price("WHEAT", inventory, custom),
                                 engine.market_price("WHEAT", inventory, custom))

    def test_pressure_simulates_two_quantities_and_stops_advancing_at_floor(self):
        engine = load_engine()
        params = copy.deepcopy(engine.MARKET_PARAMS)
        params["WHEAT"].update(base=10, I0=0, T=2, above_func="linear", above_target=1)
        self.assertEqual(sale_pressure("WHEAT", 0, 2, params), 13)
        self.assertEqual(sale_pressure("WHEAT", 2, 2, params), 0)

    def test_threatened_receipts_reorder_only_sell_slots_stably(self):
        obs = {"market": {"inventory": {item: 10000 for item in DEFAULT_MARKET_PARAMS}}}
        action = {"farmer": ["WEST"], "hands": [["HARVEST"], ["PASS"]],
                  "market": [["SELL", "WHEAT", 1], [], ["BUY_PRODUCT", "WHEAT", 3],
                             ["BUY_SEED", "MELON", 2], ["SELL", "STRAWBERRY", 8],
                             ["SELL", "MILK", 4], ["SELL", "WHEAT", 1]]}
        snapshot = copy.deepcopy((obs, action))
        revised = adjust(obs, action)
        self.assertEqual(revised["market"],
                         [["SELL", "STRAWBERRY", 8], [], ["BUY_PRODUCT", "WHEAT", 3],
                          ["BUY_SEED", "MELON", 2], ["SELL", "MILK", 4],
                          ["SELL", "WHEAT", 1], ["SELL", "WHEAT", 1]])
        assert_only_sell_order_changed(self, action, revised)
        self.assertEqual((obs, action), snapshot)

        # The same unit quantities reverse priority after crossing into glut.
        pair = dict(action, market=[["SELL", "MELON", 1], ["SELL", "CARROT", 1]])
        self.assertEqual(adjust(obs, pair)["market"],
                         [["SELL", "CARROT", 1], ["SELL", "MELON", 1]])
        deeper = copy.deepcopy(obs)
        deeper["market"]["inventory"]["MELON"] = 10100
        deeper["market"]["inventory"]["CARROT"] = 10100
        self.assertIs(adjust(deeper, pair), pair)

    def test_zero_one_sale_ties_and_unsupported_inputs_leave_action_unchanged(self):
        base = {"farmer": ["PASS"], "hands": [], "market": [[], ["SELL", "WHEAT", 2]]}
        observations = [
            {"market": {"inventory": {"WHEAT": 10000}}},
            {"market": {"inventory": {"WHEAT": "bad"}}},
            {"market": {"inventory": {"WHEAT": 10000}, "params": {"WHEAT": {"T": 0}}}},
        ]
        for obs in observations:
            with self.subTest(obs=obs):
                self.assertIs(adjust(obs, base), base)
        tied = copy.deepcopy(base)
        tied["market"] = [["SELL", "WHEAT", 2], ["SELL", "WHEAT", 2]]
        self.assertIs(adjust(observations[0], tied), tied)

    def test_unknown_public_price_shape_leaves_otherwise_reordered_action_unchanged(self):
        params = copy.deepcopy(DEFAULT_MARKET_PARAMS)
        params["WHEAT"]["below_func"] = "unsupported-shape"
        obs = {"market": {"inventory": {item: 0 for item in params}, "params": params}}
        action = {"farmer": ["PASS"], "hands": [],
                  "market": [["SELL", "WHEAT", 1], ["SELL", "CARROT", 1]]}
        snapshot = copy.deepcopy((obs, action))
        self.assertIs(adjust(obs, action), action)
        self.assertEqual((obs, action), snapshot)

    def test_wrapper_calls_parent_once_and_loaded_instances_are_independent(self):
        calls = []
        original = {"farmer": ["PASS"], "hands": [],
                    "market": [["SELL", "WHEAT", 1], ["SELL", "STRAWBERRY", 8]]}
        def parent(obs, config=None):
            calls.append((obs, config))
            return copy.deepcopy(original)
        wrapped = make_agent(parent)
        obs = {"market": {"inventory": {item: 10000 for item in DEFAULT_MARKET_PARAMS}}}
        config = {"episodeSteps": 720}
        wrapped(obs, config)
        self.assertEqual(calls, [(obs, config)])

        first, second = load_policy(CANDIDATE), load_policy(CANDIDATE)
        first_ref = first.__globals__["_reference"]
        second_ref = second.__globals__["_reference"]
        self.assertIsNot(first_ref, second_ref)
        self.assertIsNot(first_ref._STATE, second_ref._STATE)

    def test_builder_is_reproducible_exclusive_and_failure_leaves_no_artifact(self):
        before = (PARENT.read_bytes(), ADAPTER.read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            one, two = folder / "one.py", folder / "two.py"
            build(one)
            build(two)
            self.assertEqual(one.read_bytes(), two.read_bytes())
            self.assertEqual(one.read_bytes(), CANDIDATE.read_bytes())
            with self.assertRaises(FileExistsError):
                build(one)
            missing = folder / "missing.py"
            with self.assertRaises(FileNotFoundError):
                build(missing, adapter=folder / "does-not-exist.py")
            self.assertFalse(missing.exists())
        self.assertEqual(before, (PARENT.read_bytes(), ADAPTER.read_bytes()))
        self.assertEqual(render(), CANDIDATE.read_text(encoding="utf-8"))

    def test_official_loader_and_empty_cwd_python_i_execute_standalone(self):
        policy = load_policy(CANDIDATE)
        self.assertEqual(policy.__name__, "kaggle_agent")
        state, env = new_game(930053)
        payload = json.dumps([state[0].observation, env.configuration])
        code = ("import json,runpy,sys; o,c=json.load(sys.stdin); "
                "d=runpy.run_path(" + repr(str(CANDIDATE)) + "); "
                "a=d['kaggle_agent'](o,c); "
                "assert isinstance(a,dict) and set(('farmer','hands','market'))<=set(a)")
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, "-I", "-c", code], cwd=directory,
                           input=payload, text=True, check=True)

    def test_full_trajectory_differs_from_exact_parent_only_by_sell_order(self):
        engine = load_engine()
        candidate = load_policy(CANDIDATE)
        parent = load_policy(PARENT)
        state, env = new_game(930053)
        config_snapshot = copy.deepcopy(env.configuration)
        for step in range(719):
            for player in state:
                player.observation.step = step
            observation = state[0].observation
            snapshot = copy.deepcopy(observation)
            expected = parent(copy.deepcopy(observation), env.configuration)
            actual = candidate(observation, env.configuration)
            self.assertEqual(observation, snapshot)
            self.assertEqual(env.configuration, config_snapshot)
            assert_only_sell_order_changed(self, expected, actual)
            state[0].action = actual
            state[1].action = {"farmer": ["PASS"], "hands": [], "market": []}
            engine.interpreter(state, env)
        self.assertEqual([s.status for s in state], ["DONE", "DONE"])


if __name__ == "__main__":
    unittest.main()
