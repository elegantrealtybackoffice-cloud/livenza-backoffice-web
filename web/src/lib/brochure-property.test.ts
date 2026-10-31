import { describe, expect, it } from 'vitest'
import type { StayPropertyDetail } from './types'
import { propertyView } from './brochure-property'

describe('property page view', () => {
  it('keeps a curated page usable when no property record is published', () => {
    const view = propertyView('the-sienna')
    expect(view?.name).toBe('The Sienna')
    expect(view?.area).toBe('Sector 38')
    expect(view?.photos.length).toBe(5)
    expect(view?.videos.length).toBe(3)
    expect(view?.room_categories).toEqual([])
    expect(propertyView('unknown')).toBeUndefined()
  })

  it('uses published rooms without assigning another property’s photos', () => {
    const published: StayPropertyDetail = {
      id: 42, slug: 'the-elara', name: 'The Elara', city: 'Gurugram', area: 'Sector 51',
      summary: 'Published property summary', stay_types: ['corporate'],
      room_categories: [{ slug: 'studio', name: 'Studio', occupancy: 1, summary: 'Published room' }],
    }
    const view = propertyView('the-elara', published)
    expect(view?.summary).toBe('Published property summary')
    expect(view?.room_categories[0].slug).toBe('studio')
    expect(view?.photos.every(photo => photo.includes('/the-elara/'))).toBe(true)
  })
})
