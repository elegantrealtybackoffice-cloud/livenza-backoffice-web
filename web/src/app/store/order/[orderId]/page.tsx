import OrderStatus from'@/components/store/order-status'
export default async function OrderPage({params}:{params:Promise<{orderId:string}>}){const{orderId}=await params;return <main className="store-page" data-brand="store"><div className="store-inner"><OrderStatus orderId={orderId}/></div></main>}
