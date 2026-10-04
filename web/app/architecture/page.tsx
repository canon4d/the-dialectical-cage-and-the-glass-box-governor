import type { Metadata } from 'next'
import Link from 'next/link'
import Flow from '@/components/Flow'
import JsonLd from '@/components/JsonLd'
import DataTable from '@/components/DataTable'
import { StatusChip } from '@/components/Chip'
import { CHECKS, label } from '@/lib/pipeline'
import { results } from '@/lib/data'
import { breadcrumbs, pageMeta } from '@/lib/seo'
import { repoFile } from '@/lib/site'

export const metadata: Metadata = pageMeta({
  title: 'Architecture',
  description: 'The layered framework from the paper, which layer this prototype implements, the ordered checks the reference monitor runs, and how the paper’s conditions C1–C8 map to what is and is not established.',
  path: '/architecture/',
})

const LAYERS = [
  { n: 1, t: 'Normative practice and selected constitution', p: 'Records the substantive standards a deployment adopts as a versioned, inspectable constitution.', i: 'Reason-giving practice; declared standards B4–B8', o: 'A selected constitution', trust: 'Declared (A) and derived (D) in the paper; not mechanically enforced', impl: 'NOT_APPLICABLE', note: 'Not implemented here. The repository does not implement or test the philosophical layer.', open: 'Machine-checked derivations (paper §10.13)', ref: '§2–8' },
  { n: 2, t: 'Safety ontology and Safety Profile', p: 'Turns the constitution into a typed, deployment-specific contract: principals, resources, effects, fail-safe rules, residuals.', i: 'Constitution', o: 'Safety Profile', trust: 'Declared; consumed by the monitor', impl: 'IMPLEMENTED', note: 'One profile: protected-file-v1 (two files, two effects, three principals).', open: 'Other profiles; constitution-parametric instantiation', ref: '§9.2, §9.11' },
  { n: 3, t: 'Policy representation and admission', p: 'A typed policy is admitted only if it refines the profile. Admission is separate from runtime evaluation.', i: 'Candidate policy + profile', o: 'Admitted policy and its hash', trust: 'Checked before load; evaluated by the monitor', impl: 'LOCALLY_TESTED', note: 'Restricted exact-match language, deny by default, executable admission check. No proof object, no machine-checked refinement.', open: 'Condition C4: machine-checked typed refinement', ref: '§9.9, §9.24' },
  { n: 4, t: 'Reference monitor and trusted core', p: 'The only intended path to a protected effect. Small, deterministic, fail-closed.', i: 'Request + capability', o: 'ALLOW or BLOCK, plus an evidence record', trust: 'Trusted; unproven', impl: 'LOCALLY_TESTED', note: 'governor/ is the entire trusted path of v0.1 (about 700 lines, standard library only).', open: 'Conditions C2, C3: integrity and verified conformance', ref: '§9.22' },
  { n: 5, t: 'Capabilities and state-bound authorization', p: 'Authority is a signed object bound to who, what, which resource, which version, which policy, until when.', i: 'Issuer decision', o: 'Capability accepted or rejected at execution time', trust: 'Verified by the monitor at use time', impl: 'LOCALLY_TESTED', note: 'HMAC-SHA256 capabilities; version and policy binding; single-use nonce; revocation by id and epoch.', open: 'Delegation with attenuation; asymmetric signatures; authenticated principals', ref: '§9.17, §9.18' },
  { n: 6, t: 'Execution boundary', p: 'The channel through which a protected effect actually happens. Complete mediation means no other channel exists.', i: 'Authorization from the monitor', o: 'Committed effect', trust: 'Must be enforced by the environment, not by the monitor', impl: 'OPEN', note: 'In v0.1 the boundary is a class convention inside one process. Same-user code can write the files directly.', open: 'Condition C1: channel completeness; roadmap v0.2 OS-level privilege separation', ref: '§9.20, §9.25' },
  { n: 7, t: 'Evidence, governance and assurance', p: 'Tamper-evident records, release gates, independent review, incident response.', i: 'Every decision', o: 'Reconstructible evidence and an assurance case', trust: 'Evidence path must itself be trusted (C8)', impl: 'IMPLEMENTED', note: 'Local hash-chained records only. Governance, external witness and review are not implemented.', open: 'Condition C8; independent audit; external witness', ref: '§9.26, §9.27, §10' },
]

