import tempfile
import unittest

from evaluation.runner import run_evaluation
from evaluation.world import World
from governor.evidence import verify_chain


class EndToEnd(unittest.TestCase):
    def test_one_authorized_and_one_denied_operation(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = World(tmp)
            ok = w.monitor.request("agent-demo", "write_file", "record-a", w.issue(), "hello")
            self.assertEqual((ok.decision.value, ok.committed, ok.version_after), ("ALLOW", True, 1))
            self.assertEqual(w.content("record-a"), "hello")
            no = w.monitor.request("agent-demo", "delete_file", "record-a", None, None)
            self.assertEqual((no.decision.value, no.committed, no.reason), ("BLOCK", False, "MISSING_CAPABILITY"))
            self.assertEqual(w.content("record-a"), "hello")
            self.assertTrue(verify_chain(w.evidence.records))
            kinds = [r.get("kind", "decision") for r in w.evidence.records]
            self.assertEqual(kinds, ["intent", "decision", "decision"])

    def test_evidence_records_reconstruct_the_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = World(tmp)
            cap = w.issue(principal="agent-other")
            w.monitor.request("agent-demo", "write_file", "record-a", cap, "x")
            rec = w.evidence.records[-1]
            for k in ("event_id", "principal", "capability_id", "policy_hash", "profile_id", "resource_id",
                      "requested_effect", "decision", "reason_code", "checks", "nonce"):
                self.assertIn(k, rec)
            self.assertEqual(rec["reason_code"], "PRINCIPAL_MISMATCH")
            self.assertEqual(rec["checks"][-1], {"check": "principal_binding", "result": "fail"})

    def test_results_core_is_deterministic(self):
        import hashlib, json
        h = []
        for _ in range(2):
            r = run_evaluation(race_rounds=10, perf_n=5)
            h.append(hashlib.sha256(json.dumps(r["core"], sort_keys=True).encode()).hexdigest())
        self.assertEqual(h[0], h[1])


if __name__ == "__main__":
    unittest.main()
