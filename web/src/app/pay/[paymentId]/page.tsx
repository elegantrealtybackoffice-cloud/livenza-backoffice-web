import { PaymentStatus } from '@/components/booking/payment-status'
export default async function PaymentPage({params}:{params:Promise<{paymentId:string}>}){const {paymentId}=await params;return <main className="ecosystem-page"><section className="ecosystem-section"><div className="section-inner"><PaymentStatus paymentId={paymentId}/></div></section></main>}
