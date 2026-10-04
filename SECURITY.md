# Security policy

## Reporting

Email **canon@necessaryuniverse.com** with "SECURITY" in the subject, or open a GitHub
issue for non-sensitive findings. Please include the scenario (ideally as a new entry for
`evaluation/scenarios.py`), the commit you tested, and the observed versus expected result.
A machine-readable contact is published at
<https://ai.necessaryuniverse.com/.well-known/security.txt>.

## What counts as a vulnerability in v0.1

A reproducible request sequence, within the declared threat model, that:

- changes `record-a` or `record-b` without a corresponding ALLOW decision from the monitor *inside the monitor's own path*;
- yields two commits for one single-use capability;
- converts an UNKNOWN, malformed, stale or unavailable safety state into ALLOW;
- makes the evidence record disagree with what happened;
- breaks a claim marked `LOCALLY_TESTED` in `claims/CLAIMS.json`.

## What is not a vulnerability (declared residuals)

Anything listed in `LIMITATIONS.md` and `profiles/PROTECTED-FILE-V1-CHANNEL-INVENTORY.md`,
notably: direct file writes by code in the same uid; host/root compromise; the public test key;
absence of delegation, kernel assurance or an external evidence witness. Reports on these are
welcome as roadmap input but are not treated as defects of the v0.1 claim.

## Supported versions

Only the latest tagged release (currently v0.1.0). The project has not been independently audited.

## Disclosure

Credit is given in `CHANGELOG.md` unless you ask otherwise. There is no bounty programme.
