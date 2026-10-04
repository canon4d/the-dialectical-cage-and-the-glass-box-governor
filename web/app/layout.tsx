import type { Metadata, Viewport } from 'next'
import Link from 'next/link'
import Script from 'next/script'
import type { ReactNode } from 'react'
import './globals.css'
import Header from '@/components/Header'
import JsonLd from '@/components/JsonLd'
import Logo from '@/components/Logo'
import { NAV, SITE, abs, repoFile } from '@/lib/site'
import { releaseLabel, results } from '@/lib/data'

export const metadata: Metadata = {
  metadataBase: new URL(SITE.origin),
  title: { default: `${SITE.name} — ${SITE.tagline}`, template: `%s — ${SITE.name}` },
  description: SITE.description,
  applicationName: SITE.name,
  authors: [{ name: SITE.author, url: SITE.parentOrigin }],
  creator: SITE.author,
  keywords: ['AI safety', 'AI agent security', 'reference monitor', 'capability security', 'runtime verification', 'fail-closed', 'TOCTOU', 'complete mediation', 'agent execution boundary'],
  alternates: { canonical: '/' },
  formatDetection: { telephone: false, email: false, address: false },
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: 'any' },
      { url: '/assets/favicon.svg', type: 'image/svg+xml' },
      { url: '/assets/icon-192.png', sizes: '192x192', type: 'image/png' },
      { url: '/assets/icon-512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [{ url: '/assets/apple-touch-icon.png', sizes: '180x180' }],
    other: [{ rel: 'mask-icon', url: '/assets/mask-icon.svg', color: '#8a3b4a' }],
  },
  openGraph: {
    type: 'website', siteName: SITE.name, locale: 'en_US', url: SITE.origin,
    title: `${SITE.name} — ${SITE.tagline}`, description: SITE.description,
    images: [{ url: '/assets/og-card.png', width: 1200, height: 630, alt: `${SITE.name}: ${SITE.tagline}` }],
  },
  twitter: {
    card: 'summary_large_image', title: `${SITE.name} — ${SITE.tagline}`, description: SITE.description,
    images: ['/assets/og-card.png'],
  },
  robots: {
    index: true, follow: true,
    googleBot: { index: true, follow: true, 'max-image-preview': 'large', 'max-snippet': -1, 'max-video-preview': -1 },
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  colorScheme: 'light dark',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#eeefea' },
    { media: '(prefers-color-scheme: dark)', color: '#0f1418' },
  ],
}

/* Applied before first paint so the chosen theme never flashes. */
const THEME_BOOT = `(function(){try{var s=localStorage.getItem('gbg-theme');var m=window.matchMedia('(prefers-color-scheme: dark)').matches;document.documentElement.setAttribute('data-theme',s||(m?'dark':'light'));}catch(e){document.documentElement.setAttribute('data-theme','light');}})();`

const siteLd = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'WebSite', '@id': `${SITE.origin}/#website`, url: SITE.origin, name: SITE.name,
      description: SITE.description, inLanguage: 'en',
      publisher: { '@id': `${SITE.origin}/#author` }, isPartOf: { '@type': 'WebSite', name: SITE.parentName, url: SITE.parentOrigin },
    },
    {
      '@type': 'Person', '@id': `${SITE.origin}/#author`, name: SITE.author, email: SITE.email,
      jobTitle: 'Independent researcher', url: SITE.parentOrigin,
    },
  ],
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOT }} />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=JetBrains+Mono:wght@400;500&display=swap" />
        <JsonLd data={siteLd} />
        {SITE.gaId && (
          <>
            <Script src={`https://www.googletagmanager.com/gtag/js?id=${SITE.gaId}`} strategy="afterInteractive" />
            <Script id="ga4-init" strategy="afterInteractive">
              {`window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${SITE.gaId}');`}
            </Script>
          </>
        )}
      </head>
      <body>
        <a className="skip" href="#main">Skip to content</a>
        <Header />
        <main id="main">{children}</main>

        <footer className="site-foot">
          <div className="shell">
            <div className="foot-grid">
              <div>
                <h2>This project</h2>
                <ul>
                  {NAV.map((n) => <li key={n.href}><Link href={n.href}>{n.label}</Link></li>)}
                </ul>
              </div>
              <div>
                <h2>Source and data</h2>
                <ul>
                  <li><a href={SITE.repo} rel="noopener">GitHub repository</a></li>
                  <li><a href={`${SITE.repo}/releases`} rel="noopener">Releases</a></li>
                  <li><a href="/data/results.json">results.json</a></li>
                  <li><a href="/data/CLAIMS.json">CLAIMS.json</a></li>
                  <li><a href={repoFile('SECURITY.md')} rel="noopener">Security policy</a></li>
                </ul>
              </div>
              <div>
                <h2>Paper</h2>
                <ul>
                  <li><a href={SITE.pdf}>PDF</a></li>
                  <li><a href={SITE.tex}>LaTeX source</a></li>
                  <li>
                    <a href={SITE.doiUrl} rel="noopener">DOI {SITE.doi}</a>
                    {!SITE.doiLive && <span className="muted small"> (reserved)</span>}
                  </li>
                </ul>
              </div>
              <div>
                <h2>Contact</h2>
                <ul>
                  <li><a href={`mailto:${SITE.email}`}>{SITE.email}</a></li>
                  <li><a href={SITE.parentOrigin} rel="noopener">{SITE.parentName}</a> <span className="muted small">(a separate project by Canon)</span></li>
                </ul>
              </div>
            </div>
            <div className="foot-base">
              <span className="foot-brand"><Logo size={20} /> {SITE.name}</span>
              <span>
                Independent research. Not peer-reviewed. Not independently audited. {releaseLabel()} · core hash <code>{results.core_sha256.slice(0, 12)}</code> · <a href={abs('/')}>ai.necessaryuniverse.com</a>
              </span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  )
}
