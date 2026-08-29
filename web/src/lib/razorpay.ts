type RazorpayInstance={open:()=>void}
type RazorpayCtor=new (options:Record<string,unknown>)=>RazorpayInstance
declare global { interface Window { Razorpay?: RazorpayCtor } }

async function ensureRazorpay(){
  if(window.Razorpay) return
  await new Promise<void>((resolve,reject)=>{
    const existing=document.querySelector<HTMLScriptElement>('script[data-livenza-razorpay]')
    if(existing){existing.addEventListener('load',()=>resolve(),{once:true});existing.addEventListener('error',()=>reject(new Error('Payment library failed to load')),{once:true});return}
    const script=document.createElement('script')
    script.src='https://checkout.razorpay.com/v1/checkout.js'
    script.async=true
    script.dataset.livenzaRazorpay='1'
    script.onload=()=>resolve()
    script.onerror=()=>reject(new Error('Payment library failed to load'))
    document.head.appendChild(script)
  })
}

export async function openRazorpayCheckout(options:Record<string,unknown>){
  await ensureRazorpay()
  if(!window.Razorpay) throw new Error('Payment checkout is unavailable.')
  new window.Razorpay(options).open()
}
