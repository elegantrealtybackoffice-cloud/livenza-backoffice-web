const livenzaDeviceIsLimited=()=>window.matchMedia?.('(max-width:820px)').matches||Number(navigator.deviceMemory||8)<=4||Number(navigator.hardwareConcurrency||8)<=4||Boolean(navigator.connection?.saveData);
const livenzaMobilePerformance=()=>document.documentElement.classList.contains('mobile-performance');
document.documentElement.classList.toggle('mobile-performance',livenzaDeviceIsLimited());
document.addEventListener('visibilitychange',()=>document.documentElement.classList.toggle('page-paused',document.hidden));

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
  const controller=new AbortController(),timeout=window.setTimeout(()=>controller.abort(),100000);
  try{
    const fd=new FormData();fd.append('aadhaar_file',file);const r=await fetch('/agreements/aadhaar-extract',{method:'POST',body:fd,credentials:'same-origin',signal:controller.signal});
    const contentType=(r.headers.get('content-type')||'').toLowerCase();
    if(!contentType.includes('application/json'))throw new Error(r.redirected||r.url.includes('/login')?'Your secure session expired. Sign in again, then retry the Aadhaar upload.':`The server returned an unreadable response (${r.status}). Redeploy Web 1.5.13 and retry.`);
    const d=await r.json();
    if(!r.ok||!d.ok)throw new Error([d.error,d.reader_status].filter(Boolean).join(' Reader status: '));
    const fields=d.fields||{};let filled=0;['tenant_name','tenant_father','tenant_dob','tenant_address','tenant_id_type','tenant_id_no'].forEach(k=>{if(fillAgreementField(k,fields[k]))filled++});
    setAadhaarStatus(`Auto-filled ${filled} tenant fields. ${d.note||''}${fields.gender?` Gender detected: ${fields.gender}.`:''} Review all values before saving.`,'success');
  }catch(err){setAadhaarStatus(err.name==='AbortError'?'Aadhaar reading timed out after 100 seconds. Try a smaller, clearer image or a two-page PDF.':(err.message||'Automatic Aadhaar reading could not detect clear details. Try a brighter, straight photo or enter the fields manually.'),'error')}
  finally{window.clearTimeout(timeout);btn.disabled=false;btn.textContent=original}
}

const videoBytes=value=>{const n=Number(value||0);if(n<1048576)return `${(n/1024).toFixed(0)} KB`;return `${(n/1048576).toFixed(n>=104857600?0:1)} MB`};
function tusMetadata(values){
  const encode=value=>btoa(unescape(encodeURIComponent(String(value||''))));
  return Object.entries(values).map(([key,value])=>`${key} ${encode(value)}`).join(',');
}
async function sameOriginJson(url,body,method='POST'){
  const response=await fetch(url,{method,credentials:'same-origin',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify(body||{})});
  const type=(response.headers.get('content-type')||'').toLowerCase();
  if(!type.includes('application/json'))throw new Error(response.redirected?'Your session expired. Sign in again, then retry the upload.':`Unexpected server response (${response.status}).`);
  const data=await response.json();if(!response.ok||data.ok===false)throw new Error(data.error||`Request failed (${response.status})`);return data;
}
async function recoverTusOffset(uploadUrl,signature){
  const response=await fetch(uploadUrl,{method:'HEAD',headers:{'Tus-Resumable':'1.0.0','x-signature':signature}});
  if(!response.ok)throw new Error(`Upload recovery failed (${response.status}).`);
  return Number(response.headers.get('Upload-Offset')||0);
}
async function sendTusFile(file,upload,update){
  const created=await fetch(upload.endpoint,{method:'POST',headers:{
    'Tus-Resumable':'1.0.0','Upload-Length':String(file.size),'Upload-Metadata':tusMetadata({
      bucketName:upload.bucket,objectName:upload.object_name,contentType:upload.content_type,cacheControl:'3600',
    }),'x-signature':upload.signature,'x-upsert':'false',
  }});
  if(!created.ok)throw new Error(`Storage could not open the resumable upload (${created.status}). Check the bucket file-size limit.`);
  const location=created.headers.get('Location');if(!location)throw new Error('Storage did not return an upload location.');
  const uploadUrl=new URL(location,upload.endpoint).toString();let offset=Number(created.headers.get('Upload-Offset')||0),failures=0;
  while(offset<file.size){
    const end=Math.min(file.size,offset+Number(upload.chunk_size||6291456)),chunk=file.slice(offset,end);
    try{
      const response=await fetch(uploadUrl,{method:'PATCH',headers:{'Tus-Resumable':'1.0.0','Upload-Offset':String(offset),'Content-Type':'application/offset+octet-stream','x-signature':upload.signature},body:chunk});
      if(!response.ok)throw new Error(`Storage upload stopped (${response.status}).`);
      const next=Number(response.headers.get('Upload-Offset')||end);if(next<=offset)throw new Error('Storage did not advance the upload.');
      offset=next;failures=0;update(offset,file.size);
    }catch(error){
      failures++;if(failures>3)throw error;
      await new Promise(resolve=>setTimeout(resolve,600*failures));offset=await recoverTusOffset(uploadUrl,upload.signature);update(offset,file.size,true);
    }
  }
}
function initVideoWallUploader(root=document){
  const form=root.querySelector?.('#videoWallUploadForm');if(!form||form.dataset.uploadReady)return;form.dataset.uploadReady='1';
  const input=form.querySelector('#videoWallMediaFile'),button=form.querySelector('#videoWallUploadButton'),panel=form.querySelector('#videoUploadProgress'),bar=form.querySelector('#videoUploadBar'),percent=form.querySelector('#videoUploadPercent'),status=form.querySelector('#videoUploadStatus'),bytes=form.querySelector('#videoUploadBytes');
  form.addEventListener('submit',async event=>{
    const file=input?.files?.[0],external=form.querySelector('[name="external_url"]')?.value?.trim();if(!file||external)return;
    event.preventDefault();if(form.dataset.uploading==='1')return;form.dataset.uploading='1';button.disabled=true;input.disabled=true;panel.hidden=false;panel.classList.remove('error');bar.value=0;percent.textContent='0%';status.textContent='Reserving secure media storage…';bytes.textContent=`0 MB of ${videoBytes(file.size)}`;
    const update=(sent,total,recovered=false)=>{const value=Math.max(0,Math.min(100,Math.round(sent/total*100)));bar.value=value;percent.textContent=`${value}%`;status.textContent=recovered?'Connection restored • continuing upload…':'Uploading directly to media storage…';bytes.textContent=`${videoBytes(sent)} of ${videoBytes(total)}`};
    try{
      const title=form.querySelector('[name="title"]')?.value?.trim()||file.name;
      const started=await sameOriginJson(form.dataset.resumableStart,{filename:file.name,content_type:file.type,size:file.size,title});
      await sendTusFile(file,started.upload,update);status.textContent='Verifying media and adding it to Livenza…';percent.textContent='100%';bar.value=100;
      await sameOriginJson(form.dataset.resumableFinish,{reservation:started.upload.reservation});status.textContent='Upload complete • opening the media library…';bytes.textContent=`${videoBytes(file.size)} verified and ready for TV playback.`;
      window.setTimeout(()=>location.assign('/video-wall#available-media'),650);
    }catch(error){status.textContent=error.message||'Upload failed.';panel.classList.add('error');button.disabled=false;input.disabled=false;form.dataset.uploading='0'}
  });
}

