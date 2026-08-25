(()=>{
  const state=document.getElementById('electricityProviderState'),provider=document.getElementById('electricityProviderSelect');
  if(state&&provider){const options=[...provider.options].slice(1);const apply=()=>{const s=state.value;options.forEach(o=>o.hidden=Boolean(s&&o.dataset.state!==s));if(provider.selectedOptions[0]?.hidden)provider.value=''};state.addEventListener('change',apply);apply()}
  const table=document.getElementById('electricityRegisterTable'),search=document.getElementById('electricityRegisterSearch'),status=document.getElementById('electricityRegisterStatus');
  if(table){const rows=[...table.querySelectorAll('tbody tr')];const filter=()=>{const q=(search?.value||'').trim().toLowerCase(),s=(status?.value||'').trim();rows.forEach(row=>{const matchText=!q||(row.dataset.search||row.textContent.toLowerCase()).includes(q),matchStatus=!s||row.dataset.status===s;row.hidden=!(matchText&&matchStatus)})};search?.addEventListener('input',filter);status?.addEventListener('change',filter)}
})();
