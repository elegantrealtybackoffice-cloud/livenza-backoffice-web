import type { NextConfig } from 'next'

const apiOrigin = process.env.LIVENZA_API_ORIGIN ?? 'http://127.0.0.1:5000'

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: '/api/:path*', destination: `${apiOrigin}/api/:path*` },
      { source: '/backoffice', destination: `${apiOrigin}/backoffice` },
      { source: '/backoffice/:path*', destination: `${apiOrigin}/backoffice/:path*` },
    ]
  },
  images: { remotePatterns: [] },
}

export default nextConfig
