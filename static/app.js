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

// ===== Web 1.4.3 • Fullscreen + reliable orientation popover =====
(function(){
  const viewport=document.getElementById('appViewport');
  const fsBtn=document.getElementById('fullscreenToggle');
  const rotateBtn=document.getElementById('rotateMenuToggle');
  const menu=document.getElementById('rotateMenu');
  if(!viewport) return;

  const modes=['auto','portrait','landscape','90','180','270'];
  const labels={auto:'Rotate',portrait:'Portrait',landscape:'Landscape','90':'90°','180':'180°','270':'270°'};
  function fullscreenElement(){return document.fullscreenElement||document.webkitFullscreenElement||null}
  function updateFullscreenButton(){
    if(!fsBtn)return;
    const active=!!fullscreenElement();
    const label=fsBtn.querySelector('.tool-label');
    if(label)label.textContent=active?'Exit Full Screen':'Full Screen';
    fsBtn.classList.toggle('active',active);
    fsBtn.setAttribute('aria-pressed',String(active));
    fsBtn.title=active?'Exit fullscreen':'Enter fullscreen';
  }
  async function toggleFullscreen(){
    try{
      if(fullscreenElement()){
        if(document.exitFullscreen)await document.exitFullscreen();
        else if(document.webkitExitFullscreen)document.webkitExitFullscreen();
      }else{
        const target=document.documentElement;
        if(target.requestFullscreen)await target.requestFullscreen({navigationUI:'hide'});
        else if(target.webkitRequestFullscreen)target.webkitRequestFullscreen();
        else alert('Fullscreen is not supported by this browser.');
      }
    }catch(err){console.warn('Fullscreen request was blocked:',err)}
  }

  function clearViewClasses(){
    ['view-auto','view-portrait','view-landscape','view-rot-90','view-rot-180','view-rot-270'].forEach(c=>viewport.classList.remove(c));
    document.documentElement.classList.remove('site-rotation-active');
  }
  async function tryOrientationLock(mode){
    if(!window.screen?.orientation)return;
    try{
      if(mode==='auto'){screen.orientation.unlock?.();return;}
      if(!fullscreenElement()||!screen.orientation.lock)return;
      if(mode==='portrait')await screen.orientation.lock('portrait-primary');
      if(mode==='landscape')await screen.orientation.lock('landscape-primary');
    }catch(err){/* CSS simulation below remains available on desktop browsers. */}
  }
  function applyViewMode(mode,save=true){
    if(!modes.includes(mode))mode='auto';
    clearViewClasses();
    const cls=mode==='90'?'view-rot-90':mode==='180'?'view-rot-180':mode==='270'?'view-rot-270':`view-${mode}`;
    viewport.classList.add(cls);
    if(['90','180','270'].includes(mode))document.documentElement.classList.add('site-rotation-active');
    document.querySelectorAll('[data-view-mode]').forEach(b=>{
      const selected=b.dataset.viewMode===mode;
      b.classList.toggle('selected',selected);
      b.setAttribute('aria-current',selected?'true':'false');
    });
    if(rotateBtn){
      const label=rotateBtn.querySelector('.tool-label');
      if(label)label.textContent=labels[mode]||'Rotate';
      rotateBtn.dataset.mode=mode;
      rotateBtn.classList.toggle('active',mode!=='auto');
    }
    if(save){try{localStorage.setItem('livenza_view_mode',mode)}catch(e){}}
    tryOrientationLock(mode);
  }

  function positionRotateMenu(){
    if(!menu||menu.hidden||!rotateBtn)return;
    const r=rotateBtn.getBoundingClientRect();
    const gap=10,pad=10;
    // Make measurable before calculating final placement.
    menu.style.left='0px';menu.style.top='0px';
    const mw=menu.offsetWidth||280,mh=menu.offsetHeight||420;
    let left=Math.min(window.innerWidth-mw-pad,Math.max(pad,r.right-mw));
    let top=r.bottom+gap;
    if(top+mh>window.innerHeight-pad)top=Math.max(pad,r.top-mh-gap);
    menu.style.left=`${Math.round(left)}px`;
    menu.style.top=`${Math.round(top)}px`;
  }
  function openRotateMenu(){
    if(!menu||!rotateBtn)return;
    menu.hidden=false;
    menu.classList.add('open');
    rotateBtn.setAttribute('aria-expanded','true');
    requestAnimationFrame(positionRotateMenu);
  }
  function closeRotateMenu(){
    if(!menu||!rotateBtn)return;
    menu.classList.remove('open');
    rotateBtn.setAttribute('aria-expanded','false');
    window.setTimeout(()=>{if(!menu.classList.contains('open'))menu.hidden=true},150);
  }
  function toggleRotateMenu(){
    if(!menu)return;
    if(menu.hidden||!menu.classList.contains('open'))openRotateMenu();else closeRotateMenu();
  }

  fsBtn?.addEventListener('click',toggleFullscreen);
  document.addEventListener('fullscreenchange',()=>{updateFullscreenButton();applyViewMode(rotateBtn?.dataset.mode||'auto',false);positionRotateMenu()});
  document.addEventListener('webkitfullscreenchange',updateFullscreenButton);
  rotateBtn?.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();toggleRotateMenu()});
  menu?.addEventListener('click',e=>{
    const btn=e.target.closest('[data-view-mode]');if(!btn)return;
    applyViewMode(btn.dataset.viewMode);closeRotateMenu();
  });
  document.addEventListener('pointerdown',e=>{if(menu&&!menu.hidden&&!menu.contains(e.target)&&e.target!==rotateBtn&&!rotateBtn?.contains(e.target))closeRotateMenu()});
  window.addEventListener('keydown',e=>{if(e.key==='Escape')closeRotateMenu()});
  window.addEventListener('resize',positionRotateMenu,{passive:true});
  window.addEventListener('scroll',positionRotateMenu,{passive:true,capture:true});

  let initial='auto';try{initial=localStorage.getItem('livenza_view_mode')||'auto'}catch(e){}
  applyViewMode(initial,false);updateFullscreenButton();
})();

// ===== Web 1.4.3 • lively Apple-style motion + safe page navigation =====
(function(){
  const reduce=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const transition=document.getElementById('pageTransition');

  // Liquid spotlight follows the pointer without changing layout.
  if(!reduce && window.matchMedia?.('(pointer:fine)').matches){
    document.querySelectorAll('.liquid-card,.module-card,.form-card,.table-card,.query-card,.stats>div').forEach(el=>{
      el.addEventListener('pointermove',ev=>{
        const r=el.getBoundingClientRect();
        el.style.setProperty('--mx',`${ev.clientX-r.left}px`);
        el.style.setProperty('--my',`${ev.clientY-r.top}px`);
      },{passive:true});
    });
  }

  // Native navigation stays native (no SPA interception), avoiding stale-page
  // state. The overlay is purely visual and cannot block the next request.
  document.addEventListener('click',ev=>{
    const a=ev.target.closest('a[href]');
    if(!a||ev.defaultPrevented||ev.button!==0||ev.metaKey||ev.ctrlKey||ev.shiftKey||ev.altKey)return;
    const href=a.getAttribute('href')||'';
    if(!href||href.startsWith('#')||href.startsWith('javascript:')||a.target==='_blank'||a.hasAttribute('download'))return;
    let u;try{u=new URL(a.href,location.href)}catch(e){return;}
    if(u.origin!==location.origin)return;
    if(transition&&!reduce){transition.classList.add('leaving');}
  },true);

  window.addEventListener('pageshow',()=>{transition?.classList.remove('leaving')});
})();
