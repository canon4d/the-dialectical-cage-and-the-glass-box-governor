"""Runs the whole evaluation and returns plain dicts (no I/O decisions here)."""

from __future__ import annotations

import hashlib
import statistics
import tempfile
import time
from collections import OrderedDict
from pathlib import Path

from . import SUITE_VERSION
from .ablation import ABLATIONS, AblatedMonitor
from .arms import ArmA, ArmB, ArmC
from .bypass import probe
from .race import race
from .scenarios import FAMILIES, SCENARIOS, run_scenario
from .world import ROOT, World

ARM_CLASSES = {"A": ArmA, "B": ArmB, "C": ArmC}


def run_arm(arm_key, monitor_factory=None, **kw):
    """Run every scenario in its own fresh world. Returns the attempts list."""
    attempts = []
    for sc in SCENARIOS:
        with tempfile.TemporaryDirectory() as tmp:
            if arm_key == "C":
                w = World(tmp, **({"monitor_factory": monitor_factory, **kw} if monitor_factory else {}))
            else:
                w = World(tmp, monitor_factory=None)
            arm = ARM_CLASSES[arm_key](w)
            attempts.extend(run_scenario(sc, w, arm))
    return attempts


def _arm_summary(attempts):
    att = [a for a in attempts if a["expected"] == "BLOCK"]
    leg = [a for a in attempts if a["expected"] == "ALLOW"]
    return {
        "attack_attempts": len(att),
        "unauthorized_executions": sum(1 for a in att if a["state_changed"]),
        "attacks_accepted": sum(1 for a in att if a["decision"] == "ALLOW"),
        "attacks_blocked": sum(1 for a in att if a["decision"] == "BLOCK" and not a["state_changed"]),
        "legitimate_attempts": len(leg),
        "legitimate_completed": sum(1 for a in leg if a["ok"]),
        "false_blocks": sum(1 for a in leg if a["decision"] == "BLOCK"),
    }


def sha256_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def families_report(att_c):
    fams = OrderedDict()
    for fid, label in FAMILIES.items():
        rows = [a for a in att_c if a["family"] == fid]
        scen = [s for s in SCENARIOS if s.family == fid]
        reasons = {}
        for a in rows:
            reasons[a["reason"]] = reasons.get(a["reason"], 0) + 1
        fams[fid] = {
            "id": fid, "label": label, "scenarios": len(scen), "attempts": len(rows),
            "passed": sum(1 for a in rows if a["ok"]),
            "expected_allow": sum(1 for a in rows if a["expected"] == "ALLOW"),
            "unauthorized_executions": sum(1 for a in rows if a["unauthorized_execution"]),
            "protected_state_violations": sum(1 for a in rows if a["expected"] == "BLOCK" and a["state_changed"]),
            "reason_codes": dict(sorted(reasons.items())),
        }
    return list(fams.values())


def demonstrations(att_c, att_a, att_b):
    """Real traces for the website proof panel — copied from the run, not authored."""
    by = lambda atts: {a["scenario"]: a for a in atts}
    a_by, b_by = by(att_a), by(att_b)
    demos = []
    for sc in SCENARIOS:
        if not sc.demo:
            continue
        for a in [x for x in att_c if x["scenario"] == sc.id][:1]:
            aa, bb = a_by.get(sc.id), b_by.get(sc.id)
            demos.append({
                "id": sc.demo, "scenario": sc.id, "family": sc.family, "title": sc.title,
                "request": a["request"], "capability": a["capability"],
                "expected": a["expected"], "decision": a["decision"], "reason_code": a["reason"],
                "trace": a["trace"], "protected_state_changed": a["state_changed"],
                "version_before": a["version_before"], "version_after": a["version_after"],
                "event_id": a["event_id"], "integrity": a["integrity"],
                "baselines": {"A_executed": bool(aa and aa["state_changed"]),
                              "B_executed": bool(bb and bb["state_changed"])},
            })
    return demos


