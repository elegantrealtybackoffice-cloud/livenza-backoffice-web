import type { Metadata } from 'next'
import './globals.css'
import { SiteHeader } from '@/components/site-header'
import { SiteFooter } from '@/components/site-footer'

export const metadata: Metadata = {
  title: { default: 'Livenza.life — Live More', template: '%s | Livenza.life' },
  description: 'Livenza.life is a premium lifestyle ecosystem for stays, style, movement and everyday living.',
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body data-brand="life"><div className="site-shell"><SiteHeader />{children}<SiteFooter /></div></body></html>
}
