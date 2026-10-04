# Claim registry

_Generated from `claims/CLAIMS.json` by `scripts/generate_claims_snapshot.py`. Do not edit by hand._

Release scope: v0.1.0 — Protected File Mutation Profile v1

## Status vocabulary

- **SPECIFIED** — Stated in the paper or SPEC.md; not implemented or not tested here.
- **IMPLEMENTED** — Code exists; no dedicated test evidence yet.
- **LOCALLY_TESTED** — Implemented and exercised by the committed, deterministic test/attack corpus on the author's side. Not independently reproduced.
- **REPRODUCED** — Independently reproduced by someone other than the author.
- **INDEPENDENTLY_REVIEWED** — Reviewed by an independent party with a published report.
- **PRODUCTION_VALIDATED** — Validated in a production deployment with evidence.
- **OPEN** — Not established; an outside engineer could design a test or proof for it.
- **RESIDUAL** — Outside the theorem's boundary by declaration (paper section 10.15).
- **NOT_APPLICABLE** — Does not apply to this release.

## Epistemic labels (from the paper; not confidence scores)

- **D** — Derivation relative to explicit premises
- **A** — Declared normative / deployment assumption
- **S** — Security or invariant claim dependent on trusted-system conditions
- **E** — Empirical assurance claim requiring measurement
- **R** — Residual / open region

## Claims

| ID | Status | Label | Claim | Scope |
|---|---|---|---|---|
| CLM-001 | LOCALLY_TESTED | E | For the declared attack corpus, no unauthorized mutation of the two protected files occurred when requests went through the reference monitor. | protected-file-v1, attack-corpus-1, in-process monitor |
| CLM-002 | LOCALLY_TESTED | S | A capability is bound to one principal, one effect and one resource; substitution of any of the three is blocked, and edits to a signed capability are detected. | protected-file-v1 |
| CLM-003 | LOCALLY_TESTED | S | Expired, not-yet-valid and revoked capabilities (by id or by epoch) are rejected. | protected-file-v1 |
| CLM-004 | LOCALLY_TESTED | S | A single-use capability cannot be spent twice, including under concurrent attempts within one process. | protected-file-v1, single process |
| CLM-005 | LOCALLY_TESTED | S | Resource state is revalidated at execution time; a capability issued for a superseded version is rejected. | protected-file-v1 |
| CLM-006 | LOCALLY_TESTED | S | Unresolvable safety state (policy, revocation, resource metadata, evidence witness) is treated as UNKNOWN and mapped to BLOCK. | protected-file-v1 |
| CLM-007 | LOCALLY_TESTED | S | Capabilities are bound to the active policy hash, a deny-by-default policy is evaluated per request, and candidate policies are statically checked at admission against the Safety Profile. | protected-file-v1 |
| CLM-008 | LOCALLY_TESTED | E | Every mediated request produces a structured, hash-chained evidence record from which the request, the checks passed or failed, and the outcome can be reconstructed. | protected-file-v1 |
| CLM-009 | LOCALLY_TESTED | E | A change to a protected file made through a non-mediated channel is detected on the next mediated request and that request is blocked. | protected-file-v1 |
| CLM-010 | OPEN | S | Complete mediation of the protected effect surface (condition C1). | protected-file-v1 |
| CLM-011 | OPEN | S | Conformance of the monitor to verified semantics (kernel conformance, C3) and integrity of the trusted core (C2). | protected-file-v1 |
| CLM-012 | OPEN | S | Machine-checked typed refinement from the deployed policy to the admitted safety constitution (C4). | protected-file-v1 |
| CLM-013 | OPEN | S | Capability delegation with attenuation (child scope, budget and expiry bounded by the parent). | protected-file-v1 |
| CLM-014 | OPEN | E | Independent security review, external red-team validation and held-out adaptive evaluation. | protected-file-v1 |
| CLM-015 | SPECIFIED | S | Conditional Behavioral Safety Theorem: under C1-C8 every executed protected effect satisfies the admitted safety predicate. | Paper section 1.3 / Table 1 |
| CLM-016 | SPECIFIED | D | L1 (public-ground component) and NRD (no unjustified normative difference), plus the constitutional-reflexivity constraint CR/CAR, as derived in the paper's practice-based ethics. | Paper sections 2-6 |
| CLM-017 | NOT_APPLICABLE | E | Semantic assurance (G-Osem): calibrated probabilistic bounds on neural state extraction. | Not part of v0.1 |
| CLM-018 | RESIDUAL | R | Covert channels, unmediated physical effects, compromised root of trust and operator-controlled disabling are outside the guarantee. | Paper section 10.15 |

