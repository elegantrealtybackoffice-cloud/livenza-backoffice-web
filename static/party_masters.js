(()=>{
  document.querySelectorAll('.master-editor input[name="tags"]').forEach(input=>input.addEventListener('blur',()=>{input.value=input.value.split(',').map(x=>x.trim()).filter(Boolean).join(', ')}));
  document.addEventListener('submit',e=>{
    const form=e.target.closest('[data-master-reauth]');if(!form)return;
    const pwd=window.prompt('Enter your Admin password to access this protected master document.');
    if(!pwd){e.preventDefault();return}
    const field=form.querySelector('input[name="admin_password"]');if(field)field.value=pwd;
  });
})();

(()=>{
  document.addEventListener('click',async e=>{
    const btn=e.target.closest('[data-master-reveal]');if(!btn)return;
    const root=btn.closest('.master-editor')||document;
    const field=root.querySelector('[data-master-reveal-field]')?.value;if(!field)return;
    const adminPassword=window.prompt('Enter your Admin password to reveal this protected value.');if(!adminPassword)return;
    const out=root.querySelector('[data-master-reveal-output]');if(out)out.textContent='Checking…';
    try{
      const r=await fetch(`/agreement-masters/${encodeURIComponent(btn.dataset.kind)}/${btn.dataset.id}/reveal`,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify({fields:[field],admin_password:adminPassword})});
      const d=await r.json().catch(()=>({}));if(!r.ok||!d.ok)throw new Error(d.error||'Re-authentication failed.');
      if(out){out.textContent=d.fields?.[field]||'No value stored';setTimeout(()=>{out.textContent='Masked by default'},15000)}
    }catch(err){if(out)out.textContent=err.message||'Could not reveal value.'}
  });
})();

