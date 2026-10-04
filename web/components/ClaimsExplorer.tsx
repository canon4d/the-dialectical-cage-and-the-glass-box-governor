'use client'

import { useMemo, useState } from 'react'
import type { Claim } from '@/lib/data'
import { EpiChip, StatusChip } from './Chip'

export default function ClaimsExplorer({ claims, vocab }: { claims: Claim[]; vocab: Record<string, string> }) {
  const [f, setF] = useState<string>('ALL')
  const counts = useMemo(() => {
    const c: Record<string, number> = {}
    claims.forEach((x) => { c[x.status] = (c[x.status] ?? 0) + 1 })
    return c
  }, [claims])
  const shown = f === 'ALL' ? claims : claims.filter((c) => c.status === f)
  const statuses = Object.keys(counts)

  return (
    <div className="claims">
      <div className="filters" role="group" aria-label="Filter claims by status">
        <button type="button" className="pick" aria-pressed={f === 'ALL'} onClick={() => setF('ALL')}>All ({claims.length})</button>
        {statuses.map((s) => (
          <button key={s} type="button" className="pick" aria-pressed={f === s} onClick={() => setF(s)}>
            {s.replace(/_/g, ' ')} ({counts[s]})
          </button>
        ))}
      </div>
      {f !== 'ALL' && <p className="muted small">{vocab[f]}</p>}
      <ul className="claim-list">
        {shown.map((c) => (
          <li key={c.id} id={c.id} className="claim">
            <details>
              <summary>
                <span className="claim-id">{c.id}</span>
                <StatusChip status={c.status} />
                <EpiChip label={c.epistemic} />
                <span className="claim-text">{c.text}</span>
              </summary>
              <div className="claim-more">
                <p><strong>Scope.</strong> {c.scope}</p>
                {c.assumptions.length > 0 && <p><strong>Assumptions.</strong> {c.assumptions.join('; ')}</p>}
                {c.evidence.families && c.evidence.families.length > 0 && <p><strong>Attack families.</strong> {c.evidence.families.join(', ')}</p>}
                <p><strong>Known limitations.</strong></p>
                <ul>{c.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
              </div>
            </details>
          </li>
        ))}
      </ul>
    </div>
  )
}
