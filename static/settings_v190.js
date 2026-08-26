(()=>{
  'use strict';
  const root=document.querySelector('[data-system-settings]'); if(!root)return;
  const STORE='livenza.systemSettings.v190';
  const safeRead=()=>{try{return JSON.parse(localStorage.getItem(STORE)||'{}')||{}}catch(_){return {}}};
  const safeWrite=data=>{try{localStorage.setItem(STORE,JSON.stringify(data))}catch(_){}};
  let prefs=safeRead();
  const search=root.querySelector('#settingsSearch');
  const navItems=[...root.querySelectorAll('[data-settings-search]')];
  function filterNav(){const q=(search?.value||'').trim().toLowerCase();navItems.forEach(el=>{const hay=(el.dataset.settingsSearch||el.textContent||'').toLowerCase();el.hidden=!!q&&!hay.includes(q)})}
  search?.addEventListener('input',filterNav);
  search?.addEventListener('keydown',e=>{if(e.key==='Escape'){search.value='';filterNav();search.blur()}});
  const toggle=root.querySelector('#settingsNavToggle');
  const setNav=open=>{root.classList.toggle('settings-nav-open',!!open);toggle?.setAttribute('aria-expanded',String(!!open))};
  toggle?.addEventListener('click',()=>setNav(!root.classList.contains('settings-nav-open')));
  navItems.forEach(a=>a.addEventListener('click',()=>setNav(false)));

  function apply(){
    const luminance=Math.max(70,Math.min(115,Number(prefs['display.luminance']??100)))/100;
    document.documentElement.style.setProperty('--livenza-ui-luminance',String(luminance));
    document.body.style.filter=`brightness(${luminance})`;
    document.body.classList.toggle('settings-focus-mode',!!prefs['focus.enabled']);
    document.documentElement.classList.toggle('settings-reduce-transparency',!!(prefs['appearance.reduceTransparency']||prefs['accessibility.reduceTransparency']));
    document.documentElement.classList.toggle('settings-reduce-motion',!!prefs['accessibility.reduceMotion']);
    document.documentElement.classList.toggle('settings-large-text',!!prefs['accessibility.largeText']);
    root.querySelectorAll('[data-pref]').forEach(el=>{const key=el.dataset.pref;if(el.type==='checkbox')el.checked=!!prefs[key];else if(prefs[key]!=null)el.value=prefs[key]});
    root.querySelectorAll('[data-pref-button]').forEach(el=>el.classList.toggle('selected',prefs[el.dataset.prefButton]===el.dataset.value));
    root.querySelectorAll('[data-widget-key]').forEach(card=>{const key=card.dataset.widgetKey;const input=card.querySelector('input[type="checkbox"]');if(input)input.checked=prefs.widgets?.[key]!==false});
  }
  root.addEventListener('change',e=>{
    const el=e.target.closest('[data-pref]'); if(el){const key=el.dataset.pref;prefs[key]=el.type==='checkbox'?el.checked:el.value;safeWrite(prefs);apply();return}
    const widget=e.target.closest('[data-widget-key]'); if(widget&&e.target.matches('input[type="checkbox"]')){prefs.widgets=prefs.widgets||{};prefs.widgets[widget.dataset.widgetKey]=e.target.checked;safeWrite(prefs)}
  });
  root.addEventListener('click',e=>{
    const choice=e.target.closest('[data-pref-button]'); if(choice){prefs[choice.dataset.prefButton]=choice.dataset.value;safeWrite(prefs);apply();return}
    if(e.target.closest('[data-reset-widgets]')){prefs.widgets={};safeWrite(prefs);apply();return}
    if(e.target.closest('[data-reset-local-prefs]')){const widgets=prefs.widgets||{};prefs={widgets};safeWrite(prefs);apply()}
  });
  window.addEventListener('resize',()=>{if(innerWidth>=900)setNav(false)});
  apply();
  window.LivenzaSystemSettings={getPreferences:()=>({...prefs}),reset:()=>{prefs={};safeWrite(prefs);apply()},setNav};
})();
