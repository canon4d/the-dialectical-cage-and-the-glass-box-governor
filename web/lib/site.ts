/** Single source for names, URLs and the DOI state. Nothing else hard-codes these. */
export const SITE = {
  name: 'Glass-Box Governor',
  origin: 'https://ai.necessaryuniverse.com',
  parentName: 'Necessary Universe',
  parentOrigin: 'https://necessaryuniverse.com',
  author: 'Canon',
  email: 'canon@necessaryuniverse.com',
  repo: 'https://github.com/canon4d/the-dialectical-cage-and-the-glass-box-governor',
  tagline: 'An external execution boundary for AI agents.',
  description:
    'A reproducible reference-monitor prototype and attack corpus for AI-agent execution security: the model proposes an action, an independent monitor decides whether a declared protected effect may execute. Includes the paper, the evidence, and an explicit list of what is not established.',
  paperTitle: 'The Dialectical Cage and the Glass-Box Governor',
  paperSubtitle:
    'A Practice-Based Ethics, Safety Constitution, and Reference-Monitor Architecture for AI Agents',
  paperDate: '2026-10-03',
  year: 2026,
  /** Published Zenodo DOI. `doiLive` must match results/manifest.json (built with `python3 scripts/build_manifest.py --doi 10.5281/zenodo.21278446`). */
  doi: '10.5281/zenodo.21278446',
  doiUrl: 'https://doi.org/10.5281/zenodo.21278446',
  doiLive: true,
  pdf: '/paper/the-dialectical-cage-and-the-glass-box-governor.pdf',
  tex: '/paper/the-dialectical-cage-and-the-glass-box-governor.tex',
  /** GA4 measurement id. Same property as necessaryuniverse.com; the hostname report separates the two sites.
   *  Override with the NEXT_PUBLIC_GA_ID env var in Vercel, or set to '' to disable analytics entirely. */
  gaId: process.env.NEXT_PUBLIC_GA_ID ?? 'G-3GRK4FC3E9',
} as const

export const NAV = [
  { href: '/architecture/', label: 'Architecture' },
  { href: '/evidence/', label: 'Evidence' },
  { href: '/paper/', label: 'Paper' },
  { href: '/reproducibility/', label: 'Reproduce' },
  { href: '/limitations/', label: 'Limitations' },
] as const

export const abs = (path: string) => `${SITE.origin}${path}`
export const repoFile = (p: string) => `${SITE.repo}/blob/main/${p}`
export const repoTree = (p: string) => `${SITE.repo}/tree/main/${p}`
