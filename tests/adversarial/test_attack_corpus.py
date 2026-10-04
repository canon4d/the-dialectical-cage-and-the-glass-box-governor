"""One generated test per scenario in the attack corpus, run against the full
v1 governor (Arm C). A scenario passes only if (a) the decision and reason code
are the expected ones and (b) the protected files — observed independently from
disk — are byte-for-byte unchanged (or changed by exactly one version step for
legitimate requests)."""

import re
import tempfile
import unittest

from evaluation.arms import ArmC
from evaluation.scenarios import FAMILIES, SCENARIOS, run_scenario
from evaluation.world import World
from governor.decisions import Reason


class AttackCorpus(unittest.TestCase):
    pass


def _make(sc):
    def test(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = World(tmp)
            attempts = run_scenario(sc, w, ArmC(w))
            self.assertTrue(attempts, "scenario recorded no measured attempt")
            for a in attempts:
                self.assertTrue(
                    a["ok"],
                    f"{a['label']}: decision={a['decision']} reason={a['reason']} "
                    f"expected={a['expected']}/{a['expected_reasons']} state_changed={a['state_changed']}")
                if a["expected"] == "ALLOW":
                    self.assertTrue(a["exact_version_step"], "legitimate effect must advance version by exactly 1")
                else:
                    self.assertFalse(a["state_changed"])
                    self.assertEqual(a["decision"], "BLOCK")
                    self.assertTrue(a["event_id"], "every blocked request must produce an evidence event")
    return test


for _sc in SCENARIOS:
    setattr(AttackCorpus, "test_" + re.sub(r"[^A-Za-z0-9]+", "_", _sc.id), _make(_sc))


class CorpusShape(unittest.TestCase):
    def test_every_family_has_scenarios(self):
        for fid in FAMILIES:
            self.assertTrue([s for s in SCENARIOS if s.family == fid], fid)

    def test_scenario_ids_unique(self):
        ids = [s.id for s in SCENARIOS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_reason_code_coverage_is_deliberate(self):
        """A new reason code must be either covered by a scenario or explicitly listed here."""
        covered = set()
        for sc in SCENARIOS:
            with tempfile.TemporaryDirectory() as tmp:
                w = World(tmp)
                for a in run_scenario(sc, w, ArmC(w)):
                    covered.add(a["reason"])
        uncovered = set(Reason.all()) - covered
        self.assertEqual(uncovered, {"INTERNAL_ERROR", "EXECUTION_FAILED"},
                         "uncovered reason codes changed; add a scenario or document why not")


if __name__ == "__main__":
    unittest.main()
