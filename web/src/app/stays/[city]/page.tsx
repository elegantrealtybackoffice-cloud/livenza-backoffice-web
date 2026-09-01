import { getProperties } from '@/lib/api'
import { PropertyCard } from '@/components/property-card'
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
  return <main data-brand="stays">
    <section className="city-hero"><div className="stays-inner"><div className="eyebrow">LIVENZA.STAYS · CITY</div><h1>{name.toUpperCase()}</h1><p>Explore public Livenza stays in {name}. Only verified property information from the Livenza platform is shown.</p></div></section>
    <section className="city-results"><div className="stays-inner">
      {unavailable ? <div className="empty-state">Live property discovery is temporarily unavailable.</div> : properties.length ? <div className="property-grid">{properties.map(property => <PropertyCard key={property.slug} property={property} />)}</div> : <div className="empty-state">No public Livenza stays are currently published for {name}.</div>}
    </div></section>
  </main>
}
