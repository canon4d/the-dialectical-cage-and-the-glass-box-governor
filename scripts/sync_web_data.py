"""Copy canonical artifacts into web/ so the website is self-contained and the
Vercel build never depends on files outside web/.

The website is a presentation layer: it reads these copies at build time and
never computes a result. scripts/verify_public_consistency.py fails if any copy
differs from its canonical source."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, Path(__file__).resolve().parent.as_posix())
from _common import ROOT, read_json

WEB = ROOT / "web"
COPIES = [
    ("results/results.json", "web/content/results.json"),
    ("results/results.json", "web/public/data/results.json"),
    ("results/manifest.json", "web/content/manifest.json"),
    ("results/manifest.json", "web/public/data/manifest.json"),
    ("claims/CLAIMS.json", "web/content/CLAIMS.json"),
    ("claims/CLAIMS.json", "web/public/data/CLAIMS.json"),
    ("LIMITATIONS.md", "web/content/limitations.md"),
    ("research/abstract.txt", "web/content/abstract.txt"),
    ("research/paper.pdf", "web/public/paper/the-dialectical-cage-and-the-glass-box-governor.pdf"),
    ("research/paper.tex", "web/public/paper/the-dialectical-cage-and-the-glass-box-governor.tex"),
]


def main():
    for src, dst in COPIES:
        (ROOT / dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / src, ROOT / dst)
    r = read_json("results/results.json")
    m = read_json("results/manifest.json")
    meta = {"version": r["version"], "release_tag": r["release_tag"], "commit": r["commit"],
            "lastmod": r["generated_at"][:10], "doi": m["zenodo"]["doi"]}
    (WEB / "content" / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"synced {len(COPIES)} files + web/content/meta.json")


if __name__ == "__main__":
    main()
