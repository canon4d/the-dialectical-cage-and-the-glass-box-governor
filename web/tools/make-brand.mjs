// Regenerates every icon and the social card from one source of truth (the SVG mark below).
// Usage: npm i --no-save sharp && node tools/make-brand.mjs
import sharp from 'sharp'
import { writeFileSync, readFileSync } from 'node:fs'

const INK = '#14191e', PAPER = '#eeefea', ROSE = '#c2717f'

// Same badge, orbit rings and accent line as necessaryuniverse.com, plus one dot where the
// line crosses the centre: the monitor sitting on the path of the request.
const markInner = `
  <path opacity="0.45" d="M16 28C18.7614 28 21 22.6274 21 16C21 9.37258 18.7614 4 16 4C13.2386 4 11 9.37258 11 16C11 22.6274 13.2386 28 16 28Z" stroke="#EEEFEA" stroke-width="1.4"/>
  <path d="M16 22.4C22.6274 22.4 28 19.5346 28 16C28 12.4654 22.6274 9.60001 16 9.60001C9.37258 9.60001 4 12.4654 4 16C4 19.5346 9.37258 22.4 16 22.4Z" stroke="#EEEFEA" stroke-width="1.4"/>
  <path d="M6.80835 12.343L25.3177 19.6477" stroke="${ROSE}" stroke-width="2" stroke-linecap="round"/>
  <circle cx="16" cy="15.97" r="2.3" fill="${ROSE}" stroke="${INK}" stroke-width="1"/>`
const badge = `<path d="M26 0H6C2.68629 0 0 2.68629 0 6V26C0 29.3137 2.68629 32 6 32H26C29.3137 32 32 29.3137 32 26V6C32 2.68629 29.3137 0 26 0Z" fill="${INK}"/>`
const svg = (inner, size = 32) => `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 32 32" fill="none">${inner}</svg>`

writeFileSync('public/assets/favicon.svg', svg(badge + markInner) + '\n')
writeFileSync('public/favicon.svg', svg(badge + markInner) + '\n')
// Safari pinned-tab: single colour, no background
writeFileSync('public/assets/mask-icon.svg', svg(`<g stroke="#000" stroke-width="1.6"><ellipse cx="16" cy="16" rx="12" ry="6.4"/><ellipse cx="16" cy="16" rx="5" ry="12"/><path d="M6.8 12.3 25.3 19.6" stroke-linecap="round"/></g><circle cx="16" cy="15.97" r="2.3" fill="#000"/>`) + '\n')

const png = (s, file, svgText) => sharp(Buffer.from(svgText), { density: 384 }).resize(s, s).png().toFile(file)
const rounded = svg(badge + markInner)
// full-bleed square with the mark scaled down so maskable / apple icons survive any crop
const full = (scale) => svg(`<rect width="32" height="32" fill="${INK}"/><g transform="translate(${16 - 16 * scale} ${16 - 16 * scale}) scale(${scale})">${markInner}</g>`)

await png(192, 'public/assets/icon-192.png', rounded)
await png(512, 'public/assets/icon-512.png', rounded)
await png(512, 'public/assets/icon-maskable-512.png', full(0.62))
await png(180, 'public/assets/apple-touch-icon.png', full(0.8))
const sizes = [16, 32, 48]
const imgs = []
for (const s of sizes) imgs.push(await sharp(Buffer.from(rounded), { density: 384 }).resize(s, s).png().toBuffer())

// ICO container with PNG payloads
const head = Buffer.alloc(6); head.writeUInt16LE(0, 0); head.writeUInt16LE(1, 2); head.writeUInt16LE(sizes.length, 4)
let off = 6 + 16 * sizes.length
const dir = Buffer.concat(sizes.map((s, i) => {
  const e = Buffer.alloc(16); e[0] = s; e[1] = s; e.writeUInt16LE(1, 4); e.writeUInt16LE(32, 6)
  e.writeUInt32LE(imgs[i].length, 8); e.writeUInt32LE(off, 12); off += imgs[i].length; return e
}))
writeFileSync('public/favicon.ico', Buffer.concat([head, dir, ...imgs]))

// Social card 1200x630 (same layout language as the primary site's card)
const card = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="${PAPER}"/>
  <g transform="translate(72 56)">${badge}${markInner}</g>
  <text x="116" y="80" font-family="Liberation Sans, Archivo, Arial, sans-serif" font-weight="700" font-size="24" fill="${INK}">Glass-Box Governor</text>
  <text x="72" y="215" font-family="Liberation Sans, Archivo, Arial, sans-serif" font-weight="700" font-size="84" letter-spacing="-3" fill="${INK}">The model proposes.</text>
  <text x="72" y="305" font-family="Liberation Sans, Archivo, Arial, sans-serif" font-weight="700" font-size="84" letter-spacing="-3" fill="#8a3b4a">The monitor decides.</text>
  <text x="72" y="378" font-family="Liberation Serif, Source Serif 4, Georgia, serif" font-size="29" fill="#3c4750">An external execution boundary for AI agents, with a reproducible</text>
  <text x="72" y="416" font-family="Liberation Serif, Source Serif 4, Georgia, serif" font-size="29" fill="#3c4750">prototype, an attack corpus, and a list of what is not established.</text>
  <line x1="72" y1="522" x2="1128" y2="522" stroke="#d4d8d2" stroke-width="2"/>
  <text x="72" y="568" font-family="Liberation Mono, JetBrains Mono, monospace" font-size="22" fill="#6c7883">protected-file-v1   v0.1.0   ai.necessaryuniverse.com</text>
</svg>`
await sharp(Buffer.from(card), { density: 96 }).png().toFile('public/assets/og-card.png')
console.log('brand assets written')
