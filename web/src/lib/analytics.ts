export type AnalyticsEventName =
  | 'homepage_view'
  | 'stays_search'
  | 'property_view'
  | 'availability_check'
  | 'room_select'
  | 'booking_start'
  | 'parent_share'
  | 'booking_payment_start'
  | 'booking_complete'
  | 'store_view'
  | 'product_view'
  | 'add_to_cart'
  | 'checkout_start'
  | 'purchase'
  | 'signup'
  | 'login'
  | 'support_request'

export function track(name: AnalyticsEventName, properties: Record<string, string | number | boolean | null> = {}) {
  try {
    if (typeof window === 'undefined') return
    const target = window as Window & { dataLayer?: Array<Record<string, unknown>> }
    if (!Array.isArray(target.dataLayer)) return
    target.dataLayer.push({ event: name, ...properties })
  } catch {
    // Analytics must never block navigation or transactions.
  }
}
