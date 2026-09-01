import { BookingStatus } from '@/components/booking/booking-status'
export default async function BookingStatusPage({params}:{params:Promise<{bookingId:string}>}){const {bookingId}=await params;return <main className="ecosystem-page" data-brand="stays"><section className="ecosystem-section"><div className="section-inner"><BookingStatus bookingId={bookingId}/></div></section></main>}