const CONDS = [
  { id: 'C1', n: 'Complete mediation (GC)', s: 'OPEN', t: 'Not established. Bypass probe: same-uid writes succeed; detected on the next mediated request.' },
  { id: 'C2', n: 'Trusted-core integrity (TCB)', s: 'IMPLEMENTED', t: 'Core is small and isolated in governor/, but integrity is not enforced or proven.' },
  { id: 'C3', n: 'Kernel conformance (KVC)', s: 'OPEN', t: 'No verified semantics; tests only.' },
  { id: 'C4', n: 'Policy-artifact verification (PAV)', s: 'OPEN', t: 'Executable admission check; no machine-checked refinement.' },
  { id: 'C5', n: 'Principal attribution (PA)', s: 'LOCALLY_TESTED', t: 'Capabilities are principal-bound and signed; the requester’s identity is a declared string, not authenticated.' },
  { id: 'C6', n: 'Atomic revalidation (ARV)', s: 'LOCALLY_TESTED', t: 'One lock around check + commit; in-process only.' },
  { id: 'C7', n: 'Fail-closed handling (FC)', s: 'LOCALLY_TESTED', t: 'UNKNOWN → BLOCK for injected faults; real infrastructure faults untested.' },
  { id: 'C8', n: 'Evidence-path integrity (EPI)', s: 'IMPLEMENTED', t: 'Hash-chained local log; no external witness.' },
]

export default function Architecture() {
  const missing = results.pipeline.filter((c) => !(c in CHECKS))
  if (missing.length) throw new Error(`lib/pipeline.ts has no description for: ${missing.join(', ')}`)
  const rows = results.pipeline.map((c, i) => ({ i: i + 1, c }))

  return (
    <div className="shell page">
      <JsonLd data={breadcrumbs([{ name: 'Architecture', path: '/architecture/' }])} />
      <header className="page-head">
        <p className="kicker">Architecture</p>
        <h1>Seven layers, one implemented core</h1>
        <p className="lede">
          The paper separates what is philosophically derived, constitutionally declared, mechanically enforced, and empirically measured. No layer is allowed to stand in for another. This page says which layers exist as code today.
        </p>
      </header>

      <h2>The request path</h2>
      <Flow />

      <h2 id="layers">The layers</h2>
      <p className="measure">Section references are to the paper&apos;s own numbering. Implementation status uses the <Link href="/evidence/#claims">claim vocabulary</Link>.</p>
      <ol className="layers">
        {LAYERS.map((l) => (
          <li key={l.n} className="layer">
            <div className="layer-n" aria-hidden="true">{l.n}</div>
            <div className="layer-b">
              <h3>{l.t} <span className="muted small">paper {l.ref}</span></h3>
              <p>{l.p}</p>
              <dl className="kv kv-wide">
                <div><dt>input</dt><dd>{l.i}</dd></div>
                <div><dt>output</dt><dd>{l.o}</dd></div>
                <div><dt>trust status</dt><dd>{l.trust}</dd></div>
                <div><dt>implemented here</dt><dd><StatusChip status={l.impl} /> {l.note}</dd></div>
                <div><dt>open obligations</dt><dd>{l.open}</dd></div>
              </dl>
            </div>
          </li>
        ))}
      </ol>

      <h2 id="conditions">The paper&apos;s conditions C1–C8 versus this prototype</h2>
      <p className="measure">
        The conditional behavioural safety theorem holds only if all eight conditions hold for a deployment. A prototype that demonstrates some of them has not demonstrated the theorem.
      </p>
      <DataTable
        caption="Conditions C1 to C8 and their status in this prototype"
        rowKey={(r) => r.id}
        rows={CONDS}
        cols={[
          { key: 'id', label: 'ID', mono: true },
          { key: 'n', label: 'Condition' },
          { key: 's', label: 'Status', render: (r) => <StatusChip status={r.s} /> },
          { key: 't', label: 'What is and is not shown' },
        ]}
      />

      <h2 id="checks">The monitor&apos;s ordered checks</h2>
      <p className="measure">
        Every request runs these in order and stops at the first failure. The list below comes from <code>results.json</code>, so it cannot drift from the code that produced the results. Source: <a href={repoFile('governor/monitor.py')} rel="noopener">governor/monitor.py</a>.
      </p>
      <DataTable
        caption="Ordered monitor checks"
        rowKey={(r) => r.c}
        rows={rows}
        cols={[
          { key: 'i', label: '#', num: true },
          { key: 'c', label: 'Check', mono: true, render: (r) => label(r.c) },
          { key: 'w', label: 'Rejects when…', render: (r) => CHECKS[r.c].what },
          { key: 'r', label: 'Reason codes', mono: true, render: (r) => CHECKS[r.c].reasons },
        ]}
      />
      <p className="caveat">
        Fail-safe rule: any check that cannot be resolved is UNKNOWN, and UNKNOWN maps to BLOCK for every protected effect in this profile. An unexpected internal error is also treated as UNKNOWN.
      </p>
    </div>
  )
}
