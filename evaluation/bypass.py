"""Direct-bypass probe (build guide 12.14 / 13).

This does NOT claim to prove containment. It records, honestly and with the
effective uid, what a same-process / same-uid actor can do to the protected
file without going through the monitor. The classification is fixed:
complete mediation is NOT ESTABLISHED for v0.1 (in-process, no privilege
separation). Observed outcomes depend on the OS user and are therefore kept
out of the deterministic result hash.
"""

from __future__ import annotations

import os
import stat
import tempfile

from .world import World


def _try_write(path, text):
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return "SUCCEEDED"
    except OSError as exc:
        return f"DENIED ({type(exc).__name__})"


def probe() -> dict:
    out = {"effective_uid": os.geteuid() if hasattr(os, "geteuid") else None}
    with tempfile.TemporaryDirectory() as tmp:
        w = World(tmp)
        p = w.resources["record-a"].path
        out["direct_write_default_permissions"] = _try_write(p, "bypass-1")
        os.chmod(p, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        out["direct_write_after_read_only_mode"] = _try_write(p, "bypass-2")
        try:
            os.chmod(p, stat.S_IRUSR | stat.S_IWUSR)
            out["chmod_then_write_by_same_uid"] = _try_write(p, "bypass-3")
        except OSError as exc:
            out["chmod_then_write_by_same_uid"] = f"DENIED ({type(exc).__name__})"
        cap = w.issue()
        o = w.monitor.request("agent-demo", "write_file", "record-a", cap, "after-bypass")
        out["mediated_request_after_bypass"] = {"decision": o.decision.value, "reason": o.reason}
    out["classification"] = "COMPLETE_MEDIATION_NOT_ESTABLISHED"
    out["explanation"] = ("v0.1 runs the monitor in the same process and uid as the code it mediates. "
                          "Non-mediated writes are possible; they are detected on the next mediated request "
                          "(STATE_INCONSISTENT) but not prevented.")
    return out
