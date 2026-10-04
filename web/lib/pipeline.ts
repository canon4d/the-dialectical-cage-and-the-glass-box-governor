/** Human descriptions of each monitor check. The evidence page throws at build time
 *  if results.json contains a check that is not described here (drift guard). */
export const CHECKS: Record<string, { what: string; reasons: string }> = {
  request_wellformed: { what: 'Request fields have the right types; write has string content, delete has none.', reasons: 'MALFORMED_REQUEST' },
  effect_supported: { what: 'Effect is one the profile declares (write_file, delete_file).', reasons: 'UNSUPPORTED_EFFECT' },
  resource_declared: { what: 'Target resource is declared in the profile.', reasons: 'UNKNOWN_RESOURCE' },
  principal_declared: { what: 'Requesting principal is declared in the profile.', reasons: 'UNKNOWN_PRINCIPAL' },
  capability_present: { what: 'A capability was supplied at all.', reasons: 'MISSING_CAPABILITY' },
  capability_wellformed: { what: 'Strict parse: exact field set, exact types, no extras.', reasons: 'MALFORMED_CAPABILITY' },
  delegation_absent: { what: 'Capability names no parent (delegation is not implemented).', reasons: 'DELEGATION_UNSUPPORTED' },
  signature_authentic: { what: 'HMAC-SHA256 over every field verifies under the monitor key.', reasons: 'BAD_SIGNATURE' },
  principal_binding: { what: 'Capability was issued to the principal making the request.', reasons: 'PRINCIPAL_MISMATCH' },
  effect_binding: { what: 'Capability was issued for exactly this effect.', reasons: 'EFFECT_MISMATCH' },
  resource_binding: { what: 'Capability was issued for exactly this resource.', reasons: 'RESOURCE_MISMATCH' },
  validity_window: { what: 'Current time is inside [issued_at, expires_at).', reasons: 'EXPIRED, NOT_YET_VALID' },
  policy_available: { what: 'The active policy can be read.', reasons: 'POLICY_UNAVAILABLE (UNKNOWN → BLOCK)' },
  policy_binding: { what: 'Capability is bound to the hash of the active policy.', reasons: 'POLICY_MISMATCH' },
  revocation_current: { what: 'Not revoked by id or by epoch; revocation service reachable.', reasons: 'REVOKED, REVOCATION_UNAVAILABLE' },
  policy_decision: { what: 'Deny-by-default policy allows (principal, effect, resource).', reasons: 'POLICY_DENY' },
  replay_protection: { what: 'A single-use nonce has not been spent.', reasons: 'REPLAY' },
  state_current: { what: 'Resource is readable, self-consistent, and still at the capability’s version.', reasons: 'STALE_STATE, STATE_UNAVAILABLE, STATE_INCONSISTENT' },
  evidence_witness: { what: 'An intent record can be written before the effect (required for both effects).', reasons: 'EVIDENCE_UNAVAILABLE' },
  execute: { what: 'Executor commits the effect and advances the version by exactly one.', reasons: 'EXECUTION_FAILED' },
}

export const label = (c: string) => c.replace(/_/g, ' ')
