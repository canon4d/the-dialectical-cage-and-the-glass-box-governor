import Link from 'next/link'
import type { Metadata } from 'next'
import Flow from '@/components/Flow'
import JsonLd from '@/components/JsonLd'
import ProofPanel from '@/components/ProofPanel'
import { StatusChip } from '@/components/Chip'
import { SITE, abs, repoFile, repoTree } from '@/lib/site'
import { fmt, releaseLabel, results, short } from '@/lib/data'
import { pageMeta } from '@/lib/seo'

export const metadata: Metadata = {
  ...pageMeta({
    title: `${SITE.name} — ${SITE.tagline}`,
    description: SITE.description,
    path: '/',
  }),
  title: { absolute: `${SITE.name} — ${SITE.tagline}` },
}

const DEMONSTRATED = [
  { t: 'Capabilities bound to principal, effect and resource', c: 'CLM-002', d: 'A capability for A cannot be used by B, for read cannot delete, for X cannot touch Y; edits to a signed capability are detected.' },
  { t: 'Expiry and revocation', c: 'CLM-003', d: 'Expired, not-yet-valid, and revoked (by id or epoch) authority is rejected.' },
  { t: 'Single use, including under concurrency', c: 'CLM-004', d: 'Two threads racing to spend one capability: exactly one commit. A deliberately non-atomic variant double-spends, which shows the lock matters.' },
  { t: 'State and version revalidation', c: 'CLM-005', d: 'A capability issued for version 3 is useless at version 4. Check and commit happen under one lock.' },
  { t: 'Fail-closed handling of UNKNOWN', c: 'CLM-006', d: 'Unavailable policy, revocation, metadata or evidence witness blocks the protected effect; uncertainty never becomes authorization.' },
  { t: 'Policy-hash binding and deny-by-default', c: 'CLM-007', d: 'Authority does not silently survive a policy change; candidate policies are statically checked at admission.' },
  { t: 'Hash-chained evidence for every decision', c: 'CLM-008', d: 'Each request leaves a record from which the request, the checks, and the outcome can be reconstructed.' },
]

const OPEN = [
  'Complete mediation outside the declared v1 profile (the bypass probe shows same-user writes succeed and are only detected afterwards)',
  'Operating-system-level isolation and kernel assurance',
  'Machine-checked policy refinement and proofs',
  'Delegation with attenuation',
  'Independent security review and external red-team',
  'Semantic sensor assurance (not part of this release)',
  'Production validation',
]

const ld = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'SoftwareSourceCode', '@id': `${SITE.origin}/#code`, name: `${SITE.name} reference monitor (Protected File Mutation Profile v1)`,
      description: SITE.description, codeRepository: SITE.repo, programmingLanguage: 'Python',
      license: 'https://opensource.org/licenses/MIT', author: { '@id': `${SITE.origin}/#author` },
      version: results.version, runtimePlatform: 'Python 3.10+',
      isBasedOn: { '@type': 'ScholarlyArticle', name: SITE.paperTitle, url: abs('/paper/') },
    },
  ],
}

