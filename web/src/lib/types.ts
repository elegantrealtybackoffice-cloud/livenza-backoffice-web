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

export type StoreVariant = {
  id:number
  sku:string
  title:string
  price_minor:number
  currency:string
  available_stock:number
  attributes:Record<string,unknown>
}

export type StoreProduct = {
  id:number
  slug:string
  name:string
  brand:string
  category:string
  collection:string
  summary:string
  description:string
  variants:StoreVariant[]
}

export type CartItem = { variant_id:number; quantity:number }
export type CartQuoteLine = {
  variant_id:number
  product_id:number
  product_slug:string
  product_name:string
  variant_title:string
  sku:string
  unit_price_minor:number
  quantity:number
  line_total_minor:number
  currency:string
}
export type CartQuote = { items:CartQuoteLine[]; subtotal_minor:number; discount_minor:number; delivery_minor:number; total_minor:number; currency:string }
export type StoreOrderItem = { variant_id:number; sku:string; product_name:string; variant_title:string; quantity:number; unit_price_minor:number; line_total_minor:number }
export type StoreOrder = { id:string; status:'placed'|'confirmed'|'packed'|'shipped'|'delivered'|'cancelled'|'returned'; fulfilment_mode:string; subtotal_minor:number; discount_minor:number; delivery_minor:number; total_minor:number; currency:string; items:StoreOrderItem[] }

export type DeliveryOption={ id:string; type:'property_room'; label:string; property:{id:number;slug:string;name:string;city:string}; room:{id:number;code:string;display_name:string}; booking_id:string }

export type LoyaltyLedgerItem={id:number;direction:'credit'|'debit';points:number;source_type:string;source_id:number;effect_key:string;description:string;created_at:string|null}
export type RewardsSummary={status:string;balance:number;entries:LoyaltyLedgerItem[]}
