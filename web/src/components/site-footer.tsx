import Link from 'next/link'
import Image from 'next/image'
import { whatsappHref } from '@/lib/brochure'
export function SiteFooter() {
  return <footer className="site-footer"><div className="footer-inner">
    <div className="footer-grid">
      <div><Link href="/" className="brand-link brand-logo" aria-label="Livenza.life home"><span className="brand-logo-frame"><Image src="/stays/livenza-stays-logo.png" alt="Livenza Stays" width={180} height={180} /></span></Link><p>Thoughtful stays and everyday life, together.</p><a href={whatsappHref()} target="_blank" rel="noopener noreferrer">Enquire on WhatsApp ↗</a></div>
      <div><strong>Explore</strong><p><Link href="/stays">Stays</Link></p><p><Link href="/store">Store</Link></p><p><Link href="/fit">Fit</Link></p></div>
      <div><strong>Livenza</strong><p><Link href="/life">Life</Link></p><p><Link href="/about">About</Link></p><p><Link href="/contact">Contact</Link></p></div>
      <div><strong>Cities</strong><p><Link href="/stays/jaipur">Jaipur</Link></p><p><Link href="/stays/gurugram">Gurugram</Link></p></div>
    </div>
    <div className="footer-note">© {new Date().getFullYear()} Livenza Life LLP. All rights reserved.</div>
  </div></footer>
}
