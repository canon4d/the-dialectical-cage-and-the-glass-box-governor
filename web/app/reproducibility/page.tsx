import type { Metadata } from 'next'
import CodeBlock from '@/components/CodeBlock'
import JsonLd from '@/components/JsonLd'
import { fmt, manifest, results } from '@/lib/data'
import { breadcrumbs, pageMeta } from '@/lib/seo'
import { SITE, repoFile } from '@/lib/site'

export const metadata: Metadata = pageMeta({
  title: 'Reproduce',
  description: 'One command reproduces every number on this site from a clean checkout, offline, with the Python standard library only. How to verify hashes, add your own attack, and what the website is and is not.',
  path: '/reproducibility/',
})

const howTo = {
  '@context': 'https://schema.org', '@type': 'HowTo',
  name: 'Reproduce the Glass-Box Governor v0.1 results',
  step: [
    { '@type': 'HowToStep', name: 'Clone the repository', text: `git clone ${SITE.repo}` },
    { '@type': 'HowToStep', name: 'Run the release command', text: 'python3 scripts/run_release_tests.py' },
    { '@type': 'HowToStep', name: 'Verify', text: 'python3 scripts/verify_results.py' },
  ],
}

export default function Reproduce() {
  const r = results
  const h = r.headline
  const expected = `TEST SUMMARY
Total tests:                  ${r.test_suite.total}
Passed:                       ${r.test_suite.passed}
Failed:                       ${r.test_suite.failed}

Unauthorized executions:      ${fmt(h.unauthorized_protected_executions)}
Protected-state violations:   ${fmt(h.protected_state_violations)}
Legitimate completed:         ${fmt(h.legitimate_requests_completed)}
Replay blocked:               ${fmt(h.replay_blocked)}
Stale-state (TOCTOU) blocked: ${fmt(h.stale_state_blocked)}
Race double spends (full):    ${fmt(h.race_double_spends_full_monitor)}

A unconstrained:              ${fmt(h.baseline_unauthorized_unconstrained)} attacks changed protected state
B containment-only:           ${fmt(h.baseline_unauthorized_containment_only)} attacks changed protected state

core_sha256:                  ${r.core_sha256.slice(0, 16)}…
VERIFY OK — results are well-formed, bound to current sources, and reproducible`

  return (
    <div className="shell page">
      <JsonLd data={howTo} />
      <JsonLd data={breadcrumbs([{ name: 'Reproduce', path: '/reproducibility/' }])} />
      <header className="page-head">
        <p className="kicker">Reproduce</p>
        <h1>Run it yourself</h1>
        <p className="lede">
          The verification path should be shorter than the persuasion path. You need Python 3.10 or newer and git. No network access, no packages to install, no API keys.
        </p>
      </header>

      <h2 id="run">1. Clone and run</h2>
      <CodeBlock code={`git clone ${SITE.repo}\ncd the-dialectical-cage-and-the-glass-box-governor\npython3 scripts/run_release_tests.py`} />
      <p className="measure">
        This runs the unit, integration and adversarial tests, then the three-arm evaluation, the ablations and the concurrency checks, writes <code>results/results.json</code>, <code>results.md</code> and <code>manifest.json</code>, and verifies them. It takes a few seconds.
      </p>

      <h2 id="expect">2. What you should see</h2>
      <p className="measure">Generated from this release&apos;s <code>results.json</code>. Your commit line and timestamps will differ; the counts and <code>core_sha256</code> must not.</p>
      <CodeBlock label="expected output (excerpt)" code={expected} />
      <p className="small muted">Published core hash: <code>{r.core_sha256}</code></p>

      <h2 id="verify">3. Check it against what is published</h2>
      <CodeBlock code={`python3 scripts/verify_results.py\n\n# your hash vs the hash on this site\npython3 -c "import json;print(json.load(open('results/results.json'))['core_sha256'])"\ncurl -s ${SITE.origin}/data/results.json | python3 -c "import sys,json;print(json.load(sys.stdin)['core_sha256'])"`} />
      <p className="measure">
        <code>verify_results.py</code> checks the schema, the recorded hash of every source file, the manifest, the internal arithmetic, and then re-runs the evaluation to confirm the deterministic core hash reproduces. Manifest: <a href="/data/manifest.json">manifest.json</a> (published results hash <code>{manifest.tests.results_json_sha256.slice(0, 16)}…</code>).
      </p>

      <h2 id="determinism">Why the results are reproducible</h2>
      <ul className="plain">
        <li>Standard library only; no network calls; no external APIs or models.</li>
        <li>A controlled test clock and sequential ids; expiry tests never read the wall clock.</li>
        <li>Each scenario runs in a fresh temporary sandbox; protected files are observed from disk, not through the monitor.</li>
        <li>Latency, environment details and the bypass probe depend on the machine and are excluded from the hash.</li>
        <li>The canonical comparison is the hash of the deterministic result structure, not text matching.</li>
      </ul>

      <h2 id="attack">4. Add your own attack</h2>
      <CodeBlock label="python — evaluation/scenarios.py" code={`@scenario("F05", "my-attack", "What I am trying")\ndef _(c):\n    cap = c.w.issue(principal="agent-demo")\n    c.attempt("my request", "agent-other", "write_file", "record-a", cap, "evil",\n              reasons={R.PRINCIPAL_MISMATCH})`} />
      <p className="measure">
        Re-run the command. A test is generated for your scenario and it appears in all three arms and every ablation. If it succeeds against the full governor, that is a finding: see <a href={repoFile('SECURITY.md')} rel="noopener">SECURITY.md</a> or write to <a href={`mailto:${SITE.email}`}>{SITE.email}</a>.
      </p>

      <h2 id="site">What this website is</h2>
      <div className="callout">
        <p>
          The website is a presentation layer over the committed result files. It contains no second implementation of the monitor, and the replay in the proof panel is not computed in your browser. The authoritative evidence is the source code, the test suite, and the artifacts you reproduce locally. A consistency check (<code>scripts/verify_public_consistency.py</code>) fails the build pipeline if the site&apos;s data copies, version, DOI state or status claims disagree with the repository.
        </p>
      </div>

      <h2 id="audit">Auditing</h2>
      <p className="measure">
        The trusted path is five short files. <a href={repoFile('AUDIT.md')} rel="noopener">AUDIT.md</a> gives a ten-step reading order, how to confirm that a protected file really did not change, and where the trust boundary begins and ends.
      </p>
    </div>
  )
}
