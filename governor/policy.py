"""Policy representation, admission and evaluation.

What v1 contains (stated precisely, per the build guide):
  * a restricted, deny-by-default, exact-match rule language;
  * an *executable admission check* (``admit``) that statically validates a
    candidate policy against the Safety Profile before it can be loaded;
  * NO proof object and NO machine-checked refinement checker.

Admission is separate from evaluation: an inadmissible policy is rejected
when loaded, not "blocked at runtime".
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Mapping

from .decisions import Verdict
from .errors import PolicyError, PolicyUnavailable


def canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class Policy:
    version: str
    default: str
    rules: tuple
    sha256: str

    @staticmethod
    def from_obj(obj) -> "Policy":
        if not isinstance(obj, Mapping):
            raise PolicyError("policy must be an object")
        if set(obj.keys()) != {"policy_version", "default", "rules"}:
            raise PolicyError("policy keys must be exactly policy_version, default, rules")
        if not isinstance(obj["policy_version"], str) or not obj["policy_version"]:
            raise PolicyError("policy_version must be a non-empty string")
        if not isinstance(obj["rules"], list):
            raise PolicyError("rules must be a list")
        rules = []
        for r in obj["rules"]:
            if not isinstance(r, Mapping) or set(r.keys()) != {"principal", "effect", "resource", "decision"}:
                raise PolicyError("each rule needs exactly principal, effect, resource, decision")
            if not all(isinstance(r[k], str) for k in r):
                raise PolicyError("rule fields must be strings")
            rules.append(tuple(sorted(r.items())))
        return Policy(obj["policy_version"], obj["default"], tuple(rules), sha256_hex(canonical_json(obj)))

    @staticmethod
    def load(path) -> "Policy":
        try:
            obj = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise PolicyError(f"cannot read policy: {exc}") from exc
        return Policy.from_obj(obj)

    def evaluate(self, principal: str, effect: str, resource: str) -> Verdict:
        """DENY wins over ALLOW; no match falls to the default (DENY)."""
        matched = [dict(r)["decision"] for r in self.rules
                   if dict(r)["principal"] == principal
                   and dict(r)["effect"] == effect
                   and dict(r)["resource"] == resource]
        if "DENY" in matched:
            return Verdict.DENY
        if "ALLOW" in matched:
            return Verdict.ALLOW
        return Verdict.ALLOW if self.default == "ALLOW" else Verdict.DENY


def admit(policy: Policy, profile: Mapping) -> List[str]:
    """Static admission check. Returns a list of problems (empty = admitted)."""
    problems: List[str] = []
    principals = {p["id"] for p in profile["principals"]}
    resources = {r["id"] for r in profile["resources"]}
    effects = set(profile["effects"])
    if policy.default != "DENY":
        problems.append("default decision must be DENY (deny-by-default)")
    seen = {}
    for r in (dict(x) for x in policy.rules):
        if r["decision"] not in ("ALLOW", "DENY"):
            problems.append(f"invalid decision {r['decision']!r}")
        for k, universe in (("principal", principals), ("effect", effects), ("resource", resources)):
            if r[k] == "*" or r[k] not in universe:
                problems.append(f"rule {k} {r[k]!r} not declared in profile (wildcards forbidden)")
        key = (r["principal"], r["effect"], r["resource"])
        if key in seen and seen[key] != r["decision"]:
            problems.append(f"conflicting rules for {key}")
        seen[key] = r["decision"]
    return problems


class StaticPolicySource:
    """Holds the currently active, already-admitted policy."""

    def __init__(self, policy: Policy):
        self._policy = policy

    def get(self) -> Policy:
        if self._policy is None:
            raise PolicyUnavailable("no active policy")
        return self._policy

    def replace(self, policy: Policy) -> None:
        self._policy = policy
