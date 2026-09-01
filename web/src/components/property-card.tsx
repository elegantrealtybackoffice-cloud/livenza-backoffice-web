import Link from 'next/link'
import type { StayProperty } from '@/lib/types'

export function PropertyCard({ property }: { property: StayProperty }) {
  const citySlug = property.city.toLowerCase().replace(/\s+/g, '-')
  return <article className="property-card">
    <div className="property-card-media" role="img" aria-label={`${property.name} property photography placeholder`} />
    <div className="property-card-body">
      <div className="property-location">{property.area ? `${property.area} · ${property.city}` : property.city}</div>
      <h2>{property.name}</h2>
      <p>{property.summary || 'Explore this Livenza stay.'}</p>
      <div className="property-tags">{property.stay_types.map(type => <span key={type}>{type.replace('_', ' ')}</span>)}</div>
      <Link href={`/stays/${citySlug}/${property.slug}`}>See rooms →</Link>
    </div>
  </article>
}
