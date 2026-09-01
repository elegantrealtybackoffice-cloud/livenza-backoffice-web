import { ParentSharePayment } from '@/components/booking/parent-share-payment'

const apiOrigin = process.env.LIVENZA_API_ORIGIN ?? 'http://127.0.0.1:5000'

type SharePayload = {
  booking: { id:string; status:string; booking_mode:string; stay_type:string; start:string; end:string; currency:string; total_minor:number; amount_due_now_minor:number }
  property: { name:string; city:string; area:string; summary:string }
  published: Record<'safety'|'meals'|'transport'|'policies', string | null>
}

function money(minor:number, currency:string){ return new Intl.NumberFormat('en-IN',{style:'currency',currency}).format(minor/100) }

export default async function ParentSharePage({ params }:{ params:Promise<{token:string}> }){
  const {token}=await params
  const response=await fetch(`${apiOrigin}/api/v1/booking-shares/${encodeURIComponent(token)}`,{cache:'no-store'})
  if(!response.ok){ return <main className="ecosystem-page" data-brand="stays"><section className="ecosystem-hero"><div className="section-inner"><div className="ecosystem-eyebrow">LIVENZA.STAYS</div><h1>THIS SHARE LINK ISN&apos;T AVAILABLE.</h1><p>Ask the resident to create a new parent-share link.</p></div></section></main> }
  const data=(await response.json()) as SharePayload
  const sections:[string,string|null][]=[['Safety',data.published.safety],['Meals',data.published.meals],['Transport',data.published.transport],['Policies',data.published.policies]]
  return <main className="ecosystem-page" data-brand="stays"><section className="ecosystem-hero"><div className="section-inner"><div className="ecosystem-eyebrow">PARENT SHARE · LIVENZA.STAYS</div><h1>{data.property.name}</h1><p>{[data.property.area,data.property.city].filter(Boolean).join(' · ')}</p><p>{data.property.summary}</p><div className="ecosystem-actions"><div><strong>Approve & Pay</strong><ParentSharePayment token={token} bookingId={data.booking.id}/></div></div></div></section><section className="ecosystem-section"><div className="section-inner"><h2>Booking summary</h2><p>{data.booking.start} → {data.booking.end}</p><p><strong>Due now:</strong> {money(data.booking.amount_due_now_minor,data.booking.currency)}</p><p><strong>Total:</strong> {money(data.booking.total_minor,data.booking.currency)}</p><div className="ecosystem-grid">{sections.map(([label,value])=><article className="ecosystem-card" key={label}><h3>{label}</h3><p>{value || 'Not published yet'}</p></article>)}</div></div></section></main>
}
