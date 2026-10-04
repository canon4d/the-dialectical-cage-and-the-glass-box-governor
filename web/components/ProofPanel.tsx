'use client'

import { useState } from 'react'
import type { Demo } from '@/lib/data'
import { label } from '@/lib/pipeline'

const ICON: Record<string, string> = { pass: '✓', fail: '✗', unknown: '?', skipped: '–' }
const WORD: Record<string, string> = { pass: 'passed', fail: 'failed', unknown: 'unknown (treated as block)', skipped: 'not reached' }

function capLines(cap: Demo['capability']): { k: string; v: string }[] {
  if (!cap) return [{ k: 'capability', v: 'none supplied' }]
  if ('capability_id' in cap) {
    const pick = ['capability_id', 'principal_id', 'effect', 'resource_id', 'resource_version', 'expires_at', 'revocation_epoch', 'one_shot']
    return pick.filter((k) => k in cap).map((k) => ({ k, v: String(cap[k]) }))
  }
  return [{ k: 'raw value', v: JSON.stringify(cap) }]
}

export default function ProofPanel({ demos, pipeline }: { demos: Demo[]; pipeline: string[] }) {
  const [id, setId] = useState(demos[0]?.id)
  const d = demos.find((x) => x.id === id) ?? demos[0]
  if (!d) return null
  const seen = new Map(d.trace.map((t) => [t.check, t.result]))
  const allowed = d.decision === 'ALLOW'

  return (
    <div className="proof" aria-label="Interactive proof panel">
      <div className="proof-pick" role="group" aria-label="Choose a scenario">
        {demos.map((x) => (
          <button key={x.id} type="button" className="pick" aria-pressed={x.id === d.id} onClick={() => setId(x.id)}>
            {x.id.replace(/-/g, ' ')}
          </button>
        ))}
      </div>

      <div className="proof-body" aria-live="polite">
        <div className="proof-col">
          <h3 className="proof-h">Request</h3>
          <dl className="kv">
            <div><dt>principal</dt><dd>{d.request.principal}</dd></div>
            <div><dt>effect</dt><dd>{d.request.effect}</dd></div>
            <div><dt>resource</dt><dd>{d.request.resource}</dd></div>
          </dl>
          <h3 className="proof-h">Capability presented</h3>
          <dl className="kv">
            {capLines(d.capability).map((l) => (
              <div key={l.k}><dt>{l.k}</dt><dd>{l.v}</dd></div>
            ))}
          </dl>
          <p className="proof-note">{d.title}</p>
        </div>

        <div className="proof-col">
          <h3 className="proof-h">Monitor checks, in order</h3>
          <ol className="checks">
            {pipeline.map((c) => {
              const r = seen.get(c) ?? 'skipped'
              return (
                <li key={c} className={`chk chk-${r}`}>
                  <span className="chk-i" aria-hidden="true">{ICON[r]}</span>
                  <span>{label(c)}</span>
                  <span className="sr-only"> — {WORD[r]}</span>
                </li>
              )
            })}
          </ol>
        </div>

        <div className="proof-col">
          <h3 className="proof-h">Outcome</h3>
          <div className={`verdict ${allowed ? 'v-allow' : 'v-block'}`}>
            <span className="verdict-w">{d.decision}</span>
            <span className="verdict-r">{d.reason_code}</span>
          </div>
          <dl className="kv">
            <div><dt>protected state changed</dt><dd><strong>{d.protected_state_changed ? 'YES' : 'NO'}</strong></dd></div>
            <div><dt>version</dt><dd>{d.version_before ?? '—'} → {d.version_after ?? '—'}</dd></div>
            <div><dt>evidence emitted</dt><dd>{d.event_id ? 'YES' : 'NO'}</dd></div>
            <div><dt>event id</dt><dd>{d.event_id ?? '—'}</dd></div>
            <div><dt>record integrity</dt><dd>{d.integrity ? `${d.integrity.slice(0, 16)}…` : '—'}</dd></div>
          </dl>
          {!allowed && (
            <p className="proof-note">
              Same attempt without the governor: Arm A (unconstrained) {d.baselines.A_executed ? <strong>changed the file</strong> : 'did not change the file'}; Arm B (containment-only model) {d.baselines.B_executed ? <strong>changed the file</strong> : 'did not change the file'}.
            </p>
          )}
        </div>
      </div>

      <p className="proof-foot">
        Replayed from <code>results.json</code> (scenario <code>{d.scenario}</code>), not computed in your browser. The authoritative evidence is the source, the tests, and the <a href="/reproducibility/">command you run locally</a>.
      </p>
    </div>
  )
}
