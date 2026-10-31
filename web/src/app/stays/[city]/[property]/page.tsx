import Link from 'next/link'
import { notFound } from 'next/navigation'
import { ApiError, getProperty } from '@/lib/api'
import { getCuratedStay, whatsappHref } from '@/lib/brochure'
import { propertyView } from '@/lib/brochure-property'
import { PropertyGallery } from '@/components/property-gallery'
import { StickyAction } from '@/components/sticky-action'
import '../../stays.css'
import '../../property.css'

export const dynamic = 'force-dynamic'

function normaliseCity(value: string) { return decodeURIComponent(value).replace(/-/g, ' ').trim().toLowerCase() }

export default async function PropertyPage({ params }: { params: Promise<{ city: string; property: string }> }) {
  const route = await params
  let published
  try { published = await getProperty(route.property) } catch (error) { if (!getCuratedStay(route.property)) { if (error instanceof ApiError && error.status === 404) notFound(); throw error } }
  const property = propertyView(route.property, published?.city.toLowerCase() === 'gurugram' || !getCuratedStay(route.property) ? published : undefined)
  if (!property) notFound()
  if (property.city.trim().toLowerCase() !== normaliseCity(route.city)) notFound()
  const firstCategory = property.room_categories[0]
  const bookingHref = firstCategory ? `/stays/book?property=${encodeURIComponent(property.slug)}&room_category=${encodeURIComponent(firstCategory.slug)}` : '/stays'

  return <main className="property-detail" data-brand="stays">
    <section className="property-detail-hero"><div className="stays-inner"><Link className="property-back" href="/stays">← ALL STAYS</Link><div className="eyebrow">{property.area ? `${property.area} · ${property.city}` : property.city}</div><h1>{property.name}</h1><p>{property.summary}</p><div className="property-tags">{property.stay_types.map(type => <span key={type}>{type.replace('_',' ')}</span>)}</div><a className="property-hero-cta" href={whatsappHref(property.name)} target="_blank" rel="noopener noreferrer">ENQUIRE ON WHATSAPP ↗</a></div></section>
    <div className="stays-inner"><PropertyGallery propertyName={property.name} photos={property.photos} videos={property.videos}/>
      <div className="detail-grid"><div className="detail-main">
        <div className="property-story"><div className="eyebrow">THE PROPERTY</div><h2>Settle into {property.name}.</h2><p>{property.summary}</p></div>
        <div className="property-location-section"><div className="eyebrow">NEIGHBOURHOOD</div><h2>Find your way around.</h2><p>{property.area}, {property.city}{property.landmark ? ` · ${property.landmark}` : ''}</p><small>Exact building address and Google Maps directions will be added after verification.</small></div>
        <h2>Published rooms</h2>
        {property.room_categories.length ? <div className="room-grid">{property.room_categories.map(room => <article className="room-card" key={room.slug}><div className="room-meta">Up to {room.occupancy} resident{room.occupancy === 1 ? '' : 's'}</div><h3>{room.name}</h3><p>{room.summary || 'Contact Livenza for current room details.'}</p><Link href={`/stays/book?property=${encodeURIComponent(property.slug)}&room_category=${encodeURIComponent(room.slug)}`}>CHECK AVAILABILITY →</Link></article>)}</div> : <div className="unpublished">Online room categories have not yet been published for this property. Our team can share current options on WhatsApp.</div>}
      </div><aside className="detail-aside"><div className="eyebrow">START A CONVERSATION</div><h3>This could be home.</h3><p>Ask our team about {property.name}, current options and a visit.</p><a href={whatsappHref(property.name)} target="_blank" rel="noopener noreferrer">ENQUIRE ON WHATSAPP ↗</a>{firstCategory && <Link className="aside-secondary" href={bookingHref}>CHECK LIVE AVAILABILITY</Link>}</aside></div>
    </div>
    <StickyAction href={whatsappHref(property.name)} label="ENQUIRE ON WHATSAPP"/>
  </main>
}
