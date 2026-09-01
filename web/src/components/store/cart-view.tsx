'use client'
import{useEffect,useState}from'react'
import Link from'next/link'
import{quoteCart}from'@/lib/api'
import type{CartItem,CartQuote}from'@/lib/types'
const CART_KEY='livenza_store_cart_v1'
function money(minor:number,currency='INR'){return new Intl.NumberFormat('en-IN',{style:'currency',currency}).format(minor/100)}
function normalise(value:unknown):CartItem[]{if(!Array.isArray(value))return[];return value.map((x:any)=>({variant_id:Number(x?.variant_id),quantity:Number(x?.quantity)})).filter(x=>x.variant_id>0&&x.quantity>0)}
export default function CartView(){const[items,setItems]=useState<CartItem[]>([]);const[quote,setQuote]=useState<CartQuote|null>(null);const[error,setError]=useState('');const[busy,setBusy]=useState(true)
  useEffect(()=>{let parsed:unknown=[];try{parsed=JSON.parse(localStorage.getItem(CART_KEY)||'[]')}catch{};setItems(normalise(parsed));setBusy(false)},[])
  useEffect(()=>{if(busy)return;localStorage.setItem(CART_KEY,JSON.stringify(items.map(({variant_id,quantity})=>({variant_id,quantity}))));if(!items.length){setQuote(null);return};setError('');quoteCart(items).then(setQuote).catch(e=>{setQuote(null);setError(e instanceof Error?e.message:'Your bag could not be quoted.')})},[items,busy])
  function quantity(variant_id:number,next:number){setItems(old=>next<1?old.filter(i=>i.variant_id!==variant_id):old.map(i=>i.variant_id===variant_id?{...i,quantity:next}:i))}
  if(busy)return <div className="store-empty">Loading your bag…</div>
  return <div className="store-cart"><div><span className="store-kicker">YOUR BAG</span><h1>{items.length?'Ready when you are.':'Your bag is empty.'}</h1>{error?<div className="store-error">{error}</div>:null}{quote?.items.map(line=><article className="store-cart-line" key={line.variant_id}><div><small>{line.sku}</small><h3>{line.product_name}</h3><p>{line.variant_title}</p></div><div className="store-qty"><button onClick={()=>quantity(line.variant_id,line.quantity-1)} aria-label="Reduce quantity">−</button><span>{line.quantity}</span><button onClick={()=>quantity(line.variant_id,line.quantity+1)} aria-label="Increase quantity">+</button></div><strong>{money(line.line_total_minor,line.currency)}</strong></article>)}{!items.length?<Link className="store-primary inline" href="/store">EXPLORE STORE</Link>:null}</div>{quote?<aside className="store-summary"><span>SUBTOTAL</span><b>{money(quote.subtotal_minor,quote.currency)}</b><span>DELIVERY</span><b>{quote.delivery_minor?money(quote.delivery_minor,quote.currency):'Calculated at checkout'}</b><hr/><span>TOTAL</span><strong>{money(quote.total_minor,quote.currency)}</strong><Link className="store-primary" href="/store/checkout">CHECKOUT</Link><small>Prices are refreshed from Livenza before checkout.</small></aside>:null}</div>
}
