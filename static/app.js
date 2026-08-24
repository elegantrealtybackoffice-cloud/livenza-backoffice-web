async function copyText(text){try{await navigator.clipboard.writeText(text);return true}catch(e){return false}}

function validGoogleReviewUrl(v){
  try{const u=new URL(v);const h=u.hostname.toLowerCase();return h==='g.page'||h.endsWith('.g.page')||h==='google.com'||h.endsWith('.google.com')||h==='google.co.in'||h.endsWith('.google.co.in')||h==='maps.app.goo.gl'||h.endsWith('.maps.app.goo.gl')}catch(e){return false}
}
function refreshReviewQr(root=document){
  const reviewInput=root.querySelector?.('#googleReviewUrl')||document.getElementById('googleReviewUrl');
  if(!reviewInput)return;
  const v=reviewInput.value.trim(),panel=document.getElementById('reviewQrPanel'),img=document.getElementById('reviewQrImage'),ph=document.getElementById('qrPlaceholder'),open=document.getElementById('openGoogleReview'),down=document.getElementById('downloadReviewQr');
  if(validGoogleReviewUrl(v)){
    const qr=`/reviews/qr.png?url=${encodeURIComponent(v)}`;
    panel?.classList.remove('qr-awaiting'); if(img){img.src=qr;img.style.display='block'} if(ph)ph.style.display='none';
    if(open){open.href=v;open.classList.remove('disabled-link')} if(down){down.href=qr;down.classList.remove('disabled-link')}
  }else{
    panel?.classList.add('qr-awaiting'); if(img)img.style.display='none'; if(ph)ph.style.display='block';
    if(open){open.href='#';open.classList.add('disabled-link')} if(down){down.href='#';down.classList.add('disabled-link')}
  }
}

async function applyPresetFor(preset){
  const form=preset?.closest('#agreementForm')||document.getElementById('agreementForm');
  const pattern=form?.dataset?.presetUrl;
  if(!preset||!pattern)return;
  try{
    const res=await fetch(pattern.replace('__NAME__',encodeURIComponent(preset.value)),{credentials:'same-origin'}); if(!res.ok)return;
    const payload=await res.json(),values=payload.values||payload;
    Object.entries(values).forEach(([k,v])=>{const el=form.querySelector(`[name="${CSS.escape(k)}"]`);if(el)el.value=v});
    form.querySelectorAll('[name]').forEach(el=>{el.required=false;el.closest('label')?.classList.remove('required-field')});
    if(payload.profile){
      const t=document.getElementById('presetTitle'),sub=document.getElementById('presetSubtitle'),n=document.getElementById('presetNature');
      if(t)t.textContent=payload.profile.title_en||preset.value;if(sub)sub.textContent=payload.profile.subtitle_en||'';if(n)n.textContent=payload.profile.nature_en||'';
    }
    const profile=document.getElementById('presetProfile');profile?.classList.add('pulse-once');setTimeout(()=>profile?.classList.remove('pulse-once'),700);
  }catch(e){console.warn('Preset update failed',e)}
}

function setAadhaarStatus(message,state=''){
  const el=document.getElementById('aadhaarExtractStatus');if(!el)return;el.textContent=message;el.className='aadhaar-extract-status'+(state?' '+state:'');
}
function fillAgreementField(name,value){
  if(!value)return false;const el=document.querySelector(`#agreementForm [name="${CSS.escape(name)}"]`);if(!el)return false;el.value=value;el.classList.remove('aadhaar-field-flash');void el.offsetWidth;el.classList.add('aadhaar-field-flash');setTimeout(()=>el.classList.remove('aadhaar-field-flash'),950);return true;
}

