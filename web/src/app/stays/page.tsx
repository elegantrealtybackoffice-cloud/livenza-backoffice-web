import Link from 'next/link'
import Image from 'next/image'
import { getCities, getProperties } from '@/lib/api'
import type { StayType } from '@/lib/types'
import { StaysSearch } from '@/components/stays-search'
import { GurugramMap } from '@/components/gurugram-map'
import { curatedStays, whatsappHref } from '@/lib/brochure'
import './stays.css'

export const dynamic = 'force-dynamic'

type Search = { city?: string; q?: string; stay_type?: string }

export default async function StaysPage({ searchParams }: { searchParams: Promise<Search> }) {
  const params = await searchParams
  const stayType = ['student','corporate','short_stay'].includes(params.stay_type ?? '') ? params.stay_type as StayType : undefined
  let cities = [] as Awaited<ReturnType<typeof getCities>>
  let properties = [] as Awaited<ReturnType<typeof getProperties>>
  let unavailable = false
  try {
    ;[cities, properties] = await Promise.all([getCities(), getProperties({ city: params.city, q: params.q, stay_type: stayType })])
  } catch { unavailable = true }
  const showCurated = !params.q && !params.stay_type && (!params.city || params.city.toLowerCase() === 'gurugram')

  return <main className="stays-main" data-brand="stays">
    <section className="stays-hero"><div className="stays-inner"><div className="eyebrow">LIVENZA.STAYS · GURUGRAM</div><h1>Find your place<br/>in the city.</h1><p>Discover six distinct Livenza stays across Gurugram. Explore the map, step inside each space and speak to our team when you are ready.</p><div className="stays-hero-actions"><a href="#gurugram-map" className="stays-hero-primary">EXPLORE THE MAP ↗</a><a href={whatsappHref()} target="_blank" rel="noopener noreferrer" className="stays-hero-secondary">ENQUIRE ON WHATSAPP</a></div></div></section>
    {showCurated && <><GurugramMap /><section className="curated-section" id="collection"><div className="stays-inner"><div className="results-head"><div><div className="eyebrow">THE LIVENZA COLLECTION</div><h2>Six ways to feel at home.</h2><p>Explore the first Gurugram properties by neighbourhood. Images appear only for stays with property-mapped media.</p></div></div><div className="curated-grid">{curatedStays.map(stay => <Link className="curated-card" href={`/stays/gurugram/${stay.slug}`} key={stay.slug}><div className="curated-card-media">{stay.photos[0] ? <Image src={stay.photos[0]} alt={`${stay.name} property photograph`} width={640} height={450} /> : <div className="curated-pending"><span>LIVENZA STAYS</span><strong>{stay.name}</strong><small>Photography coming soon</small></div>}</div><div className="curated-card-copy"><span>GURUGRAM · SECTOR {stay.sector}</span><h3>{stay.name}</h3><p>{stay.landmark ?? `Explore a stay in Sector ${stay.sector}.`}</p><strong>EXPLORE PROPERTY ↗</strong></div></Link>)}</div></div></section></>}
    <section className="stays-search-section"><div className="stays-inner"><div className="eyebrow">FIND YOUR STAY</div><h2>Search all published properties.</h2><StaysSearch cities={cities} initialCity={params.city} initialQuery={params.q} initialStayType={stayType}/></div></section>
    <section className="results"><div className="stays-inner"><div className="results-head"><div><div className="eyebrow">PLACES THAT FIT YOUR LIFE</div><h2>{params.city ? `Stays in ${params.city}` : 'Explore Livenza stays'}</h2></div></div>
      {unavailable ? <div className="empty-state">Live room listings are temporarily unavailable. The Gurugram collection above and WhatsApp enquiry remain available.</div> : properties.length ? <div className="results-grid">{properties.map(property => <article className="simple-property" key={property.slug}><div><div className="eyebrow">{property.area ? `${property.area} · ${property.city}` : property.city}</div><h3>{property.name}</h3><p>{property.summary || 'Explore this Livenza stay.'}</p><div className="stay-type-list">{property.stay_types.map(type => <span key={type}>{type.replace('_',' ')}</span>)}</div></div><Link href={`/stays/${property.city.toLowerCase()}/${property.slug}`}>See rooms →</Link></article>)}</div> : <div className="empty-state">No public Livenza room listings match these filters yet. Try another city or search term.</div>}
    </div></section>
  </main>
}
