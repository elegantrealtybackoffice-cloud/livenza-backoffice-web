'use client'
import{useEffect,useMemo,useState}from'react'
import Link from'next/link'
import type{CartItem,StoreProduct}from'@/lib/types'
import{track}from'@/lib/analytics'
const CART_KEY='livenza_store_cart_v1'
function money(minor:number,currency='INR'){return new Intl.NumberFormat('en-IN',{style:'currency',currency}).format(minor/100)}
function loadCart():CartItem[]{try{const parsed=JSON.parse(localStorage.getItem(CART_KEY)||'[]');return Array.isArray(parsed)?parsed.filter(x=>Number(x?.variant_id)>0&&Number(x?.quantity)>0).map(x=>({variant_id:Number(x.variant_id),quantity:Number(x.quantity)})):[]}catch{return[]}}
export default function ProductDetail({product}:{product:StoreProduct}){
  const [variantId,setVariantId]=useState(product.variants[0]?.id??0);const[added,setAdded]=useState(false)
  const variant=useMemo(()=>product.variants.find(v=>v.id===variantId)??product.variants[0],[product,variantId])
  useEffect(()=>track('product_view',{product:product.slug}),[product.slug])
  function add(){if(!variant||variant.available_stock<1)return;const cart=loadCart();const existing=cart.find(i=>i.variant_id===variant.id);if(existing)existing.quantity=Math.min(existing.quantity+1,variant.available_stock);else cart.push({variant_id:variant.id,quantity:1});localStorage.setItem(CART_KEY,JSON.stringify(cart.map(({variant_id,quantity})=>({variant_id,quantity}))));track('add_to_cart',{product:product.slug,variant_id:variant.id});setAdded(true)}
  return <div className="store-product-detail"><div className="store-product-stage"><span>livenza.store</span><strong>{product.name}</strong></div><div className="store-product-copy"><span className="store-kicker">{product.collection||product.category}</span><h1>{product.name}</h1><p>{product.description||product.summary}</p>{product.variants.length?<><label>Choose variant<select value={variantId} onChange={(e:any)=>setVariantId(Number(e.target.value))}>{product.variants.map(v=><option value={v.id} key={v.id}>{v.title} · {money(v.price_minor,v.currency)}{v.available_stock<1?' · Sold out':''}</option>)}</select></label><div className="store-price">{variant?money(variant.price_minor,variant.currency):''}</div><button className="store-primary" disabled={!variant||variant.available_stock<1} onClick={add}>{variant&&variant.available_stock>0?'ADD TO BAG':'SOLD OUT'}</button>{added?<p className="store-success">Added. <Link href="/store/cart">View your bag →</Link></p>:null}</>:<div className="store-empty">Variants are not yet published.</div>}</div></div>
}
