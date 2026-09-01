'use client'
import{useEffect,useState}from'react'
import Link from'next/link'
import{getStoreOrder}from'@/lib/api'
import type{StoreOrder}from'@/lib/types'
import{track}from'@/lib/analytics'
function money(minor:number,currency='INR'){return new Intl.NumberFormat('en-IN',{style:'currency',currency}).format(minor/100)}
export default function OrderStatus({orderId}:{orderId:string}){const[order,setOrder]=useState<StoreOrder|null>(null);const[error,setError]=useState('')
 useEffect(()=>{let active=true;let timer:ReturnType<typeof setTimeout>|undefined;const load=async()=>{try{const r=await getStoreOrder(orderId);if(!active)return;setOrder(r.order);if(r.order.status==='confirmed'){track('purchase',{order_id:r.order.id,total_minor:r.order.total_minor});localStorage.removeItem('livenza_store_cart_v1')}else if(r.order.status==='placed')timer=setTimeout(load,1800)}catch(e){if(active)setError(e instanceof Error?e.message:'Order could not be loaded.')}};load();return()=>{active=false;if(timer)clearTimeout(timer)}},[orderId])
 return <div className="store-order-status"><span className="store-kicker">ORDER</span><h1>{order?order.status==='confirmed'?"IT'S YOURS.":order.status.replace('_',' ').toUpperCase():'CHECKING PAYMENT'}</h1>{error?<div className="store-error">{error}</div>:order?<><p>Order #{order.id}</p><strong>{money(order.total_minor,order.currency)}</strong>{order.status==='placed'?<p>We are waiting for the signed payment confirmation. Do not pay twice.</p>:null}<div className="store-order-actions"><Link className="store-primary inline" href="/my/orders">MY ORDERS</Link><Link href="/store">KEEP EXPLORING</Link></div></>:<p>Secure status is loading…</p>}</div>
}
