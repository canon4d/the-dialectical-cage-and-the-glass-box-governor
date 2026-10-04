import tempfile
import unittest
from pathlib import Path

from governor.errors import EvidenceUnavailable, StateInconsistent, StateUnavailable
from governor.evidence import EvidenceWriter, verify_chain
from governor.executor import Authorization, ProtectedExecutor, mint
from governor.errors import ExecutionError
from governor.state import NonceStore, ProtectedResource, RevocationStore


class StateTests(unittest.TestCase):
    def test_snapshot_commit_cycle_and_version_monotonic(self):
        with tempfile.TemporaryDirectory() as d:
            r = ProtectedResource("x", Path(d) / "x.txt")
            s0 = r.initialize("hello")
            self.assertEqual((s0.version, s0.exists), (0, True))
            s1 = r.commit("write_file", "world", r.snapshot())
            s2 = r.commit("delete_file", None, s1)
            self.assertEqual((s1.version, s2.version, s2.exists), (1, 2, False))
            self.assertEqual(r.snapshot(), s2)

    def test_out_of_band_change_is_inconsistent(self):
        with tempfile.TemporaryDirectory() as d:
            r = ProtectedResource("x", Path(d) / "x.txt")
            r.initialize("hello")
            (Path(d) / "x.txt").write_text("changed")
            with self.assertRaises(StateInconsistent):
                r.snapshot()

    def test_missing_metadata_is_unavailable(self):
        with tempfile.TemporaryDirectory() as d:
            r = ProtectedResource("x", Path(d) / "x.txt")
            r.initialize("hello")
            r.meta_path.unlink()
            with self.assertRaises(StateUnavailable):
                r.snapshot()

    def test_nonce_single_use_and_revocation_epoch(self):
        n = NonceStore()
        self.assertTrue(n.consume("a"))
        self.assertFalse(n.consume("a"))
        self.assertTrue(n.used("a"))
        rv = RevocationStore()
        self.assertFalse(rv.is_revoked("c", 0))
        rv.revoke("c")
        self.assertTrue(rv.is_revoked("c", 0))
        rv.bump_epoch()
        self.assertTrue(rv.is_revoked("other", 0))
        self.assertFalse(rv.is_revoked("other", 1))


class EvidenceTests(unittest.TestCase):
    def test_chain_verifies_and_detects_tampering(self):
        w = EvidenceWriter()
        for i in range(5):
            w.record({"event_id": f"E{i}", "decision": "BLOCK"})
        self.assertTrue(verify_chain(w.records))
        tampered = [dict(r) for r in w.records]
        tampered[2]["decision"] = "ALLOW"
        self.assertFalse(verify_chain(tampered))
        self.assertFalse(verify_chain(w.records[1:]))  # truncated head
        self.assertFalse(verify_chain([w.records[0], w.records[2]]))  # removed middle

    def test_unavailable_witness_raises(self):
        w = EvidenceWriter()
        w.available = False
        with self.assertRaises(EvidenceUnavailable):
            w.record({"event_id": "E"})
        self.assertEqual(w.records, [])


class ExecutorTests(unittest.TestCase):
    def test_authorization_cannot_be_forged_by_construction(self):
        with self.assertRaises(ExecutionError):
            Authorization(object(), "write_file", "x", "E")

    def test_executor_requires_authorization(self):
        with tempfile.TemporaryDirectory() as d:
            r = ProtectedResource("x", Path(d) / "x.txt")
            st = r.initialize("a")
            ex = ProtectedExecutor({"x": r})
            with self.assertRaises(ExecutionError):
                ex.execute("not-an-authorization", "b", st)
            with self.assertRaises(ExecutionError):
                ex.execute(mint("chmod_file", "x", "E"), "b", st)
            self.assertEqual(ex.execute(mint("write_file", "x", "E"), "b", st).version, 1)


if __name__ == "__main__":
    unittest.main()
