import{notFound}from'next/navigation'
import{ApiError,getProduct}from'@/lib/api'
import ProductDetail from'@/components/store/product-detail'
export const dynamic='force-dynamic'
export default async function ProductPage({params}:{params:Promise<{slug:string}>}){const{slug}=await params;let product;try{product=await getProduct(slug)}catch(e){if(e instanceof ApiError&&e.status===404)notFound();throw e}return <main className="store-page" data-brand="store"><div className="store-inner"><ProductDetail product={product}/></div></main>}
