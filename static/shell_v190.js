(()=>{
  'use strict';
  const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const body=document.body;
  const palette=$('#macCommandPalette'), search=$('#macGlobalSearch'), results=$('#macCommandResults');
  const openButtons=$$('[data-mac-command-open]');
  let lastFocus=null, activeIndex=0;

  const back=$('#macHistoryBack'), forward=$('#macHistoryForward');
  back?.addEventListener('click',()=>history.length>1?history.back():location.assign('/'));
  forward?.addEventListener('click',()=>history.forward());

  function visibleItems(){return results?$$('[data-command-item]:not([hidden])',results):[]}
  function paintActive(next){
    const items=visibleItems(); if(!items.length)return;
    activeIndex=Math.max(0,Math.min(next,items.length-1));
    items.forEach((item,i)=>item.classList.toggle('is-active',i===activeIndex));
    items[activeIndex]?.scrollIntoView({block:'nearest'});
  }
  function filterCommands(){
    const q=(search?.value||'').trim().toLowerCase();
    $$('[data-command-item]',results||document).forEach(item=>{
      const hay=((item.dataset.commandLabel||'')+' '+(item.dataset.commandKeywords||'')).toLowerCase();
      item.hidden=!!q&&!hay.includes(q);
    });
    paintActive(0);
  }
  function openPalette(){
    if(!palette)return; lastFocus=document.activeElement; palette.hidden=false; palette.setAttribute('aria-hidden','false'); body.classList.add('mac-command-open');
    if(search){search.value='';filterCommands();requestAnimationFrame(()=>search.focus())}
  }
  function closePalette(){
    if(!palette)return; palette.hidden=true; palette.setAttribute('aria-hidden','true'); body.classList.remove('mac-command-open');
    const restore=lastFocus; lastFocus=null; if(restore&&typeof restore.focus==='function')restore.focus();
  }
  openButtons.forEach(b=>b.addEventListener('click',openPalette));
  $('#macCommandClose')?.addEventListener('click',closePalette);
  palette?.addEventListener('click',e=>{if(e.target===palette)closePalette()});
  search?.addEventListener('input',filterCommands);
  search?.addEventListener('keydown',e=>{
    const items=visibleItems();
    if(e.key==='ArrowDown'){e.preventDefault();paintActive(activeIndex+1)}
    else if(e.key==='ArrowUp'){e.preventDefault();paintActive(activeIndex-1)}
    else if(e.key==='Enter'&&items[activeIndex]){e.preventDefault();items[activeIndex].click()}
    else if(e.key==='Escape'){e.preventDefault();e.stopPropagation();closePalette()}
  });
  document.addEventListener('keydown',e=>{
    if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();palette?.hidden?openPalette():closePalette()}
    else if(e.key==='Escape'){
      if(palette&&!palette.hidden)closePalette();
      else if($('#macInspector')&&!$('#macInspector').hidden)closeInspector();
    }
  });

  const inspector=$('#macInspector'), inspectorTemplate=$('#macInspectorTemplate'), shellBody=$('.mac-shell-body');
  function inspectorHasContent(){
    if(!inspectorTemplate)return false;
    const clone=inspectorTemplate.content.cloneNode(true);
    const text=(clone.textContent||'').trim();
    return !!text||!!clone.querySelector('*');
  }
  function hydrateInspector(){
    if(!inspector||!inspectorTemplate||!inspectorHasContent())return;
    const target=$('.mac-inspector-inner',inspector); if(!target)return;
    target.append(inspectorTemplate.content.cloneNode(true));
    inspector.hidden=false; inspector.setAttribute('aria-hidden','false'); shellBody?.classList.add('has-inspector');
  }
  function closeInspector(){if(!inspector)return;inspector.hidden=true;inspector.setAttribute('aria-hidden','true');shellBody?.classList.remove('has-inspector')}
  $('#macInspectorClose')?.addEventListener('click',closeInspector);
  $$('[data-mac-inspector-open]').forEach(b=>b.addEventListener('click',()=>{if(inspector){inspector.hidden=false;inspector.setAttribute('aria-hidden','false');shellBody?.classList.add('has-inspector')}}));
  hydrateInspector();

  // Keep shell state sane across page cache/network restores.
  const suitesDock=$('[data-suites-dock]');
  suitesDock?.addEventListener('click',()=>{suitesDock.classList.remove('is-launching');void suitesDock.offsetWidth;suitesDock.classList.add('is-launching');setTimeout(()=>suitesDock.classList.remove('is-launching'),460)});
  window.addEventListener('pageshow',()=>{if(palette&&!palette.hidden)closePalette()});
  window.LivenzaMacShell={openPalette,closePalette,openInspector:()=>{if(inspector){inspector.hidden=false;shellBody?.classList.add('has-inspector')}},closeInspector};
})();
