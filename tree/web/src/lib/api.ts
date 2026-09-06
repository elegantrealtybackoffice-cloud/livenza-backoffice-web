import type { Availability, Booking, BookingAddon, CartItem, CartQuote, City, Customer, InventoryHold, ListResponse, Payment, StayProperty, StayPropertyDetail, StayType, StoreOrder, StoreProduct, DeliveryOption, RewardsSummary } from './types'

const serverOrigin = process.env.LIVENZA_API_ORIGIN ?? 'http://127.0.0.1:5000'

export class ApiError extends Error {
  status: number
  code?: string
  constructor(status: number, message: string, code?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

function url(path: string) { return typeof window === 'undefined' ? `${serverOrigin}${path}` : path }

async function readJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url(path), { credentials: 'include', ...init })
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    let code: string | undefined
    try { const body = await response.json(); message = body.error || message; code = body.code } catch { /* non-JSON */ }
    throw new ApiError(response.status, message, code)
  }
  return response.json() as Promise<T>
}

function postJson<T>(path:string, body:unknown):Promise<T>{
  return readJson<T>(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
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
  return readJson<StayPropertyDetail>(`/api/v1/properties/${encodeURIComponent(slug)}`, { cache: 'no-store' })
}

export function getAvailability(input: { property: string; room_category: string; start: string; end: string }): Promise<Availability> {
  const params = new URLSearchParams(input)
  return readJson<Availability>(`/api/v1/availability?${params.toString()}`, { cache: 'no-store' })
}

export function requestOtp(mobile:string){ return postJson<{ok:true;expires_in_seconds:number;test_otp?:string}>('/api/v1/auth/otp/request',{mobile}) }
export function verifyOtp(mobile:string,otp:string){ return postJson<{ok:true;customer:Customer}>('/api/v1/auth/otp/verify',{mobile,otp}) }
export function getMe(){ return readJson<{ok:true;customer:Customer}>('/api/v1/me',{cache:'no-store'}) }
export function logout(){ return postJson<{ok:true}>('/api/v1/auth/logout',{}) }

export async function getBookingAddons():Promise<BookingAddon[]>{
  const data=await readJson<ListResponse<BookingAddon>>('/api/v1/booking-addons',{cache:'no-store'})
  return data.items
}

export function createHold(input:{property_slug:string;room_category_slug:string;rate_plan_code:string;start:string;end:string}){
  return postJson<{ok:true;hold:InventoryHold}>('/api/v1/bookings/hold',input)
}

export function createBooking(input:{hold_id:string;booking_mode:'book_now'|'reserve';guardian?:Record<string,string>;details?:Record<string,string>;addons?:Array<{code:string}>}){
  return postJson<{ok:true;booking:Booking}>('/api/v1/bookings',input)
}

export function getBooking(id:string){ return readJson<{ok:true;booking:Booking}>(`/api/v1/bookings/${encodeURIComponent(id)}`,{cache:'no-store'}) }
export function createParentShare(id:string){ return postJson<{ok:true;token:string;expires_at:string}>(`/api/v1/bookings/${encodeURIComponent(id)}/parent-share`,{}) }

export function createPayment(booking_id:string){
  return postJson<{ok:true;payment:Payment;checkout:{key_id:string;order_id:string;amount_minor:number;currency:string}}>('/api/v1/payments',{booking_id})
}
export function getPayment(id:string){ return readJson<{ok:true;payment:Payment}>(`/api/v1/payments/${encodeURIComponent(id)}`,{cache:'no-store'}) }

export function getMyStays(){ return readJson<ListResponse<import('./types').MyStay>>('/api/v1/me/stays',{cache:'no-store'}) }
export function getMyPayments(){ return readJson<ListResponse<Payment>>('/api/v1/me/payments',{cache:'no-store'}) }
export function getMyDocuments(){ return readJson<ListResponse<import('./types').CustomerDocumentSummary>>('/api/v1/me/documents',{cache:'no-store'}) }
export function getMySupport(){ return readJson<ListResponse<import('./types').SupportTicketSummary>>('/api/v1/me/support',{cache:'no-store'}) }
export function createSupportTicket(input:{category:'stay'|'payment'|'store'|'account'|'other';subject:string;description:string}){ return postJson<{ok:true;ticket:import('./types').SupportTicketSummary}>('/api/v1/me/support',input) }
export function patchMyProfile(input:{full_name?:string;primary_email?:string}){ return readJson<{ok:true;customer:Customer}>('/api/v1/me/profile',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(input)}) }
export function createParentPayment(token:string){ return postJson<{ok:true;payment:Payment;checkout:{key_id:string;order_id:string;amount_minor:number;currency:string}}>(`/api/v1/booking-shares/${encodeURIComponent(token)}/payments`,{}) }


