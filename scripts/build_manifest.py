"""Write results/manifest.json binding the results to release/commit/hashes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, Path(__file__).resolve().parent.as_posix())
from _common import ROOT, VERSION, read_json, sha256_file


def build(doi="PENDING"):
    r = read_json("results/results.json")
    return {
        "project": "glass-box-governor",
        "version": f"v{VERSION}",
        "release_tag": r["release_tag"],
        "commit": r["commit"],
        "profile": r["profile"],
        "policy": r["policy"],
        "tests": {"suite": r["test_suite"]["attack_corpus"],
                  "suite_sha256": r["test_suite"]["attack_corpus_sha256"],
                  "results_json_sha256": sha256_file(ROOT / "results" / "results.json"),
                  "results_md_sha256": sha256_file(ROOT / "results" / "results.md"),
                  "core_sha256": r["core_sha256"]},
        "paper": {"pdf_sha256": sha256_file(ROOT / "research" / "paper.pdf"),
                  "source_sha256": sha256_file(ROOT / "research" / "paper.tex")},
        "inputs_required_to_reproduce": [
            "governor/*.py", "evaluation/*.py", "profiles/*", "tests/**", "scripts/run_release_tests.py"],
        "reproduce": "python3 scripts/run_release_tests.py && python3 scripts/verify_results.py",
        "zenodo": {"doi": doi, "record": "https://doi.org/10.5281/zenodo.21278446" if doi != "PENDING" else "PENDING"},
        "note": "doi stays PENDING until the Zenodo record is live; then run: python3 scripts/build_manifest.py --doi 10.5281/zenodo.21278446",
    }


if __name__ == "__main__":
    doi = "PENDING"
    if "--doi" in sys.argv:
        doi = sys.argv[sys.argv.index("--doi") + 1]
    m = build(doi)
    (ROOT / "results" / "manifest.json").write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    print("wrote results/manifest.json")
