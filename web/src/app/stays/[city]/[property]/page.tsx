import Link from 'next/link'
import { notFound } from 'next/navigation'
import { ApiError, getProperty } from '@/lib/api'
import { PropertyGallery } from '@/components/property-gallery'
import { StickyAction } from '@/components/sticky-action'
import '../../stays.css'
import '../../property.css'

export const dynamic = 'force-dynamic'

function normaliseCity(value: string) { return decodeURIComponent(value).replace(/-/g, ' ').trim().toLowerCase() }

export default async function PropertyPage({ params }: { params: Promise<{ city: string; property: string }> }) {
  const route = await params
  let property
  try { property = await getProperty(route.property) } catch (error) { if (error instanceof ApiError && error.status === 404) notFound(); throw error }
  if (property.city.trim().toLowerCase() !== normaliseCity(route.city)) notFound()
  const firstCategory = property.room_categories[0]
  const bookingHref = firstCategory ? `/stays/book?property=${encodeURIComponent(property.slug)}&room_category=${encodeURIComponent(firstCategory.slug)}` : '/stays'

  return <main className="property-detail" data-brand="stays">
    <section className="property-detail-hero"><div className="stays-inner"><div className="eyebrow">{property.area ? `${property.area} · ${property.city}` : property.city}</div><h1>{property.name}</h1><p>{property.summary || 'Explore this Livenza stay.'}</p><div className="property-tags">{property.stay_types.map(type => <span key={type}>{type.replace('_',' ')}</span>)}</div></div></section>
    <div className="stays-inner"><PropertyGallery propertyName={property.name}/>
      <div className="detail-grid"><div className="detail-main">
        <h2>Choose your room</h2>
        {property.room_categories.length ? <div className="room-grid">{property.room_categories.map(room => <article className="room-card" key={room.slug}><div className="room-meta">Up to {room.occupancy} resident{room.occupancy === 1 ? '' : 's'}</div><h3>{room.name}</h3><p>{room.summary || 'Room details are being prepared for publication.'}</p><Link href={`/stays/book?property=${encodeURIComponent(property.slug)}&room_category=${encodeURIComponent(room.slug)}`}>CHECK AVAILABILITY →</Link></article>)}</div> : <div className="unpublished">Room categories have not yet been published for online booking.</div>}
        <h2>Amenities</h2><div className="unpublished">Verified amenity details have not yet been published by Livenza Admin for this property.</div>
        <h2>Policies</h2><div className="unpublished">Property-specific policies will appear here once they are approved and published.</div>
        <h2>Frequently asked questions</h2><div className="unpublished">Verified property FAQs have not yet been published.</div>
      </div><aside className="detail-aside"><h3>This could be home.</h3><p>Choose a published room category to continue into live availability and booking.</p>{firstCategory ? <Link href={bookingHref}>CHECK AVAILABILITY</Link> : <Link href="/stays">EXPLORE OTHER STAYS</Link>}</aside></div>
    </div>
    {firstCategory ? <StickyAction href={bookingHref} label="CHECK AVAILABILITY"/> : null}
  </main>
}
