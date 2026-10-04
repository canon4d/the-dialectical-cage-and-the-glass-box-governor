"""The reference monitor: the only intended path to a protected effect.

Every request runs the ordered check pipeline below inside ONE lock that also
covers the commit, so revalidation of state/nonce and the commit are atomic
with respect to other mediated requests (condition C6, within one process).

Unresolvable safety state is UNKNOWN and is mapped to BLOCK (condition C7).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, List, Optional

from . import PROFILE_ID, __version__
from .capability import Capability, CapabilityVerifier
from .decisions import Decision, Reason, Verdict
from .errors import (EvidenceUnavailable, ExecutionError, GovernorError,
                     MalformedCapability, PolicyUnavailable, RevocationUnavailable,
                     StateInconsistent, StateUnavailable)
from .evidence import EvidenceWriter
from .executor import ProtectedExecutor, mint
from .state import NonceStore, ProtectedResource, ResourceState, RevocationStore


class _Block(Exception):
    def __init__(self, reason: str, underlying: Verdict = Verdict.DENY):
        self.reason, self.underlying = reason, underlying


@dataclass
class Outcome:
    decision: Decision
    reason: str
    event_id: Optional[str]
    committed: bool
    version_before: Optional[int]
    version_after: Optional[int]
    trace: List[dict] = field(default_factory=list)
    underlying: str = "DENY"
    evidence_complete: bool = True
    integrity: Optional[str] = None


class ReferenceMonitor:
    MAX_CONTENT = 64 * 1024

    def __init__(self, *, profile: dict, policy_source, verifier: CapabilityVerifier,
                 resources: dict, revocations: RevocationStore, nonces: NonceStore,
                 evidence: EvidenceWriter, clock):
        self.profile = profile
        self._policy_source = policy_source
        self._verifier = verifier
        self._resources = resources
        self._revocations = revocations
        self._nonces = nonces
        self._evidence = evidence
        self._clock = clock
        self._executor = ProtectedExecutor(resources)
        self._lock = threading.RLock()
        self._principals = {p["id"] for p in profile["principals"]}
        self._effects = set(profile["effects"])
        self._evidence_required = set(profile["evidence"]["required_before_effect"])

    # -- pipeline ------------------------------------------------------------------
    def _pipeline(self):
        """Ordered (name, callable) pairs. Subclasses in evaluation/ may filter
        this list to build *ablations*; the trusted class itself has no off switch."""
        return [
            ("request_wellformed", self._c_request),
            ("effect_supported", self._c_effect),
            ("resource_declared", self._c_resource),
            ("principal_declared", self._c_principal_declared),
            ("capability_present", self._c_present),
            ("capability_wellformed", self._c_wellformed),
            ("delegation_absent", self._c_delegation),
            ("signature_authentic", self._c_signature),
            ("principal_binding", self._c_principal),
            ("effect_binding", self._c_effect_bind),
            ("resource_binding", self._c_resource_bind),
            ("validity_window", self._c_window),
            ("policy_available", self._c_policy_available),
            ("policy_binding", self._c_policy_bind),
            ("revocation_current", self._c_revocation),
            ("policy_decision", self._c_policy_decision),
            ("replay_protection", self._c_replay),
            ("state_current", self._c_state),
            ("evidence_witness", self._c_evidence),
        ]

    # -- public API ----------------------------------------------------------------
    def request(self, principal_id: Any, effect: Any, resource_id: Any,
                capability: Any = None, content: Any = None) -> Outcome:
        with self._lock:
            return self._request_locked(principal_id, effect, resource_id, capability, content)

    def _request_locked(self, principal_id, effect, resource_id, capability, content) -> Outcome:
        event_id = self._evidence.next_event_id()
        ctx = {"principal": principal_id, "effect": effect, "resource": resource_id,
               "raw_cap": capability, "content": content, "cap": None, "policy": None,
               "state": None, "event_id": event_id}
        trace: List[dict] = []
        try:
            for name, fn in self._pipeline():
                try:
                    fn(ctx)
                except _Block:
                    raise
                except Exception as exc:  # any unexpected error is UNKNOWN => BLOCK (fail-closed)
                    raise _Block(Reason.INTERNAL_ERROR, Verdict.UNKNOWN) from exc
                trace.append({"check": name, "result": "pass"})
        except _Block as blk:
            trace.append({"check": name, "result": "unknown" if blk.underlying == Verdict.UNKNOWN else "fail"})
            return self._finish_block(ctx, event_id, trace, blk)
        return self._commit(ctx, event_id, trace)

    # -- outcomes ------------------------------------------------------------------
    def _evidence_body(self, ctx, event_id, decision, reason, trace, underlying, version_before, version_after):
        cap: Optional[Capability] = ctx["cap"]
        pol = ctx["policy"]
        st: Optional[ResourceState] = ctx["state"]
        return {
            "event_id": event_id,
            "timestamp": self._clock.now(),
            "profile_id": PROFILE_ID,
            "monitor_version": __version__,
            "principal": ctx["principal"] if isinstance(ctx["principal"], str) else None,
            "capability_id": cap.capability_id if cap else None,
            "policy_hash": pol.sha256 if pol else None,
            "resource_id": ctx["resource"] if isinstance(ctx["resource"], str) else None,
            "resource_version": version_before,
            "state_digest": st.digest if st else None,
            "requested_effect": ctx["effect"] if isinstance(ctx["effect"], str) else None,
            "decision": decision.value,
            "underlying": underlying,
            "reason_code": reason,
            "checks": [dict(t) for t in trace],
            "approval_chain": [],
            "result_version": version_after,
            "nonce": cap.nonce if cap else None,
        }

    def _finish_block(self, ctx, event_id, trace, blk: _Block) -> Outcome:
        st: Optional[ResourceState] = ctx["state"]
        before = st.version if st else None
        complete, integ = True, None
        try:
            rec = self._evidence.record(self._evidence_body(
                ctx, event_id, Decision.BLOCK, blk.reason, trace, blk.underlying.value, before, before))
            integ = rec["integrity"]
        except EvidenceUnavailable:
            complete = False  # block stands regardless; evidence gap is itself reported
        return Outcome(Decision.BLOCK, blk.reason, event_id, False, before, before, trace,
                       blk.underlying.value, complete, integ)

    def _commit(self, ctx, event_id, trace) -> Outcome:
        cap: Capability = ctx["cap"]
        state: ResourceState = ctx["state"]
        # (the intent record, if required, was already written by the evidence_witness check)
        if cap.one_shot:
            self._nonces.consume(cap.nonce)  # burnt even if execution later fails (fail-closed)
        auth = mint(ctx["effect"], ctx["resource"], event_id)
        try:
            new = self._executor.execute(auth, ctx["content"], state)
        except ExecutionError:
            trace.append({"check": "execute", "result": "fail"})
            return self._finish_block(ctx, event_id, trace, _Block(Reason.EXECUTION_FAILED, Verdict.UNKNOWN))
        trace.append({"check": "execute", "result": "pass"})
        complete, integ = True, None
        try:
            rec = self._evidence.record(self._evidence_body(
                ctx, event_id, Decision.ALLOW, Reason.OK, trace, "ALLOW", state.version, new.version))
            integ = rec["integrity"]
        except EvidenceUnavailable:
            complete = False  # effect already committed; reported, not hidden
        return Outcome(Decision.ALLOW, Reason.OK, event_id, True, state.version, new.version,
                       trace, "ALLOW", complete, integ)

    # -- checks (each raises _Block or returns) ------------------------------------
    def _c_request(self, c):
        e, content = c["effect"], c["content"]
        if not (isinstance(c["principal"], str) and isinstance(e, str) and isinstance(c["resource"], str)):
            raise _Block(Reason.MALFORMED_REQUEST)
        if e == "write_file" and not (isinstance(content, str) and len(content.encode("utf-8")) <= self.MAX_CONTENT):
            raise _Block(Reason.MALFORMED_REQUEST)
        if e == "delete_file" and content is not None:
            raise _Block(Reason.MALFORMED_REQUEST)

    def _c_effect(self, c):
        if c["effect"] not in self._effects:
            raise _Block(Reason.UNSUPPORTED_EFFECT)

    def _c_resource(self, c):
        res = self._resources.get(c["resource"])
        if res is None:
            raise _Block(Reason.UNKNOWN_RESOURCE)

    def _c_principal_declared(self, c):
        if c["principal"] not in self._principals:
            raise _Block(Reason.UNKNOWN_PRINCIPAL)

    def _c_present(self, c):
        raw = c["raw_cap"]
        if raw is None or (isinstance(raw, (str, bytes, dict, list)) and len(raw) == 0):
            raise _Block(Reason.MISSING_CAPABILITY)

    def _c_wellformed(self, c):
        try:
            c["cap"] = Capability.from_raw(c["raw_cap"])
        except MalformedCapability:
            raise _Block(Reason.MALFORMED_CAPABILITY)

    def _c_delegation(self, c):
        if c["cap"].parent_capability_id is not None:
            raise _Block(Reason.DELEGATION_UNSUPPORTED)

    def _c_signature(self, c):
        if not self._verifier.authentic(c["cap"]):
            raise _Block(Reason.BAD_SIGNATURE)

    def _c_principal(self, c):
        if c["cap"].principal_id != c["principal"]:
            raise _Block(Reason.PRINCIPAL_MISMATCH)

    def _c_effect_bind(self, c):
        if c["cap"].effect != c["effect"]:
            raise _Block(Reason.EFFECT_MISMATCH)

    def _c_resource_bind(self, c):
        if c["cap"].resource_id != c["resource"]:
            raise _Block(Reason.RESOURCE_MISMATCH)

    def _c_window(self, c):
        now, cap = self._clock.now(), c["cap"]
        if now < cap.issued_at:
            raise _Block(Reason.NOT_YET_VALID)
        if now >= cap.expires_at:
            raise _Block(Reason.EXPIRED)

    def _c_policy_available(self, c):
        try:
            c["policy"] = self._policy_source.get()
        except PolicyUnavailable:
            raise _Block(Reason.POLICY_UNAVAILABLE, Verdict.UNKNOWN)

    def _c_policy_bind(self, c):
        if c["cap"].policy_hash != c["policy"].sha256:
            raise _Block(Reason.POLICY_MISMATCH)

    def _c_revocation(self, c):
        cap = c["cap"]
        try:
            revoked = self._revocations.is_revoked(cap.capability_id, cap.revocation_epoch)
        except RevocationUnavailable:
            raise _Block(Reason.REVOCATION_UNAVAILABLE, Verdict.UNKNOWN)
        if revoked:
            raise _Block(Reason.REVOKED)

    def _c_policy_decision(self, c):
        v = c["policy"].evaluate(c["principal"], c["effect"], c["resource"])
        if v == Verdict.UNKNOWN:
            raise _Block(Reason.POLICY_UNAVAILABLE, Verdict.UNKNOWN)
        if v == Verdict.DENY:
            raise _Block(Reason.POLICY_DENY)

    def _c_replay(self, c):
        if c["cap"].one_shot and self._nonces.used(c["cap"].nonce):
            raise _Block(Reason.REPLAY)

    def _c_state(self, c):
        res: ProtectedResource = self._resources[c["resource"]]
        try:
            c["state"] = res.snapshot()
        except StateInconsistent:
            raise _Block(Reason.STATE_INCONSISTENT, Verdict.UNKNOWN)
        except StateUnavailable:
            raise _Block(Reason.STATE_UNAVAILABLE, Verdict.UNKNOWN)
        if c["state"].version != c["cap"].resource_version:
            raise _Block(Reason.STALE_STATE)

    def _c_evidence(self, c):
        if c["effect"] in self._evidence_required:
            try:
                # intent record: the effect may not proceed unless it can be witnessed
                self._evidence.record({
                    "event_id": c["event_id"] + "-INTENT",
                    "timestamp": self._clock.now(), "profile_id": PROFILE_ID,
                    "kind": "intent", "principal": c["principal"],
                    "capability_id": c["cap"].capability_id, "requested_effect": c["effect"],
                    "resource_id": c["resource"], "resource_version": c["state"].version,
                    "policy_hash": c["policy"].sha256})
            except EvidenceUnavailable:
                raise _Block(Reason.EVIDENCE_UNAVAILABLE, Verdict.UNKNOWN)
