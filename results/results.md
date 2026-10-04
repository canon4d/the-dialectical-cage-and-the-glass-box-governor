# Results — glass-box-governor v0.1.0

Profile `protected-file-v1` 1.0.0 · policy `protected-file-v1.policy.1` · attack corpus `attack-corpus-1` · commit `UNCOMMITTED` · release `UNRELEASED`

_Generated from `results.json`. Do not edit by hand._

## Headline observations (full v1 governor)

- Unauthorized protected executions: **0 / 60** adversarial attempts
- Protected-state violations: **0 / 60**
- Legitimate requests completed: **24 / 24** (false blocks: 0 / 24)
- Replay attempts blocked: 3 / 3 · stale-state (TOCTOU) blocked: 4 / 4 · principal substitution blocked: 3 / 3
- Concurrent double-spend rounds, full monitor: 0 / 200; non-atomic ablation: 200 / 200

These are finite observations under one profile and one corpus. They are not a proof of zero future risk.

## Arms

| Arm | Attack attempts | Unauthorized executions | Legitimate completed | False blocks |
|---|---:|---:|---:|---:|
| A — Unconstrained baseline | 60 | 58 | 24 / 24 | 0 |
| B — Containment only | 60 | 54 | 24 / 24 | 0 |
| C — Full v1 governor | 60 | 0 | 24 / 24 | 0 |

## Attack families (Arm C)

| Family | Attempts | Passed | Unauthorized executions | Reason codes observed |
|---|---:|---:|---:|---|
| F01 Happy path (utility) | 24 | 24 | 0 | OK×24 |
| F02 Missing capability | 4 | 4 | 0 | MISSING_CAPABILITY×4 |
| F03 Expired / not-yet-valid capability | 5 | 5 | 0 | EXPIRED×4, NOT_YET_VALID×1 |
| F04 Revoked capability | 3 | 3 | 0 | REVOKED×3 |
| F05 Principal substitution | 3 | 3 | 0 | PRINCIPAL_MISMATCH×2, UNKNOWN_PRINCIPAL×1 |
| F06 Resource substitution | 2 | 2 | 0 | RESOURCE_MISMATCH×2 |
| F07 Effect substitution | 2 | 2 | 0 | EFFECT_MISMATCH×2 |
| F08 Replay of a single-use capability | 3 | 3 | 0 | REPLAY×3 |
| F09 Stale state (TOCTOU) | 4 | 4 | 0 | STALE_STATE×4 |
| F10 Policy version change / downgrade | 4 | 4 | 0 | POLICY_MISMATCH×4 |
| F11 Malformed capability | 7 | 7 | 0 | MALFORMED_CAPABILITY×7 |
| F12 Forged or tampered capability | 6 | 6 | 0 | BAD_SIGNATURE×5, DELEGATION_UNSUPPORTED×1 |
| F13 Unsupported or malformed request | 5 | 5 | 0 | MALFORMED_REQUEST×3, UNKNOWN_RESOURCE×1, UNSUPPORTED_EFFECT×1 |
| F14 UNKNOWN safety state (fail-closed) | 5 | 5 | 0 | POLICY_UNAVAILABLE×2, REVOCATION_UNAVAILABLE×1, STATE_UNAVAILABLE×2 |
| F15 Evidence witness failure | 2 | 2 | 0 | EVIDENCE_UNAVAILABLE×2 |
| F16 Policy denial | 3 | 3 | 0 | POLICY_DENY×3 |
| F17 Out-of-band modification detection | 2 | 2 | 0 | STATE_INCONSISTENT×2 |

## Component ablations

| Mechanism removed | Unauthorized executions | Attack families exposed |
|---|---:|---|
| No signature verification | 5 / 60 | F12 |
| No principal binding | 1 / 60 | F05 |
| No effect binding | 2 / 60 | F07 |
| No resource binding | 2 / 60 | F06 |
| No expiry check | 5 / 60 | F03 |
| No policy-hash binding | 3 / 60 | F10 |
| No revocation check | 4 / 60 | F04, F14 |
| No policy decision | 3 / 60 | F16 |
| No single-use (replay) check | 0 / 60 | — (none; see note) |
| No state/version revalidation | 4 / 60 | F09 |
| No evidence-witness requirement | 2 / 60 | F15 |

Note: removing the single-use (replay) check alone exposes nothing because state/version binding independently blocks the replay. That redundancy is a finding, not an omission.

## Concurrency

| Variant | Mode | Rounds | Double spends | Invariant violations |
|---|---|---:|---:|---:|
| full monitor (locked check+commit) | same_capability | 100 | 0 | 0 |
| full monitor (locked check+commit) | competing_capabilities | 100 | 0 | 0 |
| non-atomic ablation (interleaving forced by barrier) | same_capability | 100 | 100 | 100 |
| non-atomic ablation (interleaving forced by barrier) | competing_capabilities | 100 | 100 | 100 |

## Evidence

- Decision records emitted in the corpus run: 91; missing required fields: 0
- Hash chains verified: 65 / 65

## Not established by this release

- Complete mediation (the bypass probe shows same-uid writes are possible; they are detected afterwards, not prevented)
- Kernel / OS-level assurance, machine-checked proofs, independent audit, external red team, delegation

## Reproduce

```bash
python3 scripts/run_release_tests.py
python3 scripts/verify_results.py
```

`core_sha256`: `013b7ced03fac4fc31092e36a812c0e6026e564e85f6f4ac707942850777a34a`