### CLM-001 — LOCALLY_TESTED

For the declared attack corpus, no unauthorized mutation of the two protected files occurred when requests went through the reference monitor.

- Scope: protected-file-v1, attack-corpus-1, in-process monitor
- Evidence class: G-Omech
- Assumptions: C1 (partial: declared effect surface only, not established), C2, C5, C6, C7
- Attack families: F02, F03, F04, F05, F06, F07, F08, F09, F10, F11, F12, F13, F14, F15, F16, F17
- Artifacts: `results/results.json`, `tests/adversarial/test_attack_corpus.py`
- Known limitations:
  - Finite corpus; zero observed failures do not prove zero real-world risk
  - No complete-mediation proof
  - No independent audit

### CLM-002 — LOCALLY_TESTED

A capability is bound to one principal, one effect and one resource; substitution of any of the three is blocked, and edits to a signed capability are detected.

- Scope: protected-file-v1
- Evidence class: G-Omech
- Assumptions: C5
- Attack families: F05, F06, F07, F12
- Artifacts: `governor/capability.py`, `governor/monitor.py`
- Known limitations:
  - HMAC (symmetric): compromise of the monitor implies capability forgery
  - Principal attribution is by declared id; no authentication of the requesting process

### CLM-003 — LOCALLY_TESTED

Expired, not-yet-valid and revoked capabilities (by id or by epoch) are rejected.

- Scope: protected-file-v1
- Evidence class: G-Omech
- Assumptions: C5, C7
- Attack families: F03, F04
- Artifacts: `governor/monitor.py`, `governor/state.py`
- Known limitations:
  - Time comes from the host clock; clock tampering is out of scope
  - Revocation store is in-memory in v0.1

### CLM-004 — LOCALLY_TESTED

A single-use capability cannot be spent twice, including under concurrent attempts within one process.

- Scope: protected-file-v1, single process
- Evidence class: G-Omech
- Assumptions: C6
- Attack families: F08
- Artifacts: `evaluation/race.py`, `tests/adversarial/test_ablation_and_race.py`
- Known limitations:
  - Atomicity comes from one in-process lock; multi-process or distributed atomicity is not demonstrated
  - State/version binding independently blocks replays, so the single-use check is redundant for version-bound capabilities (reported by the ablation)

### CLM-005 — LOCALLY_TESTED

Resource state is revalidated at execution time; a capability issued for a superseded version is rejected.

- Scope: protected-file-v1
- Evidence class: G-Omech
- Assumptions: C6
- Attack families: F09
- Artifacts: `governor/state.py`, `governor/monitor.py`
- Known limitations:
  - Revalidation and commit are atomic only with respect to other mediated requests
  - Non-mediated writers are detected afterwards (CLM-009), not excluded

### CLM-006 — LOCALLY_TESTED

Unresolvable safety state (policy, revocation, resource metadata, evidence witness) is treated as UNKNOWN and mapped to BLOCK.

- Scope: protected-file-v1
- Evidence class: G-Omech
- Assumptions: C7, C8 (partial)
- Attack families: F14, F15
- Artifacts: `governor/monitor.py`
- Known limitations:
  - Failures are injected by test doubles, not by real infrastructure faults
  - If the evidence witness fails after commit, the effect has already happened; the gap is reported, not prevented

### CLM-007 — LOCALLY_TESTED

Capabilities are bound to the active policy hash, a deny-by-default policy is evaluated per request, and candidate policies are statically checked at admission against the Safety Profile.

- Scope: protected-file-v1
- Evidence class: G-Omech
- Assumptions: C4 (not established)
- Attack families: F10, F16
- Artifacts: `governor/policy.py`, `tests/unit/test_policy.py`
- Known limitations:
  - Restricted exact-match language; executable admission check only
  - No proof object and no machine-checked refinement checker (paper condition C4/PAV remains open)

### CLM-008 — LOCALLY_TESTED

Every mediated request produces a structured, hash-chained evidence record from which the request, the checks passed or failed, and the outcome can be reconstructed.

