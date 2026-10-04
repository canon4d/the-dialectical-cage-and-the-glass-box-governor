# Specification — Protected File Mutation Profile v1

Normative for the v0.1 prototype. Where this document and the code disagree, that is a bug.

## 1. Scope

| Item | Value |
|---|---|
| Profile id | `protected-file-v1` (`profiles/protected-file-v1.json`) |
| Resources | `record-a`, `record-b` (files under a sandbox directory, each with a `.version` sidecar) |
| Effects | `write_file`, `delete_file` |
| Principals | `agent-demo`, `agent-observer`, `agent-other` |
| Out of scope | every other path, OS channel, subprocess, network, semantic judgment |

## 2. Request

`request(principal_id, effect, resource_id, capability, content)` → `Outcome`.
`content` is a string (≤ 64 KiB) for `write_file` and must be absent for `delete_file`.

## 3. Capability

Fields (exact set, exact types; extras and omissions are rejected):

`capability_id, principal_id, effect, resource_id, resource_version, policy_hash, issued_at, expires_at,
revocation_epoch, nonce, one_shot, issuer, parent_capability_id, signature`

`signature = HMAC-SHA256(key, canonical_json(all fields except signature))`. Canonical JSON: sorted keys,
no whitespace, ASCII. `parent_capability_id` must be null (delegation is not implemented).

## 4. Decision pipeline

Checks run in this order; the first failure decides. The order is published in `results.json → pipeline`
and rendered on the website.

`request_wellformed → effect_supported → resource_declared → principal_declared → capability_present →
capability_wellformed → delegation_absent → signature_authentic → principal_binding → effect_binding →
resource_binding → validity_window → policy_available → policy_binding → revocation_current →
policy_decision → replay_protection → state_current → evidence_witness → execute`

The whole pipeline plus the commit runs under one re-entrant lock.

## 5. Fail-safe rule

A check that cannot be resolved is **UNKNOWN**; UNKNOWN maps to **BLOCK**. Any unexpected exception inside
a check is UNKNOWN (`INTERNAL_ERROR`). Enforced decisions are two-valued: `ALLOW` / `BLOCK`.

## 6. Policy

Restricted language: a list of exact `(principal, effect, resource) → ALLOW|DENY` rules; default `DENY`;
`DENY` wins over `ALLOW`. Admission (`policy.admit`) rejects: non-DENY default, wildcards, undeclared
principals/effects/resources, invalid decisions, conflicting rules. Policy hash = SHA-256 of canonical JSON.
No proof object is produced.

## 7. State

A resource is a file plus `<file>.version` = `{"version": n, "digest": sha256|"ABSENT"}`. Reading the
resource recomputes the digest; a mismatch is `STATE_INCONSISTENT` (UNKNOWN → BLOCK). A commit writes the
content atomically, then the sidecar with `version + 1`.

## 8. Evidence

One record per decision, plus an `intent` record before each committed effect. `integrity =
SHA-256(prev_integrity || canonical_body)`; the chain starts at 64 zeros. If the intent record cannot be
written the effect is blocked (`EVIDENCE_UNAVAILABLE`). If the decision record fails *after* a commit the
outcome reports `evidence_complete = false`.

## 9. Reason codes

Stable strings, listed in `governor/decisions.py::Reason`. Adding one requires a scenario or an entry in
`tests/adversarial/test_attack_corpus.py::test_reason_code_coverage_is_deliberate`.

## 10. Results schema

`results/results.json` (`schema_version` 1). `core_sha256` covers every deterministic field; timestamps,
environment, latency and the bypass probe are excluded. `scripts/verify_results.py` is the reference validator.
