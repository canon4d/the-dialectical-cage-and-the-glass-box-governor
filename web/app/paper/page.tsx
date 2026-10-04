import type { Metadata } from 'next'
import fs from 'node:fs'
import path from 'node:path'
import CitePanel from '@/components/CitePanel'
import CodeBlock from '@/components/CodeBlock'
import JsonLd from '@/components/JsonLd'
import { StatusChip } from '@/components/Chip'
import { claims, manifest, releaseLabel } from '@/lib/data'
import { apa, bibtex, ris } from '@/lib/cite'
import { breadcrumbs, pageMeta } from '@/lib/seo'
import { SITE, abs, repoFile } from '@/lib/site'

const abstract: string[] = fs.readFileSync(path.join(process.cwd(), 'content', 'abstract.txt'), 'utf8').trim().split(/\n\s*\n/)

export const metadata: Metadata = pageMeta({
  title: 'Paper',
  description: `${SITE.paperTitle}: ${SITE.paperSubtitle}. Abstract, PDF, LaTeX source, citation formats, and how the paper’s scope relates to the prototype.`,
  path: '/paper/',
  other: {
    citation_title: `${SITE.paperTitle}: ${SITE.paperSubtitle}`,
    citation_author: SITE.author,
    citation_publication_date: SITE.paperDate.replace(/-/g, '/'),
    citation_pdf_url: abs(SITE.pdf),
    citation_abstract_html_url: abs('/paper/'),
    citation_language: 'en',
    ...(SITE.doiLive ? { citation_doi: SITE.doi } : {}),
  },
})

const ld = {
  '@context': 'https://schema.org',
  '@type': 'ScholarlyArticle',
  '@id': `${SITE.origin}/paper/#article`,
  headline: SITE.paperTitle,
  alternativeHeadline: SITE.paperSubtitle,
  url: abs('/paper/'),
  datePublished: SITE.paperDate,
  inLanguage: 'en',
  author: { '@id': `${SITE.origin}/#author` },
  abstract: abstract[0],
  keywords: 'AI safety, runtime verification, capability security, constitutional governance, neuro-symbolic systems, policy compilation, semantic uncertainty, agent security',
  isAccessibleForFree: true,
  encoding: { '@type': 'MediaObject', contentUrl: abs(SITE.pdf), encodingFormat: 'application/pdf' },
  ...(SITE.doiLive ? { sameAs: SITE.doiUrl, identifier: { '@type': 'PropertyValue', propertyID: 'DOI', value: SITE.doi } } : {}),
  workExample: { '@type': 'SoftwareSourceCode', codeRepository: SITE.repo, name: 'Glass-Box Governor prototype v0.1' },
}

export default function Paper() {
  const formats = [
    { id: 'bibtex', label: 'BibTeX', text: bibtex() },
    { id: 'apa', label: 'APA', text: apa() },
    { id: 'ris', label: 'RIS', text: ris() },
  ]
  const epi = Object.entries(claims.epistemic_labels)
  return (
    <div className="shell page">
      <JsonLd data={ld} />
      <JsonLd data={breadcrumbs([{ name: 'Paper', path: '/paper/' }])} />
      <header className="page-head">
        <p className="kicker">Paper · framework specification · independent research</p>
        <h1>{SITE.paperTitle}</h1>
        <p className="lede">{SITE.paperSubtitle}</p>
        <p className="byline">{SITE.author} · Independent Researcher · <a href={`mailto:${SITE.email}`}>{SITE.email}</a></p>
        <div className="btn-row">
          <a className="btn btn-primary" href={SITE.pdf}>Download PDF</a>
          <a className="btn" href={SITE.tex}>LaTeX source</a>
          <a className="btn" href={SITE.doiUrl} rel="noopener">DOI {SITE.doi}</a>
          <a className="btn" href={`${SITE.repo}/releases`} rel="noopener">GitHub release</a>
        </div>
        {!SITE.doiLive && (
          <p className="small muted">The DOI is reserved and resolves once the Zenodo record is published. Until then this page, the PDF above, and the repository are the sources.</p>
        )}
      </header>

      <div className="callout">
        <strong>Paper scope versus prototype scope</strong>
        <p>
          The paper specifies a broader framework and a <em>conditional</em> execution theorem. The current repository demonstrates only the explicitly enumerated prototype profile and components. It does not claim that the complete conceptual specification has been implemented, and the paper itself lists machine-checked proofs, implementation, red-teaming and production evidence as release conditions.
        </p>
      </div>

      <h2 id="abstract">Abstract</h2>
      <div className="prose">
        {abstract.map((p) => <p key={p.slice(0, 40)}>{p}</p>)}
      </div>

      <h2 id="status">Implementation status of this release</h2>
      <p className="measure">
        Release {releaseLabel()} implements selected execution-security components for one profile (<a href="/architecture/">Architecture</a>). In the claim registry, <StatusChip status="SPECIFIED" /> marks what the paper states and this repository does not test, <StatusChip status="LOCALLY_TESTED" /> what the author&apos;s corpus exercises, and <StatusChip status="OPEN" /> what is not established. The philosophical derivations (L1, NRD, CR/CAR) are not implemented or machine-checked here.
      </p>

      <h2 id="labels">The paper&apos;s epistemic labels</h2>
      <p className="measure">These are labels for the kind of claim, not confidence scores.</p>
      <dl className="labels">
        {epi.map(([k, v]) => (
          <div key={k}><dt className={`chip ep-${k}`}><b>{k}</b></dt><dd>{v}</dd></div>
        ))}
      </dl>

      <h2 id="verify">Verify the files you downloaded</h2>
      <CodeBlock label="shell" code={`sha256sum the-dialectical-cage-and-the-glass-box-governor.pdf\n# expected: ${manifest.paper.pdf_sha256}\nsha256sum the-dialectical-cage-and-the-glass-box-governor.tex\n# expected: ${manifest.paper.source_sha256}`} />
      <p className="small muted">Hashes come from <a href="/data/manifest.json">manifest.json</a>. The mapping from public claims to paper sections is in <a href={repoFile('research/SOURCE_MAP.md')} rel="noopener">SOURCE_MAP.md</a>.</p>

      <h2 id="cite">Cite this paper</h2>
      <CitePanel formats={formats} />
      <p className="small muted">Citing software instead? The repository carries <a href={repoFile('CITATION.cff')} rel="noopener">CITATION.cff</a>.</p>
    </div>
  )
}
