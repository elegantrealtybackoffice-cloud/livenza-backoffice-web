'use client'
import{useEffect,useState}from'react'
import{getMyPayments}from'@/lib/api'
import type{Payment}from'@/lib/types'
export function MyPaymentsList(){const[items,setItems]=useState<Payment[]>([]);useEffect(()=>{getMyPayments().then(r=>setItems(r.items))},[]);return <div className="ecosystem-grid">{items.map(item=><article className="ecosystem-card" key={item.id}><h2>{(item.amount_minor/100).toLocaleString('en-IN',{style:'currency',currency:item.currency})}</h2><p>{item.status}</p><p>{item.gateway}</p></article>)}{!items.length?<p>No payments yet.</p>:null}</div>}
