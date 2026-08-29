import type{StoreProduct}from'@/lib/types'
import Storefront from '@/components/store/storefront'
import{getProducts}from'@/lib/api'
export const dynamic='force-dynamic'
export default async function StorePage(){let products:StoreProduct[]=[];try{products=await getProducts()}catch{}return <main data-brand="store"><Storefront products={products}/></main>}
