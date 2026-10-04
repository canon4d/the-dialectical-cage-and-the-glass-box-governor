"""Hash-chained evidence records.

Each record's ``integrity`` is SHA-256 over (previous integrity || canonical
record body). This detects accidental or naive tampering of a stored log; it
is NOT a claim of legal non-repudiation and NOT a claim that evidence coverage
is complete (the paper treats alternate-path detection as a separate question).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import List, Optional

from .errors import EvidenceUnavailable

GENESIS = "0" * 64


def _body_bytes(rec: dict) -> bytes:
    body = {k: v for k, v in rec.items() if k != "integrity"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


class EvidenceWriter:
    def __init__(self, path: Optional[Path] = None, ids=None):
        self.records: List[dict] = []
        self._path = Path(path) if path else None
        self._ids = ids
        self._n = 0
        self._prev = GENESIS
        self.available = True

    def next_event_id(self) -> str:
        self._n += 1
        return f"EVT-{self._n:06d}"

    def record(self, body: dict) -> dict:
        if not self.available:
            raise EvidenceUnavailable("evidence witness unavailable")
        rec = dict(body)
        rec["prev"] = self._prev
        rec["integrity"] = hashlib.sha256((self._prev + _body_bytes(rec).decode()).encode()).hexdigest()
        self._prev = rec["integrity"]
        self.records.append(rec)
        if self._path is not None:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")
        return rec


def verify_chain(records: List[dict]) -> bool:
    prev = GENESIS
    for rec in records:
        if rec.get("prev") != prev:
            return False
        want = hashlib.sha256((prev + _body_bytes(rec).decode()).encode()).hexdigest()
        if rec.get("integrity") != want:
            return False
        prev = rec["integrity"]
    return True
