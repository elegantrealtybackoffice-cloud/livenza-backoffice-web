export type StayType = 'student' | 'corporate' | 'short_stay'

export type City = { name: string }

export type StayProperty = {
  id: number
  slug: string
  name: string
  city: string
  area: string
  summary: string
  stay_types: string[]
}

export type RoomCategory = {
  slug: string
  name: string
  occupancy: number
  summary: string
}

export type StayPropertyDetail = StayProperty & { room_categories: RoomCategory[] }

export type Availability = {
  property: string
  room_category: string
  start: string
  end: string
  available_count: number
  availability_state: string
  allocatable_unit_type: string
}

export type ListResponse<T> = { items: T[] }
