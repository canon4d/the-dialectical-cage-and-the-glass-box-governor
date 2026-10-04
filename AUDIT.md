# Audit guide

**You do not need to trust the author to inspect this prototype. Start here.**

The trusted path is small: five files in `governor/` and one JSON profile. Everything in
`evaluation/`, `scripts/`, `tests/` and `web/` is untrusted tooling by design.

## The ten-step audit path

1. Read `THREAT_MODEL.md` (what is in and out of scope).
2. Read `profiles/protected-file-v1.json` and `profiles/protected-file-v1.policy.json`.
3. Read `governor/monitor.py` — the ordered check pipeline and the single lock around check + commit.
4. Read `governor/capability.py` — strict parsing, HMAC signature, field binding.
5. Read `governor/state.py` — versioned resource, digest sidecar, revocation and nonce stores.
6. Read `evaluation/scenarios.py` — 65 scenarios; each states the reason code it expects.
7. Run `python3 scripts/run_release_tests.py` (no network, standard library only).
8. Inspect `results/results.json` (machine-readable) and `results/results.md`.
9. Read `profiles/PROTECTED-FILE-V1-CHANNEL-INVENTORY.md`.
10. Read `LIMITATIONS.md`.

## What can be falsified

- "Every blocked attack leaves the protected files unchanged." The harness observes both files straight from disk (`World.observe`), not through the monitor.
- "A single-use capability cannot be spent twice." See `evaluation/race.py`.
- "UNKNOWN never becomes ALLOW." See family F14/F15.
- "Each mechanism earns its place." See the ablation table: removing a check should expose its family.

## How to confirm the protected resource really did not change

```bash
python3 - <<'PY'
from evaluation.world import World
import tempfile
with tempfile.TemporaryDirectory() as d:
    w = World(d)
    before = w.observe_all()
    w.monitor.request("agent-demo", "write_file", "record-a", None, "evil")   # no capability
    print(before == w.observe_all())                                          # True
PY
```

## How to add a new attack

1. Add a function decorated with `@scenario("F0X", "id", "title")` in `evaluation/scenarios.py`; use `c.setup(...)` for preparation and `c.attempt(..., reasons={...})` for the measured request.
2. Run `python3 -m unittest discover -s tests -t .`. A test is generated automatically.
3. Run `python3 scripts/run_release_tests.py`; the attack appears in all three arms and every ablation.
4. If it *succeeds* against Arm C, you found a bug. File it (SECURITY.md).

## Where the trust boundary begins and ends

Inside: `governor/*.py`, the profile and policy JSON, the signing key, the Python runtime.
Outside: the agent, the evaluation harness, scripts, website, documentation.
**The same-uid problem:** because the agent shares the process and uid, "outside" is a
convention in v0.1, not an enforced boundary. That is why complete mediation is reported as
not established.
