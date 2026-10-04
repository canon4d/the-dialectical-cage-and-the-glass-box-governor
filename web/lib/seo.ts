import type { Metadata } from 'next'
import { SITE, abs } from './site'

export function pageMeta(o: { title: string; description: string; path: string; other?: Record<string, string | string[]> }): Metadata {
  const url = abs(o.path)
  return {
    title: o.title,
    description: o.description,
    alternates: { canonical: o.path },
    openGraph: {
      type: 'website', siteName: SITE.name, title: `${o.title} — ${SITE.name}`, description: o.description, url,
      images: [{ url: '/assets/og-card.png', width: 1200, height: 630, alt: `${SITE.name}: ${SITE.tagline}` }],
    },
    twitter: { card: 'summary_large_image', title: `${o.title} — ${SITE.name}`, description: o.description, images: ['/assets/og-card.png'] },
    other: o.other,
  }
}

export function breadcrumbs(items: { name: string; path: string }[]) {
  return {
    '@context': 'https://schema.org', '@type': 'BreadcrumbList',
    itemListElement: [{ name: 'Home', path: '/' }, ...items].map((it, i) => ({
      '@type': 'ListItem', position: i + 1, name: it.name, item: abs(it.path),
    })),
  }
}
