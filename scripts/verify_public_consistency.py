"""Fail if the repository, the website and the claims disagree.

Checks (each failure is listed; exit status 1 if any):
  1. one version everywhere (package, pyproject, CITATION.cff, results, manifest, web)
  2. one DOI everywhere, and the website's `doiLive` flag matches the manifest
  3. website data copies are byte-identical to the canonical files
  4. claim registry is consistent with results.json
  5. required SEO / icon / security files exist; every nav route has a page
  6. prohibited marketing phrases (the paper's "honesty ledger") do not appear
  7. numbers quoted in prose (e.g. "65 scenarios") match the corpus
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, Path(__file__).resolve().parent.as_posix())
from _common import ROOT, read_json, sha256_file
from generate_claims_snapshot import check as check_claims

FAIL: list[str] = []


def need(cond, msg):
    if not cond:
        FAIL.append(msg)


def text(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def main():
    results = read_json("results/results.json")
    manifest = read_json("results/manifest.json")
    claims = read_json("claims/CLAIMS.json")
    site_ts = text("web/lib/site.ts")

    # 1. versions
    import governor
    versions = {
        "governor.__version__": governor.__version__,
        "pyproject.toml": re.search(r'^version\s*=\s*"([^"]+)"', text("pyproject.toml"), re.M).group(1),
        "CITATION.cff": re.search(r"^version:\s*([\d.]+)", text("CITATION.cff"), re.M).group(1),
        "results.json": results["version"],
        "web/package.json": re.search(r'"version":\s*"([^"]+)"', text("web/package.json")).group(1),
        "manifest.json": manifest["version"].lstrip("v"),
        "web/content/meta.json": read_json("web/content/meta.json")["version"],
    }
    need(len(set(versions.values())) == 1, f"version mismatch: {versions}")

    # 2. DOI
    doi = re.search(r"doi:\s*'([^']+)'", site_ts).group(1)
    need(doi in text("CITATION.cff"), "DOI in web/lib/site.ts not found in CITATION.cff")
    need(doi in text(".zenodo.json"), "DOI in web/lib/site.ts not found in .zenodo.json")
    need(doi in text("README.md"), "DOI not mentioned in README.md")
    live = re.search(r"doiLive:\s*(true|false)", site_ts).group(1) == "true"
    need(live == (manifest["zenodo"]["doi"] != "PENDING"),
         f"site doiLive={live} but manifest zenodo.doi={manifest['zenodo']['doi']!r}; "
         "after the Zenodo record is live set doiLive true AND run build_manifest.py --doi")

    # 3. copies
    pairs = [("results/results.json", "web/content/results.json"), ("results/results.json", "web/public/data/results.json"),
             ("results/manifest.json", "web/content/manifest.json"), ("results/manifest.json", "web/public/data/manifest.json"),
             ("claims/CLAIMS.json", "web/content/CLAIMS.json"), ("claims/CLAIMS.json", "web/public/data/CLAIMS.json"),
             ("LIMITATIONS.md", "web/content/limitations.md"), ("research/abstract.txt", "web/content/abstract.txt"),
             ("research/paper.pdf", "web/public/paper/the-dialectical-cage-and-the-glass-box-governor.pdf"),
             ("research/paper.tex", "web/public/paper/the-dialectical-cage-and-the-glass-box-governor.tex")]
    for a, b in pairs:
        need((ROOT / b).exists() and sha256_file(ROOT / a) == sha256_file(ROOT / b),
             f"{b} differs from {a} — run: python3 scripts/sync_web_data.py")
    need(results["claim_scope"]["complete_mediation"] == "NOT_ESTABLISHED", "complete mediation must read NOT_ESTABLISHED")

    # 4. claims
    FAIL.extend(check_claims(claims, results))

    # 5. files
    required = ["web/app/robots.ts", "web/app/sitemap.ts", "web/app/manifest.ts", "web/app/llms.txt/route.ts",
                "web/public/.well-known/security.txt", "web/public/favicon.ico", "web/public/assets/apple-touch-icon.png",
                "web/public/assets/icon-maskable-512.png", "web/public/assets/og-card.png", "web/vercel.json",
                "SECURITY.md", "LIMITATIONS.md", "THREAT_MODEL.md", "AUDIT.md", "LICENSE", "CITATION.cff"]
    for f in required:
        need((ROOT / f).exists(), f"missing required file: {f}")
    for href in re.findall(r"href:\s*'/([a-z-]+)/'", site_ts):
        need((ROOT / "web" / "app" / href / "page.tsx").exists(), f"nav route /{href}/ has no page")
    sec = text("web/public/.well-known/security.txt")
    need("canon@necessaryuniverse.com" in sec and "canon@necessaryuniverse.com" in text("SECURITY.md"), "security contact mismatch")
    need("Expires:" in sec, "security.txt needs an Expires field (RFC 9116)")

    # 6. prohibited phrases (quoted only where they are explicitly marked as things not to say)
    banned = ["ai safety is solved", "guaranteed safe", "provably safe", "unbreakable", "100% secure", "fully secure",
              "complete mediation is achieved", "proves zero", "military-grade", "solves ai safety", "bulletproof",
              "tamper-proof", "legally admissible", "legally binding"]
    allow_quote = {"LIMITATIONS.md", "web/content/limitations.md", "web/app/llms.txt/route.ts", "AUDIT.md",
                   "scripts/verify_public_consistency.py", "web/public/data/CLAIMS.json"}
    scan = [p for p in list(ROOT.glob("*.md")) + list((ROOT / "web" / "app").rglob("*.ts*")) + list((ROOT / "web" / "components").rglob("*.tsx"))
            + list((ROOT / "web" / "lib").rglob("*.ts")) + list((ROOT / "docs").rglob("*.md")) + list((ROOT / "scripts").glob("*.py"))
            + list((ROOT / "governor").glob("*.py")) + list((ROOT / "claims").glob("*.json"))]
    for p in scan:
        rel = str(p.relative_to(ROOT))
        if rel in allow_quote or rel == "CLAIMS.md":
            continue
        low = p.read_text(encoding="utf-8").lower()
        for b in banned:
            need(b not in low, f"prohibited phrase {b!r} in {rel}")

    # 7. quoted numbers
    from evaluation.scenarios import FAMILIES, SCENARIOS
    n = len(SCENARIOS)
    for rel in ("AUDIT.md", "CHANGELOG.md", "README.md"):
        for m in re.finditer(r"(\d+)\s+scenarios", text(rel)):
            need(int(m.group(1)) == n, f"{rel} says {m.group(1)} scenarios; corpus has {n}")
        for m in re.finditer(r"(\d+)\s+families", text(rel)):
            need(int(m.group(1)) == len(FAMILIES), f"{rel} says {m.group(1)} families; corpus has {len(FAMILIES)}")
        for m in re.finditer(r"(\d+)\s+(?:component\s+)?ablations", text(rel)):
            need(int(m.group(1)) == len(results["ablations"]), f"{rel} says {m.group(1)} ablations; results has {len(results['ablations'])}")

    arms = results["arms"]
    readme = text("README.md")
    for key, label in (("C", "0 of 60"), ("A", f"{arms['A']['unauthorized_executions']} of 60"), ("B", f"{arms['B']['unauthorized_executions']} of 60")):
        need(arms[key]["attack_attempts"] == 60 and label in readme, f"README does not quote arm {key} result as {label!r}")
    need(arms["C"]["unauthorized_executions"] == 0, "README claims zero unauthorized executions but results.json disagrees")

    if FAIL:
        print("PUBLIC CONSISTENCY FAILED")
        for f in FAIL:
            print("  -", f)
        return 1
    print(f"PUBLIC CONSISTENCY OK — version {next(iter(versions.values()))}, {n} scenarios, DOI {doi} ({'live' if live else 'reserved'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
