import json
import unittest

from governor.capability import Capability, CapabilityIssuer, CapabilityVerifier
from governor.clock import FixedClock, SequentialIds
from governor.errors import MalformedCapability

KEY = b"0123456789abcdef-test-key"


def make():
    clock, ids = FixedClock(), SequentialIds()
    return CapabilityIssuer(KEY, "iss", clock, ids), CapabilityVerifier(KEY, "iss")


class CapabilityTests(unittest.TestCase):
    def issue(self, **kw):
        iss, ver = make()
        base = dict(principal_id="p", effect="write_file", resource_id="r",
                    resource_version=0, policy_hash="h" * 64)
        base.update(kw)
        return iss.issue(**base), ver

    def test_roundtrip_and_authentic(self):
        cap, ver = self.issue()
        self.assertTrue(ver.authentic(Capability.from_raw(cap.to_dict())))
        self.assertTrue(ver.authentic(Capability.from_raw(json.dumps(cap.to_dict()))))

    def test_any_field_change_breaks_signature(self):
        cap, ver = self.issue()
        for k, v in (("principal_id", "q"), ("effect", "delete_file"), ("resource_id", "x"),
                     ("resource_version", 9), ("expires_at", 1), ("nonce", "N"), ("one_shot", False)):
            d = cap.to_dict()
            d[k] = v
            self.assertFalse(ver.authentic(Capability.from_raw(d)), k)

    def test_wrong_key_or_issuer_rejected(self):
        cap, _ = self.issue()
        self.assertFalse(CapabilityVerifier(b"another-key-0123456789", "iss").authentic(cap))
        self.assertFalse(CapabilityVerifier(KEY, "other-issuer").authentic(cap))

    def test_short_key_refused(self):
        with self.assertRaises(ValueError):
            CapabilityIssuer(b"short", "iss", FixedClock(), SequentialIds())

    def test_strict_parsing(self):
        cap, _ = self.issue()
        good = cap.to_dict()
        bad_cases = {
            "not json": "{{",
            "list": [1],
            "missing": {k: v for k, v in good.items() if k != "nonce"},
            "extra": {**good, "x": 1},
            "empty string field": {**good, "principal_id": ""},
            "float int": {**good, "issued_at": 1.5},
            "negative": {**good, "expires_at": -1},
            "bool int": {**good, "resource_version": True},
            "one_shot str": {**good, "one_shot": "yes"},
            "parent int": {**good, "parent_capability_id": 5},
        }
        for name, raw in bad_cases.items():
            with self.subTest(name), self.assertRaises(MalformedCapability):
                Capability.from_raw(raw)

    def test_ids_are_unique(self):
        iss, _ = make()
        a = iss.issue(principal_id="p", effect="e", resource_id="r", resource_version=0, policy_hash="h")
        b = iss.issue(principal_id="p", effect="e", resource_id="r", resource_version=0, policy_hash="h")
        self.assertNotEqual((a.capability_id, a.nonce), (b.capability_id, b.nonce))


if __name__ == "__main__":
    unittest.main()
