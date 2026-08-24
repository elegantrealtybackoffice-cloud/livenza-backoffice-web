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

// ===== Web 1.4.6 • unified View menu + stable fullscreen/orientation =====
(function(){
  const viewport=document.getElementById('appViewport');
  const viewBtn=document.getElementById('viewMenuToggle');
  const fsBtn=document.getElementById('fullscreenToggle');
  const menu=document.getElementById('viewMenu');
  if(!viewport) return;

  const modes=['auto','portrait','landscape','90','180','270'];
  const viewClasses=['view-auto','view-portrait','view-landscape','view-rot-90','view-rot-180','view-rot-270'];
  let currentMode='auto';

  function fullscreenElement(){return document.fullscreenElement||document.webkitFullscreenElement||null}
  function isFullscreen(){return !!fullscreenElement()}

  function updateFullscreenButton(){
    if(!fsBtn)return;
    const active=isFullscreen();
    const label=fsBtn.querySelector('.tool-label');
    if(label)label.textContent=active?'Exit Full Screen':'Full Screen';
    fsBtn.classList.toggle('active',active);
    fsBtn.setAttribute('aria-pressed',String(active));
    document.documentElement.classList.toggle('fullscreen-stable',active);
    document.body.classList.toggle('fullscreen-stable',active);
  }

  function clearViewClasses(){
    viewClasses.forEach(c=>viewport.classList.remove(c));
    document.documentElement.classList.remove('site-rotation-active');
  }
  async function unlockOrientation(){try{screen.orientation?.unlock?.()}catch(e){}}

  function updateOrientationUi(mode){
    document.querySelectorAll('#viewMenu [data-view-mode]').forEach(b=>{
      const selected=b.dataset.viewMode===mode;
      b.classList.toggle('selected',selected);
      b.setAttribute('aria-current',selected?'true':'false');
    });
  }

  async function tryNativeOrientation(mode){
    if(!screen.orientation?.lock||!isFullscreen())return false;
    try{
      if(mode==='portrait'){await screen.orientation.lock('portrait-primary');return true}
      if(mode==='landscape'){await screen.orientation.lock('landscape-primary');return true}
    }catch(e){}
    return false;
  }

  async function applyViewMode(mode,save=true){
    if(!modes.includes(mode))mode='auto';
    currentMode=mode;

    // Fullscreen remains a normal scrollable document. Native orientation is
    // attempted only for portrait/landscape; custom angles exit fullscreen.
    if(isFullscreen()){
      clearViewClasses();
      viewport.classList.add(mode==='portrait'?'view-portrait':'view-auto');
      if(mode==='auto')await unlockOrientation();
      else if(mode==='portrait'||mode==='landscape')await tryNativeOrientation(mode);
      updateOrientationUi(mode);
      if(save){try{localStorage.setItem('livenza_view_mode',mode)}catch(e){}}
      return;
    }

    await unlockOrientation();
    clearViewClasses();
    const cls=mode==='90'?'view-rot-90':mode==='180'?'view-rot-180':mode==='270'?'view-rot-270':`view-${mode}`;
    viewport.classList.add(cls);
    if(['90','180','270'].includes(mode))document.documentElement.classList.add('site-rotation-active');
    updateOrientationUi(mode);
    if(save){try{localStorage.setItem('livenza_view_mode',mode)}catch(e){}}
  }

  async function toggleFullscreen(){
    try{
      closeViewMenu();
      if(isFullscreen()){
        if(document.exitFullscreen)await document.exitFullscreen();
        else if(document.webkitExitFullscreen)document.webkitExitFullscreen();
      }else{
        // Always enter fullscreen from a clean non-transformed state.
        clearViewClasses();viewport.classList.add('view-auto');
        document.documentElement.classList.add('fullscreen-requesting');
        const target=document.body;
        if(target.requestFullscreen)await target.requestFullscreen({navigationUI:'hide'});
        else if(target.webkitRequestFullscreen)target.webkitRequestFullscreen();
        else alert('Fullscreen is not supported by this browser.');
      }
    }catch(err){console.warn('Fullscreen request was blocked:',err)}
    finally{
      document.documentElement.classList.remove('fullscreen-requesting');
      updateFullscreenButton();
    }
  }

  function positionViewMenu(){
    if(!menu||menu.hidden||!viewBtn)return;
    const r=viewBtn.getBoundingClientRect(),gap=10,pad=10;
    menu.style.left='0px';menu.style.top='0px';
    const mw=menu.offsetWidth||320,mh=menu.offsetHeight||520;
    const left=Math.min(window.innerWidth-mw-pad,Math.max(pad,r.right-mw));
    let top=r.bottom+gap;
    if(top+mh>window.innerHeight-pad)top=Math.max(pad,r.top-mh-gap);
    menu.style.left=`${Math.round(left)}px`;menu.style.top=`${Math.round(top)}px`;
  }
  function openViewMenu(){
    if(!menu||!viewBtn)return;
    menu.hidden=false;
    requestAnimationFrame(()=>{menu.classList.add('open');positionViewMenu()});
    viewBtn.setAttribute('aria-expanded','true');
  }
  function closeViewMenu(){
    if(!menu||!viewBtn)return;
    menu.classList.remove('open');viewBtn.setAttribute('aria-expanded','false');
    window.setTimeout(()=>{if(!menu.classList.contains('open'))menu.hidden=true},150);
  }
  function toggleViewMenu(){if(!menu)return;(menu.hidden||!menu.classList.contains('open'))?openViewMenu():closeViewMenu()}

  fsBtn?.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();toggleFullscreen()});
  viewBtn?.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();toggleViewMenu()});
  menu?.addEventListener('click',async e=>{
    const btn=e.target.closest('[data-view-mode]');if(!btn)return;
    const mode=btn.dataset.viewMode;closeViewMenu();
    if(isFullscreen()&&['90','180','270'].includes(mode)){
      try{
        if(document.exitFullscreen)await document.exitFullscreen();
        else if(document.webkitExitFullscreen)document.webkitExitFullscreen();
      }catch(err){}
      window.setTimeout(()=>applyViewMode(mode),80);return;
    }
    await applyViewMode(mode);
  });
  document.addEventListener('pointerdown',e=>{if(menu&&!menu.hidden&&!menu.contains(e.target)&&!viewBtn?.contains(e.target))closeViewMenu()});
  window.addEventListener('keydown',e=>{if(e.key==='Escape')closeViewMenu()});
  window.addEventListener('resize',positionViewMenu,{passive:true});
  window.addEventListener('scroll',positionViewMenu,{passive:true,capture:true});

  async function onFullscreenChange(){
    updateFullscreenButton();
    await applyViewMode(currentMode,false);
    positionViewMenu();
  }
  document.addEventListener('fullscreenchange',onFullscreenChange);
  document.addEventListener('webkitfullscreenchange',onFullscreenChange);

  let initial='auto';try{initial=localStorage.getItem('livenza_view_mode')||'auto'}catch(e){}
  currentMode=modes.includes(initial)?initial:'auto';
  applyViewMode(currentMode,false);updateFullscreenButton();

  window.LivenzaDisplay={
    isFullscreen,
    closeViewMenu,
    closeRotateMenu:closeViewMenu,
    resetForNavigation:()=>{clearViewClasses();viewport.classList.add('view-auto')}
  };
})();