async function handleAadhaarExtract(btn){
  const file=document.getElementById('aadhaarAgreementFile')?.files?.[0];
  if(!file){setAadhaarStatus('Choose an Aadhaar JPEG, PNG or PDF first.','error');return}
  if(file.size>10*1024*1024){setAadhaarStatus('The Aadhaar file must be 10 MB or smaller.','error');return}
  const original=btn.textContent;btn.disabled=true;btn.textContent='Reading Aadhaar…';setAadhaarStatus('Reading the document securely. The original upload will not be stored.','working');
  try{
    const fd=new FormData();fd.append('aadhaar_file',file);const r=await fetch('/agreements/aadhaar-extract',{method:'POST',body:fd,credentials:'same-origin'});const d=await r.json().catch(()=>({}));
    if(!r.ok||!d.ok)throw new Error(d.error||'Could not read Aadhaar document.');
    const fields=d.fields||{};let filled=0;['tenant_name','tenant_father','tenant_dob','tenant_address','tenant_id_type','tenant_id_no'].forEach(k=>{if(fillAgreementField(k,fields[k]))filled++});
    setAadhaarStatus(`Auto-filled ${filled} tenant fields. ${d.note||''}${fields.gender?` Gender detected: ${fields.gender}.`:''} Review all values before saving.`,'success');
  }catch(err){setAadhaarStatus(err.message||'Could not extract Aadhaar details.','error')}
  finally{btn.disabled=false;btn.textContent=original}
}

function initPageFeatures(root=document){
  root.querySelectorAll?.('#agreementForm [name]').forEach(el=>{el.required=false;el.closest('label')?.classList.remove('required-field')});
  refreshReviewQr(root);
  window.dispatchEvent(new CustomEvent('livenza:page-ready',{detail:{root}}));
}
window.LivenzaInitPage=initPageFeatures;

document.addEventListener('input',e=>{if(e.target?.id==='googleReviewUrl')refreshReviewQr(document)});
document.addEventListener('change',e=>{
  if(e.target?.id==='googleReviewUrl')refreshReviewQr(document);
  if(e.target?.id==='presetSelect')applyPresetFor(e.target);
});
document.addEventListener('click',async e=>{
  const copy=e.target.closest('.copy-btn');if(copy){const ta=copy.closest('.review-card')?.querySelector('textarea');if(ta){await copyText(ta.value);copy.textContent='Copied ✓';setTimeout(()=>copy.textContent='Copy Review',1200)}return}
  const copyOpen=e.target.closest('.copy-open-btn');if(copyOpen){const ta=copyOpen.closest('.review-card')?.querySelector('textarea');if(ta)await copyText(ta.value);const u=copyOpen.dataset.url;if(u)window.open(u,'_blank','noopener');copyOpen.textContent='Copied • Google Opened';setTimeout(()=>copyOpen.textContent='Copy Review + Open Google',1600);return}
  const calc=e.target.closest('#calcEnd');if(calc){
    e.preventDefault();const start=document.getElementById('startDate')?.value||'',months=document.getElementById('termMonths')?.value||0;const fd=new FormData();fd.append('start_date',start);fd.append('months',months);fd.append('days',0);
    try{const r=await fetch('/date-calculator',{method:'POST',body:fd,credentials:'same-origin'}),d=await r.json();if(d.end_date){const end=document.getElementById('endDate');if(end)end.value=d.end_date;calc.textContent=`Ends ${d.end_date} • ${d.total_days} days`;setTimeout(()=>calc.textContent='Calculate End Date',2400)}else alert(d.error||'Could not calculate date')}catch(err){alert('Could not calculate date')}return
  }
  const aadhaar=e.target.closest('#extractAadhaarBtn');if(aadhaar){e.preventDefault();await handleAadhaarExtract(aadhaar);return}
  const disabled=e.target.closest('a.disabled-link');if(disabled){e.preventDefault();return}
});

