import type { Metadata } from 'next'
import Link from 'next/link'
import ClaimsExplorer from '@/components/ClaimsExplorer'
import CodeBlock from '@/components/CodeBlock'
import DataTable from '@/components/DataTable'
import JsonLd from '@/components/JsonLd'
import { claims, fmt, manifest, releaseLabel, results, short } from '@/lib/data'
import type { Ablation, Arm, Family, Race } from '@/lib/data'
import { breadcrumbs, pageMeta } from '@/lib/seo'
import { repoFile, repoTree } from '@/lib/site'

export const metadata: Metadata = pageMeta({
  title: 'Evidence',
  description: 'Release metadata, per-family attack results, baselines, component ablations, concurrency checks, and the claim registry for the Glass-Box Governor v0.1 prototype, all generated from results.json.',
  path: '/evidence/',
})

export default function Evidence() {
  const r = results
  const bypass = r.environment_dependent.direct_bypass_probe as Record<string, unknown>
  const meta: [string, string][] = [
    ['release', releaseLabel()],
    ['version', `v${r.version}`],
    ...(r.commit === 'UNCOMMITTED' ? [] : ([['commit', r.commit]] as [string, string][])),
    ['profile', `${r.profile.id} ${r.profile.version}`],
    ['profile sha256', r.profile.sha256],
    ['policy', r.policy.version],
    ['policy sha256', r.policy.sha256],
    ['attack corpus', r.test_suite.attack_corpus],
    ['corpus sha256', r.test_suite.attack_corpus_sha256],
    ['tests', `${r.test_suite.passed} passed / ${r.test_suite.total} total / ${r.test_suite.failed} failed`],
    ['core sha256', r.core_sha256],
    ['results.json sha256', manifest.tests.results_json_sha256],
    ['generated', r.generated_at],
    ['python', `${r.environment.python} (${r.environment.implementation}, ${r.environment.platform})`],
  ]

  return (
    <div className="shell page">
      <JsonLd data={breadcrumbs([{ name: 'Evidence', path: '/evidence/' }])} />
      <header className="page-head">
        <p className="kicker">Evidence</p>
        <h1>Show me the evidence</h1>
        <p className="lede">
          Everything on this page is generated from the committed <a href="/data/results.json">results.json</a>. The website computes nothing. To check it yourself, run one command: <Link href="/reproducibility/">Reproduce</Link>.
        </p>
      </header>

      <h2 id="release">Current release</h2>
      <dl className="meta">
        {meta.map(([k, v]) => (
          <div key={k}><dt>{k}</dt><dd>{v}</dd></div>
        ))}
      </dl>
      <p className="caveat">
        <code>core sha256</code> covers every deterministic result. Timestamps, environment and latency are excluded so that a clean re-run reproduces the same hash on any machine.
      </p>

      <h2 id="arms">Same attacks, three configurations</h2>
      <p className="measure">
        Arm A has no monitor. Arm B is a simple model of containment: any presented credential permits a mutation of the confined files, with no per-request binding. Arm C is the full v1 governor. The baselines show that the corpus really does present attack opportunities.
      </p>
      <DataTable<[string, Arm]>
        caption="Results by experimental arm"
        rowKey={(x) => x[0]}
        rows={(['A', 'B', 'C'] as const).map((k) => [k, r.arms[k]] as [string, Arm])}
        cols={[
          { key: 'k', label: 'Arm', render: (x) => `${x[0]} — ${x[1].label}` },
          { key: 'a', label: 'Attack attempts', num: true, render: (x) => x[1].attack_attempts },
          { key: 'u', label: 'Changed protected state', num: true, render: (x) => `${x[1].unauthorized_executions} / ${x[1].attack_attempts}` },
          { key: 'l', label: 'Legitimate completed', num: true, render: (x) => `${x[1].legitimate_completed} / ${x[1].legitimate_attempts}` },
          { key: 'f', label: 'False blocks', num: true, render: (x) => x[1].false_blocks },
        ]}
      />

      <h2 id="families">Attack families (Arm C)</h2>
      <p className="measure">
        Each scenario is one script; “attempts” counts the measured requests inside it. A request passes only if the decision and the reason code are the expected ones <em>and</em> both protected files, observed directly from disk, are unchanged (or advanced by exactly one version for legitimate requests).
      </p>
      <DataTable<Family>
        caption="Attack families, attempts, passes and reason codes"
        rowKey={(f) => f.id}
        rows={r.families}
        cols={[
          { key: 'id', label: 'Family', render: (f) => <span><span className="mono">{f.id}</span> {f.label}</span> },
          { key: 'scenarios', label: 'Scenarios', num: true },
          { key: 'attempts', label: 'Attempts', num: true },
          { key: 'passed', label: 'Passed', num: true },
          { key: 'v', label: 'Protected-state violations', num: true, render: (f) => f.protected_state_violations },
          { key: 'rc', label: 'Reason codes observed', mono: true, render: (f) => Object.entries(f.reason_codes).map(([k, v]) => `${k}×${v}`).join(', ') },
        ]}
      />

      <h2 id="ablations">Component ablations</h2>
      <p className="measure">
        Each row removes one mechanism from a copy of the monitor (in the untrusted harness; the real monitor has no off switch) and re-runs the corpus. A mechanism earns its place if removing it lets an attack family through.
      </p>
      <DataTable<Ablation>
        caption="Effect of removing each mechanism"
        rowKey={(a) => a.removed}
        rows={r.ablations}
        cols={[
          { key: 'label', label: 'Mechanism removed' },
          { key: 'u', label: 'Attacks that changed state', num: true, render: (a) => `${a.unauthorized_executions} / ${a.attack_attempts}` },
          { key: 'f', label: 'Families exposed', mono: true, render: (a) => (a.families_exposed.length ? a.families_exposed.join(', ') : '— none') },
        ]}
      />
      <p className="caveat">
        Removing the single-use check alone exposes nothing, because the version binding independently blocks the replay. That redundancy is a finding about this profile, reported as observed.
      </p>

      <h2 id="races">Concurrency</h2>
      <p className="measure">
        Two threads race, released together, to spend authority bound to the same version. In the non-atomic variant the check and the commit are not under one lock and a barrier forces the interleaving, which demonstrates why atomic revalidation (condition C6) is required. Atomicity here is one in-process lock; multi-process or distributed atomicity is not demonstrated.
      </p>
      <DataTable<Race>
        caption="Concurrent spend experiments"
        rowKey={(x) => `${x.atomic}-${x.mode}`}
        rows={r.races}
        cols={[
          { key: 'v', label: 'Variant', render: (x) => (x.atomic ? 'Full monitor (locked)' : 'Non-atomic ablation') },
          { key: 'mode', label: 'Mode', mono: true },
          { key: 'rounds', label: 'Rounds', num: true },
          { key: 'double_spends', label: 'Double spends', num: true },
          { key: 'invariant_violations', label: 'Invariant violations', num: true },
          { key: 'lr', label: 'Loser reasons', mono: true, render: (x) => Object.entries(x.loser_reasons).map(([k, v]) => `${k}×${v}`).join(', ') || '—' },
        ]}
      />

      <h2 id="mediation">Direct-bypass probe: complete mediation</h2>
      <div className="callout callout-warn">
        <strong>Complete mediation is deployment-specific. This release demonstrates it only where the channel inventory and enforcement boundary justify that statement. For v0.1 it is not established.</strong>
        <p>
          The probe writes to a protected file without going through the monitor. In this run: direct write <code>{String(bypass.direct_write_default_permissions)}</code>, after setting the file read-only <code>{String(bypass.direct_write_after_read_only_mode)}</code> (uid {String(bypass.effective_uid)}; root ignores file modes). The next mediated request was then <code>{JSON.stringify(bypass.mediated_request_after_bypass)}</code>. The change is detected afterwards, not prevented. Outcomes depend on the operating-system user and are excluded from the reproducibility hash. Full list of channels: <a href={repoFile('profiles/PROTECTED-FILE-V1-CHANNEL-INVENTORY.md')} rel="noopener">channel inventory</a>.
        </p>
      </div>

      <h2 id="evidence-quality">Evidence quality and latency</h2>
      <p className="measure">
        Decision records emitted in the corpus run: <strong>{r.evidence.decision_records}</strong>, with <strong>{r.evidence.records_missing_required_fields}</strong> missing required fields; hash chains verified: <strong>{r.evidence.chains_valid} / {r.evidence.chains_checked}</strong>. This shows the log is well-formed and tamper-evident against naive edits. It does not show that every path to the files is logged.
      </p>
      <p className="measure">
        Latency of the in-process mechanical path ({r.performance.samples_per_path} samples per path, {r.performance.unit}, includes file I/O and fsync; varies by machine and is not part of the hash): blocked requests p50 {r.performance.blocked_path.p50}, p99 {r.performance.blocked_path.p99}; allowed requests p50 {r.performance.allowed_path.p50}, p99 {r.performance.allowed_path.p99}.
      </p>

      <h2 id="claims">Claim registry</h2>
      <p className="measure">
        Every public claim has an id, a scope, a status and its known limitations. “Locally tested” means the author&apos;s corpus exercises it; it does not mean independently reproduced. Epistemic labels D / A / S / E / R are the paper&apos;s, not confidence scores. Source: <a href="/data/CLAIMS.json">CLAIMS.json</a>.
      </p>
      <ClaimsExplorer claims={claims.claims} vocab={claims.status_vocabulary} />

      <h2 id="raw">Raw data</h2>
      <ul className="plain linkish">
        <li><a href="/data/results.json">results.json</a> — machine-readable results</li>
        <li><a href="/data/manifest.json">manifest.json</a> — release manifest binding results to hashes</li>
        <li><a href="/data/CLAIMS.json">CLAIMS.json</a> — claim registry</li>
        <li><a href={repoTree('tests')} rel="noopener">tests/</a> and <a href={repoFile('evaluation/scenarios.py')} rel="noopener">evaluation/scenarios.py</a> — the attack corpus source</li>
      </ul>

      <h2 id="reproduce">Reproduce</h2>
      <CodeBlock label="shell" code={'git clone https://github.com/canon4d/the-dialectical-cage-and-the-glass-box-governor\ncd the-dialectical-cage-and-the-glass-box-governor\npython3 scripts/run_release_tests.py'} />
      <p className="small muted">
        Then compare your <code>core sha256</code> with <code>{short(r.core_sha256, 16)}</code>. Details and troubleshooting: <Link href="/reproducibility/">Reproduce</Link>. Overall shape of the corpus: {r.attempts_total} measured requests, {fmt(r.headline.unauthorized_protected_executions)} unauthorized executions.
      </p>
    </div>
  )
}
