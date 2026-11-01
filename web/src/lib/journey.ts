export type JourneyState = { phase: 'balcony' | 'road'; activeStop: number; x: number; y: number; scale: number }

const route = [
  { at: 0, x: 78, y: 87, scale: 1 },
  { at: .15, x: 73, y: 88, scale: .94 },
  { at: .28, x: 58, y: 70, scale: .74 },
  { at: .43, x: 35, y: 69, scale: .72 },
  { at: .67, x: 49, y: 64, scale: .72 },
  { at: .88, x: 73, y: 62, scale: .72 },
  { at: 1, x: 83, y: 63, scale: .72 },
] as const

export function journeyState(progress: number): JourneyState {
  const position = Math.min(1, Math.max(0, progress))
  const nextIndex = route.findIndex(point => point.at >= position)
  const next = route[nextIndex < 0 ? route.length - 1 : nextIndex]
  const previous = route[Math.max(0, (nextIndex < 0 ? route.length - 1 : nextIndex) - 1)]
  const fraction = next.at === previous.at ? 0 : (position - previous.at) / (next.at - previous.at)
  const between = (start: number, end: number) => start + (end - start) * fraction
  return {
    phase: position < .22 ? 'balcony' : 'road',
    activeStop: position < .31 ? -1 : position < .55 ? 0 : position < .78 ? 1 : 2,
    x: between(previous.x, next.x),
    y: between(previous.y, next.y),
    scale: between(previous.scale, next.scale),
  }
}
