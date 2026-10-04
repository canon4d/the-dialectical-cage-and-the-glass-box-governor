"""Concurrency (double-spend) experiments."""

from __future__ import annotations

import tempfile
import threading

from .ablation import NonAtomicMonitor
from .world import World


def _run_pair(world, calls):
    results = [None] * len(calls)
    start = threading.Barrier(len(calls))

    def worker(i):
        start.wait(timeout=10)
        results[i] = calls[i]()

    ts = [threading.Thread(target=worker, args=(i,)) for i in range(len(calls))]
    [t.start() for t in ts]
    [t.join(timeout=20) for t in ts]
    return results


def race(rounds: int = 100, atomic: bool = True, mode: str = "same_capability") -> dict:
    """mode same_capability: two threads spend ONE single-use capability.
       mode competing_capabilities: two different capabilities bound to the same version.
       Each round uses a fresh world so one corrupted round cannot contaminate the next."""
    double_spends = zero_winner = invariant_violations = 0
    reasons: dict = {}
    for i in range(rounds):
        with tempfile.TemporaryDirectory() as tmp:
            if atomic:
                w = World(tmp)
            else:
                w = World(tmp, monitor_factory=NonAtomicMonitor, gap_barrier=threading.Barrier(2))
            v0 = w.current_version("record-a")
            cap1 = w.issue()
            cap2 = cap1 if mode == "same_capability" else w.issue()
            res = _run_pair(w, [
                lambda: w.monitor.request("agent-demo", "write_file", "record-a", cap1, f"p1-{i}"),
                lambda: w.monitor.request("agent-demo", "write_file", "record-a", cap2, f"p2-{i}"),
            ])
            wins = [r for r in res if r is not None and r.committed]
            for r in res:
                if r is not None and not r.committed:
                    reasons[r.reason] = reasons.get(r.reason, 0) + 1
            double_spends += 1 if len(wins) > 1 else 0
            zero_winner += 1 if len(wins) == 0 else 0
            try:
                v1 = w.current_version("record-a")
            except Exception:  # noqa: BLE001
                v1 = -1
            # invariant: the version advanced by exactly the number of committed effects, and exactly one is allowed
            if v1 != v0 + len(wins) or len(wins) != 1:
                invariant_violations += 1
    return {"mode": mode, "atomic": atomic, "rounds": rounds,
            "double_spends": double_spends, "zero_winner_rounds": zero_winner,
            "invariant_violations": invariant_violations,
            "loser_reasons": dict(sorted(reasons.items()))}
