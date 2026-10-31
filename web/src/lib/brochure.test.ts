import { describe, expect, it } from 'vitest'
import { curatedStays, getCuratedStay, whatsappHref } from './brochure'

describe('Gurugram brochure content', () => {
  it('names six unique stays in the supplied sectors', () => {
    expect(curatedStays.map(stay => stay.name)).toEqual([
      'The Sienna', 'The Azure', 'G 38 Getaway',
      'The Elara', 'The Maralia', 'The Avelia',
    ])
    expect(curatedStays.map(stay => stay.sector)).toEqual([38, 38, 38, 51, 52, 51])
    expect(new Set(curatedStays.map(stay => stay.slug)).size).toBe(6)
  })

  it('assigns supplied photos only to their named properties', () => {
    expect(getCuratedStay('the-sienna')?.photos.length).toBe(5)
    expect(getCuratedStay('the-sienna')?.videos.length).toBe(3)
    expect(getCuratedStay('g38-getaway')?.photos.length).toBe(9)
    expect(getCuratedStay('the-elara')?.photos.length).toBe(8)
    for (const slug of ['the-azure', 'the-maralia', 'the-avelia']) {
      expect(getCuratedStay(slug)?.photos).toEqual([])
    }
    expect(getCuratedStay('unknown')).toBeUndefined()
  })

  it('prepares a property-specific WhatsApp enquiry', () => {
    const href = whatsappHref('The Elara')
    expect(href).toMatch(/^https:\/\/wa\.me\/917688845555\?/)
    expect(decodeURIComponent(href)).toContain('The Elara')
  })
})
