# ai.necessaryuniverse.com — website

Next.js (App Router) static export, deployed on Vercel with **Root Directory = `web`**.

```bash
npm install
npm run dev        # http://localhost:3000
npm run build      # prebuild check -> next build -> ./out
npm run typecheck
```

The site is a presentation layer. It reads `content/results.json`, `content/CLAIMS.json` and friends, which
`python3 scripts/sync_web_data.py` copies from the repository root. It computes nothing and contains no
second implementation of the monitor.

| Concern | Where |
|---|---|
| Names, URLs, DOI state | `lib/site.ts` |
| Colours, type, responsive rules | `app/globals.css` |
| robots / sitemap / manifest / llms.txt | `app/robots.ts`, `app/sitemap.ts`, `app/manifest.ts`, `app/llms.txt/route.ts` |
| Icons and social card | `public/assets/*` (regenerate: `npm i --no-save sharp && npm run brand`) |
| Headers, CSP, caching | `vercel.json` |
| Analytics ID (GA4) | `lib/site.ts` → `gaId` (loaded in `app/layout.tsx`; allowed in `vercel.json` CSP) |
| Security contact | `public/.well-known/security.txt` (renew `Expires` yearly) |

Responsive behaviour: fluid type and gutters, a menu button below 52rem, tables that turn into labelled
cards below 44rem, a three-column proof panel that collapses to one, 44px touch targets, safe-area insets,
light/dark themes, reduced-motion and print styles.
