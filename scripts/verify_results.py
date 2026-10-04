"""Verify that committed results are well-formed, internally consistent, bound
to the current source files, and reproducible.

Checks
  1. results.json matches the schema below (hand-rolled, stdlib only)
  2. every artifact hash recorded in results.json matches the file on disk
  3. manifest.json matches results.json / results.md / paper hashes
  4. headline numbers are re-derived from the family table (no hand edits)
  5. (default) the deterministic core is re-computed and must reproduce core_sha256
     use --no-rerun to skip step 5
Exit status is non-zero on any failure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, Path(__file__).resolve().parent.as_posix())
from _common import ROOT, canon, read_json, sha256_file

import hashlib

FAIL = []


def check(cond, msg):
    if not cond:
        FAIL.append(msg)
    return cond


REQUIRED_TOP = {
    "schema_version": int, "project": str, "version": str, "profile": dict, "policy": dict,
    "test_suite": dict, "headline": dict, "arms": dict, "families": list, "ablations": list,
    "races": list, "evidence": dict, "demonstrations": list, "artifact_hashes": dict,
    "claim_scope": dict, "core_sha256": str, "release_tag": str, "commit": str,
    "generated_at": str, "environment": dict, "performance": dict,
}


def validate_schema(r):
    for k, t in REQUIRED_TOP.items():
        check(k in r and isinstance(r[k], t), f"schema: {k} missing or not {t.__name__}")
    for k in ("A", "B", "C"):
        a = r.get("arms", {}).get(k, {})
        for f in ("attack_attempts", "unauthorized_executions", "legitimate_attempts", "legitimate_completed", "false_blocks"):
            check(isinstance(a.get(f), int), f"schema: arms.{k}.{f}")
    for fam in r.get("families", []):
        for f in ("id", "attempts", "passed", "unauthorized_executions", "reason_codes"):
            check(f in fam, f"schema: family {fam.get('id')} missing {f}")
    for d in r.get("demonstrations", []):
        for f in ("id", "request", "decision", "reason_code", "trace", "protected_state_changed", "event_id"):
            check(f in d, f"schema: demonstration {d.get('id')} missing {f}")


def main(rerun=True):
    r = read_json("results/results.json")
    validate_schema(r)
    if FAIL:
        return report()

    # 2. artifact hashes
    for rel, h in r["artifact_hashes"].items():
        p = ROOT / rel
        check(p.exists() and sha256_file(p) == h, f"artifact hash mismatch: {rel}")

    # 3. manifest
    m = read_json("results/manifest.json")
    check(m["tests"]["results_json_sha256"] == sha256_file(ROOT / "results" / "results.json"), "manifest: results.json hash")
    check(m["tests"]["results_md_sha256"] == sha256_file(ROOT / "results" / "results.md"), "manifest: results.md hash")
    check(m["tests"]["core_sha256"] == r["core_sha256"], "manifest: core hash")
    check(m["paper"]["pdf_sha256"] == sha256_file(ROOT / "research" / "paper.pdf"), "manifest: paper.pdf hash")
    check(m["paper"]["source_sha256"] == sha256_file(ROOT / "research" / "paper.tex"), "manifest: paper.tex hash")
    check(m["commit"] == r["commit"] and m["release_tag"] == r["release_tag"], "manifest: commit/tag")

    # 4. internal arithmetic
    c = r["arms"]["C"]
    check(sum(f["unauthorized_executions"] for f in r["families"]) == c["unauthorized_executions"], "families vs arm C unauthorized")
    check(sum(f["attempts"] for f in r["families"]) == c["attack_attempts"] + c["legitimate_attempts"], "families vs arm C attempt totals")
    h = r["headline"]["unauthorized_protected_executions"]
    check(h == {"numerator": c["unauthorized_executions"], "denominator": c["attack_attempts"]}, "headline unauthorized ratio")
    check(r["test_suite"]["failed"] == 0 and r["test_suite"]["passed"] == r["test_suite"]["total"], "test suite not fully passing")
    check(r["claim_scope"]["complete_mediation"] == "NOT_ESTABLISHED", "claim_scope.complete_mediation must stay NOT_ESTABLISHED for v0.1")

    # 5. recompute deterministic core
    if rerun:
        stable = {k: v for k, v in r.items() if k not in (
            "core_sha256", "release_tag", "commit", "working_tree_dirty", "generated_at", "environment",
            "environment_dependent", "performance", "notes")}
        check(hashlib.sha256(canon(stable)).hexdigest() == r["core_sha256"], "core_sha256 does not match stored content")
        from build_results import build  # noqa: E402
        again = build({k: r["test_suite"][k] for k in ("total", "passed", "failed", "skipped") if k in r["test_suite"]}, r["release_tag"],
                      race_rounds=r["races"][0]["rounds"], perf_n=5)
        check(again["core_sha256"] == r["core_sha256"],
              "re-running the evaluation did not reproduce core_sha256 (sources, corpus or behaviour changed)")
    return report()


def report():
    if FAIL:
        print("VERIFY FAILED")
        for f in FAIL:
            print("  -", f)
        return 1
    print("VERIFY OK — results are well-formed, bound to current sources, and reproducible")
    return 0


if __name__ == "__main__":
    sys.exit(main(rerun="--no-rerun" not in sys.argv))
