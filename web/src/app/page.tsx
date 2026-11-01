import Image from 'next/image'
import Link from 'next/link'
import { HomepageAnalytics } from '@/components/homepage-analytics'
import { ScrollJourney } from '@/components/scroll-journey'
import { GurugramMap } from '@/components/gurugram-map'
import { getContent } from '@/lib/api'
import { curatedStays, whatsappHref } from '@/lib/brochure'
import styles from './home-journey.module.css'

const worlds = [
  ['Life', '/life', 'The moments beyond a room.'],
  ['Fit', '/fit', 'Move through your day.'],
  ['Store', '/store', 'Find everyday essentials.'],
  ['Groom', '/groom', 'Care for your look.'],
  ['Skin', '/skin', 'Feel good in it.'],
  ['Media', '/media', 'Create what matters.'],
] as const

export default async function Home() {
  const cms = await getContent('homepage', 'home').catch(() => null)
  const headline = typeof cms?.body?.hero_title === 'string' ? cms.body.hero_title : 'Stay beautifully.'
  const intro = typeof cms?.body?.hero_intro === 'string' ? cms.body.hero_intro : 'Thoughtful spaces and a more connected way to live in Gurugram.'
  const photographed = curatedStays.filter(stay => stay.photos.length > 0)
  const upcoming = curatedStays.filter(stay => stay.photos.length === 0)

  return <main className={styles.page}>
    <HomepageAnalytics />
    <ScrollJourney headline={headline} intro={intro} />

    <section className={styles.intro}><div className={`${styles.inner} ${styles.introGrid}`}>
      <div><span className={styles.sectionKicker}>THE LIVENZA APPROACH</span><h2>Designed for the way <span>you really live.</span></h2><p>From your first look at the city to the place you choose to call yours, Livenza brings every stay into one considered experience.</p><Link className={styles.outlineButton} href="/about">DISCOVER LIVENZA ↗</Link></div>
      <div className={styles.introImage}><Image src="/stays/the-sienna/cover.webp" alt="The Sienna interior from the supplied property gallery" width={680} height={580} /></div>
    </div></section>

    <GurugramMap />

    <section className={styles.collection} id="collection"><div className={styles.inner}>
      <div className={styles.sectionHeading}><div><span className={styles.sectionKicker}>INSIDE THE COLLECTION</span><h2>Spaces worth <span>stepping into.</span></h2></div><p>Explore the properties through their own supplied photography, then open a dedicated page for the full story.</p></div>
      <div className={styles.photoGrid}>{photographed.map(stay => <Link className={styles.photoCard} href={`/stays/gurugram/${stay.slug}`} key={stay.slug}><Image src={stay.photos[0]} alt={`${stay.name} property photograph`} width={640} height={460} /><div><span>GURUGRAM · SECTOR {stay.sector}</span><h3>{stay.name}</h3><p>{stay.landmark ?? 'Explore this Livenza stay.'} ↗</p></div></Link>)}</div>
      <div className={styles.moreGrid}>{upcoming.map(stay => <Link className={styles.moreCard} href={`/stays/gurugram/${stay.slug}`} key={stay.slug}><div><span>SECTOR {stay.sector}</span><strong>{stay.name}</strong></div><b>↗</b></Link>)}</div>
    </div></section>

    <section className={styles.universe}><div className={styles.inner}><span className={styles.sectionKicker}>ONE LIVENZA UNIVERSE</span><h2>More to explore.</h2><p>One visual language across the places you stay and the experiences you make your own.</p><div className={styles.universeGrid}>{worlds.map(([name, href, copy]) => <Link href={href} key={href}><strong>livenza.{name.toLowerCase()}</strong><span>{copy} ↗</span></Link>)}</div></div></section>

    <section className={styles.closing}><div className={styles.inner}><span className={styles.sectionKicker}>YOUR NEXT CHAPTER</span><h2>Find a stay that <span>feels like yours.</span></h2><p>Tell us where you want to be. Our team can help with the current options and the details that matter to you.</p><div className={styles.closingActions}><a className={styles.orangeButton} href={whatsappHref()} target="_blank" rel="noopener noreferrer">ENQUIRE ON WHATSAPP ↗</a><Link className={styles.outlineButton} href="/stays">VIEW ALL STAYS</Link></div></div></section>
  </main>
}
