'use client'
import{useEffect,useState}from'react'
import Link from'next/link'
import{getMyStays}from'@/lib/api'
import type{MyStay}from'@/lib/types'
export function MyStaysList(){const[items,setItems]=useState<MyStay[]>([]);const[loaded,setLoaded]=useState(false);useEffect(()=>{getMyStays().then(r=>setItems(r.items)).finally(()=>setLoaded(true))},[]);if(!loaded)return <p>Loading stays…</p>;return <div className="ecosystem-grid">{items.length?items.map(item=><article className="ecosystem-card" key={item.id}><h2>{item.property.name}</h2><p>{item.start} → {item.end}</p><p>Status: {item.status.replace('_',' ')}</p><Link href={`/stays/booking/${item.id}`}>OPEN BOOKING →</Link></article>):<article className="ecosystem-card"><h2>No stays yet</h2><Link href="/stays">EXPLORE STAYS →</Link></article>}</div>}