function initAgreementWorkspace(root=document){
  const form=root.querySelector?.('#agreementForm');if(!form||form.dataset.workspaceReady)return;form.dataset.workspaceReady='1';
  const panels=[...form.querySelectorAll('[data-wizard-panel]')],steps=[...form.querySelectorAll('[data-wizard-step]')],autosave=document.getElementById('agreementAutosaveStatus');let current=0,saveTimer=0;
  const showStep=(index,scroll=true)=>{current=Math.max(0,Math.min(panels.length-1,Number(index)||0));panels.forEach(panel=>{const active=Number(panel.dataset.wizardPanel)===current;panel.hidden=!active;panel.classList.toggle('active',active)});steps.forEach(step=>{const value=Number(step.dataset.wizardStep),active=value===current;step.classList.toggle('active',active);step.classList.toggle('complete',value<current);step.setAttribute('aria-current',active?'step':'false')});if(scroll)document.querySelector('.agreement-workspace-status')?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'})};
  steps.forEach(step=>step.addEventListener('click',()=>showStep(step.dataset.wizardStep)));
  form.querySelectorAll('[data-wizard-next]').forEach(button=>button.addEventListener('click',()=>showStep(button.dataset.wizardNext)));
  form.querySelectorAll('[data-wizard-back]').forEach(button=>button.addEventListener('click',()=>showStep(button.dataset.wizardBack)));

  form.querySelectorAll('[data-preset-card]').forEach(card=>card.addEventListener('click',()=>{const select=form.querySelector('#presetSelect');if(!select)return;select.value=card.dataset.presetCard;select.dispatchEvent(new Event('change',{bubbles:true}));form.querySelectorAll('[data-preset-card]').forEach(item=>item.classList.toggle('selected',item===card))}));
  form.querySelector('#presetSelect')?.addEventListener('change',event=>form.querySelectorAll('[data-preset-card]').forEach(card=>card.classList.toggle('selected',card.dataset.presetCard===event.target.value)));

  const key=form.dataset.draftKey,serialize=()=>{const values={};form.querySelectorAll('input[name],select[name],textarea[name]').forEach(control=>{if(control.type==='file'||control.type==='password'||control.type==='submit')return;if(control.type==='checkbox'||control.type==='radio'){values[control.name]=control.checked}else if(control.multiple)values[control.name]=[...control.selectedOptions].map(option=>option.value);else values[control.name]=control.value});return values};
  const setSaved=(text,state='saved')=>{if(!autosave)return;autosave.className=`agreement-autosave ${state}`;autosave.querySelector('span').textContent=text};
  const persist=()=>{try{localStorage.setItem(key,JSON.stringify({saved_at:Date.now(),values:serialize()}));setSaved(`Saved locally · ${new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}`)}catch(error){setSaved('Local auto-save unavailable','error')}};
  const queueSave=()=>{setSaved('Saving locally…','saving');clearTimeout(saveTimer);saveTimer=setTimeout(persist,550)};
  form.addEventListener('input',queueSave);form.addEventListener('change',queueSave);
  if(form.dataset.existing!=='1'){try{const draft=JSON.parse(localStorage.getItem(key)||'null');if(draft?.values){Object.entries(draft.values).forEach(([name,value])=>{const controls=form.querySelectorAll(`[name="${CSS.escape(name)}"]`);controls.forEach(control=>{if(control.type==='checkbox'||control.type==='radio')control.checked=Boolean(value);else if(control.multiple&&Array.isArray(value))[...control.options].forEach(option=>option.selected=value.includes(option.value));else control.value=value})});setSaved('Restored your locally saved draft')}}catch(error){}}
  form.addEventListener('submit',()=>{clearTimeout(saveTimer);try{localStorage.removeItem(key)}catch(error){};setSaved('Saving agreement…','saving')});

  let profileData={landlord:[],tenant:[]};try{profileData=JSON.parse(document.getElementById('partyProfilesData')?.textContent||'{}')}catch(error){}
  const profileStatus=document.getElementById('partyProfileStatus'),profileFields={landlord:['landlord_name','landlord_father','landlord_entity','landlord_address','landlord_id_type','landlord_id_no','landlord_pan','landlord_mobile','landlord_email','authorized_signatory'],tenant:['tenant_name','tenant_father','tenant_dob','tenant_address','tenant_id_type','tenant_id_no','tenant_mobile','tenant_whatsapp','tenant_email','emergency_contact1','emergency_contact2']};
  const say=(message,error=false)=>{if(profileStatus){profileStatus.textContent=message;profileStatus.classList.toggle('danger',error)}};
  const selectedProfile=type=>{const id=Number(form.querySelector(`[data-party-profile-select="${type}"]`)?.value||0);return (profileData[type]||[]).find(item=>Number(item.id)===id)};
  form.querySelectorAll('[data-party-profile-select]').forEach(select=>select.addEventListener('change',()=>{const type=select.dataset.partyProfileSelect,profile=selectedProfile(type),name=form.querySelector(`[data-party-profile-name="${type}"]`);if(name&&profile)name.value=profile.name}));
  form.querySelectorAll('[data-party-profile-apply]').forEach(button=>button.addEventListener('click',()=>{const type=button.dataset.partyProfileApply,profile=selectedProfile(type);if(!profile){say(`Choose a saved ${type} profile first.`,true);return}let count=0;Object.entries(profile.fields||{}).forEach(([name,value])=>{const control=form.querySelector(`[name="${CSS.escape(name)}"]`);if(control){control.value=value;control.dispatchEvent(new Event('input',{bubbles:true}));count++}});say(`Applied ${profile.name} · ${count} fields filled.`)}));
  form.querySelectorAll('[data-party-profile-save]').forEach(button=>button.addEventListener('click',async()=>{const type=button.dataset.partyProfileSave,nameInput=form.querySelector(`[data-party-profile-name="${type}"]`),name=nameInput?.value?.trim()||'';if(!name){say(`Enter a name for the ${type} profile first.`,true);nameInput?.focus();return}const fields={};(profileFields[type]||[]).forEach(field=>{const value=form.querySelector(`[name="${CSS.escape(field)}"]`)?.value?.trim();if(value)fields[field]=value});button.disabled=true;say(`Encrypting and saving ${type} profile…`);try{const data=await sameOriginJson('/api/agreement-party-profiles',{profile_type:type,name,fields}),list=profileData[type]||(profileData[type]=[]),index=list.findIndex(item=>Number(item.id)===Number(data.profile.id));if(index>=0)list[index]=data.profile;else list.push(data.profile);const select=form.querySelector(`[data-party-profile-select="${type}"]`);let option=[...select.options].find(item=>Number(item.value)===Number(data.profile.id));if(!option){option=document.createElement('option');option.value=data.profile.id;select.appendChild(option)}option.textContent=data.profile.name;select.value=String(data.profile.id);say(data.message||`${type} profile saved.`)}catch(error){say(error.message||'Could not save profile.',true)}finally{button.disabled=false}}));
  form.querySelectorAll('[data-party-profile-delete]').forEach(button=>button.addEventListener('click',async()=>{const type=button.dataset.partyProfileDelete,profile=selectedProfile(type);if(!profile){say(`Choose a saved ${type} profile first.`,true);return}if(!confirm(`Delete the saved profile “${profile.name}”?`))return;try{const response=await fetch(`/api/agreement-party-profiles/${profile.id}`,{method:'DELETE',credentials:'same-origin',headers:{'Accept':'application/json'}}),data=await response.json();if(!response.ok||data.ok===false)throw new Error(data.error||'Could not delete profile.');profileData[type]=(profileData[type]||[]).filter(item=>Number(item.id)!==Number(profile.id));form.querySelector(`[data-party-profile-select="${type}"] option[value="${profile.id}"]`)?.remove();say(data.message||'Saved profile removed.')}catch(error){say(error.message||'Could not delete profile.',true)}}));
  showStep(0,false);
}

function initPageFeatures(root=document){
  root.querySelectorAll?.('#agreementForm [name]').forEach(el=>{el.required=false;el.closest('label')?.classList.remove('required-field')});
  refreshReviewQr(root);
  initVideoWallUploader(root);
  initAgreementWorkspace(root);
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

// ===== Web 1.5.11 • restored header rotation and display menu =====
(function(){
  const root=document.documentElement;
  const viewport=document.getElementById('appViewport');
  const viewBtn=document.getElementById('viewMenuToggle');
  const fsBtn=document.getElementById('fullscreenToggle');
  const menu=document.getElementById('viewMenu');
  const orientationStatus=document.getElementById('orientationStatus');
  const homeDisplayButtons=[...document.querySelectorAll('[data-home-display]')];
  if(!viewport)return;
  if(!viewBtn&&!menu){
    ['view-portrait','view-landscape','view-rot-90','view-rot-180','view-rot-270'].forEach(name=>viewport.classList.remove(name));
    viewport.classList.add('view-auto');root.classList.remove('site-rotation-active','livenza-theatre-mode');document.body.classList.remove('livenza-theatre-mode');
    try{localStorage.removeItem('livenza_view_mode')}catch(e){}
    const fullscreenElement=()=>document.fullscreenElement||document.webkitFullscreenElement||document.webkitCurrentFullScreenElement||null;
    window.LivenzaDisplay={isFullscreen:()=>Boolean(fullscreenElement()),closeViewMenu:()=>{},closeRotateMenu:()=>{},resetForNavigation:()=>{}};
    return;
  }

  const modes=['auto','portrait','landscape','90','180','270'];
  const viewClasses=['view-auto','view-portrait','view-landscape','view-rot-90','view-rot-180','view-rot-270'];
  let currentMode='auto',rotationLocked=false,pseudoFullscreen=false,nativeAttempt='',nativeAppliedMode='',metricsFrame=0,menuFrame=0;

  function nativeFullscreenElement(){return document.fullscreenElement||document.webkitFullscreenElement||document.webkitCurrentFullScreenElement||document.mozFullScreenElement||document.msFullscreenElement||null}
  function isFullscreen(){return Boolean(nativeFullscreenElement()||pseudoFullscreen||root.classList.contains('livenza-theatre-mode'))}
  function setPseudoFullscreen(active){pseudoFullscreen=active;root.classList.toggle('livenza-theatre-mode',active);document.body.classList.toggle('livenza-theatre-mode',active)}
  function syncViewportMetrics(){
    const visual=window.visualViewport,w=Math.round(visual?.width||window.innerWidth||screen.width||1280),h=Math.round(visual?.height||window.innerHeight||screen.height||720);
    const width=`${w}px`,height=`${h}px`;
    if(root.style.getPropertyValue('--livenza-screen-width')!==width)root.style.setProperty('--livenza-screen-width',width);
    if(root.style.getPropertyValue('--livenza-screen-height')!==height)root.style.setProperty('--livenza-screen-height',height);
  }
  function scheduleViewportMetrics(){if(metricsFrame)return;metricsFrame=requestAnimationFrame(()=>{metricsFrame=0;syncViewportMetrics()})}

  function updateFullscreenButton(){
    const active=isFullscreen();
    if(fsBtn){const label=fsBtn.querySelector('.tool-label');if(label)label.textContent=active?'Exit Full Screen':'Full Screen';fsBtn.classList.toggle('active',active);fsBtn.setAttribute('aria-pressed',String(active))}
    root.classList.toggle('fullscreen-stable',active);document.body.classList.toggle('fullscreen-stable',active);
  }

  function clearViewClasses(){viewClasses.forEach(c=>viewport.classList.remove(c));root.classList.remove('site-rotation-active')}
  async function unlockOrientation(){
    try{if(screen.orientation?.unlock)screen.orientation.unlock();else (screen.unlockOrientation||screen.mozUnlockOrientation||screen.msUnlockOrientation)?.call(screen)}catch(e){}
  }

  function updateOrientationUi(mode,nativeApplied=false){
    document.querySelectorAll('#viewMenu [data-view-mode]').forEach(button=>{const selected=button.dataset.viewMode===mode;button.classList.toggle('selected',selected);button.setAttribute('aria-current',selected?'true':'false')});
    homeDisplayButtons.forEach(button=>{const action=button.dataset.homeDisplay,active=action==='lock'?rotationLocked:action===mode;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));if(action==='lock'){button.title=rotationLocked?'Unlock website rotation':'Lock website rotation';const label=button.querySelector('small');if(label)label.textContent=rotationLocked?'Locked':'Lock'}});
    if(orientationStatus){const labels={auto:'Automatic display',portrait:'Portrait view',landscape:'Landscape view','90':'90° clockwise','180':'180° rotation','270':'270° clockwise'};orientationStatus.textContent=`${labels[mode]||'Automatic display'} active${nativeApplied?' · screen orientation':' · browser-safe mode'}${rotationLocked?' · rotation locked':''}.`}
  }

  async function tryNativeOrientation(mode){
    if(!nativeFullscreenElement()||!['portrait','landscape'].includes(mode))return false;
    const value=mode==='portrait'?'portrait-primary':'landscape-primary';
    try{if(screen.orientation?.lock){await screen.orientation.lock(value);return true}}catch(e){}
    try{const legacy=screen.lockOrientation||screen.mozLockOrientation||screen.msLockOrientation;if(legacy)return Boolean(legacy.call(screen,value))}catch(e){}
    return false;
  }

  function cssClassFor(mode){return mode==='90'?'view-rot-90':mode==='180'?'view-rot-180':mode==='270'?'view-rot-270':`view-${mode}`}
  function applyCssMode(mode,nativeApplied=false){
    clearViewClasses();viewport.classList.add(cssClassFor(nativeApplied?'auto':mode));
    if(!nativeApplied&&['90','180','270'].includes(mode))root.classList.add('site-rotation-active');
    root.dataset.livenzaDisplayMode=mode;updateOrientationUi(mode,nativeApplied);
  }
  async function applyViewMode(mode,save=true){
    if(!modes.includes(mode))mode='auto';currentMode=mode;syncViewportMetrics();
    // Apply the browser-safe class immediately. Native orientation is an
    // optional enhancement and must never block the click or visual update.
    applyCssMode(mode,false);
    if(save){try{localStorage.setItem('livenza_view_mode',mode)}catch(e){}}
    if(mode==='auto'||['90','180','270'].includes(mode)){
      nativeAppliedMode='';nativeAttempt='';void unlockOrientation();return;
    }
    if(nativeAppliedMode===mode&&nativeFullscreenElement()){applyCssMode(mode,true);return}
    if(!nativeFullscreenElement()||nativeAttempt===mode)return;
    nativeAttempt=mode;
    const applied=await tryNativeOrientation(mode);nativeAttempt='';
    if(currentMode!==mode)return;
    if(applied){nativeAppliedMode=mode;applyCssMode(mode,true)}else nativeAppliedMode='';
  }

  function setRotationLock(active){
    rotationLocked=Boolean(active);
    try{localStorage.setItem('livenza_rotation_locked',rotationLocked?'1':'0')}catch(e){}
    if(rotationLocked&&currentMode==='auto')void applyViewMode(window.innerWidth>=window.innerHeight?'landscape':'portrait',true);
    else if(!rotationLocked)void applyViewMode('auto',true);
    else updateOrientationUi(currentMode,nativeAppliedMode===currentMode);
  }

  async function exitNativeFullscreen(){
    const exit=document.exitFullscreen||document.webkitExitFullscreen||document.webkitCancelFullScreen||document.mozCancelFullScreen||document.msExitFullscreen;
    if(exit){const result=exit.call(document);if(result?.then)await result}
  }
  async function requestNativeFullscreen(){
    const target=document.documentElement;
    if(target.requestFullscreen){try{await target.requestFullscreen({navigationUI:'hide'})}catch(firstError){await target.requestFullscreen()}return Boolean(nativeFullscreenElement())}
    const request=target.webkitRequestFullscreen||target.webkitRequestFullScreen||target.mozRequestFullScreen||target.msRequestFullscreen;
    if(request){const result=request.call(target);if(result?.then)await result;if(!nativeFullscreenElement())await new Promise(resolve=>window.setTimeout(resolve,180));return Boolean(nativeFullscreenElement())}
    return false;
  }

  async function toggleFullscreen(){
    closeViewMenu();root.classList.add('fullscreen-requesting');
    try{
      if(nativeFullscreenElement())await exitNativeFullscreen();
      else if(pseudoFullscreen)setPseudoFullscreen(false);
      else{
        let opened=false;try{opened=await requestNativeFullscreen()}catch(error){console.warn('Native fullscreen unavailable; using theatre mode.',error)}
        if(!opened)setPseudoFullscreen(true);
      }
    }finally{
      root.classList.remove('fullscreen-requesting');updateFullscreenButton();void applyViewMode(currentMode,false);
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
  function scheduleViewMenuPosition(){if(!menu||menu.hidden||menuFrame)return;menuFrame=requestAnimationFrame(()=>{menuFrame=0;positionViewMenu()})}
  function openViewMenu(){
    if(!menu||!viewBtn)return;
    menu.hidden=false;
    requestAnimationFrame(()=>{menu.classList.add('open');positionViewMenu();(menu.querySelector('[data-view-mode].selected')||menu.querySelector('button'))?.focus({preventScroll:true})});
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
  homeDisplayButtons.forEach(button=>button.addEventListener('click',()=>{
    const action=button.dataset.homeDisplay;
    if(action==='lock')setRotationLock(!rotationLocked);
    else if(action==='landscape'||action==='portrait')void applyViewMode(action,true);
    closeViewMenu();
  }));
  menu?.addEventListener('click',e=>{
    const btn=e.target.closest('[data-view-mode]');if(!btn)return;
    e.preventDefault();if(btn.dataset.busy==='1')return;btn.dataset.busy='1';closeViewMenu();void applyViewMode(btn.dataset.viewMode);window.setTimeout(()=>delete btn.dataset.busy,280);
  });
  menu?.addEventListener('keydown',e=>{
    const buttons=[...menu.querySelectorAll('button:not([disabled])')],current=buttons.indexOf(document.activeElement);if(!buttons.length)return;
    let next=-1;if(e.key==='ArrowDown')next=(current+1+buttons.length)%buttons.length;else if(e.key==='ArrowUp')next=(current-1+buttons.length)%buttons.length;else if(e.key==='Home')next=0;else if(e.key==='End')next=buttons.length-1;else return;
    e.preventDefault();buttons[next].focus();
  });
  document.addEventListener('pointerdown',e=>{if(menu&&!menu.hidden&&!menu.contains(e.target)&&!viewBtn?.contains(e.target))closeViewMenu()});
  window.addEventListener('keydown',e=>{if(e.key==='Escape'&&menu&&!menu.hidden){closeViewMenu();viewBtn?.focus({preventScroll:true})}});
  window.addEventListener('resize',()=>{scheduleViewportMetrics();scheduleViewMenuPosition()},{passive:true});
  window.visualViewport?.addEventListener('resize',()=>{scheduleViewportMetrics();scheduleViewMenuPosition()},{passive:true});
  window.addEventListener('scroll',scheduleViewMenuPosition,{passive:true,capture:true});

  async function onFullscreenChange(){
    if(nativeFullscreenElement()&&pseudoFullscreen)setPseudoFullscreen(false);
    if(!nativeFullscreenElement())nativeAppliedMode='';
    updateFullscreenButton();
    void applyViewMode(currentMode,false);
    scheduleViewMenuPosition();
  }
  document.addEventListener('fullscreenchange',onFullscreenChange);
  document.addEventListener('webkitfullscreenchange',onFullscreenChange);
  document.addEventListener('mozfullscreenchange',onFullscreenChange);
  document.addEventListener('MSFullscreenChange',onFullscreenChange);
  screen.orientation?.addEventListener?.('change',scheduleViewportMetrics);
  document.addEventListener('fullscreenerror',()=>{if(!nativeFullscreenElement()){setPseudoFullscreen(true);updateFullscreenButton();void applyViewMode(currentMode,false)}});

  let initial='auto';try{initial=localStorage.getItem('livenza_view_mode')||'auto';rotationLocked=localStorage.getItem('livenza_rotation_locked')==='1'}catch(e){}
  currentMode=modes.includes(initial)?initial:'auto';
  syncViewportMetrics();applyViewMode(currentMode,false);updateFullscreenButton();

  window.LivenzaDisplay={
    isFullscreen,
    getMode:()=>currentMode,
    isRotationLocked:()=>rotationLocked,
    setMode:mode=>applyViewMode(mode,true),
    setRotationLock,
    closeViewMenu,
    closeRotateMenu:closeViewMenu,
    resetForNavigation:()=>applyViewMode(currentMode,false)
  };
})();

// ===== Web 1.5.13 • personal live-avatar studio =====
(()=>{
  const form=document.getElementById('avatarForm');
  if(!form)return;
  const input=document.getElementById('avatarPhotoInput');
  const button=document.getElementById('avatarGenerateButton');
  const status=document.getElementById('avatarGenerationStatus');
  const shell=document.getElementById('avatarPreviewShell');
  const modeLabel=document.getElementById('avatarModeLabel');
  let busy=false,previewUrl='';

  function setPreview(source){
    let image=document.getElementById('avatarPreview');
    if(!image){image=document.createElement('img');image.id='avatarPreview';image.alt='Live avatar preview';document.getElementById('avatarPreviewFallback')?.replaceWith(image)}
    image.src=source;shell?.classList.add('is-ready');
  }
  function showState(kind,title,detail=''){
    if(!status)return;status.hidden=false;status.dataset.state=kind;
    const strong=status.querySelector('b'),small=status.querySelector('small');if(strong)strong.textContent=title;if(small)small.textContent=detail;
  }
  function setBusy(value){busy=value;if(button){button.disabled=value;button.textContent=value?'Creating Avatar…':'Create My Live Avatar'}input.disabled=value;shell?.classList.toggle('is-generating',value)}

  input?.addEventListener('change',()=>{
    const file=input.files?.[0];if(!file)return;
    if(file.size>12*1024*1024){showState('error','Photo is too large','Choose an image smaller than 12 MB.');input.value='';return}
    if(previewUrl)URL.revokeObjectURL(previewUrl);previewUrl=URL.createObjectURL(file);setPreview(previewUrl);
    showState('ready','Photo ready','Creating your personal avatar automatically…');
    window.setTimeout(()=>{if(!busy&&input.files?.[0]===file)form.requestSubmit()},260);
  });

  form.addEventListener('submit',async event=>{
    if(!window.fetch||busy)return;
    event.preventDefault();
    if(!input.files?.length){showState('error','Choose a profile photo','A clear front-facing JPG, PNG or WebP works best.');return}
    setBusy(true);showState('loading','Creating your polished avatar…','Preserving your identity and applying the Livenza visual finish.');
    try{
      const response=await fetch(form.action,{method:'POST',body:new FormData(form),credentials:'same-origin',headers:{Accept:'application/json','X-Requested-With':'XMLHttpRequest'}});
      const data=await response.json().catch(()=>({}));
      if(!response.ok||!data.ok)throw new Error(data.error||'The avatar could not be created.');
      setPreview(data.avatar_data_uri);showState('success','Your live avatar is ready',data.message||'Applied across the Livenza workspace.');
      if(modeLabel)modeLabel.innerHTML=`Current finish: <b>${data.mode==='ai'?'AI styled':'Polished portrait'}</b>`;
      const headerImage=document.querySelector('.profile-toggle img');if(headerImage)headerImage.src=data.avatar_data_uri;
      window.setTimeout(()=>window.location.reload(),1150);
    }catch(error){showState('error','Could not create the avatar',error.message||'Please try another clear photo.');setBusy(false)}
  });
})();

// ===== Web 1.5.2 • transparent scroll header + contextual visual storytelling =====
(()=>{
  const reduce=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches||livenzaMobilePerformance();
  const header=document.querySelector('.reference-header');
  let scrollFrame=0,lastY=window.scrollY;

  function updateScrollSurfaces(){
    scrollFrame=0;
    const y=Math.max(0,window.scrollY),progress=Math.min(1,y/260);
    if(header){
      const compact=header.classList.contains('is-scrolled')?y>10:y>28;
      header.classList.toggle('is-scrolled',compact);
      header.classList.toggle('scrolling-down',y>lastY&&y>110);
      header.style.setProperty('--header-scroll',progress.toFixed(3));
    }
    if(!reduce)document.querySelectorAll('.module-visual-ribbon').forEach(el=>{
      const rect=el.getBoundingClientRect(),viewport=window.innerHeight||800;
      const shift=Math.max(-18,Math.min(18,(viewport*.5-(rect.top+rect.height*.5))*.035));
      el.style.setProperty('--visual-shift',`${shift.toFixed(1)}px`);
    });
    lastY=y;
  }
  function queueScroll(){if(!scrollFrame)scrollFrame=requestAnimationFrame(updateScrollSurfaces)}
  window.addEventListener('scroll',queueScroll,{passive:true});

  const photos={
    agreement:{match:/agreement/,eyebrow:'DOCUMENT EXPERIENCE',title:'Clear agreements. Confident decisions.',alt:'Business agreement being reviewed',image:'https://images.unsplash.com/photo-1758518731462-d091b0b4ed0d?auto=format&fit=crop&q=78&w=1600',credit:'https://unsplash.com/photos/business-people-signing-a-contract-at-a-table-iPheGw7_UaI'},
    rooms:{match:/room|tenant/,eyebrow:'STAY OPERATIONS',title:'Every room, visibly under control.',alt:'Bright modern shared accommodation room',image:'https://images.unsplash.com/photo-1781415980730-bfcf192e38bc?auto=format&fit=crop&q=78&w=1600',credit:'https://unsplash.com/photos/clean-well-lit-room-with-several-neatly-made-beds-0xJJ2k72AQs'},
    food:{match:/food/,eyebrow:'FOOD EXPERIENCE',title:'Orders, kitchens and settlements in motion.',alt:'Restaurant staff preparing food in a professional kitchen',image:'https://images.unsplash.com/photo-1780319232447-4075b592098a?auto=format&fit=crop&q=78&w=1600',credit:'https://unsplash.com/photos/restaurant-staff-preparing-food-in-a-professional-kitchen-Ew2PDNZB4qA'},
    hospitality:{match:/video-wall|billing|rentok/,eyebrow:'HOSPITALITY EXPERIENCE',title:'A polished guest journey on every screen.',alt:'Modern hotel room interior',image:'https://images.unsplash.com/photo-1784720845648-a79a9ba6d16d?auto=format&fit=crop&q=78&w=1600',credit:'https://unsplash.com/photos/modern-hotel-room-with-a-king-size-bed-and-wooden-interior-fTiPYH7rN2A'},
    office:{match:/quer|review|whatsapp|email|drive|admin|setting|account/,eyebrow:'CONNECTED WORKSPACE',title:'One calm command centre for every operation.',alt:'Modern connected office workspace',image:'https://images.unsplash.com/photo-1774186184383-90fc06307e77?auto=format&fit=crop&q=78&w=1600',credit:'https://unsplash.com/photos/modern-office-space-with-city-view-and-desks-56U797Gamac'}
  };

  function visualForPath(){const path=location.pathname.toLowerCase();if(path.startsWith('/agreements'))return null;return Object.values(photos).find(item=>item.match.test(path))}
  function mountContextVisual(root=document){
    if(root.querySelector?.('.module-visual-ribbon,.experience-gallery,.agreement-brand-banner'))return;
    const pageHead=root.querySelector?.('.page-head');if(!pageHead)return;
    const visual=visualForPath();if(!visual)return;
    const ribbon=document.createElement('a');ribbon.className='module-visual-ribbon';ribbon.href=visual.credit;ribbon.target='_blank';ribbon.rel='noopener';ribbon.setAttribute('aria-label',`${visual.title} Photography source`);
    const img=document.createElement('img');img.src=livenzaMobilePerformance()?visual.image.replace('q=78','q=62').replace('w=1600','w=900'):visual.image;img.alt=visual.alt;img.loading='lazy';img.decoding='async';img.referrerPolicy='no-referrer';
    const wash=document.createElement('span');wash.className='module-visual-copy';
    const small=document.createElement('small');small.textContent=visual.eyebrow;
    const strong=document.createElement('strong');strong.textContent=visual.title;
    const source=document.createElement('i');source.textContent='VIEW PHOTOGRAPHY ↗';
    wash.append(small,strong,source);ribbon.append(img,wash);pageHead.insertAdjacentElement('afterend',ribbon);
  }

  function bindDepth(root=document){
    if(reduce)return;
    root.querySelectorAll?.('.module-card,.experience-shot').forEach(card=>{
      if(card.dataset.depthBound)return;card.dataset.depthBound='1';
      card.addEventListener('pointermove',e=>{const r=card.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;card.style.setProperty('--tilt-x',`${(-y*2.4).toFixed(2)}deg`);card.style.setProperty('--tilt-y',`${(x*3.2).toFixed(2)}deg`)});
      card.addEventListener('pointerleave',()=>{card.style.setProperty('--tilt-x','0deg');card.style.setProperty('--tilt-y','0deg')});
    });
  }

  function animateMetrics(root=document){
    if(reduce)return;
    root.querySelectorAll?.('.stats b').forEach(el=>{
      if(el.dataset.counted||!/^\d+$/.test(el.textContent.trim()))return;el.dataset.counted='1';
      const target=Number(el.textContent.trim());if(!target)return;const start=performance.now(),duration=720;
      const tick=now=>{const t=Math.min(1,(now-start)/duration),ease=1-Math.pow(1-t,3);el.textContent=String(Math.round(target*ease));if(t<1)requestAnimationFrame(tick)};requestAnimationFrame(tick);
    });
  }

  function enhance(root=document){mountContextVisual(root);bindDepth(root);animateMetrics(root);updateScrollSurfaces()}
  enhance(document);
  window.addEventListener('livenza:content-swapped',e=>enhance(e.detail?.root||document));
})();

// ===== Web 1.5.0 • pattern login + WebAuthn / Windows Hello =====
(function(){
  const fromB64url=value=>{
    const b64=String(value||'').replace(/-/g,'+').replace(/_/g,'/').padEnd(Math.ceil(String(value||'').length/4)*4,'=');
    const bin=atob(b64),out=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)out[i]=bin.charCodeAt(i);return out.buffer;
  };
  const toB64url=value=>{
    if(value===null||value===undefined)return null;const bytes=new Uint8Array(value);let bin='';bytes.forEach(v=>bin+=String.fromCharCode(v));return btoa(bin).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
  };
  function initPatternWidgets(root=document){
    root.querySelectorAll?.('[data-pattern-widget]').forEach(widget=>{
      if(widget.dataset.ready)return;
      widget.dataset.ready='1';
      const selected=[],selectedNodes=[],hidden=widget.querySelector('[data-pattern-value]'),nodes=[...widget.querySelectorAll('[data-pattern-node]')];
      let drawing=false,moved=false;
      const widgetId=widget.id||`pattern-${Math.random().toString(36).slice(2,9)}`;widget.id=widgetId;
      widget.setAttribute('role','group');widget.setAttribute('aria-label',widget.dataset.patternLabel||'Gesture pattern');
      nodes.forEach((node,index)=>{const dot=node.querySelector('span')||node.appendChild(document.createElement('span'));dot.classList.add('pattern-dot');if(!node.querySelector('.pattern-number')){const number=document.createElement('b');number.className='pattern-number';number.textContent=String(index+1);number.setAttribute('aria-hidden','true');node.appendChild(number)}});
      let controls=[...widget.parentElement.children].find(item=>item.hasAttribute?.('data-pattern-controls'));
      if(!controls){
        controls=document.createElement('div');controls.className='pattern-control-bar';controls.dataset.patternControls='';
        const status=document.createElement('span');status.className='pattern-selection-status';status.dataset.patternStatus='';status.setAttribute('aria-live','polite');status.innerHTML='<span class="pattern-progress-dots" data-pattern-progress-dots aria-hidden="true"><i></i><i></i><i></i><i></i></span><b data-pattern-progress-label>0 / 4 selected</b>';
        const clearButton=document.createElement('button');clearButton.type='button';clearButton.className='pattern-clear-button';clearButton.dataset.patternClear='';clearButton.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 15 7-7 6 6-7 7H6l-2-2a3 3 0 0 1 0-4Z"></path><path d="m14 11 3-3 3 3-3 3"></path></svg><span>Clear Pattern</span>';
        controls.append(status,clearButton);widget.insertAdjacentElement('afterend',controls);
      }
      const status=controls.querySelector('[data-pattern-status]'),clearButton=controls.querySelector('[data-pattern-clear]');
      if(status){status.id=status.id||`${widgetId}-status`;widget.setAttribute('aria-describedby',status.id)}
      const progressDots=[...(status?.querySelectorAll('[data-pattern-progress-dots] i')||[])],progressLabel=status?.querySelector('[data-pattern-progress-label]');
      if(window.matchMedia?.('(pointer:fine)').matches)widget.classList.add('numeric-keypad');
      const svg=document.createElementNS('http://www.w3.org/2000/svg','svg'),line=document.createElementNS('http://www.w3.org/2000/svg','polyline');svg.classList.add('pattern-links');svg.setAttribute('aria-hidden','true');line.setAttribute('fill','none');line.setAttribute('vector-effect','non-scaling-stroke');svg.appendChild(line);widget.insertBefore(svg,widget.firstChild);
      const updateLine=()=>{const bounds=widget.getBoundingClientRect();svg.setAttribute('viewBox',`0 0 ${Math.max(1,bounds.width)} ${Math.max(1,bounds.height)}`);line.setAttribute('points',selectedNodes.map(node=>{const r=node.getBoundingClientRect();return `${r.left-bounds.left+r.width/2},${r.top-bounds.top+r.height/2}`}).join(' '))};
      const announce=()=>{if(!status)return;const count=selected.length,ready=count>=4;progressDots.forEach((dot,index)=>dot.classList.toggle('filled',index<Math.min(count,4)));status.classList.toggle('is-ready',ready);if(progressLabel)progressLabel.textContent=ready?`Ready · ${count} selected`:`${count} / 4 selected`;status.setAttribute('aria-label',ready?`Pattern ready with ${count} points`:`${count} of 4 required points selected`)};
      const resetHelp=()=>{const help=widget.parentElement.querySelector('[data-pattern-help]');if(help?.dataset.defaultMessage)help.textContent=help.dataset.defaultMessage};
      const clear=(focus=false)=>{selected.splice(0);selectedNodes.splice(0);nodes.forEach(node=>{node.classList.remove('selected');node.setAttribute('aria-pressed','false')});if(hidden)hidden.value='';widget.parentElement.classList.remove('has-error');resetHelp();updateLine();announce();if(focus)nodes[0]?.focus()};
      const removeLast=()=>{const node=selectedNodes.pop();selected.pop();if(node){node.classList.remove('selected');node.setAttribute('aria-pressed','false')}if(hidden)hidden.value=selected.join('-');updateLine();announce()};
      const add=node=>{if(!node||!widget.contains(node))return;const value=node.dataset.patternNode;if(value===undefined||selected.includes(value))return;selected.push(value);selectedNodes.push(node);node.classList.add('selected');node.setAttribute('aria-pressed','true');if(hidden)hidden.value=selected.join('-');widget.parentElement.classList.remove('has-error');resetHelp();updateLine();announce();widget.dispatchEvent(new CustomEvent('livenza:pattern-change',{bubbles:true,detail:{count:selected.length}}))};
      const nodeAt=(x,y)=>document.elementFromPoint(x,y)?.closest?.('[data-pattern-node]');
      widget.addEventListener('pointerdown',event=>{if(event.pointerType==='mouse')return;if(event.button!==undefined&&event.button!==0)return;event.preventDefault();clear();drawing=true;moved=false;add(event.target.closest('[data-pattern-node]'));try{widget.setPointerCapture(event.pointerId)}catch(e){}});
      widget.addEventListener('pointermove',event=>{if(!drawing)return;event.preventDefault();moved=true;add(nodeAt(event.clientX,event.clientY))});
      const finish=event=>{if(!drawing)return;drawing=false;try{widget.releasePointerCapture(event.pointerId)}catch(e){};updateLine()};widget.addEventListener('pointerup',finish);widget.addEventListener('pointercancel',finish);
      nodes.forEach((node,index)=>{
        const row=Math.floor(index/3)+1,column=index%3+1;node.setAttribute('aria-label',node.getAttribute('aria-label')||`Pattern number ${index+1}, row ${row}, column ${column}`);node.setAttribute('aria-pressed','false');node.tabIndex=0;
        node.addEventListener('click',event=>{if(moved){event.preventDefault();moved=false;return}add(node)});
        node.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();add(node)}});
      });
      document.addEventListener('keydown',event=>{if(widget.closest('[hidden]')||widget.offsetParent===null||event.ctrlKey||event.metaKey||event.altKey)return;if(/^[1-9]$/.test(event.key)){event.preventDefault();add(nodes[Number(event.key)-1])}else if(event.key==='Backspace'){event.preventDefault();removeLast()}else if(event.key==='Delete'){event.preventDefault();clear(true)}});
      clearButton?.addEventListener('click',()=>clear(true));
      window.addEventListener('resize',updateLine,{passive:true});updateLine();announce();
    });
  }
  function initPasswordToggles(root=document){
    root.querySelectorAll?.('[data-password-toggle]').forEach(button=>{
      if(button.dataset.ready)return;button.dataset.ready='1';const input=button.parentElement?.querySelector('input');if(!input)return;
      button.addEventListener('click',()=>{const reveal=input.type==='password';input.type=reveal?'text':'password';button.classList.toggle('is-visible',reveal);button.setAttribute('aria-pressed',String(reveal));button.setAttribute('aria-label',`${reveal?'Hide':'Show'} ${input.name==='secret'?'PIN or password':'password'}`);input.focus({preventScroll:true})});
    });
  }
  function setFieldState(input,message,error=true){
    if(!input)return;const field=input.closest('[data-auth-field]'),feedback=field?.querySelector('.field-feedback');field?.classList.toggle('has-error',error);input.setAttribute('aria-invalid',String(error));if(feedback&&message)feedback.textContent=message;
  }
  function showAuthAlert(message){const alert=document.getElementById('loginFormAlert');if(!alert)return;alert.textContent=message||'';alert.hidden=!message}
  function selectAuthMethod(mode='password',focus=false){
    const chosen=mode==='pattern'?'pattern':'password',method=document.getElementById('authMethod');if(method)method.value=chosen;
    document.querySelectorAll('[data-auth-method-tab]').forEach(tab=>{const active=tab.dataset.authMethodTab===chosen;tab.classList.toggle('active',active);tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1});
    document.querySelectorAll('[data-auth-method-panel]').forEach(panel=>{const active=panel.dataset.authMethodPanel===chosen;panel.hidden=!active;panel.classList.toggle('active',active)});
    if(focus)window.setTimeout(()=>document.querySelector(`[data-auth-method-panel="${chosen}"] ${chosen==='pattern'?'[data-pattern-node]':'input'}`)?.focus(),70);
  }
  function setFallbackLayer(open,focusMode=''){
    const layer=document.getElementById('authFallbackLayer'),toggle=document.getElementById('authFallbackToggle');if(!layer||!toggle)return;
    layer.hidden=!open;layer.classList.toggle('is-open',open);toggle.setAttribute('aria-expanded',String(open));
    toggle.classList.toggle('is-open',open);if(open)selectAuthMethod(focusMode||document.getElementById('authMethod')?.value||'password',Boolean(focusMode));
  }
  function setCredentialLoader(active){
    const loader=document.getElementById('deviceCredentialLoader'),button=document.getElementById('fingerprintLogin');if(loader)loader.hidden=!active;if(button){button.disabled=active;button.classList.toggle('is-checking',active)}
  }
  function initInlineAuth(){
    const form=document.getElementById('loginForm'),username=document.getElementById('loginUsername'),password=document.getElementById('loginPassword'),method=document.getElementById('authMethod');
    const fallbackToggle=document.getElementById('authFallbackToggle');fallbackToggle?.addEventListener('click',()=>setFallbackLayer(fallbackToggle.getAttribute('aria-expanded')!=='true',method?.value==='pattern'?'pattern':'password'));
    document.querySelectorAll('[data-auth-method-tab]').forEach(tab=>{tab.addEventListener('click',()=>selectAuthMethod(tab.dataset.authMethodTab,true));tab.addEventListener('keydown',event=>{const tabs=[...document.querySelectorAll('[data-auth-method-tab]')],index=tabs.indexOf(tab);if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:event.key==='ArrowRight'?(index+1)%tabs.length:(index-1+tabs.length)%tabs.length;tabs[next].focus();selectAuthMethod(tabs[next].dataset.authMethodTab,false)})});
    username?.addEventListener('input',()=>{if(username.value.trim()){setFieldState(username,'Use the Login ID assigned by your administrator.',false);showAuthAlert('')}});
    password?.addEventListener('input',()=>{if(password.value){setFieldState(password,'Password is case-sensitive.',false);showAuthAlert('')}});
    password?.addEventListener('keyup',event=>{if(password.value&&event.getModifierState?.('CapsLock'))setFieldState(password,'Caps Lock is on.',false);else if(password.value&&!password.closest('.has-error'))setFieldState(password,'Password is case-sensitive.',false)});
    document.addEventListener('livenza:pattern-change',event=>{if(event.target.closest('#patternFallback'))showAuthAlert('')});
    form?.addEventListener('submit',event=>{
      const mode=method?.value||'password';let message='';
      if(!username?.value.trim()){message='Enter your Login ID before choosing a sign-in method.';setFieldState(username,message,true)}
      else if(mode==='password'&&!password?.value){message='Enter your password to continue.';setFieldState(password,message,true)}
      else if(mode==='pattern'){const points=(form.querySelector('[data-pattern-value]')?.value||'').split('-').filter(Boolean);if(points.length<4){message=`Choose at least four pattern points${points.length?` — ${points.length} selected`:''}.`;const shell=form.querySelector('.pattern-entry-shell'),help=shell?.querySelector('[data-pattern-help]');shell?.classList.add('has-error');if(help)help.textContent=message}}
      if(message){event.preventDefault();showAuthAlert(message);if(username?.value.trim()&&(mode==='password'||mode==='pattern'))setFallbackLayer(true,mode);window.setTimeout(()=>(mode==='pattern'?form.querySelector('[data-pattern-node]'):(!username?.value.trim()?username:password))?.focus(),70)}
    });
    const kioskForm=document.querySelector('[data-kiosk-unlock-form]');kioskForm?.addEventListener('submit',event=>{const secret=document.getElementById('kioskSecret'),alert=kioskForm.querySelector('[data-kiosk-error]');if(secret?.value)return;event.preventDefault();setFieldState(secret,'Enter your kiosk PIN or account password.',true);if(alert){alert.textContent='Enter your kiosk PIN or account password.';alert.hidden=false}secret?.focus()});
  }
  function setStatus(message,error=false){const el=document.getElementById('webauthnStatus');if(el){el.textContent=message;el.classList.toggle('danger',error)}}
  async function jsonRequest(url,body){const r=await fetch(url,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});const d=await r.json().catch(()=>({error:`Request failed (${r.status})`}));if(!r.ok||d.ok===false)throw new Error(d.error||`Request failed (${r.status})`);return d}
  async function fingerprintLogin(){
    if(!window.PublicKeyCredential)throw new Error('Fingerprint/passkeys are not supported by this browser.');
    const usernameInput=document.getElementById('loginUsername'),username=usernameInput?.value?.trim();if(!username){const message='Enter your Login ID before checking this device.';setFieldState(usernameInput,message,true);showAuthAlert(message);usernameInput?.focus();throw new Error(message)}
    setCredentialLoader(true);setStatus('Checking this device for a secure credential…');
    try{
      const options=await jsonRequest('/api/webauthn/auth/options',{username});options.challenge=fromB64url(options.challenge);(options.allowCredentials||[]).forEach(c=>c.id=fromB64url(c.id));
      setStatus('Waiting for the native identity prompt…');const credential=await navigator.credentials.get({publicKey:options});
      const payload={id:credential.id,rawId:toB64url(credential.rawId),type:credential.type,response:{clientDataJSON:toB64url(credential.response.clientDataJSON),authenticatorData:toB64url(credential.response.authenticatorData),signature:toB64url(credential.response.signature),userHandle:toB64url(credential.response.userHandle)},clientExtensionResults:credential.getClientExtensionResults()};
      const verified=await jsonRequest('/api/webauthn/auth/verify',payload);setStatus('Verified. Opening Livenza…');setCredentialLoader(false);location.assign(verified.redirect||'/');
    }catch(error){setCredentialLoader(false);throw error}
  }
  async function enrollPasskey(button){
    if(!window.PublicKeyCredential)throw new Error('Fingerprint/passkeys are not supported by this browser.');
    button.disabled=true;setStatus('Waiting for Windows Hello / fingerprint…');
    try{
      const options=await jsonRequest('/api/webauthn/register/options',{});options.challenge=fromB64url(options.challenge);options.user.id=fromB64url(options.user.id);(options.excludeCredentials||[]).forEach(c=>c.id=fromB64url(c.id));
      const credential=await navigator.credentials.create({publicKey:options});
      const payload={id:credential.id,rawId:toB64url(credential.rawId),type:credential.type,device_name:navigator.userAgentData?.platform||navigator.platform||'Windows Hello / fingerprint',response:{clientDataJSON:toB64url(credential.response.clientDataJSON),attestationObject:toB64url(credential.response.attestationObject),transports:credential.response.getTransports?.()||[]},clientExtensionResults:credential.getClientExtensionResults()};
      const result=await jsonRequest('/api/webauthn/register/verify',payload);setStatus(result.message||'Fingerprint/passkey enrolled.');button.textContent='Enrolled ✓';
    }finally{button.disabled=false}
  }
  document.getElementById('fingerprintLogin')?.addEventListener('click',async()=>{try{await fingerprintLogin()}catch(e){setStatus(`${e.message||'Device verification was unavailable.'} Choose Password or Gesture below.`,true);setFallbackLayer(true,'password')}});
  document.querySelectorAll('[data-submit-auth]').forEach(button=>button.addEventListener('click',()=>{const method=document.getElementById('authMethod');if(method)method.value=button.dataset.submitAuth||'password';showAuthAlert('')}));
  document.getElementById('loginForm')?.addEventListener('submit',async e=>{if(document.getElementById('authMethod')?.value==='fingerprint'){e.preventDefault();try{await fingerprintLogin()}catch(err){setStatus(`${err.message||'Device verification was unavailable.'} Choose Password or Gesture below.`,true);setFallbackLayer(true,'password')}}});
  document.addEventListener('click',async e=>{const btn=e.target.closest('[data-enroll-passkey]');if(!btn)return;e.preventDefault();try{await enrollPasskey(btn)}catch(err){setStatus(err.message||'Enrollment failed.',true)}});
  if(document.getElementById('authFallbackLayer')&&!document.getElementById('authFallbackLayer').hidden)selectAuthMethod(document.getElementById('authMethod')?.value||'password',false);
  if(!window.PublicKeyCredential){const method=document.getElementById('authMethod');if(method)method.value='password';setFallbackLayer(true,'password');setStatus('This browser does not support device passkeys. Choose Password or Gesture below.',true)}
  initPatternWidgets(document);initPasswordToggles(document);initInlineAuth();window.addEventListener('livenza:page-ready',e=>{initPatternWidgets(e.detail?.root||document);initPasswordToggles(e.detail?.root||document)});
})();

