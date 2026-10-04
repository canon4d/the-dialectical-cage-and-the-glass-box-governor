# Source map

Maps public claims on the website and in this repository to their location in the
paper (`research/paper.pdf`, LaTeX source `research/paper.tex`). Section numbers
come from the paper's own table of contents. Where a claim has no counterpart in
the paper, it says so.

| Public claim | Paper location | Website usage | Prototype status |
|---|---|---|---|
| Conditional Behavioral Safety Theorem (C1–C8) | §1.3, Table 1 | summarised, not expanded | specification; v0.1 demonstrates a subset only |
| Security objective is profile-specific, not "no harm in the universe" | §1.4 | quoted in scope text | n/a |
| Three binding tiers (mechanical, semantic, institutional) | §1.5 | summarised | v0.1 covers mechanical tier only, partially |
| What a deployer may and may not claim | §1.6 | reflected in the claim vocabulary | n/a |
| Capability security, delegation, model binding | §9.17 | capability fields, "delegation not implemented" | partial: binding implemented; delegation not |
| TOCTOU and state-bound authorization | §9.18 | state/version revalidation | implemented, locally tested |
| Complete-mediation deployment profiles | §9.20, §9.25 | channel inventory | **not established** |
| Fail-safe matrix | §9.21 | UNKNOWN → BLOCK mapping | implemented, locally tested |
| Minimal trusted computing base | §9.22 | `governor/` is the whole TCB of v0.1 | implemented (unproven) |
| Policy admission and proof-carrying policies | §9.24 | executable admission check only | partial; no proof object |
| Cryptographic authorization and tamper-evident evidence | §9.26 | HMAC capabilities, hash-chained evidence | partial |
| SafetyBundle and supply-chain integrity | §9.27 | release manifest (hashes) | partial; no bundle signing |
| Four assurance classes (G-Omech, G-Osem, G-Governance, G-Normative-Commitment) | §10.1 | evidence-class field in the claim registry | v0.1 touches G-Omech only |
| Conditional execution guarantee | §10.2 | summarised | specification |
| Pre-registered ablation, evaluation protocol | §10.11, Appendix F (F.5 ablation matrix) | arms and ablations | smallest useful subset |
| Evidence and implementation status; engine "specified, not implemented" | §10.13 | status wording | v0.1 is the first implementation of selected components |
| Honesty ledger (prohibited summaries) | §10.14 | banned-phrase check in `scripts/verify_public_consistency.py` | enforced for this repo and site |
| Residual region | §10.15 | `LIMITATIONS.md`, `/limitations` | declared |
| Epistemic labels D / A / S / E / R | Core claim hierarchy figure at the end of §10 | label chips in the claim registry | used as labels, never as scores |

Not in the paper: the profile `protected-file-v1`, the attack corpus, the three
experimental arms as defined here, the ablation list, and every number in
`results/results.json`. Those are products of this repository and are only as
authoritative as the code that generates them.
