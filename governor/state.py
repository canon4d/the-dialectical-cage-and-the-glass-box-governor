"""Protected resource state, revocation and single-use nonce stores.

A protected resource is a file plus a sidecar ``<name>.version`` holding
``{"version": n, "digest": sha256(content) | "ABSENT"}``. The sidecar is what
makes state revalidation (TOCTOU defence) and out-of-band-change detection
possible: if the content digest and the recorded digest disagree the resource
state is INCONSISTENT and the monitor blocks (fail-closed).
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path

from .errors import (RevocationUnavailable, StateInconsistent, StateUnavailable)

ABSENT = "ABSENT"


@dataclass(frozen=True)
class ResourceState:
    exists: bool
    version: int
    digest: str


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


class ProtectedResource:
    def __init__(self, resource_id: str, path):
        self.resource_id = resource_id
        self.path = Path(path)
        self.meta_path = self.path.with_name(self.path.name + ".version")

    # -- setup -----------------------------------------------------------------
    def initialize(self, content: str | None) -> ResourceState:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if content is None:
            if self.path.exists():
                self.path.unlink()
            digest = ABSENT
        else:
            _atomic_write(self.path, content.encode("utf-8"))
            digest = _digest(content.encode("utf-8"))
        _atomic_write(self.meta_path, json.dumps({"version": 0, "digest": digest}).encode())
        return ResourceState(content is not None, 0, digest)

    # -- observation -------------------------------------------------------------
    def snapshot(self) -> ResourceState:
        try:
            meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
            version, recorded = meta["version"], meta["digest"]
            if isinstance(version, bool) or not isinstance(version, int) or version < 0 \
                    or not isinstance(recorded, str):
                raise ValueError("bad metadata types")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise StateUnavailable(f"resource metadata unavailable: {exc}") from exc
        try:
            actual = _digest(self.path.read_bytes())
            exists = True
        except FileNotFoundError:
            actual, exists = ABSENT, False
        except OSError as exc:
            raise StateUnavailable(f"resource unreadable: {exc}") from exc
        if actual != recorded:
            raise StateInconsistent("content digest differs from recorded digest")
        return ResourceState(exists, version, actual)

    # -- mutation (called only by the executor, under the monitor lock) -----------
    def commit(self, effect: str, content: str | None, current: ResourceState) -> ResourceState:
        if effect == "write_file":
            data = (content or "").encode("utf-8")
            _atomic_write(self.path, data)
            digest, exists = _digest(data), True
        elif effect == "delete_file":
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            digest, exists = ABSENT, False
        else:  # pragma: no cover - the monitor never forwards other effects
            raise ValueError(f"unsupported effect {effect}")
        new = ResourceState(exists, current.version + 1, digest)
        _atomic_write(self.meta_path, json.dumps({"version": new.version, "digest": new.digest}).encode())
        return new


class RevocationStore:
    """Revocation by id and by epoch (``cap.revocation_epoch < epoch`` => revoked)."""

    def __init__(self):
        self.epoch = 0
        self._revoked: set[str] = set()
        self._lock = threading.Lock()

    def revoke(self, capability_id: str) -> None:
        with self._lock:
            self._revoked.add(capability_id)

    def bump_epoch(self) -> int:
        with self._lock:
            self.epoch += 1
            return self.epoch

    def is_revoked(self, capability_id: str, cap_epoch: int) -> bool:
        with self._lock:
            return capability_id in self._revoked or cap_epoch < self.epoch


class UnavailableRevocationStore(RevocationStore):
    """Test double: models an unreachable revocation service."""

    def is_revoked(self, capability_id: str, cap_epoch: int) -> bool:
        raise RevocationUnavailable("revocation service unreachable")


class NonceStore:
    def __init__(self):
        self._used: set[str] = set()

    def used(self, nonce: str) -> bool:
        return nonce in self._used

    def consume(self, nonce: str) -> bool:
        if nonce in self._used:
            return False
        self._used.add(nonce)
        return True