// ===== Web 1.4.6 • professional motion + fullscreen-safe navigation =====
(function(){
  const reduce=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches||livenzaMobilePerformance();
  const transition=document.getElementById('pageTransition');
  const motionLayer=document.getElementById('liveMotionLayer');

  // Lightweight live particles: decorative only, no canvas and no layout work.
  if(motionLayer&&!reduce){
    const count=14;
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
  const reduce=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches||livenzaMobilePerformance();

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
    const target=e.target.closest('button,.btn,.module-card,.nav-dropdown-menu>a');if(!target||reduce)return;
    const r=target.getBoundingClientRect(),dot=document.createElement('i');dot.className='touch-ripple';dot.style.left=`${e.clientX-r.left}px`;dot.style.top=`${e.clientY-r.top}px`;target.appendChild(dot);setTimeout(()=>dot.remove(),650);
  },{passive:true});

  // The mascot now owns the help conversation; there is no second launcher.
  const form=document.getElementById('assistantForm'),input=document.getElementById('assistantInput'),messages=document.getElementById('assistantMessages');
  function addMessage(text,who='bot'){
    if(!messages)return;const div=document.createElement('div');div.className=`assistant-message ${who}`;div.textContent=text;messages.appendChild(div);messages.scrollTop=messages.scrollHeight;
  }
  async function askAssistant(text){
    text=(text||'').trim();if(!text)return;window.LivenzaCompanion?.open?.('chat');addMessage(text,'user');if(input)input.value='';const thinking=document.createElement('div');thinking.className='assistant-message bot thinking';thinking.textContent='Thinking…';messages?.appendChild(thinking);messages.scrollTop=messages.scrollHeight;
    try{const r=await fetch('/api/help',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',body:JSON.stringify({message:text})});const d=await r.json();thinking.remove();addMessage(d.answer||d.error||'I could not answer that right now.','bot')}catch(e){thinking.remove();addMessage('I could not reach the help service. Please try again.','bot')}
  }
  form?.addEventListener('submit',e=>{e.preventDefault();askAssistant(input?.value)});
  document.addEventListener('click',e=>{const b=e.target.closest('[data-help-prompt]');if(b)askAssistant(b.dataset.helpPrompt)});

  // Authenticated partner portals often refuse third-party iframe embedding.
  // Copying or launching their official top-level URL keeps login and OTP flows intact.
  document.addEventListener('click',async e=>{
    const button=e.target.closest('[data-copy-portal]');if(!button)return;
    const url=button.dataset.copyPortal||'';if(!url)return;
    const original=button.textContent;
    try{await navigator.clipboard.writeText(url);button.textContent='Link Copied ✓'}catch(err){button.textContent='Copy Unavailable'}
    setTimeout(()=>button.textContent=original,1600);
  });

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
  function rowMeaningful(row){const payload=rowPayload(row);return ['customer_name','mobile','whatsapp','email','city','property_name','budget','move_in_date','stay_type','query_text','notes'].some(key=>String(payload[key]||'').trim())}
  function blankQueryRow(number){const tr=document.createElement('tr');tr.className='sheet-blank-row';tr.dataset.queryId='';tr.dataset.clientRef=`blank-${Date.now()}-${Math.random().toString(36).slice(2,8)}`;tr.innerHTML=`<td class="sheet-row-number">${number}</td><td><select data-field="source"><option>Manual</option><option>Meta</option><option>Facebook</option><option>Google</option><option>Airbnb</option><option>Booking.com</option><option>MakeMyTrip</option><option>Goibibo</option><option>Direct</option><option>Other</option></select></td><td contenteditable="true" data-field="customer_name" data-placeholder="Customer name"></td><td contenteditable="true" data-field="mobile" data-placeholder="Mobile"></td><td contenteditable="true" data-field="whatsapp" data-placeholder="WhatsApp"></td><td contenteditable="true" data-field="email" data-placeholder="Email"></td><td contenteditable="true" data-field="city" data-placeholder="City"></td><td contenteditable="true" data-field="property_name" data-placeholder="Property"></td><td contenteditable="true" data-field="budget" data-placeholder="Budget"></td><td contenteditable="true" data-field="move_in_date" data-placeholder="YYYY-MM-DD"></td><td contenteditable="true" data-field="stay_type" data-placeholder="Stay type"></td><td><select data-field="status"><option>Live</option><option>New</option><option>Follow-up</option><option>Won</option><option>Lost</option><option>Closed</option></select></td><td><select data-field="heat"><option>Warm</option><option>Hot</option><option>Cold</option></select></td><td contenteditable="true" data-field="score" inputmode="numeric" data-placeholder="50"></td><td contenteditable="true" data-field="next_follow_up" data-placeholder="Follow-up"></td><td contenteditable="true" data-field="query_text" data-placeholder="Requirement / query" class="sheet-wide-cell"></td><td contenteditable="true" data-field="notes" data-placeholder="Notes" class="sheet-wide-cell"></td><td class="sheet-action-cell"><button type="button" class="sheet-save-row" title="Save this row">✓</button></td>`;return tr}
  function addBlankQueryRows(count=10){const body=document.getElementById('querySheetBody');if(!body)return[];const added=[];for(let i=0;i<count;i++){const row=blankQueryRow(body.rows.length+1);body.appendChild(row);added.push(row)}return added}
  async function saveSheetRow(row){
    if(!row||(!row.dataset.queryId&&!rowMeaningful(row)))return;const id=row.dataset.queryId,payload=rowPayload(row);row.classList.add('saving');sheetStatus(id?`Saving #${id}…`:'Saving filled row…','saving');
    try{const d=await sameOriginJson(id?`/api/queries/${id}`:'/api/queries',payload,id?'PATCH':'POST');if(!id){row.dataset.queryId=d.id;row.classList.remove('sheet-blank-row')}row.classList.remove('save-error','dirty');row.classList.add('saved');sheetStatus(`Saved query #${d.id}`,'saved');setTimeout(()=>row.classList.remove('saved'),700)}catch(err){row.classList.add('save-error');sheetStatus(err.message||'Could not save row','error')}finally{row.classList.remove('saving')}
  }
  async function saveAllSheetRows(){const rows=[...document.querySelectorAll('#querySheetBody tr')].filter(row=>(row.dataset.queryId&&row.classList.contains('dirty'))||(!row.dataset.queryId&&rowMeaningful(row)));if(!rows.length){sheetStatus('Everything is already saved','saved');return}const button=document.getElementById('saveQuerySheetAll');if(button)button.disabled=true;rows.forEach(row=>row.classList.add('saving'));sheetStatus(`Saving ${rows.length} row${rows.length===1?'':'s'}…`,'saving');try{const payload=rows.map(row=>({...rowPayload(row),id:row.dataset.queryId||'',client_ref:row.dataset.clientRef||''})),data=await sameOriginJson('/api/queries/batch',{rows:payload});(data.saved||[]).forEach(saved=>{const row=rows.find(item=>(item.dataset.clientRef||'')===String(saved.client_ref));if(row){row.dataset.queryId=saved.id;row.classList.remove('sheet-blank-row','dirty','save-error');row.classList.add('saved');setTimeout(()=>row.classList.remove('saved'),800)}});sheetStatus(`Saved ${data.count||0} query row${data.count===1?'':'s'}`,'saved')}catch(error){rows.forEach(row=>row.classList.add('save-error'));sheetStatus(error.message||'Batch save failed','error')}finally{rows.forEach(row=>row.classList.remove('saving'));if(button)button.disabled=false}}
  function markSheetRow(row){if(!row)return;row.classList.add('dirty');if(!row.dataset.queryId)sheetStatus('Unsaved entries in blank rows','editing')}
  function queueRowSave(row,delay=320){markSheetRow(row);if(!row?.dataset.queryId)return;clearTimeout(rowSaveTimers.get(row));rowSaveTimers.set(row,setTimeout(()=>saveSheetRow(row),delay))}
  document.addEventListener('input',e=>{const field=e.target.closest?.('#querySheetTable [data-field]');if(field)markSheetRow(field.closest('tr'))});
  document.addEventListener('focusout',e=>{const cell=e.target.closest('#querySheetTable [data-field][contenteditable="true"]');if(cell)queueRowSave(cell.closest('tr'))});
  document.addEventListener('change',e=>{const field=e.target.closest('#querySheetTable [data-field]');if(field)queueRowSave(field.closest('tr'),100)});
  document.addEventListener('keydown',e=>{const cell=e.target.closest?.('#querySheetTable [contenteditable="true"]');if(cell&&e.key==='Enter'&&!e.shiftKey){e.preventDefault();const row=cell.closest('tr'),fields=[...row.querySelectorAll('[data-field]')],index=fields.indexOf(cell),next=row.nextElementSibling?.querySelectorAll('[data-field]')?.[index];cell.blur();next?.focus()}});
  document.addEventListener('paste',e=>{const start=e.target.closest?.('#querySheetTable [data-field]');if(!start)return;const text=e.clipboardData?.getData('text/plain')||'';if(!text.includes('\t')&&!/[\r\n]/.test(text))return;e.preventDefault();const matrix=text.replace(/\r/g,'').split('\n').filter((line,index,all)=>line||index<all.length-1).map(line=>line.split('\t')),startRow=start.closest('tr'),body=startRow.parentElement,allRows=()=>[...body.rows],startRowIndex=allRows().indexOf(startRow),startFieldIndex=[...startRow.querySelectorAll('[data-field]')].indexOf(start);while(allRows().length<startRowIndex+matrix.length)addBlankQueryRows(10);matrix.forEach((values,rowOffset)=>{const row=allRows()[startRowIndex+rowOffset],fields=[...row.querySelectorAll('[data-field]')];values.forEach((value,columnOffset)=>{const field=fields[startFieldIndex+columnOffset];if(!field)return;if(field.matches('select')){const option=[...field.options].find(item=>item.value.toLowerCase()===value.trim().toLowerCase());if(option)field.value=option.value}else field.textContent=value.trim()});markSheetRow(row)});sheetStatus(`Pasted ${matrix.length} row${matrix.length===1?'':'s'} · click Save All Changes`,'editing')});
  document.addEventListener('click',async e=>{
    const save=e.target.closest('.sheet-save-row');if(save){await saveSheetRow(save.closest('tr'));return}
    if(e.target.closest('#addQuerySheetRows')){const added=addBlankQueryRows(10);added[0]?.querySelector('[data-field="customer_name"]')?.focus();sheetStatus('10 more blank rows added','editing');return}
    if(e.target.closest('#saveQuerySheetAll')){await saveAllSheetRows();return}
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

// ===== Web 1.5.0 • reference-style apps menu + configurable live marquee =====
(()=>{
  const toggle=document.getElementById('appsMenuToggle'),menu=document.getElementById('appsMenu'),close=document.getElementById('appsMenuClose');
  function setMenu(open){if(!menu||!toggle)return;menu.hidden=!open;menu.classList.toggle('open',open);toggle.classList.toggle('active',open);toggle.setAttribute('aria-expanded',String(open));document.body.classList.toggle('apps-menu-open',open)}
  toggle?.addEventListener('click',e=>{e.stopPropagation();setMenu(menu.hidden)});close?.addEventListener('click',()=>setMenu(false));menu?.addEventListener('click',e=>{if(e.target.closest('a'))setMenu(false)});
  document.addEventListener('pointerdown',e=>{if(menu&&!menu.hidden&&!menu.contains(e.target)&&!toggle?.contains(e.target))setMenu(false)});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')setMenu(false)});

  const ticker=document.getElementById('liveMarqueeTrack');
  function tickerNode(item){
    const span=document.createElement('span');span.className=`marquee-item tone-${item.tone||'blue'}`;
    span.dataset.label=String(item.label||'live').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
    const label=document.createElement('b');label.textContent=item.label||'Live';span.appendChild(label);span.append(' '+(item.value||'—'));
    if(item.source){const source=document.createElement('small');source.textContent=` · ${item.source}`;span.appendChild(source)}
    if(item.url){const link=document.createElement('a');link.href=item.url;link.target='_blank';link.rel='noopener';link.title='Open source';link.appendChild(span);return link}
    return span;
  }
  function renderTicker(items){
    if(!ticker||!items?.length)return;ticker.replaceChildren();
    for(let copy=0;copy<2;copy++)items.forEach(item=>{ticker.appendChild(tickerNode(item));const gem=document.createElement('i');gem.textContent='◆';ticker.appendChild(gem)});
  }
  async function refreshTicker(){
    if(!ticker)return;let delay=60000;
    try{const r=await fetch('/api/marquee',{credentials:'same-origin',headers:{Accept:'application/json'}}),d=await r.json();if(r.ok&&d.ok){renderTicker(d.items);delay=Math.max(30000,Math.min(600000,(d.refresh_seconds||60)*1000))}}catch(e){console.warn('Live marquee refresh failed',e)}
    window.setTimeout(refreshTicker,delay);
  }
  refreshTicker();
})();

// ===== Web 1.5.3 • login-only mascot welcome, dance and automatic exit =====
(()=>{
  const welcome=document.getElementById('loginMascotWelcome');
  if(!welcome)return;
  const skip=document.getElementById('mascotWelcomeSkip');
  const reduce=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches||livenzaMobilePerformance();
  let danceTimer,leaveTimer,removeTimer,departed=false;

  function depart(){
    if(departed)return;departed=true;
    clearTimeout(danceTimer);clearTimeout(leaveTimer);clearTimeout(removeTimer);
    welcome.classList.remove('is-dancing');welcome.classList.add('is-leaving');
    removeTimer=window.setTimeout(()=>{welcome.remove();window.dispatchEvent(new CustomEvent('livenza:mascot-welcome-done'))},reduce?420:1250);
  }

  requestAnimationFrame(()=>requestAnimationFrame(()=>welcome.classList.add('is-visible')));
  danceTimer=window.setTimeout(()=>{if(!reduce&&!departed)welcome.classList.add('is-dancing')},820);
  leaveTimer=window.setTimeout(depart,reduce?3900:6100);
  skip?.addEventListener('click',depart);
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.body.contains(welcome))depart()},{once:true});
})();

// ===== Web 1.5.5 • persistent live mascot, forecast and weather scenes =====
(()=>{
  const companion=document.getElementById('mascotCompanion');
  if(!companion)return;
  const button=document.getElementById('mascotCompanionButton');
  const panel=document.getElementById('mascotCompanionPanel');
  const close=document.getElementById('mascotCompanionClose');
  const nudge=document.getElementById('mascotCompanionNudge');
  const weatherScene=document.getElementById('livenzaWeatherScene');
  const replay=document.getElementById('companionReplayWeather');
  const nextQuote=document.getElementById('companionNextQuote');
  const modeTabs=[...panel.querySelectorAll('[data-companion-tab]')];
  const modeViews=[...panel.querySelectorAll('[data-companion-view]')];
  const reduce=window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const mobilePerformance=livenzaMobilePerformance();
  let currentCity=companion.dataset.defaultCity||'Gurugram';
  let pulse=null,quoteIndex=0,nudgeIndex=0,nudgeTimer=null,refreshTimer=null,sceneTimer=null;

  function setParked(parked){companion.classList.toggle('is-parked',parked)}
  if(document.getElementById('loginMascotWelcome'))setParked(false);else requestAnimationFrame(()=>setParked(true));
  window.addEventListener('livenza:mascot-welcome-done',()=>setParked(true));

  function setPanel(open,restoreFocus=false){
    if(!panel||!button)return;
    panel.hidden=!open;panel.setAttribute('aria-hidden',String(!open));panel.classList.toggle('open',open);button.setAttribute('aria-expanded',String(open));companion.classList.toggle('panel-open',open);
    if(open){nudge?.classList.remove('show');companion.classList.remove('scroll-collapsed')}else{if(restoreFocus)button.focus();syncCompanionCollapse()}
  }
  function showMode(mode='live',focus=false){
    const chosen=mode==='chat'?'chat':'live';
    modeTabs.forEach(tab=>{const active=tab.dataset.companionTab===chosen;tab.classList.toggle('active',active);tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1});
    modeViews.forEach(view=>{const active=view.dataset.companionView===chosen;view.hidden=!active;view.classList.toggle('active',active)});
    panel.dataset.mode=chosen;if(focus&&chosen==='chat')window.setTimeout(()=>document.getElementById('assistantInput')?.focus(),70);
  }
  modeTabs.forEach(tab=>tab.addEventListener('click',()=>showMode(tab.dataset.companionTab,true)));
  window.LivenzaCompanion={open:(mode='live')=>{setPanel(true);showMode(mode,mode==='chat')},close:()=>setPanel(false,true),showMode};
  showMode('live');
  let scrollFrame=0;
  function syncCompanionCollapse(){companion.classList.toggle('scroll-collapsed',window.scrollY>140&&Boolean(panel?.hidden))}
  window.addEventListener('scroll',()=>{if(scrollFrame)return;scrollFrame=requestAnimationFrame(()=>{scrollFrame=0;syncCompanionCollapse()})},{passive:true});syncCompanionCollapse();
  button?.addEventListener('click',()=>setPanel(panel?.hidden));
  close?.addEventListener('click',()=>setPanel(false,true));
  document.addEventListener('pointerdown',event=>{if(panel&&!panel.hidden&&!companion.contains(event.target))setPanel(false)});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&panel&&!panel.hidden){event.preventDefault();setPanel(false,true)}});

  function weatherIcon(effect,isDay=true){return ({rain:'☂',storm:'ϟ',snow:'❄',fog:'≋',clouds:'☁',sun:'☀',night:'☾'})[effect]||(isDay?'☀':'☾')}
  function forecastDay(date,index){
    if(index===0)return 'Today';
    try{return new Intl.DateTimeFormat('en-IN',{weekday:'short'}).format(new Date(`${date}T12:00:00`))}catch(e){return date||'—'}
  }
  function emptyNode(className,text){const node=document.createElement('div');node.className=className;node.textContent=text;return node}

  function renderLocations(locations=[]){
    const tabs=document.getElementById('companionCityTabs');if(!tabs)return;tabs.replaceChildren();
    locations.forEach(city=>{const item=document.createElement('button');item.type='button';item.textContent=city;item.className=city===currentCity?'active':'';item.addEventListener('click',()=>{if(city===currentCity)return;currentCity=city;loadPulse(city,true)});tabs.appendChild(item)});
  }
  function renderForecast(weather){
    const wrap=document.getElementById('companionForecast');if(!wrap)return;wrap.replaceChildren();
    if(!weather?.forecast?.length){wrap.appendChild(emptyNode('companion-loading','Forecast unavailable'));return}
    weather.forecast.forEach((day,index)=>{const card=document.createElement('div');card.className='companion-forecast-day';const label=document.createElement('small');label.textContent=forecastDay(day.date,index);const icon=document.createElement('span');icon.textContent=weatherIcon(day.effect,true);const temp=document.createElement('b');temp.textContent=`${day.high??'—'}° / ${day.low??'—'}°`;const rain=document.createElement('i');rain.textContent=`${day.rain_chance||0}% rain`;card.append(label,icon,temp,rain);wrap.appendChild(card)});
  }
  function renderOperations(operations=[]){
    const wrap=document.getElementById('companionOperations');if(!wrap)return;wrap.replaceChildren();
    if(!operations.length){wrap.appendChild(emptyNode('companion-loading','Operational pulse unavailable'));return}
    operations.forEach(item=>{const card=document.createElement('div');card.className=`companion-operation tone-${item.tone||'blue'}`;const icon=document.createElement('span');icon.textContent=item.icon||'✦';const copy=document.createElement('div');const label=document.createElement('small');label.textContent=item.label||'Live';const value=document.createElement('b');value.textContent=item.value||'—';copy.append(label,value);card.append(icon,copy);wrap.appendChild(card)});
  }
  function showQuote(index=0){
    const target=document.getElementById('companionQuote');const quotes=pulse?.quotes||[];if(!target||!quotes.length)return;
    quoteIndex=(index+quotes.length)%quotes.length;target.classList.remove('quote-enter');void target.offsetWidth;target.textContent=quotes[quoteIndex];target.classList.add('quote-enter');
  }
  nextQuote?.addEventListener('click',()=>showQuote(quoteIndex+1));

  function nudgeLines(){
    if(!pulse)return[];const lines=[];const weather=pulse.weather;
    if(weather?.available)lines.push(`${weather.city}: ${weather.temperature}° · ${weather.condition}`);
    (pulse.operations||[]).slice(0,3).forEach(item=>lines.push(`${item.label}: ${item.value}`));
    if(pulse.quotes?.length)lines.push(pulse.quotes[quoteIndex%pulse.quotes.length]);
    return lines;
  }
  function showNextNudge(){
    if(!nudge||!panel?.hidden)return;const lines=nudgeLines();if(!lines.length)return;
    const text=nudge.querySelector('span');if(text)text.textContent=lines[nudgeIndex++%lines.length];nudge.classList.add('show');window.setTimeout(()=>nudge.classList.remove('show'),4200);
  }
  function restartNudges(){if(!nudge)return;clearInterval(nudgeTimer);window.setTimeout(showNextNudge,1800);nudgeTimer=window.setInterval(showNextNudge,15000)}

  function clearWeatherScene(){
    clearTimeout(sceneTimer);if(!weatherScene)return;weatherScene.classList.remove('is-active','is-leaving');weatherScene.replaceChildren();weatherScene.removeAttribute('data-effect');document.body.classList.forEach(name=>{if(name.startsWith('weather-tone-'))document.body.classList.remove(name)});
  }
  function sceneParticle(className,styles={}){const node=document.createElement('i');node.className=className;Object.entries(styles).forEach(([key,value])=>node.style.setProperty(key,value));weatherScene?.appendChild(node)}
  function playWeatherScene(effect,seconds=11,force=false){
    if(reduce||!weatherScene||!effect||effect==='none')return;
    const block=Math.floor(new Date().getHours()/3),date=new Date().toISOString().slice(0,10),key=`livenza-weather-${currentCity}-${effect}-${date}-${block}`;
    try{if(!force&&sessionStorage.getItem(key))return;sessionStorage.setItem(key,'1')}catch(e){}
    clearWeatherScene();weatherScene.dataset.effect=effect;document.body.classList.add(`weather-tone-${effect}`);
    if(effect==='rain'||effect==='storm'){
      const count=mobilePerformance?12:72;for(let i=0;i<count;i++)sceneParticle('weather-rain-drop',{'--weather-x':`${Math.random()*100}vw`,'--weather-delay':`${(-Math.random()*2.4).toFixed(2)}s`,'--weather-speed':`${.7+Math.random()*.8}s`,'--weather-length':`${18+Math.random()*36}px`});
      if(!mobilePerformance)for(let i=0;i<4;i++)sceneParticle('weather-cloud',{'--weather-x':`${-12+i*30}vw`,'--weather-delay':`${-i*2.1}s`,'--weather-scale':`${.72+Math.random()*.55}`});
      if(effect==='storm'&&!mobilePerformance)sceneParticle('weather-lightning');
    }else if(effect==='snow'){
      const count=mobilePerformance?10:48;for(let i=0;i<count;i++)sceneParticle('weather-snowflake',{'--weather-x':`${Math.random()*100}vw`,'--weather-delay':`${(-Math.random()*7).toFixed(2)}s`,'--weather-speed':`${5+Math.random()*5}s`,'--weather-size':`${5+Math.random()*9}px`,'--weather-drift':`${-40+Math.random()*80}px`});
    }else if(effect==='fog'){
      if(!mobilePerformance)for(let i=0;i<7;i++)sceneParticle('weather-fog-band',{'--weather-y':`${9+i*13}vh`,'--weather-delay':`${-i*1.3}s`});
    }else if(effect==='clouds'){
      if(!mobilePerformance)for(let i=0;i<7;i++)sceneParticle('weather-cloud',{'--weather-x':`${-18+i*20}vw`,'--weather-delay':`${-i*1.5}s`,'--weather-scale':`${.65+Math.random()*.65}`});
    }else if(effect==='sun'){
      if(!mobilePerformance){sceneParticle('weather-sun-glow');for(let i=0;i<10;i++)sceneParticle('weather-light-speck',{'--weather-x':`${8+Math.random()*84}vw`,'--weather-y':`${12+Math.random()*76}vh`,'--weather-delay':`${-Math.random()*4}s`})}
    }else if(effect==='night'){
      const count=mobilePerformance?8:24;for(let i=0;i<count;i++)sceneParticle('weather-night-star',{'--weather-x':`${Math.random()*100}vw`,'--weather-y':`${Math.random()*72}vh`,'--weather-delay':`${-Math.random()*3}s`});
    }
    requestAnimationFrame(()=>weatherScene.classList.add('is-active'));
    const duration=Math.max(7,Math.min(20,Number(seconds)||11))*1000;
    window.setTimeout(()=>weatherScene.classList.add('is-leaving'),Math.max(1000,duration-1100));sceneTimer=window.setTimeout(clearWeatherScene,duration);
  }
  replay?.addEventListener('click',()=>{if(pulse?.weather?.available)playWeatherScene(pulse.weather.effect,pulse.effect_seconds,true)});

  function renderPulse(data,autoEffect=true){
    pulse=data;const weather=data.weather||{};currentCity=weather.city||currentCity;
    const city=document.getElementById('companionWeatherCity'),temperature=document.getElementById('companionWeatherTemperature'),condition=document.getElementById('companionWeatherCondition'),icon=document.getElementById('companionWeatherIcon'),chip=document.getElementById('mascotWeatherChip');
    if(city)city.textContent=weather.city||currentCity;
    if(temperature)temperature.textContent=weather.available?`${weather.temperature}°`:'—°';
    if(condition)condition.textContent=weather.condition||'Weather unavailable';
    if(icon)icon.textContent=weatherIcon(weather.effect,weather.is_day);
    if(chip)chip.textContent=weather.available?`${weather.temperature}°`:'LIVE';
    const feels=document.getElementById('companionWeatherFeels'),humidity=document.getElementById('companionWeatherHumidity'),wind=document.getElementById('companionWeatherWind'),source=document.getElementById('companionWeatherSource');
    if(feels)feels.textContent=`Feels ${weather.feels_like??'—'}°`;if(humidity)humidity.textContent=`Humidity ${weather.humidity??'—'}%`;if(wind)wind.textContent=`Wind ${weather.wind??'—'} km/h`;if(source)source.textContent=weather.available?'Weather by Open-Meteo':'Weather reconnecting';
    renderLocations(data.locations||[]);renderForecast(weather);renderOperations(data.operations||[]);showQuote(0);restartNudges();
    if(autoEffect&&data.weather_effects&&companion.dataset.weatherEffects!=='0'&&weather.available)playWeatherScene(weather.effect,data.effect_seconds,false);
  }
  async function loadPulse(city=currentCity,autoEffect=true){
    companion.classList.add('is-syncing');clearTimeout(refreshTimer);
    try{const response=await fetch(`/api/companion/pulse?city=${encodeURIComponent(city)}`,{credentials:'same-origin',headers:{Accept:'application/json'}}),data=await response.json();if(!response.ok||!data.ok)throw new Error(data.error||'Pulse unavailable');if(data.enabled===false){companion.hidden=true;return}renderPulse(data,autoEffect);refreshTimer=window.setTimeout(()=>loadPulse(currentCity,false),Math.max(120000,(data.refresh_seconds||600)*1000))}
    catch(error){const condition=document.getElementById('companionWeatherCondition');if(condition)condition.textContent='Live update will reconnect shortly';refreshTimer=window.setTimeout(()=>loadPulse(currentCity,false),120000)}
    finally{companion.classList.remove('is-syncing')}
  }

  const funnyActions=['funny-wave','funny-hop','funny-peek','funny-wobble','funny-celebrate'];
  function performFunnyAction(){if(!panel?.hidden||reduce)return;const choices=mobilePerformance?['funny-wave','funny-wobble']:funnyActions;const action=choices[Math.floor(Math.random()*choices.length)];companion.classList.add(action);window.setTimeout(()=>companion.classList.remove(action),1800)}
  window.setTimeout(performFunnyAction,mobilePerformance?8500:4200);window.setInterval(performFunnyAction,mobilePerformance?30000:10500);
  loadPulse(currentCity,true);
})();
