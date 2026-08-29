import Link from 'next/link'
import styles from './page.module.css'
import { HomepageAnalytics } from '@/components/homepage-analytics'
import { getContent } from '@/lib/api'

const universe = [
  ['livenza.stays', '/stays', 'Find your place', 'stays'],
  ['livenza.fit', '/fit', 'Move your way.', 'fit'],
  ['livenza.store', '/store', 'Wear Livenza.', 'store'],
  ['livenza.groom', '/groom', 'Own your look.', 'groom'],
  ['livenza.skin', '/skin', 'Feel good in it.', 'skin'],
  ['livenza.media', '/media', 'Create what matters.', 'media'],
] as const

export default async function Home() {
  const cms = await getContent('homepage','home').catch(() => null)
  const cmsHero = typeof cms?.body?.hero_title === 'string' ? cms.body.hero_title : 'LIVE MORE.'
  const cmsIntro = typeof cms?.body?.hero_intro === 'string' ? cms.body.hero_intro : 'Stay. Move. Wear. Care. Create. One lifestyle ecosystem designed around the way a new generation lives.'
  return <main className={styles.page}><HomepageAnalytics />
    <section className={styles.hero}>
      <div className={styles.heroMedia} aria-hidden="true" />
      <div className={styles.heroContent}>
        <div className={styles.eyebrow}>LIVENZA.LIFE</div>
        <h1>{cmsHero}</h1>
        <p>{cmsIntro}</p>
        <div className={styles.actions}><Link className={styles.primary} href="/stays">BOOK A STAY</Link><Link className={styles.secondary} href="#universe">EXPLORE LIVENZA</Link></div>
      </div>
    </section>

    <section className={styles.section} id="universe"><div className={styles.inner}>
      <div className={styles.eyebrow}>THE LIVENZA UNIVERSE</div>
      <h2 className={styles.sectionTitle}>One life. Many Livenza experiences.</h2>
      <p className={styles.lede}>One master brand, different expressions—connected through a single Livenza identity.</p>
      <div className={styles.universe}>{universe.map(([name,href,line,tone]) => <Link href={href} className={styles.brandCard} data-tone={tone} key={href}><strong>{name}</strong><span>{line} →</span></Link>)}</div>
    </div></section>

    <section className={`${styles.section} ${styles.dark}`}><div className={styles.inner}>
      <div className={styles.eyebrow}>LIVENZA.STAYS</div><h2 className={styles.sectionTitle}>Find your place.</h2>
      <p className={styles.lede}>Student living, corporate living and short stays—built around comfort, community and everyday convenience.</p>
      <div className={styles.split}><div className={styles.visual} role="img" aria-label="Livenza lifestyle development photography placeholder"/><div className={styles.panel}><div><h3>YOUR PLACE. YOUR PEOPLE. YOUR LIFE.</h3><div className={styles.featureRow}><span>Student Living</span><span>Corporate Living</span><span>Short Stays</span></div></div><Link className={styles.inlineLink} href="/stays">Explore stays →</Link></div></div>
    </div></section>

    <section className={styles.section}><div className={styles.inner}>
      <div className={styles.eyebrow}>DESTINATIONS</div><h2 className={styles.sectionTitle}>Find your city</h2>
      <div className={styles.cityGrid}><Link className={styles.cityCard} href="/stays/jaipur"><strong>JAIPUR</strong><span>Student living · university neighbourhoods</span></Link><Link className={styles.cityCard} href="/stays/gurugram"><strong>GURUGRAM</strong><span>Corporate living · premium urban stays</span></Link></div>
    </div></section>

    <section className={styles.section}><div className={styles.inner}>
      <div className={styles.eyebrow}>LIFE AT LIVENZA</div><h2 className={styles.sectionTitle}>{"Life isn't a room"}</h2>
      <p className={styles.lede}>The experience continues beyond four walls: eat, train, meet, play, study, work and celebrate.</p>
      <div className={styles.lifeWords}>{['EAT','TRAIN','MEET','PLAY','STUDY','WORK','CREATE','CELEBRATE'].map(word => <div key={word}>{word}</div>)}</div>
    </div></section>

    <section className={`${styles.section} ${styles.dark}`}><div className={styles.inner}>
      <div className={styles.eyebrow}>LIVENZA.STORE</div><h2 className={styles.sectionTitle}>WEAR THE LIFE.</h2>
      <p className={styles.lede}>A curated lifestyle collection spanning wear, move, live and everyday essentials.</p>
      <Link className={styles.inlineLink} href="/store">Explore the first drop →</Link>
      <div className={styles.split}><div className={styles.panel}><div><span className={styles.eyebrow}>LIVE MORE / COLLECTION 01</span><h3 className={styles.mega}>01</h3></div><p className={styles.lede}>Apparel, movement essentials, room goods and move-in kits.</p></div><div className={styles.visual} role="img" aria-label="Livenza Store collection development photography placeholder"/></div>
    </div></section>

    <section className={`${styles.section} ${styles.dark}`}><div className={styles.inner}>
      <div className={styles.eyebrow}>WHAT&apos;S NEXT</div><h2 className={styles.sectionTitle}>The Livenza universe is getting bigger.</h2>
      <div className={styles.emerging}><Link href="/fit"><strong>livenza.fit</strong><span>Early access →</span></Link><Link href="/groom"><strong>livenza.groom</strong><span>Early access →</span></Link><Link href="/skin"><strong>livenza.skin</strong><span>Early access →</span></Link><Link href="/media"><strong>livenza.media</strong><span>Early access →</span></Link></div>
    </div></section>

    <section className={styles.section}><div className={styles.inner}>
      <div className={styles.eyebrow}>OUR STANDARD</div><h2 className={styles.sectionTitle}>The Livenza Standard</h2>
      <div className={styles.standardGrid}>{[['DESIGN','Spaces worth living in.'],['COMFORT','Everything where it should be.'],['COMMUNITY','Better together.'],['TECH','Living made simpler.'],['SAFETY','Designed into the experience.'],['SERVICE','Help when it matters.']].map(([title,copy]) => <div className={styles.standardItem} key={title}><strong>{title}</strong><p>{copy}</p></div>)}</div>
    </div></section>

    <section className={styles.section}><div className={styles.inner}>
      <div className={styles.eyebrow}>COMMUNITY</div><h2 className={styles.sectionTitle}>Real residents. Real Livenza.</h2>
      <p className={styles.lede}>Resident stories and verified social proof will appear here as the content library is connected. No fabricated ratings or review counts are shown.</p>
      <div className={styles.quoteGrid}><div className={styles.quoteCard}>Built around the moments between moving in and moving forward.</div><div className={styles.quoteCard}>#LiveMore</div></div>
    </div></section>

    <section className={styles.closing}><div className={styles.inner}><div className={styles.eyebrow}>LIVENZA.LIFE</div><h2 className={styles.sectionTitle}>FROM WHERE YOU STAY TO HOW YOU LIVE.</h2><div className={styles.actions}><Link className={styles.primary} href="/stays">FIND YOUR PLACE</Link><Link className={styles.secondary} href="/about">MEET LIVENZA</Link></div></div></section>
  </main>
}
