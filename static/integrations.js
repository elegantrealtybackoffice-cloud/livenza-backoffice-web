(function(){
  'use strict';
  function qs(s,r){return (r||document).querySelector(s)}
  function qsa(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))}
  qsa('[data-safe-tabs]').forEach(function(tablist){
    tablist.addEventListener('keydown',function(ev){
      if(ev.key!=='ArrowLeft'&&ev.key!=='ArrowRight')return;
      var items=qsa('a,button',tablist); if(!items.length)return;
      var i=items.indexOf(document.activeElement); if(i<0)i=0;
      i=(i+(ev.key==='ArrowRight'?1:-1)+items.length)%items.length; items[i].focus(); ev.preventDefault();
    });
  });
})();
