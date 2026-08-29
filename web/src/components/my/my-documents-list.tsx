'use client'
import{useEffect,useState}from'react'
import{getMyDocuments}from'@/lib/api'
import type{CustomerDocumentSummary}from'@/lib/types'
export function MyDocumentsList(){const[items,setItems]=useState<CustomerDocumentSummary[]>([]);useEffect(()=>{getMyDocuments().then(r=>setItems(r.items))},[]);return <div className="ecosystem-grid">{items.map(item=><article className="ecosystem-card" key={item.id}><h2>{item.display_name}</h2><p>{item.document_type.replace('_',' ')}</p><p>{item.private?'Private document':'Customer document'}</p></article>)}{!items.length?<p>No documents are available yet.</p>:null}</div>}
