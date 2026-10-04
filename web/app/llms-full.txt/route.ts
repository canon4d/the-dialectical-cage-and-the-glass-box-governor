import fs from 'node:fs'
import path from 'node:path'
import { SITE, abs } from '@/lib/site'
import { claims, fmt, results, releaseLabel } from '@/lib/data'

export const dynamic = 'force-static'

/** Long-form plain text for AI systems: scope, results, claims and limitations in one fetch. */
export function GET() {
  const h = results.headline
  const lim = fs.readFileSync(path.join(process.cwd(), 'content', 'limitations.md'), 'utf8')
  const abstract = fs.readFileSync(path.join(process.cwd(), 'content', 'abstract.txt'), 'utf8').trim()
  const L: string[] = []
  L.push(`# ${SITE.name} — full text`, '', `Source: ${abs('/')} · Repository: ${SITE.repo} · Release: ${releaseLabel()}`, '')
  L.push('## What this is', '', 'A reference-monitor prototype for AI-agent execution security, an attack corpus, deterministic results, and the paper it accompanies. The model proposes an action; an independent monitor decides whether a declared protected effect may execute. Independent research; not peer-reviewed; not independently audited.', '')
  L.push('## Paper', '', `${SITE.paperTitle}: ${SITE.paperSubtitle}. ${SITE.author}, ${SITE.year}. DOI ${SITE.doi}${SITE.doiLive ? '' : ' (reserved; resolves when the Zenodo record is published)'}.`, '', abstract, '')
  L.push('## Results (generated from results.json)', '')
  L.push(`- Profile ${results.profile.id}; policy ${results.policy.version}; attack corpus ${results.test_suite.attack_corpus}; ${results.test_suite.passed}/${results.test_suite.total} tests passing.`)
  L.push(`- Full governor (Arm C): ${fmt(h.unauthorized_protected_executions)} unauthorized protected executions; ${fmt(h.protected_state_violations)} protected-state violations; ${fmt(h.legitimate_requests_completed)} legitimate requests completed.`)
  L.push(`- Same attacks with no monitor (Arm A): ${fmt(h.baseline_unauthorized_unconstrained)} changed protected state. Containment-only model (Arm B): ${fmt(h.baseline_unauthorized_containment_only)}.`)
  L.push(`- Concurrent double spends: ${fmt(h.race_double_spends_full_monitor)} with the full monitor; ${fmt(h.race_double_spends_non_atomic_ablation)} in a deliberately non-atomic variant.`)
  L.push('- These are finite observations under one profile and one corpus, not a proof of zero real-world risk.', '')
  L.push('## Attack families', '')
  for (const f of results.families) L.push(`- ${f.id} ${f.label}: ${f.passed}/${f.attempts} passed; ${f.protected_state_violations} protected-state violations`)
  L.push('', '## Claim registry', '')
  for (const c of claims.claims) L.push(`- ${c.id} [${c.status}; ${c.epistemic}] ${c.text} Scope: ${c.scope}. Limitations: ${c.limitations.join('; ')}.`)
  L.push('', '## Limitations (verbatim from LIMITATIONS.md)', '', lim.trim(), '')
  return new Response(L.join('\n'), { headers: { 'Content-Type': 'text/plain; charset=utf-8' } })
}
