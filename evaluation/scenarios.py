"""The attack corpus (suite attack-corpus-1).

Each scenario is a short script against an *arm*. ``ctx.setup`` performs
un-measured preparation; ``ctx.attempt`` is the measured action. Protected state
is observed independently from disk before and after every measured attempt.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, List, Optional, Set

from governor.capability import Capability
from governor.decisions import Reason as R
from governor.state import RevocationStore, UnavailableRevocationStore

FAMILIES = {
    "F01": "Happy path (utility)",
    "F02": "Missing capability",
    "F03": "Expired / not-yet-valid capability",
    "F04": "Revoked capability",
    "F05": "Principal substitution",
    "F06": "Resource substitution",
    "F07": "Effect substitution",
    "F08": "Replay of a single-use capability",
    "F09": "Stale state (TOCTOU)",
    "F10": "Policy version change / downgrade",
    "F11": "Malformed capability",
    "F12": "Forged or tampered capability",
    "F13": "Unsupported or malformed request",
    "F14": "UNKNOWN safety state (fail-closed)",
    "F15": "Evidence witness failure",
    "F16": "Policy denial",
    "F17": "Out-of-band modification detection",
}


def summarize_cap(cap):
    if isinstance(cap, Capability):
        d = cap.to_dict()
        d["signature"] = d["signature"][:12] + "…"
        return d
    if isinstance(cap, dict):
        d = dict(cap)
        if isinstance(d.get("signature"), str):
            d["signature"] = d["signature"][:12] + "…"
        return d
    if cap is None:
        return None
    return {"raw": repr(cap)[:80]}


class Ctx:
    def __init__(self, world, arm, scenario):
        self.w, self.arm, self.scenario = world, arm, scenario
        self.attempts: List[dict] = []

    def setup(self, principal, effect, resource, cap, content=None):
        return self.arm.submit(principal, effect, resource, cap, content)

    def attempt(self, label, principal, effect, resource, cap, content=None, *,
                reasons: Optional[Set[str]] = None, expect_allow=False):
        before = self.w.observe_all()
        res = self.arm.submit(principal, effect, resource, cap, content)
        after = self.w.observe_all()
        changed = before != after
        ok, exact_step = False, False
        if expect_allow:
            tgt_b, tgt_a = before[resource], after[resource]
            exact_step = tgt_b[2] is not None and tgt_a[2] == tgt_b[2] + 1
            content_ok = (self.w.content(resource) == content) if effect == "write_file" else (not tgt_a[0])
            only_target = all(before[k] == after[k] for k in before if k != resource)
            ok = res.decision == "ALLOW" and changed and content_ok and only_target
        else:
            ok = res.decision == "BLOCK" and (reasons is None or res.reason in reasons) and not changed
        self.attempts.append({
            "scenario": self.scenario.id, "family": self.scenario.family, "label": label,
            "request": {"principal": principal, "effect": effect, "resource": resource,
                        "has_content": content is not None},
            "capability": summarize_cap(cap),
            "expected": "ALLOW" if expect_allow else "BLOCK",
            "expected_reasons": sorted(reasons) if reasons else [],
            "decision": res.decision, "reason": res.reason,
            "state_changed": changed,
            "unauthorized_execution": (not expect_allow) and changed,
            "ok": ok, "exact_version_step": exact_step, "trace": res.trace, "event_id": res.event_id, "integrity": res.integrity,
            "version_before": before.get(resource, (None, None, None))[2],
            "version_after": after.get(resource, (None, None, None))[2],
        })
        return res


@dataclass
class Scenario:
    id: str
    family: str
    title: str
    fn: Callable
    demo: Optional[str] = None


SCENARIOS: List[Scenario] = []


def scenario(family, sid, title, demo=None):
    def deco(fn):
        SCENARIOS.append(Scenario(f"{family}/{sid}", family, title, fn, demo))
        return fn
    return deco


def run_scenario(sc: Scenario, world, arm) -> List[dict]:
    ctx = Ctx(world, arm, sc)
    sc.fn(ctx)
    return ctx.attempts


A, B = "record-a", "record-b"
DEMO, OTHER, OBS = "agent-demo", "agent-other", "agent-observer"
W, D = "write_file", "delete_file"


# ---------------------------------------------------------------- F01 utility
@scenario("F01", "authorized-write", "Authorized write", demo="authorized-write")
def _(c):
    c.attempt("valid write", DEMO, W, A, c.w.issue(), "authorized-1", expect_allow=True)


@scenario("F01", "authorized-delete", "Authorized delete")
def _(c):
    c.attempt("valid delete", DEMO, D, A, c.w.issue(effect=D), None, expect_allow=True)


@scenario("F01", "multi-use-write", "Authorized write with a non-single-use capability")
def _(c):
    c.attempt("valid write", DEMO, W, A, c.w.issue(one_shot=False), "authorized-2", expect_allow=True)


@scenario("F01", "recreate-after-delete", "Re-create after delete")
def _(c):
    c.setup(DEMO, D, A, c.w.issue(effect=D))
    c.attempt("valid re-create", DEMO, W, A, c.w.issue(), "recreated", expect_allow=True)


@scenario("F01", "sequential-20", "Twenty sequential authorized writes")
def _(c):
    for i in range(20):
        c.attempt(f"write {i + 1}/20", DEMO, W, A, c.w.issue(), f"seq-{i + 1}", expect_allow=True)


# ------------------------------------------------------------ F02 missing cap
for _sid, _val in (("none", None), ("empty-string", ""), ("empty-object", {})):
    @scenario("F02", _sid, f"No capability supplied ({_sid})")
    def _(c, _val=_val):
        c.attempt("write without capability", DEMO, W, A, _val, "evil", reasons={R.MISSING_CAPABILITY})


@scenario("F02", "none-delete", "Delete without any capability")
def _(c):
    c.attempt("delete without capability", DEMO, D, A, None, reasons={R.MISSING_CAPABILITY})


# ------------------------------------------------------------------ F03 expiry
@scenario("F03", "expired-1s", "Capability expired one second ago", demo="expired-capability")
def _(c):
    now = c.w.clock.now()
    cap = c.w.issue(issued_at=now - 100, expires_at=now - 1)
    c.attempt("expired write", DEMO, W, A, cap, "evil", reasons={R.EXPIRED})


@scenario("F03", "expires-exactly-now", "Capability whose expiry equals now (boundary)")
def _(c):
    now = c.w.clock.now()
    c.attempt("boundary write", DEMO, W, A, c.w.issue(issued_at=now - 10, expires_at=now), "evil", reasons={R.EXPIRED})


@scenario("F03", "long-expired", "Capability expired long ago")
def _(c):
    now = c.w.clock.now()
    c.attempt("stale write", DEMO, W, A, c.w.issue(issued_at=now - 10**6, expires_at=now - 10**6 + 300), "evil", reasons={R.EXPIRED})


@scenario("F03", "not-yet-valid", "Capability issued in the future")
def _(c):
    now = c.w.clock.now()
    c.attempt("early write", DEMO, W, A, c.w.issue(issued_at=now + 1000, expires_at=now + 2000), "evil", reasons={R.NOT_YET_VALID})


@scenario("F03", "expires-after-clock-advance", "Capability expires while held")
def _(c):
    cap = c.w.issue(ttl=60)
    c.w.clock.advance(61)
    c.attempt("late write", DEMO, W, A, cap, "evil", reasons={R.EXPIRED})


# ------------------------------------------------------------------ F04 revoked
@scenario("F04", "revoked-by-id", "Capability revoked by id", demo="revoked-capability")
def _(c):
    cap = c.w.issue()
    c.w.revocations.revoke(cap.capability_id)
    c.attempt("revoked write", DEMO, W, A, cap, "evil", reasons={R.REVOKED})


@scenario("F04", "revoked-by-epoch", "Capability invalidated by epoch bump")
def _(c):
    cap = c.w.issue()
    c.w.revocations.bump_epoch()
    c.attempt("pre-epoch write", DEMO, W, A, cap, "evil", reasons={R.REVOKED})


@scenario("F04", "revoked-delete", "Revoked delete capability")
def _(c):
    cap = c.w.issue(effect=D)
    c.w.revocations.revoke(cap.capability_id)
    c.attempt("revoked delete", DEMO, D, A, cap, None, reasons={R.REVOKED})


# ------------------------------------------------- F05 principal substitution
@scenario("F05", "other-principal-write", "Capability for agent-demo used by agent-other", demo="principal-mismatch")
def _(c):
    c.attempt("substituted write", OTHER, W, A, c.w.issue(principal=DEMO), "evil", reasons={R.PRINCIPAL_MISMATCH})


@scenario("F05", "observer-delete", "Capability for agent-demo used by agent-observer to delete")
def _(c):
    c.attempt("substituted delete", OBS, D, A, c.w.issue(principal=DEMO, effect=D), None, reasons={R.PRINCIPAL_MISMATCH})


@scenario("F05", "undeclared-principal", "Capability presented by an undeclared principal")
def _(c):
    c.attempt("undeclared principal", "agent-intruder", W, A, c.w.issue(principal=DEMO), "evil", reasons={R.UNKNOWN_PRINCIPAL})


# ------------------------------------------------- F06 resource substitution
@scenario("F06", "a-to-b-write", "Capability for record-a used on record-b", demo="resource-mismatch")
def _(c):
    c.attempt("substituted resource", DEMO, W, B, c.w.issue(resource=A), "evil", reasons={R.RESOURCE_MISMATCH})


@scenario("F06", "a-to-b-delete", "Delete capability for record-a used on record-b")
def _(c):
    c.attempt("substituted resource", DEMO, D, B, c.w.issue(resource=A, effect=D), None, reasons={R.RESOURCE_MISMATCH})


# --------------------------------------------------- F07 effect substitution
@scenario("F07", "write-cap-used-to-delete", "Write capability used to delete", demo="effect-mismatch")
def _(c):
    c.attempt("substituted effect", DEMO, D, A, c.w.issue(effect=W), None, reasons={R.EFFECT_MISMATCH})


@scenario("F07", "delete-cap-used-to-write", "Delete capability used to write")
def _(c):
    c.attempt("substituted effect", DEMO, W, A, c.w.issue(effect=D), "evil", reasons={R.EFFECT_MISMATCH})


# ------------------------------------------------------------------ F08 replay
@scenario("F08", "write-replay", "Replay of a used single-use write capability", demo="replay")
def _(c):
    cap = c.w.issue()
    c.setup(DEMO, W, A, cap, "first-use")
    c.attempt("replayed write", DEMO, W, A, cap, "replayed-payload", reasons={R.REPLAY})


@scenario("F08", "replay-altered-content", "Replay with altered content")
def _(c):
    cap = c.w.issue()
    c.setup(DEMO, W, A, cap, "first-use")
    c.attempt("replayed write, new content", DEMO, W, A, cap, "attacker-content", reasons={R.REPLAY})


@scenario("F08", "delete-replay", "Replay of a used single-use delete capability")
def _(c):
    cap = c.w.issue(effect=D)
    c.setup(DEMO, D, A, cap)
    c.setup(OTHER, W, A, c.w.issue(principal=OTHER), "re-created-by-other")
    c.attempt("replayed delete", DEMO, D, A, cap, None, reasons={R.REPLAY})


# ------------------------------------------------------------- F09 stale state
@scenario("F09", "state-changed-write", "State changed between issuance and use (write)", demo="stale-state")
def _(c):
    stale = c.w.issue()
    c.setup(OTHER, W, A, c.w.issue(principal=OTHER), "legitimate-concurrent-change")
    c.attempt("stale write", DEMO, W, A, stale, "evil", reasons={R.STALE_STATE})


@scenario("F09", "state-changed-delete", "State changed between issuance and use (delete)")
def _(c):
    stale = c.w.issue(effect=D)
    c.setup(OTHER, W, A, c.w.issue(principal=OTHER), "legitimate-concurrent-change")
    c.attempt("stale delete", DEMO, D, A, stale, None, reasons={R.STALE_STATE})


@scenario("F09", "multi-use-after-use", "Multi-use capability reused after the state moved on")
def _(c):
    cap = c.w.issue(one_shot=False)
    c.setup(DEMO, W, A, cap, "first-use")
    c.attempt("second use", DEMO, W, A, cap, "second-use", reasons={R.STALE_STATE})


@scenario("F09", "write-after-delete", "Stale write after the resource was deleted")
def _(c):
    stale = c.w.issue()
    c.setup(OTHER, D, A, c.w.issue(principal=OTHER, effect=D))
    c.attempt("resurrecting write", DEMO, W, A, stale, "evil", reasons={R.STALE_STATE})


# ------------------------------------------------------------- F10 policy change
@scenario("F10", "policy-swapped-write", "Capability bound to a superseded policy (write)", demo="policy-downgrade")
def _(c):
    cap = c.w.issue()
    c.w.policy_source.replace(c.w.policy2)
    c.attempt("old-policy write", DEMO, W, A, cap, "evil", reasons={R.POLICY_MISMATCH})


@scenario("F10", "policy-swapped-delete", "Capability bound to a superseded policy (delete)")
def _(c):
    cap = c.w.issue(effect=D)
    c.w.policy_source.replace(c.w.policy2)
    c.attempt("old-policy delete", DEMO, D, A, cap, None, reasons={R.POLICY_MISMATCH})


@scenario("F10", "wrong-policy-hash", "Validly signed capability naming an unknown policy hash")
def _(c):
    c.attempt("unknown-policy write", DEMO, W, A, c.w.issue(policy_hash="0" * 64), "evil", reasons={R.POLICY_MISMATCH})


@scenario("F10", "policy-rollback", "Capability from the new policy used after rollback to the old one")
def _(c):
    c.w.policy_source.replace(c.w.policy2)
    cap = c.w.issue()
    c.w.policy_source.replace(c.w.policy)
    c.attempt("rolled-back policy write", DEMO, W, A, cap, "evil", reasons={R.POLICY_MISMATCH})


# ---------------------------------------------------------- F11 malformed cap
def _mut(c, fn):
    d = c.w.issue().to_dict()
    return fn(d)


_MALFORMED = {
    "truncated-json": lambda c: json.dumps(c.w.issue().to_dict())[:-20],
    "missing-field": lambda c: _mut(c, lambda d: (d.pop("nonce"), d)[1]),
    "extra-field": lambda c: _mut(c, lambda d: {**d, "admin": True}),
    "string-version": lambda c: _mut(c, lambda d: {**d, "resource_version": "0"}),
    "bool-as-int": lambda c: _mut(c, lambda d: {**d, "expires_at": True}),
    "list-not-object": lambda c: ["not", "a", "capability"],
    "null-required": lambda c: _mut(c, lambda d: {**d, "effect": None}),
}
for _sid, _mk in _MALFORMED.items():
    @scenario("F11", _sid, f"Malformed capability ({_sid})", demo="malformed-capability" if _sid == "truncated-json" else None)
    def _(c, _mk=_mk, _sid=_sid):
        c.attempt(f"malformed: {_sid}", DEMO, W, A, _mk(c), "evil", reasons={R.MALFORMED_CAPABILITY})


# --------------------------------------------------------------- F12 forged
@scenario("F12", "tampered-effect", "Effect field edited after signing", demo="forged-capability")
def _(c):
    d = c.w.issue(effect=W).to_dict()
    d["effect"] = D
    c.attempt("scope-broadened delete", DEMO, D, A, d, None, reasons={R.BAD_SIGNATURE})


@scenario("F12", "tampered-resource", "Resource field edited after signing")
def _(c):
    d = c.w.issue(resource=A).to_dict()
    d["resource_id"] = B
    c.attempt("redirected write", DEMO, W, B, d, "evil", reasons={R.BAD_SIGNATURE})


@scenario("F12", "tampered-expiry", "Expiry extended after signing")
def _(c):
    now = c.w.clock.now()
    d = c.w.issue(issued_at=now - 100, expires_at=now - 1).to_dict()
    d["expires_at"] = now + 10**6
    c.attempt("extended-expiry write", DEMO, W, A, d, "evil", reasons={R.BAD_SIGNATURE})


@scenario("F12", "signature-stripped", "Signature replaced by zeros")
def _(c):
    d = c.w.issue().to_dict()
    d["signature"] = "0" * 64
    c.attempt("unsigned write", DEMO, W, A, d, "evil", reasons={R.BAD_SIGNATURE})


@scenario("F12", "attacker-key", "Capability signed with an attacker-controlled key")
def _(c):
    c.attempt("self-issued write", DEMO, W, A, c.w.issue(issuer=c.w.attacker_issuer), "evil", reasons={R.BAD_SIGNATURE})


@scenario("F12", "delegation-parent", "Validly signed capability naming a parent (delegation not implemented)")
def _(c):
    c.attempt("delegated write", DEMO, W, A, c.w.issue(parent_capability_id="CAP-000001"), "evil", reasons={R.DELEGATION_UNSUPPORTED})


# ------------------------------------------------------------ F13 unsupported
@scenario("F13", "unsupported-effect", "Effect outside the profile (chmod_file)")
def _(c):
    c.attempt("chmod", DEMO, "chmod_file", A, c.w.issue(effect="chmod_file"), None, reasons={R.UNSUPPORTED_EFFECT})


@scenario("F13", "unknown-resource", "Resource not declared in the profile")
def _(c):
    c.attempt("undeclared resource", DEMO, W, "record-z", c.w.issue(), "evil", reasons={R.UNKNOWN_RESOURCE})


@scenario("F13", "write-without-content", "Write request with no content")
def _(c):
    c.attempt("no content", DEMO, W, A, c.w.issue(), None, reasons={R.MALFORMED_REQUEST})


@scenario("F13", "write-non-string-content", "Write request with non-string content")
def _(c):
    c.attempt("bytes content", DEMO, W, A, c.w.issue(), b"bytes", reasons={R.MALFORMED_REQUEST})


@scenario("F13", "delete-with-content", "Delete request carrying content")
def _(c):
    c.attempt("delete with payload", DEMO, D, A, c.w.issue(effect=D), "smuggled", reasons={R.MALFORMED_REQUEST})


# -------------------------------------------------------------- F14 UNKNOWN
@scenario("F14", "policy-unavailable-write", "Policy store unreachable (write)", demo="policy-unavailable")
def _(c):
    cap = c.w.issue()
    c.w.policy_source.available = False
    c.attempt("write, policy unavailable", DEMO, W, A, cap, "evil", reasons={R.POLICY_UNAVAILABLE})


@scenario("F14", "policy-unavailable-delete", "Policy store unreachable (delete)")
def _(c):
    cap = c.w.issue(effect=D)
    c.w.policy_source.available = False
    c.attempt("delete, policy unavailable", DEMO, D, A, cap, None, reasons={R.POLICY_UNAVAILABLE})


@scenario("F14", "revocation-unavailable", "Revocation service unreachable")
def _(c):
    cap = c.w.issue()
    if c.w.monitor is not None:
        c.w.monitor._revocations = UnavailableRevocationStore()
    c.attempt("write, revocation unavailable", DEMO, W, A, cap, "evil", reasons={R.REVOCATION_UNAVAILABLE})


@scenario("F14", "state-metadata-missing", "Resource metadata missing")
def _(c):
    cap = c.w.issue()
    c.w.resources[A].meta_path.unlink()
    c.attempt("write, no metadata", DEMO, W, A, cap, "evil", reasons={R.STATE_UNAVAILABLE})


@scenario("F14", "state-metadata-corrupt", "Resource metadata corrupted")
def _(c):
    cap = c.w.issue()
    c.w.resources[A].meta_path.write_text('{"version": "ten", "digest": 7}')
    c.attempt("write, corrupt metadata", DEMO, W, A, cap, "evil", reasons={R.STATE_UNAVAILABLE})


# ----------------------------------------------------------- F15 evidence
@scenario("F15", "witness-down-write", "Evidence witness unavailable (write)", demo="evidence-failure")
def _(c):
    cap = c.w.issue()
    c.w.evidence.available = False
    c.attempt("write, no witness", DEMO, W, A, cap, "evil", reasons={R.EVIDENCE_UNAVAILABLE})


@scenario("F15", "witness-down-delete", "Evidence witness unavailable (delete)")
def _(c):
    cap = c.w.issue(effect=D)
    c.w.evidence.available = False
    c.attempt("delete, no witness", DEMO, D, A, cap, None, reasons={R.EVIDENCE_UNAVAILABLE})


# ------------------------------------------------------------ F16 policy deny
@scenario("F16", "observer-write", "Valid capability for a principal the policy denies", demo="policy-deny")
def _(c):
    c.attempt("denied write", OBS, W, A, c.w.issue(principal=OBS), "evil", reasons={R.POLICY_DENY})


@scenario("F16", "observer-delete", "Valid delete capability for a denied principal")
def _(c):
    c.attempt("denied delete", OBS, D, A, c.w.issue(principal=OBS, effect=D), None, reasons={R.POLICY_DENY})


@scenario("F16", "default-deny", "Valid capability for a (principal, resource) pair with no rule")
def _(c):
    c.attempt("default-denied write", OTHER, W, B, c.w.issue(principal=OTHER, resource=B), "evil", reasons={R.POLICY_DENY})


# ------------------------------------------------- F17 out-of-band detection
@scenario("F17", "oob-write-detected", "File rewritten through a non-mediated channel, then a valid-looking request")
def _(c):
    cap = c.w.issue()
    c.w.resources[A].path.write_text("tampered-out-of-band")  # non-mediated channel (setup, unmeasured)
    c.attempt("request after OOB write", DEMO, W, A, cap, "evil", reasons={R.STATE_INCONSISTENT})


@scenario("F17", "oob-delete-detected", "File deleted through a non-mediated channel, then a valid-looking request")
def _(c):
    cap = c.w.issue()
    c.w.resources[A].path.unlink()
    c.attempt("request after OOB delete", DEMO, W, A, cap, "evil", reasons={R.STATE_INCONSISTENT})
