"""Shared helpers for the release scripts (untrusted tooling)."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VERSION = "0.1.0"


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def git(*args):
    try:
        out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def git_state():
    sha = git("rev-parse", "HEAD")
    if not sha:
        return {"commit": "UNCOMMITTED", "dirty": None}
    # generated outputs are excluded: they change every time the release command runs
    status = git("status", "--porcelain", "--untracked-files=no") or ""
    generated = ("results/", "web/", "CLAIMS.md")
    dirty = any(not line[3:].startswith(generated) for line in status.splitlines() if line.strip())
    return {"commit": sha, "dirty": dirty}


def environment():
    return {"python": platform.python_version(), "implementation": platform.python_implementation(),
            "platform": platform.system(), "machine": platform.machine()}


def artifact_hashes():
    files = sorted(list((ROOT / "governor").glob("*.py")) + list((ROOT / "evaluation").glob("*.py")))
    files += [ROOT / "profiles" / n for n in ("protected-file-v1.json", "protected-file-v1.policy.json",
                                               "protected-file-v1.policy.2.json",
                                               "PROTECTED-FILE-V1-CHANNEL-INVENTORY.md")]
    files += [ROOT / "claims" / "CLAIMS.json", ROOT / "research" / "paper.pdf", ROOT / "research" / "paper.tex"]
    return {str(f.relative_to(ROOT)): sha256_file(f) for f in files if f.exists()}


def read_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))
