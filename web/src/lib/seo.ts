import type { Metadata } from 'next'

export const SITE_ORIGIN = (process.env.LIVENZA_SITE_URL ?? 'https://livenza.life').replace(/\/$/, '')

export function buildMetadata(input: { title: string; description: string; path: string }): Metadata {
  const canonical = `${SITE_ORIGIN}${input.path.startsWith('/') ? input.path : `/${input.path}`}`
  return {
    title: input.title,
    description: input.description,
    alternates: { canonical },
    openGraph: { title: input.title, description: input.description, url: canonical, siteName: 'Livenza.life', type: 'website' },
  }
}
