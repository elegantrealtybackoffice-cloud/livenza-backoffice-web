import { describe, expect, it } from 'vitest'
import nextConfig from '../../next.config'

const apiOrigin = process.env.LIVENZA_API_ORIGIN ?? 'http://127.0.0.1:5000'

describe('backoffice routing', () => {
  it('preserves the backoffice prefix when rewriting to Flask', async () => {
    expect(nextConfig.rewrites).toBeTypeOf('function')
    const rewrites = await nextConfig.rewrites!()
    expect(rewrites).toEqual(
      expect.arrayContaining([
        {
          source: '/api/:path*',
          destination: `${apiOrigin}/api/:path*`,
        },
        {
          source: '/backoffice',
          destination: `${apiOrigin}/backoffice`,
        },
        {
          source: '/backoffice/:path*',
          destination: `${apiOrigin}/backoffice/:path*`,
        },
      ]),
    )
  })
})
