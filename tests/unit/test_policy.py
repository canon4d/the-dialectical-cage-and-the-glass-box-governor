import json
import tempfile
import unittest
from pathlib import Path

from governor.decisions import Verdict
from governor.errors import PolicyError
from governor.policy import Policy, admit
from evaluation.world import load_policy, load_profile


def pol(**over):
    base = {"policy_version": "t", "default": "DENY", "rules": []}
    base.update(over)
    return Policy.from_obj(base)


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile()

    def test_shipped_policies_are_admitted(self):
        for n in ("protected-file-v1.policy.json", "protected-file-v1.policy.2.json"):
            self.assertEqual(admit(load_policy(n), self.profile), [])

    def test_deny_by_default_and_deny_wins(self):
        p = pol(rules=[
            {"principal": "agent-demo", "effect": "write_file", "resource": "record-a", "decision": "ALLOW"},
            {"principal": "agent-demo", "effect": "write_file", "resource": "record-a", "decision": "DENY"}])
        self.assertEqual(p.evaluate("agent-demo", "write_file", "record-a"), Verdict.DENY)
        self.assertEqual(p.evaluate("agent-demo", "delete_file", "record-a"), Verdict.DENY)

    def test_admission_rejects_bad_policies(self):
        rule = {"principal": "agent-demo", "effect": "write_file", "resource": "record-a", "decision": "ALLOW"}
        cases = {
            "allow default": pol(default="ALLOW"),
            "wildcard principal": pol(rules=[{**rule, "principal": "*"}]),
            "undeclared effect": pol(rules=[{**rule, "effect": "chmod_file"}]),
            "undeclared resource": pol(rules=[{**rule, "resource": "record-z"}]),
            "bad decision": pol(rules=[{**rule, "decision": "MAYBE"}]),
            "conflict": pol(rules=[rule, {**rule, "decision": "DENY"}]),
        }
        for name, p in cases.items():
            with self.subTest(name):
                self.assertTrue(admit(p, self.profile), name)

    def test_hash_is_canonical(self):
        a = Policy.from_obj({"policy_version": "t", "default": "DENY", "rules": []})
        b = Policy.from_obj({"rules": [], "default": "DENY", "policy_version": "t"})
        self.assertEqual(a.sha256, b.sha256)
        self.assertNotEqual(a.sha256, pol(policy_version="u").sha256)

    def test_corrupted_policy_artifact_is_rejected_at_load(self):
        with tempfile.TemporaryDirectory() as d:
            for name, text in (("garbage", "{not json"), ("extra", '{"policy_version":"t","default":"DENY","rules":[],"x":1}'),
                               ("bad rule", '{"policy_version":"t","default":"DENY","rules":[{"principal":"a"}]}')):
                p = Path(d) / name
                p.write_text(text)
                with self.subTest(name), self.assertRaises(PolicyError):
                    Policy.load(p)
            with self.assertRaises(PolicyError):
                Policy.load(Path(d) / "missing.json")


if __name__ == "__main__":
    unittest.main()
