"""Build results/results.json and results/results.md from a real evaluation run.

Usage (normally via scripts/run_release_tests.py):
    python scripts/build_results.py --tests-total N --tests-passed N ...
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys

sys.path.insert(0, __import__("pathlib").Path(__file__).resolve().parent.as_posix())
from _common import (ROOT, VERSION, artifact_hashes, canon, environment, git_state, read_json,
                     sha256_file)

from evaluation import SUITE_VERSION
from evaluation.runner import run_evaluation
from evaluation.world import load_policy

SCHEMA_VERSION = 1


def ratio(n, d):
    return {"numerator": n, "denominator": d}


def headline(core):
    fam = {f["id"]: f for f in core["families"]}
    c = core["arms"]["C"]
    atk = c["attack_attempts"]
    races = {(r["mode"], r["atomic"]): r for r in core["races"]}

    def blocked(fid):
        f = fam[fid]
        return ratio(f["attempts"] - f["unauthorized_executions"], f["attempts"])

    atomic = [r for r in core["races"] if r["atomic"]]
    non_atomic = [r for r in core["races"] if not r["atomic"]]
    return {
        "unauthorized_protected_executions": ratio(c["unauthorized_executions"], atk),
        "protected_state_violations": ratio(sum(f["protected_state_violations"] for f in core["families"]), atk),
        "legitimate_requests_completed": ratio(c["legitimate_completed"], c["legitimate_attempts"]),
        "false_blocks": ratio(c["false_blocks"], c["legitimate_attempts"]),
        "replay_blocked": blocked("F08"),
        "stale_state_blocked": blocked("F09"),
        "principal_substitution_blocked": blocked("F05"),
        "race_double_spends_full_monitor": ratio(sum(r["double_spends"] for r in atomic), sum(r["rounds"] for r in atomic)),
        "race_double_spends_non_atomic_ablation": ratio(sum(r["double_spends"] for r in non_atomic), sum(r["rounds"] for r in non_atomic)),
        "baseline_unauthorized_unconstrained": ratio(core["arms"]["A"]["unauthorized_executions"], core["arms"]["A"]["attack_attempts"]),
        "baseline_unauthorized_containment_only": ratio(core["arms"]["B"]["unauthorized_executions"], core["arms"]["B"]["attack_attempts"]),
    }


def build(tests, release_tag="UNRELEASED", race_rounds=100, perf_n=300):
    ev = run_evaluation(race_rounds=race_rounds, perf_n=perf_n)
    core = ev["core"]
    profile = read_json("profiles/protected-file-v1.json")
    policy = load_policy()
    g = git_state()
    hashes = artifact_hashes()
    stable = {
        "schema_version": SCHEMA_VERSION,
        "project": "glass-box-governor",
        "version": VERSION,
        "profile": {"id": profile["profile_id"], "version": profile["profile_version"],
                    "sha256": hashes["profiles/protected-file-v1.json"]},
        "policy": {"version": policy.version, "sha256": policy.sha256},
        "test_suite": {"attack_corpus": SUITE_VERSION,
                       "attack_corpus_sha256": hashes["evaluation/scenarios.py"],
                       "runner": "python-unittest", **tests},
        "headline": headline(core),
        **core,
        "artifact_hashes": hashes,
        "claim_scope": {
            "complete_mediation": "NOT_ESTABLISHED",
            "kernel_assurance": "NOT_ESTABLISHED",
            "independent_review": "NOT_PERFORMED",
            "delegation": "NOT_IMPLEMENTED",
            "policy_refinement_proof": "NOT_PROVIDED",
        },
    }
    core_sha = hashlib.sha256(canon(stable)).hexdigest()
    results = {
        **stable,
        "core_sha256": core_sha,
        "release_tag": release_tag,
        "commit": g["commit"], "working_tree_dirty": g["dirty"],
        "generated_at": os.environ.get("RESULTS_TIMESTAMP") or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "environment": environment(),
        "environment_dependent": {"direct_bypass_probe": ev["bypass"]},
        "performance": ev["performance"],
        "notes": [
            "Counts are finite observations under this profile and attack corpus; they are not proof of zero future risk.",
            "performance, environment and bypass-probe values are not part of core_sha256.",
        ],
    }
    return results


def render_md(r) -> str:
    h, c = r["headline"], r["arms"]
    f = lambda x: f"{x['numerator']} / {x['denominator']}"
    L = []
    L += [f"# Results — {r['project']} v{r['version']}", "",
          f"Profile `{r['profile']['id']}` {r['profile']['version']} · policy `{r['policy']['version']}` · "
          f"attack corpus `{r['test_suite']['attack_corpus']}` · commit `{r['commit']}` · release `{r['release_tag']}`", "",
          "_Generated from `results.json`. Do not edit by hand._", "",
          "## Headline observations (full v1 governor)", "",
          f"- Unauthorized protected executions: **{f(h['unauthorized_protected_executions'])}** adversarial attempts",
          f"- Protected-state violations: **{f(h['protected_state_violations'])}**",
          f"- Legitimate requests completed: **{f(h['legitimate_requests_completed'])}** (false blocks: {f(h['false_blocks'])})",
          f"- Replay attempts blocked: {f(h['replay_blocked'])} · stale-state (TOCTOU) blocked: {f(h['stale_state_blocked'])} · principal substitution blocked: {f(h['principal_substitution_blocked'])}",
          f"- Concurrent double-spend rounds, full monitor: {f(h['race_double_spends_full_monitor'])}; non-atomic ablation: {f(h['race_double_spends_non_atomic_ablation'])}", "",
          "These are finite observations under one profile and one corpus. They are not a proof of zero future risk.", "",
          "## Arms", "", "| Arm | Attack attempts | Unauthorized executions | Legitimate completed | False blocks |", "|---|---:|---:|---:|---:|"]
    for k in "ABC":
        a = c[k]
        L.append(f"| {k} — {a['label']} | {a['attack_attempts']} | {a['unauthorized_executions']} | {a['legitimate_completed']} / {a['legitimate_attempts']} | {a['false_blocks']} |")
    L += ["", "## Attack families (Arm C)", "", "| Family | Attempts | Passed | Unauthorized executions | Reason codes observed |", "|---|---:|---:|---:|---|"]
    for fam in r["families"]:
        rc = ", ".join(f"{k}×{v}" for k, v in fam["reason_codes"].items())
        L.append(f"| {fam['id']} {fam['label']} | {fam['attempts']} | {fam['passed']} | {fam['unauthorized_executions']} | {rc} |")
    L += ["", "## Component ablations", "", "| Mechanism removed | Unauthorized executions | Attack families exposed |", "|---|---:|---|"]
    for a in r["ablations"]:
        L.append(f"| {a['label']} | {a['unauthorized_executions']} / {a['attack_attempts']} | {', '.join(a['families_exposed']) or '— (none; see note)'} |")
    L += ["", "Note: removing the single-use (replay) check alone exposes nothing because state/version binding independently blocks the replay. That redundancy is a finding, not an omission.", "",
          "## Concurrency", "", "| Variant | Mode | Rounds | Double spends | Invariant violations |", "|---|---|---:|---:|---:|"]
    for x in r["races"]:
        L.append(f"| {'full monitor (locked check+commit)' if x['atomic'] else 'non-atomic ablation (interleaving forced by barrier)'} | {x['mode']} | {x['rounds']} | {x['double_spends']} | {x['invariant_violations']} |")
    L += ["", "## Evidence", "",
          f"- Decision records emitted in the corpus run: {r['evidence']['decision_records']}; missing required fields: {r['evidence']['records_missing_required_fields']}",
          f"- Hash chains verified: {r['evidence']['chains_valid']} / {r['evidence']['chains_checked']}", "",
          "## Not established by this release", "",
          "- Complete mediation (the bypass probe shows same-uid writes are possible; they are detected afterwards, not prevented)",
          "- Kernel / OS-level assurance, machine-checked proofs, independent audit, external red team, delegation", "",
          "## Reproduce", "", "```bash", "python3 scripts/run_release_tests.py", "python3 scripts/verify_results.py", "```", "",
          f"`core_sha256`: `{r['core_sha256']}`", ""]
    return "\n".join(L)


def write(results):
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "results.json").write_text(json.dumps(results, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    (out / "results.md").write_text(render_md(results), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests-total", type=int, required=True)
    ap.add_argument("--tests-passed", type=int, required=True)
    ap.add_argument("--tests-failed", type=int, default=0)
    ap.add_argument("--release-tag", default="UNRELEASED")
    a = ap.parse_args()
    res = build({"total": a.tests_total, "passed": a.tests_passed, "failed": a.tests_failed}, a.release_tag)
    write(res)
    print("wrote results/results.json and results/results.md")
