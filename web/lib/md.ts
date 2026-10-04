/** Tiny markdown reader for the one file the site renders verbatim (LIMITATIONS.md). */
export type Block =
  | { type: 'h1'; text: string }
  | { type: 'h2'; text: string }
  | { type: 'p'; text: string }
  | { type: 'ol'; items: string[] }
  | { type: 'ul'; items: string[] }

export function parseMd(src: string): Block[] {
  const out: Block[] = []
  let list: { type: 'ol'; items: string[] } | { type: 'ul'; items: string[] } | null = null
  let para: string[] = []
  const flushP = () => { if (para.length) { out.push({ type: 'p', text: para.join(' ') }); para = [] } }
  const flushL = () => { if (list) { out.push(list); list = null } }
  for (const raw of src.split('\n')) {
    const line = raw.trimEnd()
    if (!line.trim()) { flushP(); flushL(); continue }
    let m = /^(#{1,2})\s+(.*)$/.exec(line)
    if (m) { flushP(); flushL(); out.push(m[1].length === 1 ? { type: 'h1', text: m[2] } : { type: 'h2', text: m[2] }); continue }
    m = /^\d+\.\s+(.*)$/.exec(line)
    if (m) { flushP(); if (!list || list.type !== 'ol') { flushL(); list = { type: 'ol', items: [] } } list!.items.push(m[1]); continue }
    m = /^[-*]\s+(.*)$/.exec(line)
    if (m) { flushP(); if (!list || list.type !== 'ul') { flushL(); list = { type: 'ul', items: [] } } list!.items.push(m[1]); continue }
    if (list && /^\s+\S/.test(line)) { list.items[list.items.length - 1] += ' ' + line.trim(); continue }
    flushL(); para.push(line.trim())
  }
  flushP(); flushL()
  return out
}

export type Inline = { t: 'text' | 'b' | 'code'; s: string }
export function inline(src: string): Inline[] {
  const out: Inline[] = []
  const re = /(\*\*[^*]+\*\*|`[^`]+`)/g
  let last = 0
  for (const m of src.matchAll(re)) {
    const i = m.index ?? 0
    if (i > last) out.push({ t: 'text', s: src.slice(last, i) })
    const tok = m[0]
    out.push(tok.startsWith('**') ? { t: 'b', s: tok.slice(2, -2) } : { t: 'code', s: tok.slice(1, -1) })
    last = i + tok.length
  }
  if (last < src.length) out.push({ t: 'text', s: src.slice(last) })
  return out
}
