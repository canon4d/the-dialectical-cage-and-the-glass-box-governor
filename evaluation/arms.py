"""The three experimental arms (build guide section 16).

Arm A  unconstrained      the agent can directly mutate the resources.
Arm B  containment-only   a *model* of credential-restricted containment defined
                          here: presenting any non-empty credential permits a
                          mutation of the confined resources; no per-request
                          binding of principal, effect, version, expiry,
                          replay, policy or revocation. It is a deliberately
                          simple baseline, NOT a claim about any real product.
Arm C  full governor      the reference monitor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Result:
    decision: str
    reason: str
    trace: List[dict] = field(default_factory=list)
    event_id: Optional[str] = None
    integrity: Optional[str] = None
    committed: bool = False


def _raw_apply(world, effect, resource, content) -> bool:
    res = world.resources.get(resource)
    if res is None or effect not in ("write_file", "delete_file"):
        return False
    if effect == "write_file":
        res.path.parent.mkdir(parents=True, exist_ok=True)
        res.path.write_text(content if isinstance(content, str) else "", encoding="utf-8")
    else:
        try:
            res.path.unlink()
        except FileNotFoundError:
            pass
    return True


class ArmA:
    name = "A"
    label = "Unconstrained baseline"

    def __init__(self, world):
        self.w = world

    def submit(self, principal, effect, resource, cap, content=None) -> Result:
        ok = _raw_apply(self.w, effect, resource, content)
        return Result("ALLOW" if ok else "BLOCK", "OK" if ok else "UNSUPPORTED", committed=ok)


class ArmB:
    name = "B"
    label = "Containment only"

    def __init__(self, world):
        self.w = world

    def submit(self, principal, effect, resource, cap, content=None) -> Result:
        has_credential = cap is not None and not (isinstance(cap, (str, bytes, dict, list)) and len(cap) == 0)
        if not has_credential:
            return Result("BLOCK", "NO_CREDENTIAL")
        ok = _raw_apply(self.w, effect, resource, content)
        return Result("ALLOW" if ok else "BLOCK", "OK" if ok else "OUTSIDE_CONFINEMENT", committed=ok)


class ArmC:
    name = "C"
    label = "Full v1 governor"

    def __init__(self, world):
        self.w = world

    def submit(self, principal, effect, resource, cap, content=None) -> Result:
        o = self.w.monitor.request(principal, effect, resource, cap, content)
        return Result(o.decision.value, o.reason, o.trace, o.event_id, o.integrity, o.committed)
