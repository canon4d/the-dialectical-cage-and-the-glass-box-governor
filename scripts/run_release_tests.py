"""The one canonical command.

    python3 scripts/run_release_tests.py [--release v0.1.0] [--race-rounds 100]

Runs the unit/adversarial/integration tests, then the evaluation (3 arms,
ablations, races), then writes results/results.json, results/results.md and
results/manifest.json and verifies them. No network access is used or needed.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, Path(__file__).resolve().parent.as_posix())
from _common import ROOT, VERSION, git_state
import build_manifest
import build_results
import verify_results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", default="UNRELEASED")
    ap.add_argument("--race-rounds", type=int, default=100)
    a = ap.parse_args()

    g = git_state()
    if a.release != "UNRELEASED" and g["dirty"]:
        print("refusing to build a release with a dirty working tree")
        return 2

    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
    buf = io.StringIO()
    res = unittest.TextTestRunner(stream=buf, verbosity=0).run(suite)
    total = res.testsRun
    failed = len(res.failures) + len(res.errors)
    tests = {"total": total, "passed": total - failed - len(res.skipped), "failed": failed, "skipped": len(res.skipped)}
    if failed:
        print(buf.getvalue())
        print("TESTS FAILED — results not written")
        return 1

    results = build_results.build(tests, a.release, race_rounds=a.race_rounds)
    build_results.write(results)
    (ROOT / "results" / "manifest.json").write_text(json.dumps(build_manifest.build(), indent=2) + "\n", encoding="utf-8")

    h, arms = results["headline"], results["arms"]
    n = lambda x: f"{x['numerator']} / {x['denominator']}"
    fam = {f["id"]: f for f in results["families"]}
    print(f"""
GLASS-BOX GOVERNOR
Profile: {results['profile']['id']}   Policy: {results['policy']['version']}
Release: {results['release_tag']}   Version: v{VERSION}
Commit:  {results['commit']}

TEST SUMMARY
------------
Total tests:                  {tests['total']}
Passed:                       {tests['passed']}
Failed:                       {tests['failed']}

PROTECTED-EFFECT ASSERTIONS (Arm C: full v1 governor)
-----------------------------------------------------
Unauthorized executions:      {n(h['unauthorized_protected_executions'])}
Protected-state violations:   {n(h['protected_state_violations'])}
Legitimate completed:         {n(h['legitimate_requests_completed'])}
False blocks:                 {n(h['false_blocks'])}
Replay blocked:               {n(h['replay_blocked'])}
Stale-state (TOCTOU) blocked: {n(h['stale_state_blocked'])}
Principal substitution blocked: {n(h['principal_substitution_blocked'])}
Race double spends (full):    {n(h['race_double_spends_full_monitor'])}

BASELINES (same attacks, no governor)
-------------------------------------
A unconstrained:              {n(h['baseline_unauthorized_unconstrained'])} attacks changed protected state
B containment-only:           {n(h['baseline_unauthorized_containment_only'])} attacks changed protected state
Non-atomic ablation:          {n(h['race_double_spends_non_atomic_ablation'])} race rounds double-spent

EVIDENCE
--------
Decision records emitted:     {results['evidence']['decision_records']}
Missing required fields:      {results['evidence']['records_missing_required_fields']}
Hash chains valid:            {results['evidence']['chains_valid']} / {results['evidence']['chains_checked']}

NOT ESTABLISHED: complete mediation, kernel assurance, independent review.
REPRODUCIBILITY
---------------
Result manifest:              results/manifest.json
core_sha256:                  {results['core_sha256'][:16]}…
""")
    return verify_results.main(rerun=True)


if __name__ == "__main__":
    sys.exit(main())
