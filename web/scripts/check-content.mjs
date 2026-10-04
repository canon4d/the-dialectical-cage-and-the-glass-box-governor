// Runs before `next build`. Fails the build early if the synced evidence files are
// missing or malformed, so a broken deploy can never show stale or empty evidence.
import { readFileSync, existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const need = [
  'content/results.json', 'content/manifest.json', 'content/CLAIMS.json', 'content/meta.json',
  'content/abstract.txt', 'content/limitations.md',
  'public/paper/the-dialectical-cage-and-the-glass-box-governor.pdf',
  'public/paper/the-dialectical-cage-and-the-glass-box-governor.tex',
  'public/assets/og-card.png', 'public/assets/icon-192.png', 'public/assets/icon-512.png',
  'public/assets/icon-maskable-512.png', 'public/assets/apple-touch-icon.png', 'public/favicon.ico',
]
const problems = []
for (const f of need) if (!existsSync(join(root, f))) problems.push(`missing: ${f}`)
if (!problems.length) {
  const r = JSON.parse(readFileSync(join(root, 'content/results.json'), 'utf8'))
  for (const k of ['headline', 'arms', 'families', 'ablations', 'races', 'demonstrations', 'pipeline', 'core_sha256'])
    if (!(k in r)) problems.push(`results.json lacks "${k}" — run: python3 scripts/run_release_tests.py && python3 scripts/sync_web_data.py`)
  if (r.test_suite?.failed) problems.push('results.json records failing tests')
  if (r.claim_scope?.complete_mediation !== 'NOT_ESTABLISHED') problems.push('claim_scope.complete_mediation must be NOT_ESTABLISHED for v0.1')
}
if (problems.length) {
  console.error('\ncontent check failed:\n' + problems.map((p) => '  - ' + p).join('\n') + '\n')
  process.exit(1)
}
console.log('content check ok')
