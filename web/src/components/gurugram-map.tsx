import Link from 'next/link'
import { curatedStays } from '@/lib/brochure'

export function GurugramMap() {
  return <section className="gurugram-section" id="gurugram-map" aria-labelledby="gurugram-map-title">
    <div className="stays-inner">
      <div className="map-intro"><div><div className="eyebrow">THE CITY, THROUGH LIVENZA</div><h2 id="gurugram-map-title">Explore Gurugram.</h2></div><p>Six distinct stays across Sectors 38, 51 and 52. Select a name to discover its own space.</p></div>
      <div className="gurugram-map" aria-label="Illustrated sector map of Gurugram">
        <svg className="map-roads" viewBox="0 0 1000 560" aria-hidden="true" preserveAspectRatio="xMidYMid slice">
          <defs><pattern id="map-grid" width="70" height="70" patternUnits="userSpaceOnUse"><path d="M70 0H0V70" fill="none" stroke="#4084c8" strokeWidth="1" opacity=".2" /></pattern></defs>
          <rect width="1000" height="560" fill="url(#map-grid)" />
          <path d="M-30 182 C190 112 272 259 505 168 S840 82 1030 156 M-20 409 C204 361 345 478 539 371 S817 309 1030 391 M210 -20 C273 132 226 292 350 580 M674 -20 C610 152 762 322 694 590" fill="none" stroke="#216aaa" strokeWidth="45" opacity=".2" />
          <path d="M-30 182 C190 112 272 259 505 168 S840 82 1030 156 M-20 409 C204 361 345 478 539 371 S817 309 1030 391 M210 -20 C273 132 226 292 350 580 M674 -20 C610 152 762 322 694 590" fill="none" stroke="#66b8e6" strokeWidth="2" strokeDasharray="10 12" opacity=".55" />
          <circle cx="510" cy="285" r="215" fill="#1472c8" opacity=".08" />
        </svg>
        <div className="map-city-label">GURUGRAM <span>HARYANA · INDIA</span></div>
        <div className="map-sector-label map-sector-38">SECTOR 38</div><div className="map-sector-label map-sector-51">SECTOR 51</div><div className="map-sector-label map-sector-52">SECTOR 52</div>
        {curatedStays.map((stay, index) => <Link className={`map-pin map-pin-${index + 1}`} href={`/stays/gurugram/${stay.slug}`} key={stay.slug} aria-label={`Open ${stay.name} property page`}><span className="map-pin-dot" /><span className="map-pin-name">{stay.name}</span></Link>)}
      </div>
      <p className="map-disclaimer">Sector locations are approximate. Exact building pins and Google directions will appear after each address is verified.</p>
    </div>
  </section>
}