// ===== Web 1.4.6 • professional motion + fullscreen-safe navigation =====
(function(){
  const reduce=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const transition=document.getElementById('pageTransition');
  const motionLayer=document.getElementById('liveMotionLayer');

  // Lightweight live particles: decorative only, no canvas and no layout work.
  if(motionLayer&&!reduce){
    const count=window.innerWidth<700?7:14;
    for(let i=0;i<count;i++){
      const p=document.createElement('i');
      p.className='live-particle';
      p.style.setProperty('--x',`${Math.round(Math.random()*100)}vw`);
      p.style.setProperty('--size',`${4+Math.round(Math.random()*8)}px`);
      p.style.setProperty('--delay',`${(-Math.random()*16).toFixed(2)}s`);
      p.style.setProperty('--duration',`${12+Math.round(Math.random()*12)}s`);
      p.style.setProperty('--drift',`${-55+Math.round(Math.random()*110)}px`);
      motionLayer.appendChild(p);
    }
  }

  // Liquid spotlight follows the pointer without changing layout.
  if(!reduce && window.matchMedia?.('(pointer:fine)').matches){
    document.querySelectorAll('.liquid-card,.module-card,.form-card,.table-card,.query-card,.stats>div').forEach(el=>{
      el.addEventListener('pointermove',ev=>{
        const r=el.getBoundingClientRect();
        el.style.setProperty('--mx',`${ev.clientX-r.left}px`);
        el.style.setProperty('--my',`${ev.clientY-r.top}px`);
      },{passive:true});
    });
    document.addEventListener('pointermove',ev=>{
      document.documentElement.style.setProperty('--pointer-x',`${ev.clientX}px`);
      document.documentElement.style.setProperty('--pointer-y',`${ev.clientY}px`);
    },{passive:true});
  }

  // Internal navigation remains native. In fullscreen we first leave the
  // Fullscreen API, then navigate once. This prevents Chromium/Edge from
  // leaving the old fullscreen document half-active while the next page loads.
  document.addEventListener('click',async ev=>{
    const a=ev.target.closest('a[href]');
    if(!a||ev.defaultPrevented||ev.button!==0||ev.metaKey||ev.ctrlKey||ev.shiftKey||ev.altKey)return;
    const href=a.getAttribute('href')||'';
    if(!href||href.startsWith('#')||href.startsWith('javascript:')||a.target==='_blank'||a.hasAttribute('download'))return;
    let u;try{u=new URL(a.href,location.href)}catch(e){return;}
    if(u.origin!==location.origin)return;

    if(transition&&!reduce)transition.classList.add('leaving');
    if(window.LivenzaDisplay?.isFullscreen?.()){
      ev.preventDefault();
      window.LivenzaDisplay.closeViewMenu?.();
      window.LivenzaDisplay.resetForNavigation?.();
      try{
        if(document.exitFullscreen)await document.exitFullscreen();
        else if(document.webkitExitFullscreen)document.webkitExitFullscreen();
      }catch(e){}
      // Let fullscreen teardown finish before replacing the document.
      window.setTimeout(()=>location.assign(u.href),45);
    }
  },true);

  window.addEventListener('pageshow',()=>{
    transition?.classList.remove('leaving');
    document.documentElement.classList.remove('fullscreen-requesting');
    document.documentElement.classList.remove('fullscreen-stable');
    document.body.classList.remove('fullscreen-stable');
  });

  // Reveal content as it enters the viewport. This is decorative and never
  // blocks clicks, scrolling or form interaction.
  if(!reduce && 'IntersectionObserver' in window){
    const revealItems=document.querySelectorAll('.module-card,.stats>div,.city-card,.form-card,.table-card,.query-card,.review-card,.screen-card,.media-card');
    const io=new IntersectionObserver(entries=>{
      entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('reveal-in');io.unobserve(entry.target)}});
    },{threshold:.08,rootMargin:'0px 0px -30px 0px'});
    revealItems.forEach((el,i)=>{el.classList.add('reveal-ready');el.style.setProperty('--reveal-delay',`${Math.min(i%8,7)*32}ms`);io.observe(el)});
  }
})();

// ===== Web 1.4.6 • clean reference header dropdown discipline =====
(()=>{
  const header=document.querySelector('.reference-header');
  if(!header)return;
  const dropdowns=[...header.querySelectorAll('details.nav-dropdown')];
  dropdowns.forEach(d=>d.addEventListener('toggle',()=>{
    if(!d.open)return;
    dropdowns.forEach(other=>{if(other!==d)other.open=false});
  }));
  document.addEventListener('pointerdown',e=>{
    dropdowns.forEach(d=>{if(d.open&&!d.contains(e.target))d.open=false});
  });
  document.addEventListener('keydown',e=>{if(e.key==='Escape')dropdowns.forEach(d=>d.open=false)});
})();
