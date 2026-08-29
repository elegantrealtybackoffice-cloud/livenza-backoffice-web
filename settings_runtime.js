(()=>{
  'use strict';
  const root=document.documentElement;
  const KEY='livenza.settings.v2702';
  const PREVIOUS='livenza.settings.v2701';
  const LEGACY='livenza.systemSettings.v190';
  const CUSTOM_WALLPAPER='livenza.wallpaper.custom';
  const DEFAULTS={
    'appearance.mode':'light',
    'appearance.contrast':false,
    'appearance.reduceTransparency':false,
    'accessibility.reduceTransparency':false,
    'accessibility.reduceMotion':false,
    'accessibility.largeText':false,
    'accessibility.focusIndicators':true,
    'focus.enabled':false,
    'focus.companion':true,
    'dock.size':'regular',
    'dock.magnification':true,
    'dock.autohide':false,
    'wallpaper.variant':'livenza-life',
    'wallpaper.fit':'fill',
    'wallpaper.positionX':50,
    'wallpaper.positionY':50,
    'wallpaper.zoom':100,
    'widgets.visible':false,
    'notifications.operational':true,
    'notifications.badges':true,
    'notifications.companion':true,
    'notifications.reminders':true
  };
  const safeParse=(value)=>{try{const parsed=JSON.parse(value||'{}');return parsed&&typeof parsed==='object'&&!Array.isArray(parsed)?parsed:{}}catch(_){return {}}};
  const readStorage=(key)=>{try{return safeParse(localStorage.getItem(key))}catch(_){return {}}};
  const writeStorage=(state)=>{try{localStorage.setItem(KEY,JSON.stringify(state))}catch(_){}};
  const clamp=(value,min,max,fallback)=>{const number=Number(value);return Number.isFinite(number)?Math.max(min,Math.min(max,number)):fallback};
  const asBoolean=(value,fallback=false)=>value===true||value==='true'||value===1||value==='1'?true:value===false||value==='false'||value===0||value==='0'?false:fallback;
  const normalize=(input={})=>{
    const state={...DEFAULTS,...input};
    state['appearance.mode']=state['appearance.mode']==='dark'?'dark':'light';
    state['appearance.contrast']=asBoolean(state['appearance.contrast']);
    state['appearance.reduceTransparency']=asBoolean(state['appearance.reduceTransparency']);
    state['accessibility.reduceTransparency']=asBoolean(state['accessibility.reduceTransparency']);
    state['accessibility.reduceMotion']=asBoolean(state['accessibility.reduceMotion']);
    state['accessibility.largeText']=asBoolean(state['accessibility.largeText']);
    state['accessibility.focusIndicators']=asBoolean(state['accessibility.focusIndicators'],true);
    state['focus.enabled']=asBoolean(state['focus.enabled']);
    state['focus.companion']=asBoolean(state['focus.companion'],true);
    state['dock.size']=['small','regular','large'].includes(state['dock.size'])?state['dock.size']:'regular';
    state['dock.magnification']=asBoolean(state['dock.magnification'],true);
    state['dock.autohide']=asBoolean(state['dock.autohide']);
    state['wallpaper.variant']=String(state['wallpaper.variant']||'livenza-life');
    state['wallpaper.fit']=['fill','fit','stretch','center'].includes(state['wallpaper.fit'])?state['wallpaper.fit']:'fill';
    state['wallpaper.positionX']=clamp(state['wallpaper.positionX'],0,100,50);
    state['wallpaper.positionY']=clamp(state['wallpaper.positionY'],0,100,50);
    state['wallpaper.zoom']=clamp(state['wallpaper.zoom'],80,160,100);
    state['widgets.visible']=asBoolean(state['widgets.visible']);
    for(const key of ['notifications.operational','notifications.badges','notifications.companion','notifications.reminders']) state[key]=asBoolean(state[key],true);
    return state;
  };
  const load=()=>{
    const old=readStorage(LEGACY),previous=readStorage(PREVIOUS),next=readStorage(KEY);
    const legacy={...old,...previous};
    if(!Object.prototype.hasOwnProperty.call(next,'appearance.mode')) delete legacy['appearance.mode'];
    return normalize({...legacy,...next});
  };
  let state=load();
  const applyWallpaper=()=>{
    root.dataset.wallpaper=state['wallpaper.variant'];
    root.dataset.wallpaperFit=state['wallpaper.fit'];
    root.style.setProperty('--wallpaper-position-x',`${state['wallpaper.positionX']}%`);
    root.style.setProperty('--wallpaper-position-y',`${state['wallpaper.positionY']}%`);
    root.style.setProperty('--wallpaper-zoom',String(state['wallpaper.zoom']/100));
    if(state['wallpaper.variant']==='custom'){
      try{const custom=localStorage.getItem(CUSTOM_WALLPAPER)||'';if(custom)root.style.setProperty('--user-wallpaper',`url("${custom.replace(/"/g,'%22')}")`);else root.style.removeProperty('--user-wallpaper')}catch(_){root.style.removeProperty('--user-wallpaper')}
    }else root.style.removeProperty('--user-wallpaper');
  };
  const apply=()=>{
    root.dataset.appearance=state['appearance.mode'];
    root.dataset.dockSize=state['dock.size'];
    root.classList.toggle('settings-increase-contrast',state['appearance.contrast']);
    root.classList.toggle('settings-reduce-transparency',state['appearance.reduceTransparency']||state['accessibility.reduceTransparency']);
    root.classList.toggle('settings-reduce-motion',state['accessibility.reduceMotion']);
    root.classList.toggle('settings-large-text',state['accessibility.largeText']);
    root.classList.toggle('settings-strong-focus',state['accessibility.focusIndicators']);
    root.classList.toggle('focus-mode',state['focus.enabled']);
    root.classList.toggle('focus-hide-companion',state['focus.enabled']&&state['focus.companion']);
    root.classList.toggle('dock-autohide',state['dock.autohide']);
    root.classList.toggle('dock-magnification-off',!state['dock.magnification']);
    root.classList.toggle('notifications-operational-off',!state['notifications.operational']);
    root.classList.toggle('notifications-badges-off',!state['notifications.badges']);
    root.classList.toggle('notifications-companion-off',!state['notifications.companion']);
    root.classList.toggle('notifications-reminders-off',!state['notifications.reminders']);
    applyWallpaper();
    const body=document.body;
    if(body){
      body.dataset.appearance=state['appearance.mode'];
      body.classList.toggle('appearance-dark',state['appearance.mode']==='dark');
      body.classList.toggle('appearance-light',state['appearance.mode']!=='dark');
      body.classList.toggle('settings-focus-mode',state['focus.enabled']);
      body.classList.toggle('focus-hide-companion',state['focus.enabled']&&state['focus.companion']);
      body.classList.toggle('desktop-widgets-hidden',!state['widgets.visible']);
    }
    return {...state};
  };
  const emit=(key)=>{try{window.dispatchEvent(new CustomEvent('livenza:preferences-changed',{detail:{key,state:{...state}}}))}catch(_){}};
  const set=(key,value)=>{state=normalize({...state,[key]:value});writeStorage(state);apply();emit(key);return state[key]};
  const reset=()=>{state=normalize({});writeStorage(state);apply();emit('*');return {...state}};
  const reload=()=>{state=load();apply();emit('*');return {...state}};
  window.LivenzaPreferences={get:(key)=>state[key],getAll:()=>({...state}),set,reset,reload,apply,defaults:{...DEFAULTS}};
  apply();
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});
})();