def run_evaluation(race_rounds=100, perf_n=300) -> dict:
    att_a, att_b, att_c = run_arm("A"), run_arm("B"), run_arm("C")
    arms = {k: {"label": ARM_CLASSES[k].label, **_arm_summary(v)} for k, v in (("A", att_a), ("B", att_b), ("C", att_c))}

    ablations = []
    for name, label in ABLATIONS:
        att = run_arm("C", monitor_factory=AblatedMonitor, skip=(name,))
        att_x = [a for a in att if a["expected"] == "BLOCK"]
        hit = sorted({a["family"] for a in att_x if a["state_changed"]})
        ablations.append({"removed": name, "label": label, "attack_attempts": len(att_x),
                          "unauthorized_executions": sum(1 for a in att_x if a["state_changed"]),
                          "families_exposed": hit})

    races = [
        race(race_rounds, True, "same_capability"),
        race(race_rounds, True, "competing_capabilities"),
        race(race_rounds, False, "same_capability"),
        race(race_rounds, False, "competing_capabilities"),
    ]

    # evidence quality: every attempt in Arm C produced a record; chain verifies per world
    required = {"event_id", "timestamp", "profile_id", "principal", "capability_id", "policy_hash",
                "resource_id", "resource_version", "requested_effect", "decision", "reason_code", "checks"}
    evidence = _evidence_quality(required)

    with tempfile.TemporaryDirectory() as tmp:
        pipeline = [n for n, _ in World(tmp).monitor._pipeline()] + ["execute"]

    core = {
        "pipeline": pipeline,
        "arms": arms,
        "attempts_total": len(att_c),
        "families": families_report(att_c),
        "ablations": ablations,
        "races": races,
        "evidence": evidence,
        "demonstrations": demonstrations(att_c, att_a, att_b),
    }
    return {"core": core, "attempts_c": att_c, "performance": measure_performance(perf_n),
            "bypass": probe()}


def _evidence_quality(required):
    from governor.evidence import verify_chain
    total = missing = chains_ok = chains = 0
    for sc in SCENARIOS:
        with tempfile.TemporaryDirectory() as tmp:
            w = World(tmp)
            arm = ArmC(w)
            run_scenario(sc, w, arm)
            recs = [r for r in w.evidence.records if r.get("kind") != "intent"]
            total += len(recs)
            missing += sum(1 for r in recs if not required.issubset(r.keys()))
            chains += 1
            chains_ok += 1 if verify_chain(w.evidence.records) else 0
    return {"decision_records": total, "records_missing_required_fields": missing,
            "chains_checked": chains, "chains_valid": chains_ok}


def measure_performance(n):
    """Wall-clock latency of the in-process mechanical path. NON-DETERMINISTIC;
    excluded from the reproducibility hash. Includes file I/O and fsync."""
    out = {"deterministic": False, "samples_per_path": n, "unit": "microseconds"}
    with tempfile.TemporaryDirectory() as tmp:
        w = World(tmp)
        blocked, allowed = [], []
        for i in range(n):
            t = time.perf_counter()
            w.monitor.request("agent-demo", "write_file", "record-a", None, "x")
            blocked.append((time.perf_counter() - t) * 1e6)
        for i in range(n):
            cap = w.issue()
            t = time.perf_counter()
            w.monitor.request("agent-demo", "write_file", "record-a", cap, f"v{i}")
            allowed.append((time.perf_counter() - t) * 1e6)

    def pct(xs, q):
        xs = sorted(xs)
        return round(xs[min(len(xs) - 1, int(q * len(xs)))], 1)
    out["blocked_path"] = {"p50": pct(blocked, .5), "p99": pct(blocked, .99), "mean": round(statistics.mean(blocked), 1)}
    out["allowed_path"] = {"p50": pct(allowed, .5), "p99": pct(allowed, .99), "mean": round(statistics.mean(allowed), 1)}
    return out
