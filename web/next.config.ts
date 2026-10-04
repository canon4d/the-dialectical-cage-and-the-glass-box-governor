import type { NextConfig } from 'next'

/**
 * Fully static output: `next build` writes a self-contained site to ./out.
 * Vercel serves it from the CDN; no Node runtime is needed in production, and
 * the same output also works on any other static host.
 */
const nextConfig: NextConfig = {
  output: 'export',
  trailingSlash: true,
  reactStrictMode: true,
  poweredByHeader: false,
  images: { unoptimized: true },
}

export default nextConfig
