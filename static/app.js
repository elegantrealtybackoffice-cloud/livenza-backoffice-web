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
  // Web 1.3.2: all Agreement Studio inputs remain optional for every preset.
  document.querySelectorAll('#agreementForm [name]').forEach(el=>{el.required=false;el.closest('label')?.classList.remove('required-field')});
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

// Web 1.3 liquid-glass interaction layer
const footerYear=document.getElementById('footerYear'); if(footerYear) footerYear.textContent=new Date().getFullYear();
if(matchMedia('(pointer:fine)').matches && !matchMedia('(prefers-reduced-motion:reduce)').matches){
  document.querySelectorAll('.module-card,.city-card,.query-card,.stats>div').forEach(card=>{
    card.addEventListener('pointermove',e=>{const r=card.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;card.style.transform=`translateY(-5px) perspective(800px) rotateX(${-y*2.4}deg) rotateY(${x*2.4}deg)`});
    card.addEventListener('pointerleave',()=>card.style.transform='');
  });
}

// Web 1.3.1 Aadhaar -> Agreement tenant autofill
const aadhaarAgreementFile=document.getElementById('aadhaarAgreementFile');
const extractAadhaarBtn=document.getElementById('extractAadhaarBtn');
const aadhaarExtractStatus=document.getElementById('aadhaarExtractStatus');
function setAadhaarStatus(message,state=''){
  if(!aadhaarExtractStatus)return;
  aadhaarExtractStatus.textContent=message;
  aadhaarExtractStatus.className='aadhaar-extract-status'+(state?' '+state:'');
}
function fillAgreementField(name,value){
  if(!value)return false;
  const el=document.querySelector(`#agreementForm [name="${name}"]`);
  if(!el)return false;
  el.value=value;
  el.classList.remove('aadhaar-field-flash');
  void el.offsetWidth;
  el.classList.add('aadhaar-field-flash');
  setTimeout(()=>el.classList.remove('aadhaar-field-flash'),950);
  return true;
}
if(extractAadhaarBtn){
  extractAadhaarBtn.addEventListener('click',async()=>{
    const file=aadhaarAgreementFile?.files?.[0];
    if(!file){setAadhaarStatus('Choose an Aadhaar JPEG, PNG or PDF first.','error');return;}
    if(file.size>10*1024*1024){setAadhaarStatus('The Aadhaar file must be 10 MB or smaller.','error');return;}
    const original=extractAadhaarBtn.textContent;
    extractAadhaarBtn.disabled=true; extractAadhaarBtn.textContent='Reading Aadhaar…';
    setAadhaarStatus('Reading the document securely. The original upload will not be stored.','working');
    try{
      const fd=new FormData(); fd.append('aadhaar_file',file);
      const r=await fetch('/agreements/aadhaar-extract',{method:'POST',body:fd,credentials:'same-origin'});
      const d=await r.json().catch(()=>({}));
      if(!r.ok||!d.ok)throw new Error(d.error||'Could not read Aadhaar document.');
      const fields=d.fields||{}; let filled=0;
      ['tenant_name','tenant_father','tenant_dob','tenant_address','tenant_id_type','tenant_id_no'].forEach(k=>{if(fillAgreementField(k,fields[k]))filled++});
      const extra=fields.gender?` Gender detected: ${fields.gender}.`:'';
      setAadhaarStatus(`Auto-filled ${filled} tenant fields. ${d.note||''}${extra} Review all values before saving.`, 'success');
    }catch(err){
      setAadhaarStatus(err.message||'Could not extract Aadhaar details.','error');
    }finally{
      extractAadhaarBtn.disabled=false; extractAadhaarBtn.textContent=original;
    }
  });
}

