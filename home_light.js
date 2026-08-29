(()=>{
  'use strict';
  const $=(q,r=document)=>r.querySelector(q), $$=(q,r=document)=>Array.from(r.querySelectorAll(q));
  const body=document.body;
  const prefs=window.LivenzaPreferences;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  const setHidden=(el,hidden)=>{if(!el)return;el.hidden=hidden;el.setAttribute('aria-hidden',hidden?'true':'false')};

  const drawer=$('#appsDrawer'), backdrop=$('#appsMenuBackdrop');
  const setDrawer=(open)=>{if(!drawer)return;setHidden(drawer,!open);setHidden(backdrop,!open);$$('[data-suites-dock]').forEach(b=>b.setAttribute('aria-expanded',open?'true':'false'));};
  if(drawer){$$('[data-suites-dock]').forEach(b=>b.addEventListener('click',e=>{e.preventDefault();setDrawer(drawer.hidden!==false)}));}
  $('[data-drawer-close]')?.addEventListener('click',()=>setDrawer(false));backdrop?.addEventListener('click',()=>setDrawer(false));

  $$('.app-category-tabs [data-tv-target]').forEach(tab=>tab.addEventListener('click',()=>{
    const target=tab.dataset.tvTarget; const host=tab.closest('.application-groups');
    $$('.app-category-tabs button',host).forEach(b=>{const on=b===tab;b.classList.toggle('active',on);b.setAttribute('aria-selected',on?'true':'false')});
    $$('.app-category-panel',host).forEach(p=>{p.hidden=p.dataset.tvPanel!==target;p.classList.toggle('active',!p.hidden)});
  }));

  const closeMenus=()=>$$('.desktop-menu-popover').forEach(m=>m.hidden=true);
  $$('[data-window-menu-trigger]').forEach(btn=>btn.addEventListener('click',e=>{const menu=$(`[data-window-menu="${btn.dataset.windowMenuTrigger}"]`);if(!menu)return;e.preventDefault();e.stopPropagation();const open=menu.hidden;closeMenus();menu.hidden=!open;}));
  document.addEventListener('click',e=>{if(!e.target.closest('.desktop-menu-popover')&&!e.target.closest('[data-window-menu-trigger]'))closeMenus()});

  const widgetStack=$('.home-widget-stack');
  const setWidgets=(show)=>{body.classList.toggle('desktop-widgets-hidden',!show);$$('[data-home-widgets-toggle]').forEach(b=>b.setAttribute('aria-pressed',show?'true':'false'));if(prefs)prefs.set('widgets.visible',show)};
  if(widgetStack){$$('[data-home-widgets-toggle]').forEach(b=>b.addEventListener('click',e=>{e.preventDefault();setWidgets(body.classList.contains('desktop-widgets-hidden'))}));if(prefs)setWidgets(Boolean(prefs.get('widgets.visible')));}
  $$('[data-home-command="toggle-widgets"]').forEach(b=>b.addEventListener('click',()=>{setWidgets(body.classList.contains('desktop-widgets-hidden'));closeMenus()}));
  $$('[data-home-command="fullscreen"]').forEach(b=>b.addEventListener('click',async()=>{closeMenus();try{if(!document.fullscreenElement)await document.documentElement.requestFullscreen();else await document.exitFullscreen()}catch(_){}}));

  const companion=$('.home-companion-panel');
  const setCompanion=(open)=>{if(companion)companion.hidden=!open;};
  if(companion){$$('[data-home-companion-open]').forEach(b=>b.addEventListener('click',e=>{e.preventDefault();setCompanion(companion.hidden!==false)}));}
  $('[data-home-companion-close]')?.addEventListener('click',()=>setCompanion(false));

  const palette=$('#macCommandPalette'), search=$('#macGlobalSearch');
  const setPalette=(open)=>{if(!palette)return;setHidden(palette,!open);if(open){search?.focus();search?.select()}else if(search){search.value='';$$('[data-command-item]',palette).forEach(a=>a.hidden=false)}};
  if(palette){$$('[data-mac-command-open]').forEach(b=>b.addEventListener('click',e=>{e.preventDefault();setPalette(true)}));}$('#macCommandClose')?.addEventListener('click',()=>setPalette(false));palette?.addEventListener('click',e=>{if(e.target===palette)setPalette(false)});
  search?.addEventListener('input',()=>{const q=search.value.trim().toLowerCase();$$('[data-command-item]',palette).forEach(a=>a.hidden=!!q&&!`${a.dataset.commandLabel||''} ${a.dataset.commandKeywords||''}`.toLowerCase().includes(q))});

  const dateEl=$('#homeCurrentDate'),timeEl=$('#homeCurrentTime');
  const paintClock=()=>{const d=new Date();if(dateEl)dateEl.textContent=d.toLocaleDateString(undefined,{weekday:'short',month:'short',day:'numeric'});if(timeEl)timeEl.textContent=d.toLocaleTimeString(undefined,{hour:'numeric',minute:'2-digit'})};paintClock();const clockTimer=setInterval(paintClock,30000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)paintClock()});

  const dock=$('#macDock'),items=$$('.mac-dock-item',dock);let frame=0,pointerX=null;
  const resetDock=()=>items.forEach(i=>{i.style.setProperty('--dock-scale','1');i.style.setProperty('--dock-lift','0px')});
  const paintDock=()=>{frame=0;if(pointerX===null||reduced||document.documentElement.classList.contains('dock-magnification-off')){resetDock();return}items.forEach(item=>{const r=item.getBoundingClientRect(),c=r.left+r.width/2,d=Math.abs(pointerX-c),influence=Math.max(0,1-d/100),scale=1+influence*.26,lift=-Math.round(influence*9);item.style.setProperty('--dock-scale',scale.toFixed(3));item.style.setProperty('--dock-lift',`${lift}px`)})};
  if(dock&&!reduced){dock.addEventListener('pointermove',e=>{pointerX=e.clientX;if(!frame)frame=requestAnimationFrame(paintDock)},{passive:true});dock.addEventListener('pointerleave',()=>{pointerX=null;if(!frame)frame=requestAnimationFrame(paintDock)})}
  window.addEventListener('livenza:preferences-changed',()=>{if(prefs){setWidgets(Boolean(prefs.get('widgets.visible')))}resetDock();pointerX=null});

  document.addEventListener('keydown',e=>{if(e.key==='Escape'){setDrawer(false);setPalette(false);setCompanion(false);closeMenus()}if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();setPalette(true)}});
  document.documentElement.dataset.homeRuntime='ready';
  document.documentElement.classList.remove('home-runtime-failed');
  window.addEventListener('pagehide',()=>clearInterval(clockTimer),{once:true});
})();
