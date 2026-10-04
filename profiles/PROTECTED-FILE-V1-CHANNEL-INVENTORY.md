# Protected File v1 — channel inventory

Complete mediation is **deployment-specific**. This release demonstrates it only
where the inventory and enforcement boundary justify the statement. For v0.1 the
honest result is: **not established**.

Legend — *Exists*: the channel exists in the v0.1 setup. *In boundary*: the
profile claims to cover it. *Mediated*: it traverses the reference monitor.
*Evidence*: what supports the entry. *Status*: OPEN, RESIDUAL, or TESTED.

| # | Channel to the protected effect | Exists | In boundary | Mediated | Evidence | Status |
|---|---|---|---|---|---|---|
| 1 | `ReferenceMonitor.request()` (the intended path) | yes | yes | yes | `tests/adversarial/`, `results/results.json` | TESTED (corpus-limited) |
| 2 | Direct file-system write/delete/chmod by code in the same process or uid | yes | **no** (nothing prevents it) | no | `evaluation/bypass.py` probe; Arm A/B baselines | OPEN — roadmap v0.2 |
| 3 | Subprocess / helper binary run as the same uid | yes (possible) | no | no | not tested | OPEN |
| 4 | Shell command (`rm`, `cp`, `echo >`) | yes (possible) | no | no | not tested | OPEN |
| 5 | Plugin / extension execution inside the agent process | n/a in v0.1 harness | no | no | none | OPEN |
| 6 | Scheduler / cron / background worker | n/a in v0.1 harness | no | no | none | OPEN |
| 7 | Webhook / network service proxy | n/a (no network in v0.1) | no | no | none | RESIDUAL for v0.1 |
| 8 | Local IPC / sockets | n/a | no | no | none | OPEN |
| 9 | Browser automation | n/a | no | no | none | RESIDUAL for v0.1 |
| 10 | Administrative operator path (root, owner) | yes | **no, by declaration** | no | `THREAT_MODEL.md` (owner is in the threat model but not constrained by v0.1) | RESIDUAL |
| 11 | Recovery / restore from backup | yes (outside the repo) | no | no | none | OPEN |
| 12 | Test-harness direct-write path (`evaluation/`) | yes | no (untrusted tooling) | no | harness code review | RESIDUAL — test scaffolding only |
| 13 | Version-sidecar tampering together with a matching content change | yes | no | no | `CLM-009` limitation | OPEN |
| 14 | Physical access, covert channels | yes | no | no | none | RESIDUAL (paper 10.15) |

## What the v0.1 bypass probe shows

`evaluation/bypass.py` records what a same-uid actor can do without the monitor
and then shows the monitor *detecting* the change on the next mediated request
(`STATE_INCONSISTENT`). Detection is not prevention. Outcomes depend on the
operating-system user (for example, root ignores read-only file modes), so they
are stored under `environment_dependent` and excluded from the reproducibility
hash.

## Closing the gap (roadmap v0.2)

Run the monitor as a separate OS principal that is the only writer of the
protected directory; give the agent process no write permission; add negative
tests for each row above that the new boundary claims to cover.
