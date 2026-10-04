import type { MetadataRoute } from 'next'
import { SITE } from '@/lib/site'

export const dynamic = 'force-static'

/**
 * Everything is allowed for everyone. This site exists to be read, cited and checked,
 * by people, search engines and AI systems alike. The wildcard rule is sufficient on its
 * own; the named groups are listed so the policy is auditable at a glance and so that
 * narrowing one group later cannot accidentally narrow every unnamed crawler.
 * To opt a crawler out, add an explicit `disallow` for it rather than deleting it here.
 */
const SEARCH_ENGINES = [
  'Googlebot', 'Googlebot-Image', 'Bingbot', 'Applebot', 'DuckDuckBot', 'Slurp',
  'YandexBot', 'Baiduspider', 'Yeti', 'SeznamBot', 'Qwantify', 'Sogou', 'ia_archiver',
]

const AI_CRAWLERS = [
  'GPTBot', 'ChatGPT-User', 'OAI-SearchBot',
  'ClaudeBot', 'anthropic-ai', 'Claude-User', 'Claude-SearchBot',
  'PerplexityBot', 'Perplexity-User',
  'Google-Extended', 'Google-CloudVertexBot', 'Applebot-Extended',
  'CCBot', 'Bytespider', 'Amazonbot',
  'Meta-ExternalAgent', 'Meta-ExternalFetcher', 'FacebookBot',
  'Diffbot', 'cohere-ai', 'cohere-training-data-crawler',
  'DuckAssistBot', 'MistralAI-User', 'YouBot', 'PetalBot', 'Ai2Bot',
  'Timpibot', 'omgili', 'ImagesiftBot',
]

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      { userAgent: '*', allow: '/' },
      { userAgent: SEARCH_ENGINES, allow: '/' },
      { userAgent: AI_CRAWLERS, allow: '/' },
    ],
    sitemap: `${SITE.origin}/sitemap.xml`,
  }
}
