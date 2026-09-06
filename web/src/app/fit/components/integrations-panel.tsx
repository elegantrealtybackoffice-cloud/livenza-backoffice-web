'use client';

import { useEffect, useState } from 'react';
import { connectFitIntegration, getFitIntegrations, type FitIntegration } from '@/lib/api';
import styles from '../fit.module.css';

const integrations=[
  {provider:'health_connect',name:'Google Fit / Health Connect',status:'Android companion',copy:'Modern Android sync uses Health Connect permissions through an Android companion, then syncs only authorized summaries to Livenza.'},
  {provider:'samsung_health',name:'Samsung Health',status:'Android companion + partner setup',copy:'Samsung Health Data SDK requires an eligible Android/Samsung Health environment. The web app never reads the local health database directly.'},
  {provider:'apple_health',name:'Apple Health + Apple Watch',status:'iOS/watchOS companion',copy:'HealthKit access stays on Apple platforms under user permission. The companion sends only the data you authorize.'},
  {provider:'fitbit',name:'Fitbit',status:'OAuth adapter',copy:'Fitbit cloud data uses user-authorized OAuth. Access and refresh tokens stay server-side in protected integration storage.'},
];
export function IntegrationsPanel(){
  const[connections,setConnections]=useState<FitIntegration[]>([]);const[busy,setBusy]=useState('');const[msg,setMsg]=useState('');
  useEffect(()=>{void getFitIntegrations().then(setConnections).catch(()=>undefined)},[]);
  async function connect(provider:string){setBusy(provider);setMsg('');try{const result=await connectFitIntegration(provider);setConnections(items=>[...items.filter(item=>item.provider!==provider),result]);setMsg(result.status==='requires_companion'?'Companion connection is ready to be completed on the supported device.':'Connection started.');}catch{setMsg('This provider needs its production adapter/credentials configured in the Livenza Integrations Center.');}finally{setBusy('');}}
  return <section className={styles.panel}><div className={styles.panelHeader}><div><span className={styles.eyebrow}>WEARABLE HUB</span><h2>Connected fitness</h2></div><span className={styles.statusPill}>privacy first</span></div><div className={styles.integrationGrid}>{integrations.map((item)=>{const saved=connections.find(connection=>connection.provider===item.provider);return <article key={item.provider} className={styles.integrationCard}><div className={styles.integrationIcon}>↻</div><div><strong>{item.name}</strong><span className={styles.connectorStatus}>{saved?.status||item.status}</span><p>{item.copy}</p></div><button className={styles.secondaryButton} disabled={busy===item.provider} onClick={()=>void connect(item.provider)}>{busy===item.provider?'Connecting…':saved?.status==='requires_companion'?'Companion required':'Connect'}</button></article>})}</div>{msg&&<p className={styles.connectorStatus}>{msg}</p>}<p className={styles.safetyNote}>No integration is shown as connected until the real provider/native authorization succeeds. Browser source and localStorage never receive provider client secrets or refresh tokens.</p></section>
}
