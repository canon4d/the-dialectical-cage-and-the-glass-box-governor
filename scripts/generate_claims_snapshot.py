"""Render claims/CLAIMS.json to CLAIMS.md and check it against results.json."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, Path(__file__).resolve().parent.as_posix())
from _common import ROOT, read_json


def check(claims, results):
    fams = {f["id"]: f for f in results["families"]}
    problems = []
    for c in claims["claims"]:
        for fid in c.get("evidence", {}).get("families", []):
            if fid not in fams:
                problems.append(f"{c['id']}: unknown family {fid}")
            elif c["status"] == "LOCALLY_TESTED" and fams[fid]["passed"] != fams[fid]["attempts"]:
                problems.append(f"{c['id']}: family {fid} has failing attempts but claim is LOCALLY_TESTED")
        for art in c.get("evidence", {}).get("artifacts", []):
            if not (ROOT / art.split("#")[0]).exists():
                problems.append(f"{c['id']}: evidence artifact missing: {art}")
        if c["status"] not in claims["status_vocabulary"]:
            problems.append(f"{c['id']}: unknown status {c['status']}")
        if c["epistemic"] not in claims["epistemic_labels"]:
            problems.append(f"{c['id']}: unknown epistemic label")
    return problems


def render(claims):
    L = ["# Claim registry", "", "_Generated from `claims/CLAIMS.json` by `scripts/generate_claims_snapshot.py`. Do not edit by hand._", "",
         f"Release scope: {claims['release_scope']}", "", "## Status vocabulary", ""]
    for k, v in claims["status_vocabulary"].items():
        L.append(f"- **{k}** — {v}")
    L += ["", "## Epistemic labels (from the paper; not confidence scores)", ""]
    for k, v in claims["epistemic_labels"].items():
        L.append(f"- **{k}** — {v}")
    L += ["", "## Claims", "", "| ID | Status | Label | Claim | Scope |", "|---|---|---|---|---|"]
    for c in claims["claims"]:
        L.append(f"| {c['id']} | {c['status']} | {c['epistemic']} | {c['text']} | {c['scope']} |")
    L += [""]
    for c in claims["claims"]:
        L += [f"### {c['id']} — {c['status']}", "", c["text"], "",
              f"- Scope: {c['scope']}", f"- Evidence class: {c['evidence_class']}",
              f"- Assumptions: {', '.join(c['assumptions']) or '—'}"]
        ev = c.get("evidence", {})
        if ev.get("families"):
            L.append(f"- Attack families: {', '.join(ev['families'])}")
        if ev.get("artifacts"):
            L.append(f"- Artifacts: {', '.join('`' + a + '`' for a in ev['artifacts'])}")
        L.append("- Known limitations:")
        L += [f"  - {x}" for x in c["limitations"]]
        L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    claims, results = read_json("claims/CLAIMS.json"), read_json("results/results.json")
    problems = check(claims, results)
    if problems:
        print("CLAIMS CHECK FAILED"); [print(" -", p) for p in problems]; sys.exit(1)
    (ROOT / "CLAIMS.md").write_text(render(claims), encoding="utf-8")
    print("wrote CLAIMS.md (claims consistent with results.json)")
