import { StaysExplorer } from '@/components/stays-explorer'
import './stays.css'

export const dynamic = 'force-dynamic'

export default function StaysPage() {
  return <main className="stays-main" data-brand="stays">
    <StaysExplorer />
    <section className="stays-offers" aria-labelledby="offers-title"><div className="stays-inner">
      <div className="stays-intro"><span>FOR YOUR NEXT ARRIVAL</span><h2 id="offers-title">Offers for you.</h2><p>Thoughtful options, shaped around the way you need to stay.</p></div>
      <div className="offer-grid">
        <article><span>WELCOME STAY</span><h3>A considered start to your first Livenza stay.</h3><p>Share your dates and the team will guide you to the right address.</p><a href="https://wa.me/917688845555">Speak to us →</a></article>
        <article><span>LONGER, LIGHTER</span><h3>More time to settle into the city.</h3><p>For longer stays, our team can help shape a stay around your routine.</p><a href="https://wa.me/917688845555">Plan a stay →</a></article>
        <article><span>FESTIVE CITY EDIT</span><h3>Thoughtful extras for a Diwali city stay.</h3><p>Ask our team about seasonal details available for your dates.</p><a href="https://wa.me/917688845555">Speak to us →</a></article>
      </div>
    </div></section>
    <section className="stays-trust" aria-labelledby="trust-title"><div className="stays-inner">
      <div className="stays-intro"><span>THE LIVENZA STANDARD</span><h2 id="trust-title">Your trusted stay partner.</h2></div>
      <div className="trust-grid">
        <article><i aria-hidden="true">✦</i><div><h3>Curated city stays</h3><p>Thoughtfully selected addresses, made for the way you live.</p></div></article>
        <article><i aria-hidden="true">◌</i><div><h3>A team that stays close</h3><p>Direct, human help before arrival and throughout your stay.</p></div></article>
        <article><i aria-hidden="true">↗</i><div><h3>Simple, secure booking</h3><p>Clear next steps and a considered path from search to stay.</p></div></article>
      </div>
    </div></section>
    <section className="stays-marquee" aria-label="Livenza highlights"><div><span>Livenza Stays</span><span>Thoughtful city living</span><span>Gurugram and Jaipur</span><span>Made for the way you arrive</span><span>Livenza Stays</span><span>Thoughtful city living</span><span>Gurugram and Jaipur</span><span>Made for the way you arrive</span></div></section>
  </main>
}
