import type { Metadata } from 'next'
import fs from 'node:fs'
import path from 'node:path'
import Link from 'next/link'
import JsonLd from '@/components/JsonLd'
import { inline, parseMd } from '@/lib/md'
import type { Block } from '@/lib/md'
import { breadcrumbs, pageMeta } from '@/lib/seo'
import { repoFile } from '@/lib/site'

export const metadata: Metadata = pageMeta({
  title: 'What this project does not prove',
  description: 'The honesty ledger for the Glass-Box Governor v0.1: complete mediation, kernel assurance, policy refinement, evidence, delegation, review and the residual region are not established.',
  path: '/limitations/',
})

function Inline({ s }: { s: string }) {
  return <>{inline(s).map((x, i) => (x.t === 'b' ? <strong key={i}>{x.s}</strong> : x.t === 'code' ? <code key={i}>{x.s}</code> : <span key={i}>{x.s}</span>))}</>
}

export default function Limitations() {
  const blocks: Block[] = parseMd(fs.readFileSync(path.join(process.cwd(), 'content', 'limitations.md'), 'utf8'))
  return (
    <div className="shell page">
      <JsonLd data={breadcrumbs([{ name: 'Limitations', path: '/limitations/' }])} />
      <header className="page-head">
        <p className="kicker">Limitations</p>
        <h1>What this project does not prove</h1>
        <p className="lede">
          A serious reviewer should find this page first. It is rendered directly from <a href={repoFile('LIMITATIONS.md')} rel="noopener">LIMITATIONS.md</a> in the repository, so the site cannot say something softer than the repository does.
        </p>
      </header>

      <div className="callout callout-warn">
        <strong>Headline:</strong> the monitor is demonstrated on a closed two-file, two-effect surface, in one process, by tests the author wrote. Complete mediation, kernel assurance, machine-checked policy refinement and independent review are not established. See the <Link href="/evidence/#mediation">bypass probe</Link>.
      </div>

      <div className="ledger">
        {blocks.map((b, i) => {
          if (b.type === 'h1') return null // page title is rendered above
          if (b.type === 'h2') return <h2 key={i}>{b.text}</h2>
          if (b.type === 'p') return <p key={i} className="measure"><Inline s={b.text} /></p>
          if (b.type === 'ol') return <ol key={i} className="ledger-ol">{b.items.map((t, j) => <li key={j}><Inline s={t} /></li>)}</ol>
          return <ul key={i} className="plain">{b.items.map((t, j) => <li key={j}><Inline s={t} /></li>)}</ul>
        })}
      </div>

      <p className="measure">
        Related: <a href={repoFile('THREAT_MODEL.md')} rel="noopener">threat model</a> · <a href={repoFile('profiles/PROTECTED-FILE-V1-CHANNEL-INVENTORY.md')} rel="noopener">channel inventory</a> · <Link href="/evidence/#claims">claim registry</Link>
      </p>
    </div>
  )
}
