# Changelog

## v0.1.0 — first public release (unreleased until tagged)

- Reference monitor for Protected File Mutation Profile v1 (`governor/`), standard library only.
- Capability model: principal / effect / resource / version / policy-hash / expiry / revocation-epoch / single-use nonce, HMAC-SHA256.
- Deny-by-default restricted policy language with an executable admission check.
- Fail-closed handling of UNKNOWN safety state.
- Hash-chained evidence records.
- Attack corpus `attack-corpus-1` (65 scenarios, 17 families), three experimental arms, 11 component ablations, concurrency races, direct-bypass probe.
- Deterministic results (`results/results.json`, `results.md`, `manifest.json`) and verifier.
- Website at https://ai.necessaryuniverse.com (Next.js static export on Vercel).
- Paper: *The Dialectical Cage and the Glass-Box Governor* (Zenodo DOI: 10.5281/zenodo.21278446).

Explicitly not in v0.1: complete mediation, OS-level isolation, delegation, formal verification, independent audit.
