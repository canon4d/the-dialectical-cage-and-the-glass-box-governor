import type { MetadataRoute } from 'next'
import { SITE } from '@/lib/site'

export const dynamic = 'force-static'

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: '/',
    name: `${SITE.name} — ${SITE.tagline}`,
    short_name: 'Glass-Box',
    description: SITE.description,
    start_url: '/',
    scope: '/',
    display: 'standalone',
    orientation: 'any',
    lang: 'en',
    background_color: '#eeefea',
    theme_color: '#14191e',
    categories: ['security', 'education', 'science'],
    icons: [
      { src: '/assets/favicon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any' },
      { src: '/assets/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
      { src: '/assets/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
      { src: '/assets/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
    ],
    shortcuts: [
      { name: 'Evidence', url: '/evidence/' },
      { name: 'Reproduce', url: '/reproducibility/' },
      { name: 'Limitations', url: '/limitations/' },
    ],
  }
}