export default function Home() {
  const h = results.headline
  const a = results.arms
  return (
    <>
      <JsonLd data={ld} />

      <section className="hero">
        <div className="shell">
          <p className="kicker">AI agent execution security · reference prototype · {releaseLabel()}</p>
          <h1>An external execution boundary for AI&nbsp;agents.</h1>
          <p className="lede">
            The model proposes an action; the reference monitor independently decides whether a declared protected effect may execute. This site exists so you can inspect the code, run the attacks, and see exactly what is <em>not</em> established.
          </p>
          <div className="btn-row">
            <Link className="btn btn-primary" href="/evidence/">Read the evidence</Link>
            <a className="btn" href={SITE.repo} rel="noopener">GitHub</a>
            <Link className="btn" href="/paper/">Paper</Link>
            <Link className="btn" href="/reproducibility/">Reproduce</Link>
          </div>
          <p className="status-line">
            Profile <code>protected-file-v1</code> · in-process prototype · complete mediation <strong>not established</strong> · no independent audit
          </p>
        </div>
      </section>

      <section className="sec">
        <div className="shell">
          <h2>The mechanism</h2>
          <p className="measure">
            The model is not the final enforcement boundary. It may make mistakes, be manipulated, or behave adversarially. For a declared set of protected effects, the monitor decides from the current capability, policy and state, and records the decision as evidence.
          </p>
          <Flow />
        </div>
      </section>

      <section className="sec sec-alt">
        <div className="shell">
          <h2>Proof snapshot</h2>
          <p className="measure">
            Values below are read from the committed <a href="/data/results.json">results.json</a> at build time, not written into this page. They are counts from one profile and one attack corpus.
          </p>
          <div className="stats">
            <div className="stat stat-key">
              <span className="stat-n">{fmt(h.unauthorized_protected_executions)}</span>
              <span className="stat-l">unauthorized protected executions</span>
              <span className="stat-s">adversarial requests through the full v1 governor</span>
            </div>
            <div className="stat">
              <span className="stat-n">{fmt(h.protected_state_violations)}</span>
              <span className="stat-l">protected-state violations</span>
              <span className="stat-s">files observed from disk, independent of the monitor</span>
            </div>
            <div className="stat">
              <span className="stat-n">{fmt(h.replay_blocked)}</span>
              <span className="stat-l">replays blocked</span>
            </div>
            <div className="stat">
              <span className="stat-n">{fmt(h.stale_state_blocked)}</span>
              <span className="stat-l">stale-state (TOCTOU) attempts blocked</span>
            </div>
            <div className="stat">
              <span className="stat-n">{fmt(h.principal_substitution_blocked)}</span>
              <span className="stat-l">principal substitutions blocked</span>
            </div>
            <div className="stat">
              <span className="stat-n">{fmt(h.race_double_spends_full_monitor)}</span>
              <span className="stat-l">concurrent double spends</span>
              <span className="stat-s">non-atomic ablation: {fmt(h.race_double_spends_non_atomic_ablation)}</span>
            </div>
          </div>

          <h3 className="mt">Same attacks, three configurations</h3>
          <div className="arms">
            {(['A', 'B', 'C'] as const).map((k) => (
              <div key={k} className={`arm ${k === 'C' ? 'arm-c' : ''}`}>
                <span className="arm-k">Arm {k}</span>
                <strong>{a[k].label}</strong>
                <span className="arm-n">{a[k].unauthorized_executions} / {a[k].attack_attempts}</span>
                <span className="arm-s">attacks changed protected state</span>
                <span className="arm-s">{a[k].legitimate_completed} / {a[k].legitimate_attempts} legitimate requests completed</span>
              </div>
            ))}
          </div>
          <p className="caveat">
            Zero observed failures is a finite observation, not a proof of zero real-world risk. Arm B is a simple model of containment defined in the repository, not a measurement of any real product. Counts, corpus and caveats: <Link href="/evidence/">Evidence</Link>.
          </p>
        </div>
      </section>

      <section className="sec">
        <div className="shell">
          <h2>Try the decision path</h2>
          <p className="measure">Pick a scenario to see which check decides it, what the monitor records, and whether the protected file changed.</p>
          <ProofPanel demos={results.demonstrations} pipeline={results.pipeline} />
        </div>
      </section>

      <section className="sec sec-alt">
        <div className="shell">
          <h2>What is demonstrated now</h2>
          <p className="measure">
            Each item is <StatusChip status="LOCALLY_TESTED" /> — implemented and exercised by the author&apos;s committed corpus, not independently reproduced. Click through for scope and limits.
          </p>
          <ul className="ticks">
            {DEMONSTRATED.map((x) => (
              <li key={x.c}>
                <span className="tick" aria-hidden="true">✓</span>
                <div>
                  <strong>{x.t}</strong> <Link className="cid" href={`/evidence/#${x.c}`}>{x.c}</Link>
                  <p>{x.d}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="sec">
        <div className="shell">
          <h2>Three things, kept separate</h2>
          <div className="trio">
            <div className="trio-c">
              <h3>Demonstrated by code</h3>
              <p>What the prototype enforces and the corpus tests: the capability, policy, state, fail-closed and evidence behaviours above, for two files and two effects.</p>
            </div>
            <div className="trio-c">
              <h3>Assumed by the theorem</h3>
              <p>The paper&apos;s conditional safety theorem needs eight conditions (C1–C8): complete mediation, trusted-core integrity, kernel conformance, verified policy refinement, principal attribution, atomic revalidation, fail-closed handling, evidence-path integrity. This release does not establish all of them.</p>
            </div>
            <div className="trio-c">
              <h3>Open empirical questions</h3>
              <ul className="plain">
                {OPEN.map((o) => <li key={o}>{o}</li>)}
              </ul>
            </div>
          </div>
          <p className="measure mt">
            The repository implements a concrete prototype of selected execution-security components described in the framework. It does not claim that the complete conceptual specification has been implemented. <Link href="/limitations/">What this project does not prove →</Link>
          </p>
        </div>
      </section>

      <section className="sec sec-alt">
        <div className="shell">
          <h2>Read the evidence</h2>
          <div className="btn-row">
            <a className="btn" href={repoTree('governor')} rel="noopener">View source</a>
            <a className="btn" href={repoTree('tests')} rel="noopener">View tests</a>
            <a className="btn" href="/data/results.json">results.json</a>
            <Link className="btn" href="/reproducibility/">Reproduce locally</Link>
            <Link className="btn" href="/paper/">Read the paper</Link>
            <a className="btn" href={repoFile('AUDIT.md')} rel="noopener">Audit guide</a>
          </div>
          <p className="small muted mt">
            Release {releaseLabel()}{results.commit !== 'UNCOMMITTED' && <> · commit <code>{short(results.commit, 12)}</code></>} · attack corpus <code>{results.test_suite.attack_corpus}</code> · core hash <code>{short(results.core_sha256, 16)}</code>
          </p>
        </div>
      </section>

      <section className="sec">
        <div className="shell">
          <h2>Try to break it</h2>
          <p className="measure">
            The repository contains a reproducible prototype of the execution-security layer described in the paper. Attempts to falsify the protected-effect claim are welcome, especially around channel completeness, state races, policy admission, and root-of-trust assumptions. Write to <a href={`mailto:${SITE.email}`}>{SITE.email}</a> or open an issue on GitHub; <a href={repoFile('SECURITY.md')} rel="noopener">SECURITY.md</a> says what counts as a finding.
          </p>
        </div>
      </section>
    </>
  )
}
