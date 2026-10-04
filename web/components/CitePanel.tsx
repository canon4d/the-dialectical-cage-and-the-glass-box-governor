'use client'

import { useState } from 'react'
import CopyButton from './CopyButton'

export default function CitePanel({ formats }: { formats: { id: string; label: string; text: string }[] }) {
  const [id, setId] = useState(formats[0].id)
  const cur = formats.find((f) => f.id === id) ?? formats[0]
  return (
    <div className="cite">
      <div className="tabs" role="tablist" aria-label="Citation format">
        {formats.map((f) => (
          <button key={f.id} role="tab" type="button" id={`tab-${f.id}`} aria-selected={f.id === id}
            aria-controls="cite-panel" tabIndex={f.id === id ? 0 : -1} onClick={() => setId(f.id)}>{f.label}</button>
        ))}
      </div>
      <div id="cite-panel" role="tabpanel" aria-labelledby={`tab-${cur.id}`}>
        <pre tabIndex={0} aria-label={`${cur.label} citation (scrollable)`}><code>{cur.text}</code></pre>
        <CopyButton text={cur.text} label={`Copy ${cur.label}`} />
      </div>
    </div>
  )
}
