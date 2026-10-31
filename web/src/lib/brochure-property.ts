import { getCuratedStay } from './brochure'
import type { RoomCategory, StayPropertyDetail } from './types'

export type BrochurePropertyView = {
  slug: string
  name: string
  city: string
  area: string
  summary: string
  stay_types: string[]
  room_categories: RoomCategory[]
  photos: string[]
  videos: string[]
  landmark?: string
}

export function propertyView(slug: string, published?: StayPropertyDetail): BrochurePropertyView | undefined {
  const curated = getCuratedStay(slug)
  if (!curated && !published) return undefined
  if (!curated && published) return { ...published, photos: [], videos: [] }
  if (!curated) return undefined
  return {
    slug: curated.slug,
    name: curated.name,
    city: 'Gurugram',
    area: published?.area || `Sector ${curated.sector}`,
    summary: published?.summary || `Explore ${curated.name} in Gurugram's Sector ${curated.sector}.`,
    stay_types: published?.stay_types ?? [],
    room_categories: published?.room_categories ?? [],
    photos: curated.photos,
    videos: curated.videos,
    landmark: curated.landmark,
  }
}