- Scope: protected-file-v1
- Evidence class: G-Omech
- Assumptions: C8 (partial)
- Artifacts: `governor/evidence.py`, `results/results.json#evidence`, `tests/unit/test_state_evidence.py`
- Known limitations:
  - Local log only; no external witness
  - Hash chain detects naive tampering; it does not establish legal non-repudiation
  - Evidence completeness across alternate paths is not established

### CLM-009 — LOCALLY_TESTED

A change to a protected file made through a non-mediated channel is detected on the next mediated request and that request is blocked.

- Scope: protected-file-v1
- Evidence class: G-Omech
- Assumptions: —
- Attack families: F17
- Artifacts: `evaluation/bypass.py`, `tests/adversarial/test_bypass.py`
- Known limitations:
  - Detection after the fact, not prevention
  - An attacker who also rewrites the version sidecar consistently is not detected by this mechanism

### CLM-010 — OPEN

Complete mediation of the protected effect surface (condition C1).

- Scope: protected-file-v1
- Evidence class: G-Omech
- Assumptions: C1
- Artifacts: `profiles/PROTECTED-FILE-V1-CHANNEL-INVENTORY.md`, `results/results.json#environment_dependent`
- Known limitations:
  - v0.1 runs monitor and mediated code in one process and uid; direct writes are possible (bypass probe)
  - Roadmap v0.2: OS-level privilege separation and alternate-path tests

### CLM-011 — OPEN

Conformance of the monitor to verified semantics (kernel conformance, C3) and integrity of the trusted core (C2).

- Scope: protected-file-v1
- Evidence class: G-Omech
- Assumptions: C2, C3
- Known limitations:
  - No formal verification or kernel-level assurance
  - Trusted core is small (governor/*.py) but unproven

### CLM-012 — OPEN

Machine-checked typed refinement from the deployed policy to the admitted safety constitution (C4).

- Scope: protected-file-v1
- Evidence class: G-Omech
- Assumptions: C4
- Known limitations:
  - Roadmap v0.3

### CLM-013 — OPEN

Capability delegation with attenuation (child scope, budget and expiry bounded by the parent).

- Scope: protected-file-v1
- Evidence class: G-Omech
- Assumptions: —
- Attack families: F12
- Artifacts: `governor/capability.py`
- Known limitations:
  - Not implemented; capabilities naming a parent are rejected (tested), nothing more
  - Roadmap v0.4

### CLM-014 — OPEN

Independent security review, external red-team validation and held-out adaptive evaluation.

- Scope: protected-file-v1
- Evidence class: G-Omech
- Assumptions: —
- Known limitations:
  - None performed; invitations to falsify are in SECURITY.md and AUDIT.md

### CLM-015 — SPECIFIED

Conditional Behavioral Safety Theorem: under C1-C8 every executed protected effect satisfies the admitted safety predicate.

- Scope: Paper section 1.3 / Table 1
- Evidence class: G-Omech
- Assumptions: C1, C2, C3, C4, C5, C6, C7, C8
- Artifacts: `research/paper.pdf`, `research/SOURCE_MAP.md`
- Known limitations:
  - Conditional on all eight conditions; this prototype demonstrates only a subset (see CLM-001..CLM-009 and CLM-010..CLM-012)

### CLM-016 — SPECIFIED

L1 (public-ground component) and NRD (no unjustified normative difference), plus the constitutional-reflexivity constraint CR/CAR, as derived in the paper's practice-based ethics.

- Scope: Paper sections 2-6
- Evidence class: n/a
- Assumptions: Paper premises P1 and following; classical first-order logic
- Artifacts: `research/paper.pdf`
- Known limitations:
  - Derivations are not machine-checked (paper section 10.13)
  - Substantive standards B4-B8 are declared (A), not derived
  - This repository does not implement or test the philosophical layer

### CLM-017 — NOT_APPLICABLE

Semantic assurance (G-Osem): calibrated probabilistic bounds on neural state extraction.

- Scope: Not part of v0.1
- Evidence class: G-Osem
- Assumptions: SA (sensor adequacy)
- Known limitations:
  - The v0.1 monitor is purely mechanical and makes no semantic judgments

### CLM-018 — RESIDUAL

Covert channels, unmediated physical effects, compromised root of trust and operator-controlled disabling are outside the guarantee.

- Scope: Paper section 10.15
- Evidence class: n/a
- Assumptions: —
- Artifacts: `LIMITATIONS.md`
- Known limitations:
  - These are the boundary of the theorem, not defects of terminology
