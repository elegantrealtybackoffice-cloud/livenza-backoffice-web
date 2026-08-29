(()=>{
  'use strict';
  const prefs=window.LivenzaPreferences;
  if(!prefs)return;
  const $=(selector,root=document)=>root.querySelector(selector);
  const $$=(selector,root=document)=>[...root.querySelectorAll(selector)];
  const root=document.querySelector('[data-system-settings]');
  if(!root)return;

  const coerce=(el)=>el.type==='checkbox'?el.checked:el.type==='range'?Number(el.value):el.value;
  const formatOutput=(key,value)=>{
    if(['wallpaper.zoom','wallpaper.positionX','wallpaper.positionY'].includes(key))return `${value}%`;
    return String(value??'');
  };
  const sync=()=>{
    $$('[data-pref]',root).forEach(el=>{
      const value=prefs.get(el.dataset.pref);
      if(el.type==='checkbox')el.checked=Boolean(value);
      else if(value!==undefined&&value!==null)el.value=String(value);
    });
    $$('[data-pref-button]',root).forEach(btn=>btn.setAttribute('aria-pressed',String(prefs.get(btn.dataset.prefButton)===btn.dataset.value)));
    $$('[data-pref-output]',root).forEach(out=>{const key=out.dataset.prefOutput;out.textContent=formatOutput(key,prefs.get(key))});
    $$('[data-wallpaper-value]',root).forEach(btn=>{
      const active=prefs.get('wallpaper.variant')===btn.dataset.wallpaperValue;
      btn.setAttribute('aria-checked',String(active));btn.classList.toggle('selected',active);
    });
  };

  root.addEventListener('change',event=>{
    const el=event.target.closest?.('[data-pref]');
    if(el)prefs.set(el.dataset.pref,coerce(el));
  });
  root.addEventListener('input',event=>{
    const el=event.target.closest?.('input[type="range"][data-pref]');
    if(el)prefs.set(el.dataset.pref,coerce(el));
  });
  root.addEventListener('click',event=>{
    const button=event.target.closest?.('[data-pref-button]');
    if(button){event.preventDefault();prefs.set(button.dataset.prefButton,button.dataset.value);return}
    const wallpaper=event.target.closest?.('[data-wallpaper-value]');
    if(wallpaper&&wallpaper.dataset.wallpaperValue!=='custom'){event.preventDefault();prefs.set('wallpaper.variant',wallpaper.dataset.wallpaperValue);return}
    const resetWidgets=event.target.closest?.('[data-reset-widgets]');
    if(resetWidgets){event.preventDefault();prefs.set('widgets.visible',false)}
  });
  window.addEventListener('livenza:preferences-changed',sync);
  sync();

  const search=$('#settingsSearch',root);
  const filterSettings=()=>{
    const query=(search?.value||'').trim().toLowerCase();
    $$('[data-settings-search]',root).forEach(item=>{item.hidden=Boolean(query)&&!String(item.dataset.settingsSearch||item.textContent||'').toLowerCase().includes(query)});
    $$('.settings-nav-group',root).forEach(group=>{
      let next=group.nextElementSibling,visible=false;
      while(next&&!next.classList.contains('settings-nav-group')){if(next.matches?.('[data-settings-search]')&&!next.hidden)visible=true;next=next.nextElementSibling}
      group.hidden=Boolean(query)&&!visible;
    });
  };
  search?.addEventListener('input',filterSettings);
  search?.addEventListener('keydown',event=>{if(event.key==='Escape'){search.value='';filterSettings();search.blur()}});
  document.addEventListener('keydown',event=>{if((event.metaKey||event.ctrlKey)&&event.key.toLowerCase()==='f'&&search){event.preventDefault();search.focus();search.select()}});

  const sidebar=$('#systemSettingsSidebar',root),toggle=$('#settingsNavToggle',root);
  toggle?.addEventListener('click',()=>{const open=!sidebar?.classList.contains('is-open');sidebar?.classList.toggle('is-open',open);toggle.setAttribute('aria-expanded',String(open))});

  const network=$('[data-network-diagnostics]',root);
  if(network){
    const set=(selector,text,tone='')=>{const el=$(selector,network);if(!el)return;el.textContent=text;el.classList.remove('semantic-success','semantic-warning','semantic-danger');if(tone)el.classList.add(tone)};
    const browserFacts=()=>{
      set('[data-network-online]',navigator.onLine?'Online':'Offline',navigator.onLine?'semantic-success':'semantic-danger');
      const connection=navigator.connection||navigator.mozConnection||navigator.webkitConnection;
      set('[data-network-effective-type]',connection?.effectiveType?String(connection.effectiveType).toUpperCase():'Not available in this browser');
      set('[data-network-downlink]',Number.isFinite(connection?.downlink)?`${connection.downlink} Mbps`:'Not available in this browser');
      set('[data-network-rtt]',Number.isFinite(connection?.rtt)?`${connection.rtt} ms`:'Not available in this browser');
      set('[data-network-secure]',window.isSecureContext?'Secure (HTTPS)':'Not secure',window.isSecureContext?'semantic-success':'semantic-warning');
      set('[data-network-revision]',network.dataset.revision||document.body?.dataset.buildRevision||'Unknown');
    };
    let controller=null;
    const refreshBackend=async()=>{
      controller?.abort();controller=new AbortController();
      const timeout=setTimeout(()=>controller.abort(),5000);
      set('[data-network-backend]','Checking…');
      try{
        const response=await fetch('/health/db',{cache:'no-store',headers:{Accept:'application/json'},signal:controller.signal});
        const data=await response.json();
        if(!response.ok||!data?.ok)throw new Error('health');
        const latency=Number(data.latency_ms);
        set('[data-network-backend]',Number.isFinite(latency)?`Healthy · ${Math.round(latency)} ms`:'Healthy','semantic-success');
        if(data.revision)set('[data-network-revision]',String(data.revision));
      }catch(_){set('[data-network-backend]','Backend health unavailable','semantic-warning')}
      finally{clearTimeout(timeout)}
    };
    const refresh=()=>{browserFacts();refreshBackend()};
    $('[data-network-refresh]',network)?.addEventListener('click',refresh);
    window.addEventListener('online',browserFacts);window.addEventListener('offline',browserFacts);
    requestAnimationFrame(()=>setTimeout(refresh,0));
  }
})();
