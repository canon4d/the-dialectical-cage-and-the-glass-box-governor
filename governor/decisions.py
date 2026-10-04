"""Decision vocabulary.

The monitor's *enforced* decision is two-valued (ALLOW / BLOCK). Safety state
that cannot be resolved is modelled explicitly as UNKNOWN (three-valued
``Verdict``) and mapped by the declared fail-safe rule ``UNKNOWN -> BLOCK``.
"""

from enum import Enum


class Decision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


class Verdict(str, Enum):
    """Three-valued result of one safety check."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    UNKNOWN = "UNKNOWN"


class Reason:
    """Stable, machine-readable reason codes (part of the public result schema)."""

    OK = "OK"
    MALFORMED_REQUEST = "MALFORMED_REQUEST"
    UNSUPPORTED_EFFECT = "UNSUPPORTED_EFFECT"
    UNKNOWN_RESOURCE = "UNKNOWN_RESOURCE"
    UNKNOWN_PRINCIPAL = "UNKNOWN_PRINCIPAL"
    MISSING_CAPABILITY = "MISSING_CAPABILITY"
    MALFORMED_CAPABILITY = "MALFORMED_CAPABILITY"
    DELEGATION_UNSUPPORTED = "DELEGATION_UNSUPPORTED"
    BAD_SIGNATURE = "BAD_SIGNATURE"
    PRINCIPAL_MISMATCH = "PRINCIPAL_MISMATCH"
    EFFECT_MISMATCH = "EFFECT_MISMATCH"
    RESOURCE_MISMATCH = "RESOURCE_MISMATCH"
    EXPIRED = "EXPIRED"
    NOT_YET_VALID = "NOT_YET_VALID"
    POLICY_UNAVAILABLE = "POLICY_UNAVAILABLE"
    POLICY_MISMATCH = "POLICY_MISMATCH"
    POLICY_DENY = "POLICY_DENY"
    REVOCATION_UNAVAILABLE = "REVOCATION_UNAVAILABLE"
    REVOKED = "REVOKED"
    REPLAY = "REPLAY"
    STATE_UNAVAILABLE = "STATE_UNAVAILABLE"
    STATE_INCONSISTENT = "STATE_INCONSISTENT"
    STALE_STATE = "STALE_STATE"
    EVIDENCE_UNAVAILABLE = "EVIDENCE_UNAVAILABLE"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    @classmethod
    def all(cls):
        return sorted(v for k, v in vars(cls).items() if k.isupper() and isinstance(v, str))
