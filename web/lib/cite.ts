import { SITE } from './site'

export const CITE_KEY = 'CanonGlassBox'
const doiNote = SITE.doiLive ? '' : ' (DOI reserved; resolves once the Zenodo record is published)'

export const bibtex = () => `@misc{${CITE_KEY},
  author       = {Canon},
  title        = {{${SITE.paperTitle}: ${SITE.paperSubtitle}}},
  year         = {${SITE.year}},
  publisher    = {Zenodo},
  doi          = {${SITE.doi}},
  url          = {${SITE.doiUrl}},
  note         = {Independent research; not peer-reviewed. Code: ${SITE.repo}}
}`

export const apa = () =>
  `Canon. (${SITE.year}). ${SITE.paperTitle}: ${SITE.paperSubtitle}. Zenodo. ${SITE.doiUrl}${doiNote}`

export const ris = () => `TY  - GEN
AU  - Canon
TI  - ${SITE.paperTitle}: ${SITE.paperSubtitle}
PY  - ${SITE.year}
PB  - Zenodo
DO  - ${SITE.doi}
UR  - ${SITE.doiUrl}
ER  - `