(()=>{
  const form=document.getElementById('agreementForm');if(!form)return;
  const status=document.getElementById('agreementMasterStatus');
  const say=(message,error=false)=>{if(status){status.textContent=message;status.classList.toggle('danger',error)}};
  const selectFor=kind=>form.querySelector(`[data-agreement-master-select="${kind}"]`);
  const hiddenFor=kind=>document.getElementById(kind==='landlord'?'landlordMasterId':'tenantMasterId');
  const annexureHidden=document.getElementById('annexureDocumentIds');
  const selectedAnnexures=new Set(String(annexureHidden?.value||'').split(',').map(x=>Number.parseInt(x,10)).filter(x=>Number.isInteger(x)&&x>0));
  const loadedAnnexures={landlord:new Set(),tenant:new Set()};
  const syncAnnexureHidden=()=>{if(annexureHidden)annexureHidden.value=[...selectedAnnexures].join(',')};
  async function loadAnnexures(kind,{clearLoaded=false}={}){
    const host=form.querySelector(`[data-annexure-list="${kind}"]`);if(!host)return;
    if(clearLoaded){loadedAnnexures[kind].forEach(id=>selectedAnnexures.delete(id));loadedAnnexures[kind].clear();syncAnnexureHidden()}
    const id=selectFor(kind)?.value;host.replaceChildren();
    if(!id){const note=document.createElement('small');note.textContent=`Choose a ${kind} master to load documents.`;host.appendChild(note);return}
    const loading=document.createElement('small');loading.textContent='Loading protected document references…';host.appendChild(loading);
    try{
      const r=await fetch(`/api/agreement-masters/${kind}/${id}/documents-for-annexure`,{credentials:'same-origin',headers:{Accept:'application/json'}}),d=await r.json().catch(()=>({}));
      if(!r.ok||!d.ok)throw new Error(d.error||'Could not load document references.');host.replaceChildren();
      if(!(d.documents||[]).length){const note=document.createElement('small');note.textContent='No active documents stored for this master.';host.appendChild(note);return}
      d.documents.forEach(doc=>{loadedAnnexures[kind].add(Number(doc.id));const label=document.createElement('label');label.className='annexure-document-option';const input=document.createElement('input');input.type='checkbox';input.value=String(doc.id);input.checked=selectedAnnexures.has(Number(doc.id));input.addEventListener('change',()=>{if(input.checked)selectedAnnexures.add(Number(doc.id));else selectedAnnexures.delete(Number(doc.id));syncAnnexureHidden()});const text=document.createElement('span');const title=document.createElement('b');title.textContent=doc.display_label||doc.category||'Supporting document';const detail=document.createElement('small');detail.textContent=`${String(doc.extension||'').toUpperCase()} · ${doc.verification_status||'unverified'}${doc.embeddable?'':' · selected reference only — not embeddable in PDF'}`;text.append(title,detail);label.append(input,text);host.appendChild(label)});
    }catch(err){host.replaceChildren();const note=document.createElement('small');note.className='danger';note.textContent=err.message||'Could not load document references.';host.appendChild(note)}
  }
  const formFields=()=>{const fields={};form.querySelectorAll('[name]').forEach(el=>{if(el.type==='file'||el.type==='password'||el.type==='submit')return;fields[el.name]=el.value??''});return fields};
  async function jsonPost(url,body){const r=await fetch(url,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify(body||{})});const d=await r.json().catch(()=>({}));if(!r.ok||d.ok===false)throw new Error(d.error||`Request failed (${r.status})`);return d}
  function applyAgreementMasterFields(fields,{replace=false}={}){let filled=0,skipped=0;Object.entries(fields||{}).forEach(([name,value])=>{const control=document.querySelector(`#agreementForm [name="${CSS.escape(name)}"]`);if(!control||!String(value||'').trim())return;if(!replace&&String(control.value||'').trim()){skipped++;return}control.value=value;control.dispatchEvent(new Event('input',{bubbles:true}));filled++});return {filled,skipped}}
  window.applyAgreementMasterFields=applyAgreementMasterFields;
  form.querySelectorAll('[data-agreement-master-select]').forEach(select=>select.addEventListener('change',()=>{const kind=select.dataset.agreementMasterSelect,hidden=hiddenFor(kind);if(hidden)hidden.value=select.value||'';loadAnnexures(kind,{clearLoaded:true})}));
  ['landlord','tenant'].forEach(kind=>loadAnnexures(kind));
  form.querySelectorAll('[data-agreement-master-apply]').forEach(btn=>btn.addEventListener('click',async()=>{const kind=btn.dataset.agreementMasterApply,select=selectFor(kind),id=select?.value;if(!id){say(`Choose a saved ${kind} master first.`,true);return}const replace=btn.dataset.replace==='1';if(replace&&!confirm(`Replace existing ${kind} agreement values with the selected master?`))return;btn.disabled=true;try{const r=await fetch(`/api/agreement-masters/${kind}/${id}/apply`,{credentials:'same-origin',headers:{Accept:'application/json'}}),d=await r.json();if(!r.ok||!d.ok)throw new Error(d.error||'Could not apply master.');const result=applyAgreementMasterFields(d.fields,{replace});hiddenFor(kind).value=String(id);loadAnnexures(kind);say(`${d.master.name}: ${result.filled} field${result.filled===1?'':'s'} filled${result.skipped?`, ${result.skipped} existing value${result.skipped===1?'':'s'} preserved`:''}.`)}catch(err){say(err.message||'Could not apply master.',true)}finally{btn.disabled=false}}));
  form.querySelectorAll('[data-master-from-agreement]').forEach(btn=>btn.addEventListener('click',async()=>{const kind=btn.dataset.masterFromAgreement,name=prompt(`Name this new ${kind} master profile:`);if(!name)return;btn.disabled=true;try{const d=await jsonPost(`/api/agreement-masters/${kind}/from-agreement`,{profile_name:name,fields:formFields()});const select=selectFor(kind),opt=document.createElement('option');opt.value=d.master.id;opt.textContent=d.master.profile_name;opt.selected=true;select?.appendChild(opt);hiddenFor(kind).value=String(d.master.id);loadAnnexures(kind,{clearLoaded:true});say(d.message||'Master created.')}catch(err){say(err.message,true)}finally{btn.disabled=false}}));
  form.querySelectorAll('[data-master-update-from-agreement]').forEach(btn=>btn.addEventListener('click',async()=>{const kind=btn.dataset.masterUpdateFromAgreement,id=selectFor(kind)?.value;if(!id){say(`Choose the ${kind} master to update first.`,true);return}if(!confirm(`Update the selected ${kind} master using compatible fields from this agreement? Protected data not represented here will be preserved.`))return;btn.disabled=true;try{const d=await jsonPost(`/api/agreement-masters/${kind}/${id}/update-from-agreement`,{fields:formFields()});say(d.message||'Master updated.')}catch(err){say(err.message,true)}finally{btn.disabled=false}}));
})();
