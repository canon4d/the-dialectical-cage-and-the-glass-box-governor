# Evidence model

Evidence answers: who asked for what, under which authority, which checks ran, what was decided and what changed.

| Field | Meaning |
|---|---|
| `event_id` | `EVT-nnnnnn`, unique within a run |
| `timestamp` | monitor clock (test clock in the corpus) |
| `profile_id`, `monitor_version` | what produced the decision |
| `principal`, `capability_id`, `nonce` | who and under which authority |
| `policy_hash` | the active policy at decision time |
| `resource_id`, `resource_version`, `state_digest` | the state decided against |
| `requested_effect` | what was asked |
| `decision`, `underlying`, `reason_code` | ALLOW/BLOCK, DENY/UNKNOWN/ALLOW, stable code |
| `checks` | ordered `{check, result}` list |
| `result_version` | resource version after the decision |
| `prev`, `integrity` | hash chain |

**What the chain gives you:** detection of edits, deletions and reordering of a stored log.
**What it does not give you:** proof the log is complete across alternate paths, an external witness,
or legal non-repudiation. See `LIMITATIONS.md` item 8.
