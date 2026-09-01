import type{StoreProduct}from'@/lib/types'
import Storefront from '@/components/store/storefront'
import{getProducts}from'@/lib/api'
const ALLOWED=new Set(['wear','move','live','accessories','limited','residents'])
export const dynamic='force-dynamic'
export default async function CollectionPage({params}:{params:Promise<{collection:string}>}){const{collection}=await params;const key=decodeURIComponent(collection).toLowerCase();let products:StoreProduct[]=[];try{products=ALLOWED.has(key)?await getProducts({category:key}):[]}catch{}return <main data-brand="store"><Storefront products={products}/></main>}
