import { getProperties } from '@/lib/api'
import { PropertyCard } from '@/components/property-card'
import { GurugramMap } from '@/components/gurugram-map'
import { curatedStays } from '@/lib/brochure'
import Link from 'next/link'
import Image from 'next/image'
import '../stays.css'
import '../property.css'

export const dynamic = 'force-dynamic'

function cityName(value: string) { return decodeURIComponent(value).replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) }

export default async function CityPage({ params }: { params: Promise<{ city: string }> }) {
  const { city } = await params
  const name = cityName(city)
  let properties = [] as Awaited<ReturnType<typeof getProperties>>
  let unavailable = false
  try { properties = await getProperties({ city: name }) } catch { unavailable = true }
  const isGurugram = name.toLowerCase() === 'gurugram'
  const extraProperties = isGurugram ? properties.filter(property => !curatedStays.some(stay => stay.slug === property.slug)) : properties
  return <main data-brand="stays">
    <section className="city-hero"><div className="stays-inner"><div className="eyebrow">LIVENZA.STAYS · CITY</div><h1>{name.toUpperCase()}</h1><p>{isGurugram ? 'Discover six Livenza stays across Gurugram. Property photos are shown only where they were supplied for that stay.' : `Explore published Livenza stays in ${name}.`}</p></div></section>
    {isGurugram && <><GurugramMap /><section className="curated-section"><div className="stays-inner"><div className="results-head"><div><div className="eyebrow">THE GURUGRAM COLLECTION</div><h2>Explore each stay.</h2></div></div><div className="curated-grid">{curatedStays.map(stay => <Link className="curated-card" href={`/stays/gurugram/${stay.slug}`} key={stay.slug}><div className="curated-card-media">{stay.photos[0] ? <Image src={stay.photos[0]} alt={`${stay.name} property photograph`} width={640} height={450} /> : <div className="curated-pending"><span>LIVENZA STAYS</span><strong>{stay.name}</strong><small>Photography coming soon</small></div>}</div><div className="curated-card-copy"><span>GURUGRAM · SECTOR {stay.sector}</span><h3>{stay.name}</h3><p>{stay.landmark ?? `Explore a stay in Sector ${stay.sector}.`}</p><strong>EXPLORE PROPERTY ↗</strong></div></Link>)}</div></div></section></>}
    <section className="city-results"><div className="stays-inner">
      {unavailable ? <div className="empty-state">Live room listings are temporarily unavailable. Please contact our team for current options.</div> : extraProperties.length ? <div className="property-grid">{extraProperties.map(property => <PropertyCard key={property.slug} property={property} />)}</div> : !isGurugram ? <div className="empty-state">No public Livenza stays are currently published for {name}.</div> : null}
    </div></section>
  </main>
}
