# Threat model (v0.1)

Security objective: for the declared profile, protected effects occur only through the
admitted execution path and only when the required checks succeed. Nothing wider.

## Protected effect surface

`write_file` and `delete_file` on the two resources `record-a` and `record-b`
(`profiles/protected-file-v1.json`).

## Adversaries (in scope)

| Adversary | Capabilities modelled | Corpus families |
|---|---|---|
| Malicious or compromised model / agent | Arbitrary requests, arguments and capability values | all |
| Prompt-injection source | Causes the agent to issue unintended requests (the monitor cannot tell why) | all |
| Credential thief | Replays, substitutes, edits or forges capabilities | F04, F05–F08, F11, F12 |
| Confused deputy | Uses authority bound to another principal, effect or resource | F05–F07 |
| State-race attacker | Changes state between issuance and use; races single-use authority | F08, F09, races |
| Policy-downgrade attacker | Presents authority from a superseded or rolled-back policy | F10 |
| Environment adversary | Poisons external content (affects what the agent asks for, not what the monitor allows) | indirect |
| Faulty infrastructure | Policy, revocation, state or evidence services unavailable or corrupt | F14, F15, F17 |

## Root-of-trust assumptions for v0.1 (out of scope, assumed to hold)

- Operating-system, interpreter and Python standard-library integrity, including `hmac` and `hashlib`.
- Confidentiality of the signing key held by the monitor and issuer (the repository's test key is public by design).
- The host clock.
- The owner/administrator is **not** constrained: an operator with root can disable the monitor. The paper (§1.4) notes this means owner-independent enforcement cannot be claimed; v0.1 does not claim it.
- No physical access, covert channels or side channels.
- No external services other than the stand-ins used for fault injection.

## Known uncovered paths

See `profiles/PROTECTED-FILE-V1-CHANNEL-INVENTORY.md`. The most important: any code in the
agent's uid can write the protected files directly.

## How to challenge this model

Open an issue or write to canon@necessaryuniverse.com with a failing scenario. The most
valuable reports: a request that changes the protected files without an ALLOW; a race that
yields two commits; a capability accepted that should not be; a UNKNOWN state that
becomes ALLOW.
