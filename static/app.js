async function copyText(text){try{await navigator.clipboard.writeText(text);return true}catch(e){return false}}

document.addEventListener('click', async (e)=>{
  if(e.target.classList.contains('copy-btn')){
    const ta=e.target.closest('.review-card').querySelector('textarea');
    await copyText(ta.value); e.target.textContent='Copied ✓'; setTimeout(()=>e.target.textContent='Copy Review',1200);
  }
  if(e.target.classList.contains('copy-open-btn')){
    const ta=e.target.closest('.review-card').querySelector('textarea'); await copyText(ta.value);
    const u=e.target.dataset.url; if(u) window.open(u,'_blank','noopener');
    e.target.textContent='Copied • Google Opened'; setTimeout(()=>e.target.textContent='Copy Review + Open Google',1600);
  }
});

const preset=document.getElementById('presetSelect');
async function applyPreset(){
  if(!preset||!window.PRESET_URL)return;
  const url=window.PRESET_URL.replace('__NAME__',encodeURIComponent(preset.value));
  const res=await fetch(url); if(!res.ok)return; const payload=await res.json();
  const values=payload.values||payload;
  Object.entries(values).forEach(([k,v])=>{const el=document.querySelector(`[name="${k}"]`);if(el)el.value=v});
  if(Array.isArray(payload.required)){
    document.querySelectorAll('#agreementForm [name]').forEach(el=>{el.required=false;el.closest('label')?.classList.remove('required-field')});
    payload.required.forEach(k=>{const el=document.querySelector(`#agreementForm [name="${k}"]`);if(el){el.required=true;el.closest('label')?.classList.add('required-field')}});
  }
  if(payload.profile){
    const t=document.getElementById('presetTitle'),s=document.getElementById('presetSubtitle'),n=document.getElementById('presetNature');
    if(t)t.textContent=payload.profile.title_en||preset.value;
    if(s)s.textContent=payload.profile.subtitle_en||'';
    if(n)n.textContent=payload.profile.nature_en||'';
  }
  const calc=document.getElementById('calcEnd'); if(calc&&document.getElementById('startDate')?.value) calc.click();
  document.getElementById('presetProfile')?.classList.add('pulse-once'); setTimeout(()=>document.getElementById('presetProfile')?.classList.remove('pulse-once'),700);
}
if(preset) preset.addEventListener('change',applyPreset);

const calc=document.getElementById('calcEnd');
if(calc){calc.addEventListener('click',async()=>{
  const fd=new FormData(); fd.append('start_date',document.getElementById('startDate').value); fd.append('months',document.getElementById('termMonths').value||0); fd.append('days',0);
  const r=await fetch('/date-calculator',{method:'POST',body:fd}); const d=await r.json();
  if(d.end_date){document.getElementById('endDate').value=d.end_date; calc.textContent=`Ends ${d.end_date} • ${d.total_days} days`; setTimeout(()=>calc.textContent='Calculate End Date',2400)} else alert(d.error||'Could not calculate date');
});}

function validGoogleReviewUrl(v){
  try{const u=new URL(v);const h=u.hostname.toLowerCase();return h==='g.page'||h.endsWith('.g.page')||h==='google.com'||h.endsWith('.google.com')||h==='google.co.in'||h.endsWith('.google.co.in')||h==='maps.app.goo.gl'||h.endsWith('.maps.app.goo.gl')}catch(e){return false}
}
const reviewInput=document.getElementById('googleReviewUrl');
function refreshReviewQr(){
  if(!reviewInput)return; const v=reviewInput.value.trim(); const panel=document.getElementById('reviewQrPanel'),img=document.getElementById('reviewQrImage'),ph=document.getElementById('qrPlaceholder'),open=document.getElementById('openGoogleReview'),down=document.getElementById('downloadReviewQr');
  if(validGoogleReviewUrl(v)){
    const qr=`/reviews/qr.png?url=${encodeURIComponent(v)}`;
    panel?.classList.remove('qr-awaiting'); if(img){img.src=qr;img.style.display='block'} if(ph)ph.style.display='none';
    if(open){open.href=v;open.classList.remove('disabled-link')} if(down){down.href=qr;down.classList.remove('disabled-link')}
  } else {
    panel?.classList.add('qr-awaiting'); if(img)img.style.display='none'; if(ph)ph.style.display='block'; if(open){open.href='#';open.classList.add('disabled-link')} if(down){down.href='#';down.classList.add('disabled-link')}
  }
}
if(reviewInput){reviewInput.addEventListener('input',refreshReviewQr);reviewInput.addEventListener('change',refreshReviewQr);refreshReviewQr()}

document.querySelectorAll('a.disabled-link').forEach(a=>a.addEventListener('click',e=>{if(a.classList.contains('disabled-link'))e.preventDefault()}));

function updateFooterClock(){const el=document.getElementById('footerClock');if(el)el.textContent=new Date().toLocaleString(undefined,{weekday:'short',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'})}
updateFooterClock();setInterval(updateFooterClock,1000);
