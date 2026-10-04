"""Test world: sandbox, profile, policy, issuer, monitor — plus an *independent
observer* that reads the protected files straight from disk and never trusts the
monitor's own account of what happened."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from governor.capability import CapabilityIssuer, CapabilityVerifier
from governor.clock import FixedClock, SequentialIds
from governor.evidence import EvidenceWriter
from governor.errors import PolicyUnavailable
from governor.monitor import ReferenceMonitor
from governor.policy import Policy, StaticPolicySource, admit
from governor.state import NonceStore, ProtectedResource, RevocationStore

ROOT = Path(__file__).resolve().parent.parent
TEST_KEY = b"glass-box-governor/TEST-ONLY-KEY/not-a-secret"
ISSUER_ID = "issuer-test-1"
BASELINE = {"record-a": "baseline-record-a", "record-b": "baseline-record-b"}


class SwitchablePolicySource(StaticPolicySource):
    """Policy source whose availability can be toggled (models an unreachable
    or corrupted policy store)."""

    def __init__(self, policy):
        super().__init__(policy)
        self.available = True

    def get(self):
        if not self.available:
            raise PolicyUnavailable("policy store unreachable")
        return super().get()


def load_profile() -> dict:
    return json.loads((ROOT / "profiles" / "protected-file-v1.json").read_text(encoding="utf-8"))


def load_policy(name="protected-file-v1.policy.json") -> Policy:
    return Policy.load(ROOT / "profiles" / name)


class World:
    def __init__(self, workdir, monitor_factory=ReferenceMonitor, **monitor_kwargs):
        self.root = Path(workdir)
        self.profile = load_profile()
        self.policy = load_policy()
        self.policy2 = load_policy("protected-file-v1.policy.2.json")
        for p in (self.policy, self.policy2):
            problems = admit(p, self.profile)
            if problems:
                raise AssertionError(f"policy not admitted: {problems}")
        self.clock = FixedClock()
        self.ids = SequentialIds()
        self.resources = {}
        for r in self.profile["resources"]:
            res = ProtectedResource(r["id"], self.root / "sandbox" / r["path"])
            res.initialize(BASELINE[r["id"]])
            self.resources[r["id"]] = res
        self.revocations = RevocationStore()
        self.nonces = NonceStore()
        self.evidence = EvidenceWriter()
        self.policy_source = SwitchablePolicySource(self.policy)
        self.issuer = CapabilityIssuer(TEST_KEY, ISSUER_ID, self.clock, self.ids)
        self.attacker_issuer = CapabilityIssuer(b"attacker-controlled-key-0000", ISSUER_ID, self.clock, self.ids)
        self.verifier = CapabilityVerifier(TEST_KEY, ISSUER_ID)
        self.monitor = None
        if monitor_factory is not None:
            self.monitor = monitor_factory(
                profile=self.profile, policy_source=self.policy_source, verifier=self.verifier,
                resources=self.resources, revocations=self.revocations, nonces=self.nonces,
                evidence=self.evidence, clock=self.clock, **monitor_kwargs)

    # -- capability helpers -------------------------------------------------------
    def current_version(self, rid) -> int:
        return json.loads(self.resources[rid].meta_path.read_text())["version"]

    def issue(self, principal="agent-demo", effect="write_file", resource="record-a",
              version=None, issuer=None, **kw):
        return (issuer or self.issuer).issue(
            principal_id=principal, effect=effect, resource_id=resource,
            resource_version=self.current_version(resource) if version is None else version,
            policy_hash=kw.pop("policy_hash", self.policy_source._policy.sha256),
            revocation_epoch=kw.pop("revocation_epoch", self.revocations.epoch), **kw)

    # -- independent observation ----------------------------------------------------
    def observe(self, rid):
        res = self.resources[rid]
        try:
            digest = hashlib.sha256(res.path.read_bytes()).hexdigest()
            exists = True
        except FileNotFoundError:
            digest, exists = "ABSENT", False
        try:
            version = json.loads(res.meta_path.read_text())["version"]
        except Exception:  # noqa: BLE001 - observer must never crash the harness
            version = None
        return (exists, digest, version)

    def observe_all(self):
        return {rid: self.observe(rid) for rid in self.resources}

    def content(self, rid):
        p = self.resources[rid].path
        return p.read_text() if p.exists() else None
