'use client'
import{useEffect,useState}from'react'
import{getPayment}from'@/lib/api'
import type{Payment}from'@/lib/types'
export function PaymentStatus({paymentId}:{paymentId:string}){const[payment,setPayment]=useState<Payment|null>(null);const[error,setError]=useState('');useEffect(()=>{getPayment(paymentId).then(r=>setPayment(r.payment)).catch(e=>setError(e instanceof Error?e.message:'Payment not found.'))},[paymentId]);return <div className="booking-panel"><div className="ecosystem-eyebrow">PAYMENT</div><h1>{payment?payment.status.toUpperCase():'CHECKING PAYMENT'}</h1>{error?<p>{error}</p>:payment?<p>{(payment.amount_minor/100).toLocaleString('en-IN',{style:'currency',currency:payment.currency})}</p>:<p>Loading secure status…</p>}</div>}
