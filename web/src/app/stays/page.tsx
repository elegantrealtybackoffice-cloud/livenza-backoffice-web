import Link from 'next/link'
import { getCities, getProperties } from '@/lib/api'
import type { StayType } from '@/lib/types'
import { StaysSearch } from '@/components/stays-search'
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

  return <main className="stays-main" data-brand="stays">
    <section className="stays-hero"><div className="stays-inner"><div className="eyebrow">LIVENZA.STAYS</div><h1>FIND YOUR PLACE.</h1><p>Search student living, corporate living and short stays by city, college, area, landmark or property.</p><StaysSearch cities={cities} initialCity={params.city} initialQuery={params.q} initialStayType={stayType}/></div></section>
    <section className="results"><div className="stays-inner"><div className="results-head"><div><div className="eyebrow">PLACES THAT FIT YOUR LIFE</div><h2>{params.city ? `Stays in ${params.city}` : 'Explore Livenza stays'}</h2></div></div>
      {unavailable ? <div className="empty-state">Live property discovery is temporarily unavailable. Please try again shortly.</div> : properties.length ? <div className="results-grid">{properties.map(property => <article className="simple-property" key={property.slug}><div><div className="eyebrow">{property.area ? `${property.area} · ${property.city}` : property.city}</div><h3>{property.name}</h3><p>{property.summary || 'Explore this Livenza stay.'}</p><div className="stay-type-list">{property.stay_types.map(type => <span key={type}>{type.replace('_',' ')}</span>)}</div></div><Link href={`/stays/${property.city.toLowerCase()}/${property.slug}`}>See rooms →</Link></article>)}</div> : <div className="empty-state">No public Livenza properties match these filters yet. Try another city or search term.</div>}
    </div></section>
  </main>
}
