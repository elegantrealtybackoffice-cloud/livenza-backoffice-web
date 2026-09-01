'use client'
import {useEffect,useState} from 'react'
import Link from 'next/link'
import {getBooking} from '@/lib/api'
import type {Booking} from '@/lib/types'
import {track} from '@/lib/analytics'
export function BookingStatus({bookingId}:{bookingId:string}){
 const [booking,setBooking]=useState<Booking|null>(null);const [timedOut,setTimedOut]=useState(false);const [error,setError]=useState('')
 useEffect(()=>{let active=true;const started=Date.now();let timer:ReturnType<typeof setTimeout>|undefined;const poll=async()=>{try{const result=await getBooking(bookingId);if(!active)return;setBooking(result.booking);if(result.booking.status==='confirmed'){track('booking_complete',{booking_id:bookingId});return}if(['cancelled','expired'].includes(result.booking.status))return;if(Date.now()-started>=60_000){setTimedOut(true);return}timer=setTimeout(poll,2000)}catch(e){if(active)setError(e instanceof Error?e.message:'Booking status could not be loaded.')}};void poll();return()=>{active=false;if(timer)clearTimeout(timer)}},[bookingId])
 if(error)return <div className="booking-panel"><h1>Booking status unavailable</h1><p>{error}</p></div>
 return <div className="booking-panel"><div className="ecosystem-eyebrow">BOOKING {bookingId}</div><h1>{booking?.status==='confirmed'?'YOU’RE IN.':'CONFIRMING YOUR BOOKING…'}</h1>{booking?<><p>Status: <strong>{booking.status.replace('_',' ')}</strong></p><p>Due now: {(booking.amount_due_now_minor/100).toLocaleString('en-IN',{style:'currency',currency:booking.currency})}</p></>:<p>Checking the secure payment status…</p>}{booking?.status==='confirmed'?<div className="ecosystem-actions"><a className="ecosystem-primary" href={`/api/v1/bookings/${encodeURIComponent(bookingId)}/receipt`} target="_blank">VIEW RECEIPT</a><Link className="ecosystem-secondary" href="/my">My Livenza</Link></div>:null}{timedOut?<p>Payment confirmation is taking longer than expected. Refresh this page or check My Livenza; do not pay again unless the booking shows payment failed.</p>:null}</div>
}
