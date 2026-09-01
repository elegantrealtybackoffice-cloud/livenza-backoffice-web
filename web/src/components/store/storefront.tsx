'use client'
import Link from 'next/link'
import {useEffect} from 'react'
import type{StoreProduct}from'@/lib/types'
import{track}from'@/lib/analytics'

const WORLDS=[['Wear','wear','Everyday apparel with a quiet Livenza signature.'],['Move','move','Training, gym and active-life essentials.'],['Live','live','Room, desk and everyday living objects.'],['Accessories','accessories','Bags, bottles, caps and useful carry.']] as const
function money(minor:number,currency='INR'){return new Intl.NumberFormat('en-IN',{style:'currency',currency}).format(minor/100)}
export default function Storefront({products}:{products:StoreProduct[]}){
  useEffect(()=>track('store_view'),[])
  return <div className="storefront">
    <section className="store-hero"><div className="store-inner"><span className="store-kicker">LIVENZA.STORE</span><h1>WEAR THE LIFE.</h1><p>Curated pieces for moving, living, travelling and showing up your way.</p><div className="store-hero-actions"><a href="#new">SHOP NEW ARRIVALS</a><Link href="/store/cart">YOUR BAG</Link></div></div></section>
    <section className="store-section"><div className="store-inner"><div className="store-section-head"><span>SHOP BY WORLD</span><h2>Built around how you live.</h2></div><div className="store-world-grid">{WORLDS.map(([label,slug,copy])=><Link href={`/store/${slug}`} className="store-world" key={slug}><span>.{slug}</span><h3>{label}</h3><p>{copy}</p><b>EXPLORE →</b></Link>)}</div></div></section>
    <section className="store-section" id="new"><div className="store-inner"><div className="store-section-head"><span>LIVE MORE / COLLECTION 01</span><h2>New arrivals.</h2></div>{products.length?<div className="store-product-grid">{products.slice(0,8).map(product=>{const first=product.variants[0];return <Link className="store-product-card" href={`/store/product/${product.slug}`} key={product.slug}><div className="store-product-image" aria-hidden="true"><span>livenza.{product.category}</span></div><div><small>{product.collection||product.category}</small><h3>{product.name}</h3><p>{product.summary}</p>{first?<strong>{money(first.price_minor,first.currency)}</strong>:<strong>COMING SOON</strong>}</div></Link>})}</div>:<div className="store-empty"><h3>The first drop is being curated.</h3><p>Products appear here only after inventory, variants and pricing are published in Livenza Admin.</p></div>}</div></section>
  </div>
}
