# Limitations — the honesty ledger

Written to be specific enough that an outside engineer can design a test for each
item. It must stay synchronised with the implementation (`scripts/verify_public_consistency.py`
checks the headline items).

## What v0.1 does not establish

1. **Not a universal AI-safety guarantee.** The security objective is limited to the declared profile `protected-file-v1` (paper §1.4).
2. **Complete mediation is not established.** The monitor runs in the same process and uid as the code it mediates. Direct writes succeed and are only *detected* on the next mediated request. See `profiles/PROTECTED-FILE-V1-CHANNEL-INVENTORY.md` and the bypass probe. (Paper condition C1.)
3. **No kernel or OS-level assurance.** No privilege separation, no sandboxing, no formal verification of the monitor. (C2, C3.)
4. **No machine-checked policy refinement.** The policy language is restricted and exact-match; admission is an executable static check, not a proof. (C4.)
5. **Principal attribution is by declared id.** The requesting process is not authenticated. (C5, partial.)
6. **Capabilities use HMAC-SHA256 (symmetric).** Anyone holding the monitor's key can forge capabilities. The key in the repository is a test key. No key custody, rotation or HSM testing.
7. **Atomic revalidation is one in-process lock.** Multi-process, multi-host or crash-consistency behaviour is not demonstrated. A crash between the content write and the version-sidecar write leaves an inconsistent state, which the monitor then detects and blocks.
8. **Evidence is a local hash chain.** No external witness; coverage across alternate paths is not established; signed or chained logs are not legal non-repudiation. If the evidence witness fails *after* a commit, the effect has happened and the gap is reported.
9. **Delegation is not implemented.** Capabilities that name a parent are rejected. (Paper §9.17.)
10. **Semantic judgments are out of scope.** The monitor is purely mechanical. (G-Osem not applicable.)
11. **No independent audit and no external red team.** All attacks in the corpus were written by the author.
12. **Finite observations.** "0 / 60" is a count under one corpus, not a proof of zero future risk. Adaptive attackers, new channels and implementation bugs are outside the corpus.
13. **Fault injection is simulated.** Unavailable policy, revocation and evidence services are test doubles.
14. **Baselines are models.** Arm B ("containment only") is a simple model defined in `evaluation/arms.py`, not a measurement of any real product.
15. **The paper's philosophical derivations (L1, NRD, CR/CAR) are not implemented or machine-checked here.** The paper itself lists machine-checked proof as open (§10.13).
16. **Two reason codes are not exercised by the corpus** (`INTERNAL_ERROR`, `EXECUTION_FAILED`); both fail closed by construction and are listed in a test so new codes cannot be added silently.

## Residual region (declared, paper §10.15)

Unmediated physical effects; hidden or covert channels; communication whose safety is not objectively labelable; compromised root-of-trust infrastructure; operator-controlled disabling outside the governed profile; semantic categories whose truth cannot be independently verified; future attack strategies outside the evaluation regime.

## What a reader may and may not say

May: "On this corpus, with this profile, 0 of 60 adversarial requests changed the protected files when mediated by the v0.1 reference monitor."
May not: "The governor makes AI safe", "complete mediation is achieved", "zero observed failures prove zero risk", "signed logs prove liability."