function updateFooterClock(){const el=document.getElementById('footerClock');if(el)el.textContent=new Date().toLocaleString(undefined,{weekday:'short',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit'})}
updateFooterClock();setInterval(updateFooterClock,1000);const footerYear=document.getElementById('footerYear');if(footerYear)footerYear.textContent=new Date().getFullYear();
initPageFeatures(document);

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

  // Fullscreen navigation stays inside the same document. This preserves the
  // browser Fullscreen API while switching Operations Cloud modules.
  async function swapFullscreenPage(url,push=true){
    const main=document.getElementById('appMain');if(!main)return false;
    try{
      main.classList.add('ajax-loading');
      const res=await fetch(url,{credentials:'same-origin',headers:{'X-Livenza-Partial':'1'}});
      if(!res.ok)throw new Error(`Navigation failed (${res.status})`);
      const text=await res.text();const doc=new DOMParser().parseFromString(text,'text/html');const next=doc.getElementById('appMain');
      if(!next||doc.querySelector('.login-card')){location.assign(url);return false}
      main.className=next.className;main.innerHTML=next.innerHTML;document.title=doc.title||document.title;
      if(push)history.pushState({livenzaSpa:true},'',url);
      document.querySelectorAll('.reference-nav a.active').forEach(el=>el.classList.remove('active'));
      document.querySelectorAll('.reference-nav .nav-dropdown.active').forEach(el=>el.classList.remove('active'));
      const fetchedActive=doc.querySelector('.reference-nav a.active');
      if(fetchedActive){const h=fetchedActive.getAttribute('href');document.querySelectorAll('.reference-nav a').forEach(a=>{if(a.getAttribute('href')===h)a.classList.add('active')})}
      if(doc.querySelector('.reference-nav .operations-dropdown.active'))document.querySelector('.reference-nav .operations-dropdown')?.classList.add('active');
      document.querySelectorAll('.reference-header details[open]').forEach(d=>d.open=false);
      window.LivenzaInitPage?.(main);window.dispatchEvent(new CustomEvent('livenza:content-swapped',{detail:{root:main,url}}));
      main.classList.remove('ajax-loading');window.scrollTo({top:0,left:0,behavior:reduce?'auto':'smooth'});return true;
    }catch(err){console.warn('Fullscreen in-place navigation failed',err);main.classList.remove('ajax-loading');return false}
  }

  document.addEventListener('click',async ev=>{
    const a=ev.target.closest('a[data-app-nav]');
    if(!a||ev.defaultPrevented||ev.button!==0||ev.metaKey||ev.ctrlKey||ev.shiftKey||ev.altKey)return;
    let u;try{u=new URL(a.href,location.href)}catch(e){return}if(u.origin!==location.origin)return;
    if(window.LivenzaDisplay?.isFullscreen?.()){
      ev.preventDefault();window.LivenzaDisplay.closeViewMenu?.();
      if(transition&&!reduce){transition.classList.add('leaving');setTimeout(()=>transition.classList.remove('leaving'),280)}
      const ok=await swapFullscreenPage(u.href,true);if(!ok)location.assign(u.href);
    }
  },true);
  window.addEventListener('popstate',async()=>{
    if(window.LivenzaDisplay?.isFullscreen?.())await swapFullscreenPage(location.href,false);else location.reload();
  });
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

// ===== Web 1.4.7 • dynamic page polish, Query Sheet, assistant & easter egg =====
(()=>{
  const reduce=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

  function animateDynamicRoot(root=document){
    if(reduce)return;
    const items=root.querySelectorAll?.('.module-card,.stats>div,.city-card,.form-card,.table-card,.query-card,.review-card,.screen-card,.media-card,.agreement-section,.sheet-toolbar,.query-sheet-wrap')||[];
    if('IntersectionObserver' in window){
      const io=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('reveal-in');io.unobserve(entry.target)}}),{threshold:.06,rootMargin:'0px 0px -20px 0px'});
      items.forEach((el,i)=>{el.classList.add('reveal-ready');el.style.setProperty('--reveal-delay',`${Math.min(i%7,6)*28}ms`);io.observe(el)});
    }
    root.querySelectorAll?.('.liquid-card,.module-card,.form-card,.table-card,.query-card,.stats>div,.agreement-section').forEach(el=>{
      if(el.dataset.liquidBound)return;el.dataset.liquidBound='1';
      el.addEventListener('pointermove',ev=>{const r=el.getBoundingClientRect();el.style.setProperty('--mx',`${ev.clientX-r.left}px`);el.style.setProperty('--my',`${ev.clientY-r.top}px`)},{passive:true});
    });
  }
  animateDynamicRoot(document);
  window.addEventListener('livenza:content-swapped',e=>animateDynamicRoot(e.detail?.root||document));

  // Click/touch ripple for a more tactile but still professional feel.
  document.addEventListener('pointerdown',e=>{
    const target=e.target.closest('button,.btn,.module-card,.nav-dropdown-menu>a,.assistant-launcher');if(!target||reduce)return;
    const r=target.getBoundingClientRect(),dot=document.createElement('i');dot.className='touch-ripple';dot.style.left=`${e.clientX-r.left}px`;dot.style.top=`${e.clientY-r.top}px`;target.appendChild(dot);setTimeout(()=>dot.remove(),650);
  },{passive:true});

  // Footer-adjacent feature assistant.
  const launcher=document.getElementById('assistantLauncher'),panel=document.getElementById('assistantPanel'),close=document.getElementById('assistantClose'),form=document.getElementById('assistantForm'),input=document.getElementById('assistantInput'),messages=document.getElementById('assistantMessages');
  function setAssistant(open){if(!panel||!launcher)return;panel.hidden=!open;launcher.setAttribute('aria-expanded',String(open));panel.classList.toggle('open',open);if(open)setTimeout(()=>input?.focus(),60)}
  function addMessage(text,who='bot'){
    if(!messages)return;const div=document.createElement('div');div.className=`assistant-message ${who}`;div.textContent=text;messages.appendChild(div);messages.scrollTop=messages.scrollHeight;
  }
  async function askAssistant(text){
    text=(text||'').trim();if(!text)return;setAssistant(true);addMessage(text,'user');if(input)input.value='';const thinking=document.createElement('div');thinking.className='assistant-message bot thinking';thinking.textContent='Thinking…';messages?.appendChild(thinking);messages.scrollTop=messages.scrollHeight;
    try{const r=await fetch('/api/help',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',body:JSON.stringify({message:text})});const d=await r.json();thinking.remove();addMessage(d.answer||d.error||'I could not answer that right now.','bot')}catch(e){thinking.remove();addMessage('I could not reach the help service. Please try again.','bot')}
  }
  launcher?.addEventListener('click',()=>setAssistant(panel?.hidden));close?.addEventListener('click',()=>setAssistant(false));form?.addEventListener('submit',e=>{e.preventDefault();askAssistant(input?.value)});
  document.addEventListener('click',e=>{const b=e.target.closest('[data-help-prompt]');if(b)askAssistant(b.dataset.helpPrompt)});

  // Transparent Livenza easter egg with a gentle star burst.
  const egg=document.getElementById('livenzaEasterEgg'),toast=document.getElementById('easterToast');
  egg?.addEventListener('click',()=>{
    egg.classList.add('awake');setTimeout(()=>egg.classList.remove('awake'),1100);if(toast){toast.hidden=false;toast.classList.add('show');setTimeout(()=>{toast.classList.remove('show');setTimeout(()=>toast.hidden=true,220)},1800)}
    if(!reduce){for(let i=0;i<12;i++){const star=document.createElement('i');star.className='easter-star';star.textContent=i%3===0?'✦':'·';star.style.setProperty('--angle',`${i*30}deg`);star.style.setProperty('--distance',`${48+Math.random()*42}px`);egg.appendChild(star);setTimeout(()=>star.remove(),900)}}
  });

  // Spreadsheet-like Query Manager.
  const rowSaveTimers=new WeakMap();
  function sheetStatus(text,state=''){const el=document.getElementById('sheetSaveStatus');if(!el)return;el.textContent=text;el.dataset.state=state}
  function rowPayload(row){const out={};row.querySelectorAll('[data-field]').forEach(el=>{out[el.dataset.field]=el.matches('select,input,textarea')?el.value:el.textContent.trim()});return out}
  async function saveSheetRow(row){
    if(!row)return;const id=row.dataset.queryId;if(!id)return;row.classList.add('saving');sheetStatus(`Saving #${id}…`,'saving');
    try{const r=await fetch(`/api/queries/${id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},credentials:'same-origin',body:JSON.stringify(rowPayload(row))});const d=await r.json();if(!r.ok||!d.ok)throw new Error(d.error||'Save failed');row.classList.remove('save-error');row.classList.add('saved');sheetStatus(`Saved #${id}`,'saved');setTimeout(()=>row.classList.remove('saved'),700)}catch(err){row.classList.add('save-error');sheetStatus(`Could not save #${id}`,'error')}finally{row.classList.remove('saving')}
  }
  function queueRowSave(row,delay=280){clearTimeout(rowSaveTimers.get(row));rowSaveTimers.set(row,setTimeout(()=>saveSheetRow(row),delay))}
  document.addEventListener('focusout',e=>{const cell=e.target.closest('#querySheetTable [data-field][contenteditable="true"]');if(cell)queueRowSave(cell.closest('tr'))});
  document.addEventListener('change',e=>{const field=e.target.closest('#querySheetTable [data-field]');if(field)queueRowSave(field.closest('tr'),80)});
  document.addEventListener('keydown',e=>{const cell=e.target.closest?.('#querySheetTable [contenteditable="true"]');if(cell&&e.key==='Enter'&&!e.shiftKey){e.preventDefault();cell.blur()}});
  document.addEventListener('click',async e=>{
    const save=e.target.closest('.sheet-save-row');if(save){await saveSheetRow(save.closest('tr'));return}
    if(e.target.closest('#addQuerySheetRow')){
      const btn=e.target.closest('#addQuerySheetRow');btn.disabled=true;sheetStatus('Creating row…','saving');
      try{const r=await fetch('/api/queries',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',body:JSON.stringify({source:'Manual',status:'Live',heat:'Warm',score:50})});const d=await r.json();if(!r.ok||!d.ok)throw new Error('Create failed');
        const body=document.getElementById('querySheetBody');if(body){const tr=document.createElement('tr');tr.dataset.queryId=d.id;tr.className='new-sheet-row';tr.innerHTML=`<td class="sheet-row-number">NEW</td><td><select data-field="source"><option>Manual</option><option>Meta</option><option>Facebook</option><option>Google</option><option>Airbnb</option><option>Booking.com</option><option>MakeMyTrip</option><option>Goibibo</option><option>Direct</option><option>Other</option></select></td><td contenteditable="true" data-field="customer_name"></td><td contenteditable="true" data-field="mobile"></td><td contenteditable="true" data-field="whatsapp"></td><td contenteditable="true" data-field="email"></td><td contenteditable="true" data-field="city"></td><td contenteditable="true" data-field="property_name"></td><td contenteditable="true" data-field="budget"></td><td contenteditable="true" data-field="move_in_date"></td><td contenteditable="true" data-field="stay_type"></td><td><select data-field="status"><option>Live</option><option>New</option><option>Follow-up</option><option>Won</option><option>Lost</option><option>Closed</option></select></td><td><select data-field="heat"><option>Warm</option><option>Hot</option><option>Cold</option></select></td><td contenteditable="true" data-field="score">50</td><td contenteditable="true" data-field="next_follow_up"></td><td contenteditable="true" data-field="query_text" class="sheet-wide-cell"></td><td contenteditable="true" data-field="notes" class="sheet-wide-cell"></td><td class="sheet-action-cell"><button type="button" class="sheet-save-row">✓</button></td>`;body.prepend(tr);tr.querySelector('[data-field="customer_name"]')?.focus();sheetStatus(`Row #${d.id} ready`,'saved')}}catch(err){sheetStatus('Could not create row','error')}finally{btn.disabled=false}
    }
  });
})();

// ===== Web 1.4.8 • food partner portal polish =====
(()=>{
  // Partner browser tabs are ordinary same-origin navigation; if the user is
  // fullscreen, the existing in-place navigator keeps fullscreen active.
  document.addEventListener('livenza:content-swapped',e=>{
    const root=e.detail?.root||document;
    root.querySelectorAll?.('.partner-status-pill,.integration-card,.portal-tab').forEach((el,i)=>{
      el.style.setProperty('--live-delay',`${(i%6)*70}ms`);
    });
  });
})();
