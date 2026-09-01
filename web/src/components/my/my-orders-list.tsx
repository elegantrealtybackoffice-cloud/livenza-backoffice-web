'use client'
import{useEffect,useState}from'react'
import Link from'next/link'
import{getMyOrders}from'@/lib/api'
import type{StoreOrder}from'@/lib/types'
function money(minor:number,currency='INR'){return new Intl.NumberFormat('en-IN',{style:'currency',currency}).format(minor/100)}
export function MyOrdersList(){const[items,setItems]=useState<StoreOrder[]>([]);const[loading,setLoading]=useState(true);const[error,setError]=useState('');useEffect(()=>{getMyOrders().then(r=>setItems(r.items)).catch(e=>setError(e instanceof Error?e.message:'Orders could not be loaded.')).finally(()=>setLoading(false))},[]);if(loading)return <p>Loading orders…</p>;if(error)return <div className="ecosystem-card"><h2>Sign in to view orders</h2><p>{error}</p><Link href="/account?next=/my/orders">SIGN IN →</Link></div>;return <div><div className="ecosystem-eyebrow">STORE ORDERS</div><h1>YOUR ORDERS.</h1>{items.length?<div className="ecosystem-grid">{items.map(order=><article className="ecosystem-card" key={order.id}><div className="ecosystem-eyebrow">{order.status}</div><h2>{money(order.total_minor,order.currency)}</h2><p>{order.items.length} item{order.items.length===1?'':'s'}</p><Link href={`/store/order/${order.id}`}>VIEW ORDER →</Link></article>)}</div>:<div className="ecosystem-card"><h2>No store orders yet</h2><Link href="/store">EXPLORE LIVENZA.STORE →</Link></div>}</div>}
