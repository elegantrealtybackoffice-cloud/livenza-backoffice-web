'use client'

import { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { ApiError, createBooking, createHold, createPayment, getAvailability, getBookingAddons, getMe, getProperty, requestOtp, verifyOtp } from '@/lib/api'
import type { Booking, BookingAddon, Customer, RatePlan, StayPropertyDetail, StayType } from '@/lib/types'
import { track } from '@/lib/analytics'
import { openRazorpayCheckout as loadRazorpay } from '@/lib/razorpay'
// loadRazorpay lazy-loads https://checkout.razorpay.com/v1/checkout.js only from the payment action.

const STEPS=['Stay','Sign in','Resident','Guardian','Add-ons','Summary','Payment'] as const

function money(minor:number,currency='INR'){return new Intl.NumberFormat('en-IN',{style:'currency',currency}).format(minor/100)}

export function BookingWizard({initialProperty='',initialRoomCategory=''}:{initialProperty?:string;initialRoomCategory?:string}){
  const router=useRouter()
  const [step,setStep]=useState(0)
  const [propertySlug,setPropertySlug]=useState(initialProperty)
  const [property,setProperty]=useState<StayPropertyDetail|null>(null)
  const [roomCategory,setRoomCategory]=useState(initialRoomCategory)
  const [ratePlanCode,setRatePlanCode]=useState('')
  const [start,setStart]=useState('')
  const [end,setEnd]=useState('')
  const [customer,setCustomer]=useState<Customer|null>(null)
  const [mobile,setMobile]=useState('')
  const [otp,setOtp]=useState('')
  const [otpSent,setOtpSent]=useState(false)
  const [residentName,setResidentName]=useState('')
  const [residentContext,setResidentContext]=useState('')
  const [guardianName,setGuardianName]=useState('')
  const [guardianMobile,setGuardianMobile]=useState('')
  const [companyName,setCompanyName]=useState('')
  const [addons,setAddons]=useState<BookingAddon[]>([])
  const [selectedAddons,setSelectedAddons]=useState<string[]>([])
  const [bookingMode,setBookingMode]=useState<'book_now'|'reserve'>('book_now')
  const [booking,setBooking]=useState<Booking|null>(null)
  const [paymentPending,setPaymentPending]=useState(false)
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')

  useEffect(()=>{ getMe().then(r=>setCustomer(r.customer)).catch(()=>undefined); getBookingAddons().then(setAddons).catch(()=>setAddons([])) },[])
  useEffect(()=>{ if(!propertySlug){setProperty(null);return} ; getProperty(propertySlug).then(data=>{setProperty(data); setRoomCategory(current=>current || data.room_categories[0]?.slug || '')}).catch(()=>setProperty(null)) },[propertySlug])

  const category=useMemo(()=>property?.room_categories.find(item=>item.slug===roomCategory)??null,[property,roomCategory])
  const plans=category?.rate_plans??[]
  const plan=plans.find(item=>item.code===ratePlanCode)??plans[0]??null
  const stayType=(plan?.stay_type??property?.stay_types[0]??'student') as StayType
  useEffect(()=>{ if(plan && !ratePlanCode) setRatePlanCode(plan.code) },[plan,ratePlanCode])

  async function next(){
    setError('')
    if(step===0){
      if(!propertySlug||!roomCategory||!plan||!start||!end){setError('Choose a property, room, rate plan and dates.');return}
      setBusy(true); try{const a=await getAvailability({property:propertySlug,room_category:roomCategory,start,end}); if(a.available_count<1){setError('No live inventory is available for those dates.');return}; track('availability_check',{property:propertySlug,available:a.available_count}); setStep(1)}catch(e){setError(e instanceof Error?e.message:'Availability could not be checked.')}finally{setBusy(false)}; return
    }
    if(step===1){ if(!customer){setError('Sign in with your mobile number before continuing.');return}; setStep(2); return }
    if(step===2){ if(!residentName.trim()){setError('Resident name is required.');return}; setStep(3); return }
    if(step===3){ if(stayType === 'student' && (!guardianName.trim()||!guardianMobile.trim())){setError('Guardian name and mobile are required for student bookings.');return}; if(stayType === 'corporate' && !companyName.trim()){setError('Company name is required for a corporate booking.');return}; setStep(4); return }
    if(step===4){ setStep(5); return }
    if(step===5){
      if(!plan){setError('Rate plan is missing.');return}
      setBusy(true)
      try{
        const held=await createHold({property_slug:propertySlug,room_category_slug:roomCategory,rate_plan_code:plan.code,start,end})
        const created=await createBooking({hold_id:held.hold.id,booking_mode:bookingMode,guardian:stayType==='student'?{name:guardianName,mobile:guardianMobile}:undefined,details:{resident_name:residentName,context:residentContext,company:companyName},addons:selectedAddons.map(code=>({code}))})
        setBooking(created.booking); track('booking_start',{booking_id:created.booking.id,mode:bookingMode}); setStep(6)
      }catch(e){setError(e instanceof Error?e.message:'Booking could not be created.')}finally{setBusy(false)}
    }
  }

  async function sendOtp(){setError('');setBusy(true);try{const result=await requestOtp(mobile);setOtpSent(true); if(result.test_otp) setOtp(result.test_otp)}catch(e){setError(e instanceof Error?e.message:'OTP could not be sent.')}finally{setBusy(false)}}
  async function confirmOtp(){setError('');setBusy(true);try{const result=await verifyOtp(mobile,otp);setCustomer(result.customer);track('login');}catch(e){setError(e instanceof Error?e.message:'OTP could not be verified.')}finally{setBusy(false)}}

  async function pay(){
    if(!booking||paymentPending)return
    setPaymentPending(true);setError('');track('booking_payment_start',{booking_id:booking.id})
    try{
      const result=await createPayment(booking.id)
      await loadRazorpay({
        key:result.checkout.key_id,amount:result.checkout.amount_minor,currency:result.checkout.currency,
        order_id:result.checkout.order_id,name:'Livenza.life',description:`Booking ${booking.id}`,
        handler:()=>router.push(`/stays/booking/${booking.id}`),
        modal:{ondismiss:()=>setPaymentPending(false)},
        prefill:{name:residentName,contact:customer?.primary_mobile||mobile},
        theme:{color:'#6d45e5'},
      })
    }catch(e){setPaymentPending(false);setError(e instanceof ApiError?e.message:(e instanceof Error?e.message:'Payment could not start.'))}
  }

  const dueNow=plan ? (bookingMode === 'reserve' ? plan.reservation_amount_minor : plan.amount_minor + plan.security_deposit_minor + selectedAddons.reduce((sum,code)=>sum+(addons.find(a=>a.code===code)?.amount_minor??0),0)) : 0

  return <div className="booking-shell">
    <ol className="booking-steps" aria-label="Booking progress">{STEPS.map((label,index)=><li key={label} data-active={index===step} data-complete={index<step}><button type="button" data-booking-step={index} aria-current={index===step?'step':undefined} disabled={index>=step} onClick={()=>setStep(index)}>{label}</button></li>)}</ol>
    {error?<div className="booking-error" role="alert">{error}</div>:null}
    {step===0?<section className="booking-panel"><h1>Choose your stay</h1><label>Property<input value={propertySlug} onChange={(e:any)=>setPropertySlug(e.target.value)} placeholder="Property slug"/></label><label>Room category<select value={roomCategory} onChange={(e:any)=>{setRoomCategory(e.target.value);setRatePlanCode('')}}><option value="">Choose room</option>{property?.room_categories.map(item=><option key={item.slug} value={item.slug}>{item.name}</option>)}</select></label><label>Rate plan<select value={ratePlanCode||plan?.code||''} onChange={(e:any)=>setRatePlanCode(e.target.value)}><option value="">Choose rate plan</option>{plans.map(item=><option key={item.code} value={item.code}>{item.billing_period} · {money(item.amount_minor,item.currency)}</option>)}</select></label><div className="booking-row"><label>Move-in<input type="date" value={start} onChange={(e:any)=>setStart(e.target.value)}/></label><label>Move-out<input type="date" value={end} onChange={(e:any)=>setEnd(e.target.value)}/></label></div><button onClick={next} disabled={busy}>CHECK LIVE AVAILABILITY</button></section>:null}
    {step===1?<section className="booking-panel"><h1>Sign in</h1>{customer?<><p>Signed in as {customer.primary_mobile}</p><button onClick={next}>CONTINUE</button></>:<><label>Mobile number<input inputMode="tel" value={mobile} onChange={(e:any)=>setMobile(e.target.value)} placeholder="9876543210"/></label><button onClick={sendOtp} disabled={busy||!mobile}>SEND OTP</button>{otpSent?<><label>6-digit OTP<input inputMode="numeric" value={otp} onChange={(e:any)=>setOtp(e.target.value)} maxLength={6}/></label><button onClick={confirmOtp} disabled={busy||otp.length!==6}>VERIFY OTP</button></>:null}</>}</section>:null}
    {step===2?<section className="booking-panel"><h1>Resident</h1><label>Resident name<input value={residentName} onChange={(e:any)=>setResidentName(e.target.value)}/></label><label>{stayType==='corporate'?'Role / employee reference':'College / course'}<input value={residentContext} onChange={(e:any)=>setResidentContext(e.target.value)}/></label><button onClick={next}>CONTINUE</button></section>:null}
    {step===3?<section className="booking-panel"><h1>{stayType==='student'?'Guardian':'Corporate details'}</h1>{stayType === 'student'?<><label>Guardian name<input value={guardianName} onChange={(e:any)=>setGuardianName(e.target.value)}/></label><label>Guardian mobile<input inputMode="tel" value={guardianMobile} onChange={(e:any)=>setGuardianMobile(e.target.value)}/></label></>:<label>Company name<input value={companyName} onChange={(e:any)=>setCompanyName(e.target.value)}/></label>}<button onClick={next}>CONTINUE</button></section>:null}
    {step===4?<section className="booking-panel"><h1>Add-ons</h1>{addons.length?addons.map(item=><label className="booking-check" key={item.code}><input type="checkbox" checked={selectedAddons.includes(item.code)} onChange={(e:any)=>setSelectedAddons(current=>e.target.checked?[...current,item.code]:current.filter(code=>code!==item.code))}/><span>{item.label}<small>{item.amount_minor?money(item.amount_minor):'Included / no charge'}</small></span></label>):<p>No paid add-ons are published for online booking yet.</p>}<button onClick={next}>CONTINUE</button></section>:null}
    {step===5&&plan?<section className="booking-panel"><h1>Summary</h1><p>{property?.name} · {category?.name}</p><p>{start} → {end}</p><div className="booking-mode"><button data-selected={bookingMode==='book_now'} onClick={()=>setBookingMode('book_now')}>BOOK NOW</button>{plan.reservation_amount_minor>0?<button data-selected={bookingMode === 'reserve'} onClick={()=>setBookingMode('reserve')}>RESERVE</button>:null}</div>{bookingMode === 'reserve'?<p>Reservation due now: <strong>{money(plan.reservation_amount_minor,plan.currency)}</strong>. Full stay total remains payable under the published booking terms.</p>:<p>Due now: <strong>{money(dueNow,plan.currency)}</strong></p>}<button onClick={next} disabled={busy}>CREATE SECURE BOOKING</button></section>:null}
    {step===6&&booking?<section className="booking-panel"><h1>Payment</h1><p>Booking {booking.id}</p><p>Due now: <strong>{money(booking.amount_due_now_minor,booking.currency)}</strong></p><button onClick={pay} disabled={paymentPending}>{paymentPending?'OPENING PAYMENT…':'PAY SECURELY'}</button><p className="booking-note">Confirmation comes from the payment gateway webhook. Closing the browser does not mark the booking as paid.</p></section>:null}
  </div>
}
