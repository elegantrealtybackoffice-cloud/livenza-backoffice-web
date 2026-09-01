import Link from 'next/link'
export function SiteFooter() {
  return <footer className="site-footer"><div className="footer-inner">
    <div className="footer-grid">
      <div><div className="brand-link">LIVENZA<span className="suffix">.life</span></div><p>From where you stay to how you live.</p></div>
      <div><strong>Explore</strong><p><Link href="/stays">Stays</Link></p><p><Link href="/store">Store</Link></p><p><Link href="/fit">Fit</Link></p></div>
      <div><strong>Livenza</strong><p><Link href="/life">Life</Link></p><p><Link href="/about">About</Link></p><p><Link href="/contact">Contact</Link></p></div>
      <div><strong>Cities</strong><p><Link href="/stays/jaipur">Jaipur</Link></p><p><Link href="/stays/gurugram">Gurugram</Link></p></div>
    </div>
    <div className="footer-note">© {new Date().getFullYear()} Livenza Life LLP. All rights reserved.</div>
  </div></footer>
}
