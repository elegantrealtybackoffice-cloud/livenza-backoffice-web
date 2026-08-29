import type { Availability, Booking, BookingAddon, City, Customer, InventoryHold, ListResponse, Payment, StayProperty, StayPropertyDetail, StayType } from './types'

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
