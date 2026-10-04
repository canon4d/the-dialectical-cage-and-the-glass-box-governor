"""Component ablations and a deliberately non-atomic variant (UNTRUSTED code).

The trusted ReferenceMonitor has no off-switches. Ablations are built by
subclassing here, so removing a check can never happen by configuration in
production code.
"""

from __future__ import annotations

import threading

from governor.decisions import Reason, Verdict
from governor.errors import StateInconsistent, StateUnavailable
from governor.monitor import ReferenceMonitor, _Block


class AblatedMonitor(ReferenceMonitor):
    def __init__(self, *args, skip=(), **kwargs):
        super().__init__(*args, **kwargs)
        self._skip = set(skip)

    def _pipeline(self):
        out = []
        for name, fn in super()._pipeline():
            if name not in self._skip:
                out.append((name, fn))
            elif name == "state_current":
                # state must still be read so the commit can proceed; only the version comparison is removed
                out.append((name, self._state_without_version_check))
        return out

    def _state_without_version_check(self, c):
        try:
            c["state"] = self._resources[c["resource"]].snapshot()
        except StateInconsistent:
            raise _Block(Reason.STATE_INCONSISTENT, Verdict.UNKNOWN)
        except StateUnavailable:
            raise _Block(Reason.STATE_UNAVAILABLE, Verdict.UNKNOWN)


class NonAtomicMonitor(ReferenceMonitor):
    """Same checks, but no lock around check+commit and a hook between them.
    Used to show that atomic revalidation (C6) is what prevents double spend."""

    def __init__(self, *args, gap_barrier=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._gap = gap_barrier

    def request(self, principal_id, effect, resource_id, capability=None, content=None):
        return self._request_locked(principal_id, effect, resource_id, capability, content)

    def _commit(self, ctx, event_id, trace):
        if self._gap is not None:
            try:
                self._gap.wait(timeout=5)
            except threading.BrokenBarrierError:
                pass
        return super()._commit(ctx, event_id, trace)


ABLATIONS = [
    ("signature_authentic", "No signature verification"),
    ("principal_binding", "No principal binding"),
    ("effect_binding", "No effect binding"),
    ("resource_binding", "No resource binding"),
    ("validity_window", "No expiry check"),
    ("policy_binding", "No policy-hash binding"),
    ("revocation_current", "No revocation check"),
    ("policy_decision", "No policy decision"),
    ("replay_protection", "No single-use (replay) check"),
    ("state_current", "No state/version revalidation"),
    ("evidence_witness", "No evidence-witness requirement"),
]
