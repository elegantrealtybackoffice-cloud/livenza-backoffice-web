import { describe, expect, it } from 'vitest'
import { journeyState } from './journey'

describe('scroll journey', () => {
  it('starts on the balcony and visits properties in order', () => {
    expect(journeyState(0).phase).toBe('balcony')
    expect(journeyState(0).activeStop).toBe(-1)
    expect(journeyState(0.34).activeStop).toBe(0)
    expect(journeyState(0.59).activeStop).toBe(1)
    expect(journeyState(0.84).activeStop).toBe(2)
    expect(journeyState(1).phase).toBe('road')
  })

  it('clamps scroll and advances the traveller toward the road', () => {
    expect(journeyState(-2)).toEqual(journeyState(0))
    expect(journeyState(2)).toEqual(journeyState(1))
    expect(journeyState(0.25).y).toBeLessThan(journeyState(0).y)
  })
})
