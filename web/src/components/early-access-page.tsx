import Link from 'next/link'
export function EarlyAccessPage({ brand, eyebrow, headline, copy, contactHref = '/contact' }: { brand: string; eyebrow: string; headline: string; copy: string; contactHref?: string }) {
  return <main className="ecosystem-page"><section className="ecosystem-hero"><div className="section-inner"><div className="ecosystem-eyebrow">{eyebrow}</div><div className="ecosystem-brand">{brand}</div><h1>{headline}</h1><p>{copy}</p><div className="ecosystem-actions"><Link href={contactHref} className="ecosystem-primary">REGISTER INTEREST</Link><Link href="/" className="ecosystem-secondary">BACK TO LIVENZA.LIFE</Link></div></div></section></main>
}
