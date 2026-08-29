import type { Availability, City, ListResponse, StayProperty, StayPropertyDetail, StayType } from './types'

const serverOrigin = process.env.LIVENZA_API_ORIGIN ?? 'http://127.0.0.1:5000'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function url(path: string) {
  return typeof window === 'undefined' ? `${serverOrigin}${path}` : path
}

async function readJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url(path), init)
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try { const body = await response.json(); message = body.error || message } catch { /* non-JSON */ }
    throw new ApiError(response.status, message)
  }
  return response.json() as Promise<T>
}

export async function getCities(): Promise<City[]> {
  const data = await readJson<ListResponse<City>>('/api/v1/cities', { next: { revalidate: 300 } })
  return data.items
}

export async function getProperties(filters: { city?: string; q?: string; stay_type?: StayType } = {}): Promise<StayProperty[]> {
  const params = new URLSearchParams()
  if (filters.city) params.set('city', filters.city)
  if (filters.q) params.set('q', filters.q)
  if (filters.stay_type) params.set('stay_type', filters.stay_type)
  const query = params.toString()
  const data = await readJson<ListResponse<StayProperty>>(`/api/v1/properties${query ? `?${query}` : ''}`, { cache: 'no-store' })
  return data.items
}

export function getProperty(slug: string): Promise<StayPropertyDetail> {
  return readJson<StayPropertyDetail>(`/api/v1/properties/${encodeURIComponent(slug)}`, { next: { revalidate: 120 } })
}

export function getAvailability(input: { property: string; room_category: string; start: string; end: string }): Promise<Availability> {
  const params = new URLSearchParams(input)
  return readJson<Availability>(`/api/v1/availability?${params.toString()}`, { cache: 'no-store' })
}
