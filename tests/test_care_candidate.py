import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evaluation.build_candidate import ADAPTER, PARENT, build, render
from evaluation.engine import load_engine, load_policy, new_game

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "candidates" / "k_pro6_care_fp.py"
SPECIES = ("COW", "SHEEP", "GOOSE")


def reference(policy):
    return policy.__globals__["_reference"]


def prices(ref):
    result = {item: 100 for item in ref.PARAMS}
    result["WHEAT"] = 1
    return result


def tile(animal, placed_day, **changes):
    result = dict(kind="PASTURE" if animal != "GOOSE" else "COOP",
                  animal=animal, placed_day=placed_day, yield_units=0,
                  consecutive_unfed=0, fed_today=False, cared_today=False,
                  fertilizer_available=True, pending_care_bonus=0)
    result.update(changes)
    return result


def products_through_day_29(engine, animal_tile, day, cared):
    """Use official refresh as the oracle; do not restate its calendar."""
    farm = {"tiles": [[copy.deepcopy(animal_tile)]]}
    farm["tiles"][0][0]["cared_today"] = cared
    produced = 0
    for refresh_day in range(day, 29):
        current = farm["tiles"][0][0]
        if "animal" not in current:
            break
        current["fed_today"] = True
        engine._daily_refresh_animals(farm, refresh_day)
        current = farm["tiles"][0][0]
        produced += current.get("yield_units", 0)
        current["yield_units"] = 0
    return produced


class CareCandidateTests(unittest.TestCase):
    def test_parent_defect_and_candidate_horizon_behavior(self):
        engine = load_engine()
        parent = reference(load_policy(PARENT))
        candidate = reference(load_policy(CANDIDATE))
        witnessed = {animal: 0 for animal in SPECIES}
        for animal in SPECIES:
            for day in range(30):
                for placed_day in range(day + 1):
                    animal_tile = tile(animal, placed_day)
                    old, _ = parent.animal_tasks(animal_tile, day, prices(parent), {})
                    if ["CARE"] not in old:
                        continue
                    without = products_through_day_29(engine, animal_tile, day, False)
                    with_care = products_through_day_29(engine, animal_tile, day, True)
                    new, _ = candidate.animal_tasks(animal_tile, day, prices(candidate), {})
                    with self.subTest(animal=animal, day=day, placed_day=placed_day):
                        if with_care == without:
                            witnessed[animal] += 1
                            self.assertNotIn(["CARE"], new)
                        else:
                            self.assertIn(["CARE"], new)
        self.assertTrue(all(witnessed.values()))

    def test_only_care_is_removed_from_late_multitask_animals(self):
        parent = reference(load_policy(PARENT))
        candidate = reference(load_policy(CANDIDATE))
        engine = load_engine()
        for animal in SPECIES:
            found = False
            for day in range(29):
                for placed_day in range(day + 1):
                    animal_tile = tile(animal, placed_day, yield_units=1)
                    old, _ = parent.animal_tasks(animal_tile, day, prices(parent), {})
                    calendar_tile = tile(animal, placed_day)
                    ineffective = (products_through_day_29(engine, calendar_tile, day, True)
                                   == products_through_day_29(engine, calendar_tile, day, False))
                    if ["CARE"] in old and ineffective:
                        new, _ = candidate.animal_tasks(animal_tile, day, prices(candidate), {})
                        self.assertEqual(new, [task for task in old if task != ["CARE"]])
                        for task in (["HARVEST"], ["FEED"], ["COLLECT_FERTILIZER"]):
                            self.assertIn(task, new)
                        found = True
                        break
                if found:
                    break
            self.assertTrue(found, f"no late multi-task witness for {animal}")

    def test_build_is_reproducible_exclusive_and_sources_unchanged(self):
        before = (PARENT.read_bytes(), ADAPTER.read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            one, two = Path(directory) / "one.py", Path(directory) / "two.py"
            build(one)
            build(two)
            self.assertEqual(one.read_bytes(), two.read_bytes())
            self.assertEqual(one.read_bytes(), CANDIDATE.read_bytes())
            with self.assertRaises(FileExistsError):
                build(one)
        self.assertEqual(before, (PARENT.read_bytes(), ADAPTER.read_bytes()))
        self.assertEqual(render(), CANDIDATE.read_text(encoding="utf-8"))

    def test_official_loader_selects_final_agent_and_empty_cwd_executes_it(self):
        policy = load_policy(CANDIDATE)
        self.assertEqual(policy.__name__, "kaggle_agent")
        state, env = new_game(920001)
        payload = json.dumps([state[0].observation, env.configuration])
        code = ("import json,runpy,sys; o,c=json.load(sys.stdin); "
                "d=runpy.run_path(" + repr(str(CANDIDATE)) + "); "
                "a=d['kaggle_agent'](o,c); "
                "assert isinstance(a,dict) and set(('farmer','hands','market'))<=set(a)")
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, "-I", "-c", code], cwd=directory,
                           input=payload, text=True, check=True)

    def test_loaded_instances_are_independent_and_do_not_mutate_input(self):
        first, second = load_policy(CANDIDATE), load_policy(CANDIDATE)
        self.assertIsNot(reference(first), reference(second))
        self.assertIsNot(reference(first)._STATE, reference(second)._STATE)
        state, env = new_game(920000)
        observation = copy.deepcopy(state[0].observation)
        snapshot = copy.deepcopy(observation)
        first(observation, env.configuration)
        self.assertEqual(observation, snapshot)
        self.assertEqual(reference(second)._STATE, {})


if __name__ == "__main__":
    unittest.main()
