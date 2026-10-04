"""Capability object, issuance and verification.

Authenticity uses HMAC-SHA256 from the Python standard library. No custom
cryptography is implemented. Because HMAC is symmetric, the verifier holds the
signing key: *monitor compromise implies capability forgery* (declared in
LIMITATIONS.md; an asymmetric scheme is a roadmap item).
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, asdict, fields
from typing import Any, Mapping, Optional

from .errors import MalformedCapability

_STR = ("capability_id", "principal_id", "effect", "resource_id", "policy_hash",
        "nonce", "issuer", "signature")
_INT = ("resource_version", "issued_at", "expires_at", "revocation_epoch")


@dataclass(frozen=True)
class Capability:
    capability_id: str
    principal_id: str
    effect: str
    resource_id: str
    resource_version: int
    policy_hash: str
    issued_at: int
    expires_at: int
    revocation_epoch: int
    nonce: str
    one_shot: bool
    issuer: str
    parent_capability_id: Optional[str]
    signature: str

    def to_dict(self) -> dict:
        return asdict(self)

    def signing_bytes(self) -> bytes:
        d = self.to_dict()
        d.pop("signature")
        return json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()

    @staticmethod
    def field_names() -> tuple:
        return tuple(f.name for f in fields(Capability))

    @staticmethod
    def from_raw(raw: Any) -> "Capability":
        """Strictly parse an untrusted value. Anything unexpected raises."""
        if isinstance(raw, Capability):
            raw = raw.to_dict()
        if isinstance(raw, (str, bytes)):
            try:
                raw = json.loads(raw)
            except (ValueError, UnicodeDecodeError) as exc:
                raise MalformedCapability("not valid JSON") from exc
        if not isinstance(raw, Mapping):
            raise MalformedCapability("capability must be an object")
        names = set(Capability.field_names())
        keys = set(raw.keys())
        if keys != names:
            missing = sorted(names - keys)
            extra = sorted(str(k) for k in keys - names)
            raise MalformedCapability(f"fields mismatch missing={missing} extra={extra}")
        for k in _STR:
            if not isinstance(raw[k], str) or not raw[k]:
                raise MalformedCapability(f"{k} must be a non-empty string")
        for k in _INT:
            v = raw[k]
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise MalformedCapability(f"{k} must be a non-negative integer")
        if not isinstance(raw["one_shot"], bool):
            raise MalformedCapability("one_shot must be boolean")
        p = raw["parent_capability_id"]
        if p is not None and not isinstance(p, str):
            raise MalformedCapability("parent_capability_id must be string or null")
        return Capability(**{n: raw[n] for n in Capability.field_names()})


def _mac(key: bytes, data: bytes) -> str:
    return hmac.new(key, data, hashlib.sha256).hexdigest()


class CapabilityIssuer:
    """Issues signed capabilities. Lives on the trusted side only."""

    def __init__(self, key: bytes, issuer_id: str, clock, ids):
        if not isinstance(key, (bytes, bytearray)) or len(key) < 16:
            raise ValueError("signing key must be at least 16 bytes")
        self._key = bytes(key)
        self.issuer_id = issuer_id
        self._clock = clock
        self._ids = ids

    def issue(self, *, principal_id: str, effect: str, resource_id: str,
              resource_version: int, policy_hash: str, ttl: int = 300,
              revocation_epoch: int = 0, one_shot: bool = True,
              issued_at: Optional[int] = None, expires_at: Optional[int] = None,
              parent_capability_id: Optional[str] = None) -> Capability:
        now = self._clock.now() if issued_at is None else issued_at
        exp = now + ttl if expires_at is None else expires_at
        unsigned = Capability(
            capability_id=self._ids.next("CAP"), principal_id=principal_id,
            effect=effect, resource_id=resource_id, resource_version=resource_version,
            policy_hash=policy_hash, issued_at=now, expires_at=exp,
            revocation_epoch=revocation_epoch, nonce=self._ids.next("NONCE"),
            one_shot=one_shot, issuer=self.issuer_id,
            parent_capability_id=parent_capability_id, signature="-")
        return Capability(**{**unsigned.to_dict(), "signature": _mac(self._key, unsigned.signing_bytes())})


class CapabilityVerifier:
    def __init__(self, key: bytes, issuer_id: str):
        self._key = bytes(key)
        self.issuer_id = issuer_id

    def authentic(self, cap: Capability) -> bool:
        return cap.issuer == self.issuer_id and hmac.compare_digest(
            _mac(self._key, cap.signing_bytes()), cap.signature)