export async function getProducts(filters:{category?:string;collection?:string;q?:string}={}):Promise<StoreProduct[]>{
  const params=new URLSearchParams()
  if(filters.category) params.set('category',filters.category)
  if(filters.collection) params.set('collection',filters.collection)
  if(filters.q) params.set('q',filters.q)
  const query=params.toString()
  const data=await readJson<{ok:true;products:StoreProduct[]}>(`/api/v1/products${query?`?${query}`:''}`,{cache:'no-store'})
  return data.products
}
export function getProduct(slug:string){ return readJson<{ok:true;product:StoreProduct}>(`/api/v1/products/${encodeURIComponent(slug)}`,{cache:'no-store'}).then(r=>r.product) }
export function quoteCart(items:CartItem[],delivery_mode='address'){ return postJson<{ok:true;quote:CartQuote}>('/api/v1/cart/quote',{items,delivery_mode}).then(r=>r.quote) }
export function createStoreOrder(input:{items:CartItem[];delivery_mode:string;delivery?:Record<string,string>}){ return postJson<{ok:true;order:StoreOrder;payment:Payment;checkout:{key_id:string;order_id:string;amount_minor:number;currency:string}}>('/api/v1/orders',input) }
export function getStoreOrder(id:string){ return readJson<{ok:true;order:StoreOrder}>(`/api/v1/orders/${encodeURIComponent(id)}`,{cache:'no-store'}) }

export function getDeliveryOptions(){ return readJson<ListResponse<DeliveryOption>>('/api/v1/me/delivery-options',{cache:'no-store'}).then(r=>r.items) }

export function getMyOrders(){ return readJson<ListResponse<StoreOrder>>('/api/v1/me/orders',{cache:'no-store'}) }
export function getMyRewards(){ return readJson<{ok:true;rewards:RewardsSummary}>('/api/v1/me/rewards',{cache:'no-store'}).then(r=>r.rewards) }

export type CmsContent = { type:string; key:string; locale:string; title:string; body:Record<string,unknown>; seo:Record<string,unknown>; updated_at?:string|null }
export function getContent(contentType:string,key:string,locale='en'){
  const params=new URLSearchParams({locale})
  return readJson<{ok:true;content:CmsContent}>(`/api/v1/content/${encodeURIComponent(contentType)}/${encodeURIComponent(key)}?${params.toString()}`,{next:{revalidate:60}}).then(r=>r.content)
}

// Livenza.fit authenticated sync ------------------------------------------------
export type FitProfile = {
  units: 'metric' | 'imperial'
  height_cm: number | null
  default_rep_seconds: number
  goal: string
  preferences: Record<string, unknown>
  updated_at?: string | null
}
export type FitWorkout = {
  id: number
  client_record_id: string
  exercise_id: string
  exercise_name: string
  sets: number
  reps: number
  rep_seconds: number
  duration_seconds: number
  estimated_calories?: number | null
  source: string
  metadata: Record<string, unknown>
  completed_at: string
}
export type FitHealthLog = {
  id: number
  provider_record_id?: string | null
  source: string
  recorded_at: string
  weight_kg?: number | null
  height_cm?: number | null
  bmi?: number | null
  steps?: number | null
  active_calories?: number | null
  total_calories?: number | null
  activity_minutes?: number | null
  resting_heart_rate?: number | null
  sleep_minutes?: number | null
  summary?: Record<string, unknown>
}
export type FitIntegration = {
  provider: string
  status: string
  scopes: string[]
  provider_metadata: Record<string, unknown>
  last_sync_at?: string | null
}

export function getFitProfile(){
  return readJson<{ok:true;profile:FitProfile}>('/api/v1/fit/profile',{cache:'no-store'}).then(r=>r.profile)
}
export function saveFitProfile(input:Partial<Pick<FitProfile,'units'|'height_cm'|'default_rep_seconds'|'goal'|'preferences'>>){
  return readJson<{ok:true;profile:FitProfile}>('/api/v1/fit/profile',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(input)}).then(r=>r.profile)
}
export function getFitWorkouts(limit=50){
  const safe=Math.max(1,Math.min(100,Math.floor(limit)))
  return readJson<{ok:true;items:FitWorkout[]}>(`/api/v1/fit/workouts?limit=${safe}`,{cache:'no-store'}).then(r=>r.items)
}
export function syncFitWorkout(input:{client_record_id:string;exercise_id:string;exercise_name:string;sets:number;reps:number;rep_seconds:number;duration_seconds:number;estimated_calories?:number;source?:string;completed_at:string;metadata?:Record<string,unknown>}){
  return postJson<{ok:true;workout:FitWorkout;idempotent?:boolean}>('/api/v1/fit/workouts',input).then(r=>r.workout)
}
export function getFitHealthLogs(limit=100){
  const safe=Math.max(1,Math.min(200,Math.floor(limit)))
  return readJson<{ok:true;items:FitHealthLog[]}>(`/api/v1/fit/health/logs?limit=${safe}`,{cache:'no-store'}).then(r=>r.items)
}
export function syncFitHealthLog(input:{recorded_at:string;weight_kg?:number;height_cm?:number;steps?:number;active_calories?:number;total_calories?:number;activity_minutes?:number;resting_heart_rate?:number;sleep_minutes?:number;source?:string;provider_record_id?:string;summary?:Record<string,unknown>}){
  return postJson<{ok:true;health_log:FitHealthLog;idempotent?:boolean}>('/api/v1/fit/health/logs',input).then(r=>r.health_log)
}
export function getFitIntegrations(){
  return readJson<{ok:true;items:FitIntegration[]}>('/api/v1/fit/integrations',{cache:'no-store'}).then(r=>r.items)
}
export function connectFitIntegration(provider:string){
  return postJson<{ok:true;connection:FitIntegration}>(`/api/v1/fit/integrations/${encodeURIComponent(provider)}/connect`,{}).then(r=>r.connection)
}