// ===== Web 1.4.1 • Fullscreen + website orientation controls =====
(function(){
  const viewport=document.getElementById('appViewport');
  const fsBtn=document.getElementById('fullscreenToggle');
  const rotateBtn=document.getElementById('rotateMenuToggle');
  const menu=document.getElementById('rotateMenu');
  if(!viewport) return;

  const modes=['auto','portrait','landscape','90','180','270'];
  function fullscreenElement(){return document.fullscreenElement||document.webkitFullscreenElement||null}
  function updateFullscreenButton(){
    if(!fsBtn)return;
    const active=!!fullscreenElement();
    const label=fsBtn.querySelector('.tool-label');
    const icon=fsBtn.querySelector('.tool-icon');
    if(label)label.textContent=active?'Exit Full Screen':'Full Screen';
    if(icon)icon.textContent=active?'⛶':'⛶';
    fsBtn.classList.toggle('active',active);
    fsBtn.title=active?'Exit fullscreen':'Enter fullscreen';
  }
  async function toggleFullscreen(){
    try{
      if(fullscreenElement()){
        if(document.exitFullscreen)await document.exitFullscreen();
        else if(document.webkitExitFullscreen)document.webkitExitFullscreen();
      }else{
        if(viewport.requestFullscreen)await viewport.requestFullscreen({navigationUI:'hide'});
        else if(viewport.webkitRequestFullscreen)viewport.webkitRequestFullscreen();
        else alert('Fullscreen is not supported by this browser.');
      }
    }catch(err){console.warn('Fullscreen request was blocked:',err)}
  }

  function clearViewClasses(){
    ['view-auto','view-portrait','view-landscape','view-rot-90','view-rot-180','view-rot-270'].forEach(c=>viewport.classList.remove(c));
    document.documentElement.classList.remove('site-rotation-active');
  }
  async function tryOrientationLock(mode){
    if(!screen.orientation)return;
    try{
      if(mode==='auto') { if(screen.orientation.unlock) screen.orientation.unlock(); return; }
      if(!fullscreenElement() || !screen.orientation.lock)return;
      if(mode==='portrait')await screen.orientation.lock('portrait');
      if(mode==='landscape')await screen.orientation.lock('landscape');
    }catch(err){/* Browser may restrict orientation lock; CSS fallback remains active. */}
  }
  function applyViewMode(mode,save=true){
    if(!modes.includes(mode))mode='auto';
    clearViewClasses();
    viewport.classList.add(mode==='90'?'view-rot-90':mode==='180'?'view-rot-180':mode==='270'?'view-rot-270':`view-${mode}`);
    if(['90','180','270'].includes(mode))document.documentElement.classList.add('site-rotation-active');
    document.querySelectorAll('[data-view-mode]').forEach(b=>b.classList.toggle('selected',b.dataset.viewMode===mode));
    if(rotateBtn){
      const label=rotateBtn.querySelector('.tool-label');
      if(label)label.textContent=mode==='auto'?'Rotate':mode==='portrait'?'Portrait':mode==='landscape'?'Landscape':`${mode}°`;
      rotateBtn.dataset.mode=mode;
    }
    if(save){try{localStorage.setItem('livenza_view_mode',mode)}catch(e){}}
    tryOrientationLock(mode);
  }

  fsBtn?.addEventListener('click',toggleFullscreen);
  document.addEventListener('fullscreenchange',()=>{updateFullscreenButton();applyViewMode(rotateBtn?.dataset.mode||'auto',false)});
  document.addEventListener('webkitfullscreenchange',updateFullscreenButton);
  rotateBtn?.addEventListener('click',e=>{
    e.stopPropagation();
    if(!menu)return;
    menu.hidden=!menu.hidden;
    rotateBtn.setAttribute('aria-expanded',String(!menu.hidden));
  });
  menu?.addEventListener('click',e=>{
    const btn=e.target.closest('[data-view-mode]');if(!btn)return;
    applyViewMode(btn.dataset.viewMode);
    menu.hidden=true;rotateBtn?.setAttribute('aria-expanded','false');
  });
  document.addEventListener('click',e=>{if(menu&&!menu.hidden&&!e.target.closest('.rotate-control')){menu.hidden=true;rotateBtn?.setAttribute('aria-expanded','false')}});
  window.addEventListener('keydown',e=>{if(e.key==='Escape'&&menu&&!menu.hidden){menu.hidden=true;rotateBtn?.setAttribute('aria-expanded','false')}});

  let initial='auto';try{initial=localStorage.getItem('livenza_view_mode')||'auto'}catch(e){}
  applyViewMode(initial,false);updateFullscreenButton();
})();
