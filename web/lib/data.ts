import resultsJson from '@/content/results.json'
import manifestJson from '@/content/manifest.json'
import claimsJson from '@/content/CLAIMS.json'
import metaJson from '@/content/meta.json'

export interface Ratio { numerator: number; denominator: number }
export interface TraceStep { check: string; result: 'pass' | 'fail' | 'unknown' }
export interface Demo {
  id: string; scenario: string; family: string; title: string
  request: { principal: string; effect: string; resource: string; has_content: boolean }
  capability: Record<string, unknown> | null
  expected: string; decision: string; reason_code: string
  trace: TraceStep[]; protected_state_changed: boolean
  version_before: number | null; version_after: number | null
  event_id: string | null; integrity: string | null
  baselines: { A_executed: boolean; B_executed: boolean }
}
export interface Family {
  id: string; label: string; scenarios: number; attempts: number; passed: number
  expected_allow: number; unauthorized_executions: number; protected_state_violations: number
  reason_codes: Record<string, number>
}
export interface Arm {
  label: string; attack_attempts: number; unauthorized_executions: number
  attacks_accepted: number; attacks_blocked: number
  legitimate_attempts: number; legitimate_completed: number; false_blocks: number
}
export interface Ablation { removed: string; label: string; attack_attempts: number; unauthorized_executions: number; families_exposed: string[] }
export interface Race {
  mode: string; atomic: boolean; rounds: number; double_spends: number
  zero_winner_rounds: number; invariant_violations: number; loser_reasons: Record<string, number>
}
export interface Latency { p50: number; p99: number; mean: number }
export interface Results {
  schema_version: number; project: string; version: string
  profile: { id: string; version: string; sha256: string }
  policy: { version: string; sha256: string }
  test_suite: { attack_corpus: string; attack_corpus_sha256: string; total: number; passed: number; failed: number; skipped?: number }
  headline: Record<string, Ratio>
  pipeline: string[]
  arms: Record<'A' | 'B' | 'C', Arm>
  attempts_total: number
  families: Family[]
  ablations: Ablation[]
  races: Race[]
  evidence: { decision_records: number; records_missing_required_fields: number; chains_checked: number; chains_valid: number }
  demonstrations: Demo[]
  artifact_hashes: Record<string, string>
  claim_scope: Record<string, string>
  core_sha256: string; release_tag: string; commit: string; generated_at: string
  environment: { python: string; implementation: string; platform: string; machine: string }
  environment_dependent: { direct_bypass_probe: Record<string, unknown> }
  performance: { samples_per_path: number; unit: string; blocked_path: Latency; allowed_path: Latency }
}
export interface Claim {
  id: string; text: string; scope: string; status: string; epistemic: string; evidence_class: string
  assumptions: string[]; evidence: { families?: string[]; artifacts?: string[] }; limitations: string[]
}
export interface Claims {
  release_scope: string
  status_vocabulary: Record<string, string>
  epistemic_labels: Record<string, string>
  claims: Claim[]
}
export interface Manifest {
  version: string; release_tag: string; commit: string
  tests: { results_json_sha256: string; core_sha256: string }
  paper: { pdf_sha256: string; source_sha256: string }
  zenodo: { doi: string }
}

export const results = resultsJson as unknown as Results
export const manifest = manifestJson as unknown as Manifest
export const claims = claimsJson as unknown as Claims
export const meta = metaJson as { version: string; release_tag: string; commit: string; lastmod: string; doi: string }

export const fmt = (r: Ratio) => `${r.numerator} / ${r.denominator}`
export const short = (h: string, n = 12) => (h.length > n ? `${h.slice(0, n)}…` : h)
export const shaOrPending = (c: string) => (c === 'UNCOMMITTED' ? 'uncommitted build' : c.slice(0, 12))
export const releaseLabel = () => `v${results.version}`
