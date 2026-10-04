"""Tests that the harness has teeth: removing a mechanism must expose the attack
family it is responsible for, and a non-atomic monitor must double-spend."""

import unittest

from evaluation.ablation import ABLATIONS, AblatedMonitor
from evaluation.race import race
from evaluation.runner import run_arm

EXPECTED_EXPOSURE = {
    "signature_authentic": {"F12"},
    "principal_binding": {"F05"},
    "effect_binding": {"F07"},
    "resource_binding": {"F06"},
    "validity_window": {"F03"},
    "policy_binding": {"F10"},
    "revocation_current": {"F04"},
    "policy_decision": {"F16"},
    "state_current": {"F09"},
    "evidence_witness": {"F15"},
}


class Ablations(unittest.TestCase):
    def test_each_ablation_exposes_its_family(self):
        for name, _ in ABLATIONS:
            att = [a for a in run_arm("C", monitor_factory=AblatedMonitor, skip=(name,)) if a["expected"] == "BLOCK"]
            exposed = {a["family"] for a in att if a["state_changed"]}
            with self.subTest(name):
                if name == "replay_protection":
                    # documented finding: state/version binding independently blocks replays
                    self.assertEqual(exposed, set())
                else:
                    self.assertTrue(EXPECTED_EXPOSURE[name] <= exposed, f"{name}: exposed {exposed}")


class Arms(unittest.TestCase):
    def test_baselines_are_actually_attackable(self):
        a = run_arm("A")
        b = run_arm("B")
        att = lambda xs: [x for x in xs if x["expected"] == "BLOCK"]
        self.assertGreaterEqual(sum(x["state_changed"] for x in att(a)), 55)
        self.assertGreaterEqual(sum(x["state_changed"] for x in att(b)), 50)
        self.assertEqual(sum(x["state_changed"] for x in att(run_arm("C"))), 0)


class Races(unittest.TestCase):
    def test_atomic_monitor_never_double_spends(self):
        for mode in ("same_capability", "competing_capabilities"):
            r = race(60, True, mode)
            self.assertEqual((r["double_spends"], r["zero_winner_rounds"], r["invariant_violations"]), (0, 0, 0), mode)

    def test_non_atomic_variant_does_double_spend(self):
        r = race(20, False, "same_capability")
        self.assertEqual(r["double_spends"], 20)


if __name__ == "__main__":
    unittest.main()
