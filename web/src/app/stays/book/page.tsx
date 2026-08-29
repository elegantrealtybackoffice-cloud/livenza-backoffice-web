import { BookingWizard } from '@/components/booking/booking-wizard'
import '../stays.css'

export default async function BookingPage({searchParams}:{searchParams:Promise<{property?:string;room_category?:string}>}){
  const query=await searchParams
  return <main className="booking-page" data-brand="stays"><div className="stays-inner"><div className="eyebrow">LIVENZA.STAYS · SECURE BOOKING</div><BookingWizard initialProperty={query.property||''} initialRoomCategory={query.room_category||''}/></div></main>
}
