'use client'

import Link from 'next/link'
import Image from 'next/image'
import { useState } from 'react'
import { whatsappHref } from '@/lib/brochure'

const verticals = [
  ['Stays', '/stays'], ['Fit', '/fit'], ['Store', '/store'],
  ['Groom', '/groom'], ['Skin', '/skin'], ['Media', '/media'],
] as const

export function SiteHeader() {
  const [open, setOpen] = useState(false)
  return <header className="site-header">
    <div className="header-inner">
      <Link href="/" className="brand-link brand-logo" aria-label="Livenza.life home"><span className="brand-logo-frame"><Image src="/stays/livenza-stays-logo.png" alt="Livenza Stays" width={180} height={180} priority /></span><span className="brand-site-label">LIVENZA.LIFE</span></Link>
      <nav className="primary-nav" aria-label="Livenza brands">
        {verticals.map(([label, href]) => <Link key={href} href={href}>{label}</Link>)}
      </nav>
      <nav className="utility-nav" aria-label="Primary">
        <Link href="/life">Life</Link><Link href="/about">About</Link><Link href="/account">Account</Link><a href={whatsappHref()} target="_blank" rel="noopener noreferrer" className="cta">ENQUIRE ON WHATSAPP ↗</a>
      </nav>
      <button className="mobile-menu-button" type="button" aria-label="Open menu" aria-expanded={open} onClick={() => setOpen(v => !v)}>{open ? 'Close' : 'Menu'}</button>
    </div>
    <nav className="mobile-panel" data-open={open} aria-label="Mobile">
      {verticals.map(([label, href]) => <Link key={href} href={href} onClick={() => setOpen(false)}>{label}</Link>)}
      <Link href="/life" onClick={() => setOpen(false)}>Life</Link><Link href="/about" onClick={() => setOpen(false)}>About</Link>
      <Link href="/account" onClick={() => setOpen(false)}>Account</Link><a href={whatsappHref()} target="_blank" rel="noopener noreferrer" className="cta" onClick={() => setOpen(false)}>ENQUIRE ON WHATSAPP ↗</a>
    </nav>
  </header>
}
