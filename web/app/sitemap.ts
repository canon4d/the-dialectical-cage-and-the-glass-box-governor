import type { MetadataRoute } from 'next'
import { NAV, SITE, abs } from '@/lib/site'
import { meta } from '@/lib/data'

export const dynamic = 'force-static'

/**
 * `lastModified` is the date of the evidence release (from results.json via web/content/meta.json),
 * not the build time: a deploy that changes nothing must not claim a content change.
 */
export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date(`${meta.lastmod}T00:00:00Z`)
  return [
    { url: abs('/'), lastModified, changeFrequency: 'monthly', priority: 1 },
    ...NAV.map((n) => ({
      url: abs(n.href), lastModified, changeFrequency: 'monthly' as const,
      priority: n.href === '/evidence/' || n.href === '/limitations/' ? 0.9 : 0.8,
    })),
    { url: abs(SITE.pdf), lastModified, changeFrequency: 'yearly', priority: 0.6 },
  ]
}
