import type { NextConfig } from 'next'

const apiOrigin = process.env.LIVENZA_API_ORIGIN ?? 'http://127.0.0.1:5000'
const renderCommit = process.env.RENDER_GIT_COMMIT?.trim() || 'local'

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-Livenza-Git-Commit', value: renderCommit },
        ],
      },
    ]
  },
  async rewrites() {
    return [
      { source: '/api/:path*', destination: `${apiOrigin}/api/:path*` },
      { source: '/backoffice', destination: `${apiOrigin}/backoffice/` },
      { source: '/backoffice/:path*', destination: `${apiOrigin}/backoffice/:path*` },
    ]
  },
  images: { remotePatterns: [] },
}

export default nextConfig
