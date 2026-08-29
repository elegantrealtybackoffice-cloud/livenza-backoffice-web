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

export type RatePlan = {
  code: string
  stay_type: StayType
  billing_period: string
  currency: string
  amount_minor: number
  security_deposit_minor: number
  reservation_amount_minor: number
}

export type RoomCategory = {
  slug: string
  name: string
  occupancy: number
  summary: string
  rate_plans?: RatePlan[]
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

export type Customer = {
  id: string
  full_name: string
  primary_mobile: string
  primary_email: string
  status: string
}

export type BookingAddon = { code:string; label:string; amount_minor:number }

export type InventoryHold = {
  id: string
  status: string
  start: string
  end: string
  expires_at: string
  rate_plan_id: number
}

export type Booking = {
  id: string
  status: 'draft'|'held'|'pending_payment'|'confirmed'|'cancelled'|'expired'
  booking_mode: 'book_now'|'reserve'
  stay_type: StayType
  start: string
  end: string
  currency: string
  subtotal_minor: number
  security_deposit_minor: number
  addon_total_minor: number
  total_minor: number
  amount_due_now_minor: number
}

export type Payment = {
  id: string
  source_type: string
  status: 'created'|'pending'|'paid'|'failed'|'refunded'|'partially_refunded'
  amount_minor: number
  currency: string
  gateway: string
  gateway_order_id: string
  gateway_payment_id: string
}

export type ListResponse<T> = { items: T[] }

export type MyStay = Booking & { property:{name:string;city:string;area:string} }
export type CustomerDocumentSummary = { id:number; booking_id:number|null; document_type:string; display_name:string; private:boolean; created_at:string|null }
export type SupportTicketSummary = { id:string; category:'stay'|'payment'|'store'|'account'|'other'; subject:string; description:string; status:string; created_at?:string|null }
