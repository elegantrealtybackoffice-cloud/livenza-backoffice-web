'use client'

import { useEffect, useRef } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { getCuratedStay, whatsappHref } from '@/lib/brochure'
import { journeyState } from '@/lib/journey'
import styles from '@/app/home-journey.module.css'

const stops = ['the-sienna', 'g38-getaway', 'the-elara'].map(slug => getCuratedStay(slug)!)

export function ScrollJourney({ headline, intro }: { headline: string; intro: string }) {
  const section = useRef<HTMLElement>(null)
  const traveller = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    const root = section.current
    const boy = traveller.current
    if (!root || !boy) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      root.dataset.motion = 'reduced'
      return
    }

    let frame = 0
    const update = () => {
      frame = 0
      const bounds = root.getBoundingClientRect()
      const distance = Math.max(1, bounds.height - window.innerHeight)
      const progress = Math.min(1, Math.max(0, -bounds.top / distance))
      const state = journeyState(progress)
      boy.style.left = `${state.x}%`
      boy.style.top = `${state.y}%`
      boy.style.setProperty('--boy-scale', String(state.scale))
      root.dataset.phase = state.phase
      root.dataset.stop = String(state.activeStop)
      root.dataset.walking = progress > .015 && progress < .98 ? 'true' : 'false'
      root.style.setProperty('--journey-progress', String(progress))
    }
    const schedule = () => { if (!frame) frame = requestAnimationFrame(update) }
    update()
    window.addEventListener('scroll', schedule, { passive: true })
    window.addEventListener('resize', schedule)
    return () => { cancelAnimationFrame(frame); window.removeEventListener('scroll', schedule); window.removeEventListener('resize', schedule) }
  }, [])

  return <section ref={section} className={styles.journey} data-phase="balcony" data-stop="-1" data-walking="false" aria-label="Scroll journey through Livenza Stays">
    <div className={styles.sticky}>
      <div className={styles.journeyArt} aria-hidden="true" />
      <div className={styles.stars} aria-hidden="true" />
      <div className={styles.roadScene} aria-hidden="true">
        <svg viewBox="0 0 1200 720" preserveAspectRatio="xMidYMid slice"><path d="M-60 630 C190 540 285 645 490 505 S900 420 1260 260"/><path d="M-30 650 C220 560 290 665 510 525 S920 440 1270 280"/></svg>
        <span className={styles.trafficOne}/><span className={styles.trafficTwo}/>
      </div>
      <div className={styles.heroCopy}><span className={styles.kicker}>LIVENZA STAYS · GURUGRAM</span><h1><strong>{headline}</strong><em>Live your way.</em></h1><p>{intro}</p><div className={styles.heroActions}><a href="#gurugram-map" className={styles.orangeButton}>EXPLORE THE CITY ↗</a><a href={whatsappHref()} target="_blank" rel="noopener noreferrer" className={styles.outlineButton}>SPEAK TO THE TEAM</a></div></div>
      <div className={styles.roadHeading}><span className={styles.kicker}>FOLLOW THE JOURNEY</span><h2>One city.<br/><em>Places to belong.</em></h2><p>Walk with us from the balcony into Gurugram. Each stop opens a real Livenza stay.</p></div>
      <span className={styles.traveller} ref={traveller} role="img" aria-label="Illustrated traveller walking through Gurugram" />
      <div className={styles.stopCards}>{stops.map((stay, index) => <article className={styles.stopCard} key={stay.slug}><div className={styles.stopImage}><Image src={stay.photos[0]} alt={`${stay.name} property photograph`} width={560} height={390} /></div><div className={styles.stopText}><span>STOP {String(index + 1).padStart(2, '0')} · SECTOR {stay.sector}</span><h3>{stay.name}</h3><p>{stay.landmark ?? 'Explore this Gurugram stay.'}</p><Link href={`/stays/gurugram/${stay.slug}`}>STEP INSIDE ↗</Link></div></article>)}</div>
      <div className={styles.journeyProgress} aria-hidden="true"><span /></div>
      <span className={styles.scrollPrompt}>SCROLL TO EXPLORE <i>↓</i></span>
    </div>
  </section>
}
