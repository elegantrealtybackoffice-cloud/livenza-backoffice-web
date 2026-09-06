'use client';

import { useEffect, useState } from 'react';
import { calculateBmi, classifyBmi } from '@/lib/fit/engine';
import { normalizeHealthLog, STORAGE_KEYS, type HealthLog } from '@/lib/fit/storage';
import { getFitHealthLogs, syncFitHealthLog } from '@/lib/api';
import styles from '../fit.module.css';

type SavedHealthLog = HealthLog & { at: string };

export function HealthDashboard() {
  const [weight, setWeight] = useState(70);
  const [height, setHeight] = useState(175);
  const [steps, setSteps] = useState(0);
  const [activity, setActivity] = useState(0);
  const [heartRate, setHeartRate] = useState(0);
  const [logs, setLogs] = useState<SavedHealthLog[]>([]);
  useEffect(()=>{
    let local:SavedHealthLog[]=[];
    try { local=JSON.parse(localStorage.getItem(STORAGE_KEYS.healthLogs)||'[]'); setLogs(local); } catch {}
    void getFitHealthLogs().then((remote)=>{
      const mapped=remote.filter(item=>item.weight_kg&&item.height_cm).map(item=>({weightKg:Number(item.weight_kg),heightCm:Number(item.height_cm),steps:item.steps??undefined,activityMinutes:item.activity_minutes??undefined,restingHeartRate:item.resting_heart_rate??undefined,at:item.recorded_at}));
      const byAt=new Map([...local,...mapped].map(item=>[item.at,item]));
      const merged=[...byAt.values()].sort((a,b)=>b.at.localeCompare(a.at)).slice(0,60);
      localStorage.setItem(STORAGE_KEYS.healthLogs,JSON.stringify(merged));setLogs(merged);
    }).catch(()=>undefined);
  },[]);
  const bmi = calculateBmi(weight,height);
  function save(){ const normalized=normalizeHealthLog({weightKg:weight,heightCm:height,steps,activityMinutes:activity,restingHeartRate:heartRate||undefined}); if(!normalized)return; const at=new Date().toISOString(); const next=[{...normalized,at},...logs].slice(0,60); localStorage.setItem(STORAGE_KEYS.healthLogs,JSON.stringify(next)); setLogs(next); void syncFitHealthLog({recorded_at:at,weight_kg:normalized.weightKg,height_cm:normalized.heightCm,steps:normalized.steps,activity_minutes:normalized.activityMinutes,resting_heart_rate:normalized.restingHeartRate,source:'manual'}).catch(()=>undefined); }
  return <section className={styles.workspaceGrid}><div className={styles.panel}><span className={styles.eyebrow}>HEALTH SNAPSHOT</span><h2>Body & Activity</h2><div className={styles.metricHero}><div><strong>{bmi ?? '—'}</strong><span>BMI</span><small>{bmi ? classifyBmi(bmi).replace('-', ' ') : 'Add valid height & weight'}</small></div><div><strong>{steps.toLocaleString()}</strong><span>steps</span><small>manual or wearable sync</small></div><div><strong>{activity}</strong><span>active min</span><small>today</small></div><div><strong>{heartRate || '—'}</strong><span>bpm</span><small>resting HR</small></div></div><div className={styles.formGrid}><label>Weight (kg)<input type="number" value={weight} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setWeight(Number(e.target.value))}/></label><label>Height (cm)<input type="number" value={height} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setHeight(Number(e.target.value))}/></label><label>Steps<input type="number" value={steps} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setSteps(Number(e.target.value))}/></label><label>Activity minutes<input type="number" value={activity} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setActivity(Number(e.target.value))}/></label><label>Resting heart rate<input type="number" value={heartRate} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setHeartRate(Number(e.target.value))}/></label></div><button className={styles.primaryButton} onClick={save}>Save health log</button><p className={styles.safetyNote}>BMI is a broad screening calculation and does not measure body composition or diagnose health. Wearable values can also vary by device.</p></div><aside className={styles.panel}><span className={styles.eyebrow}>TREND</span><h3>Recent logs</h3>{logs.length===0?<p className={styles.muted}>No local health logs yet.</p>:<div className={styles.historyList}>{logs.slice(0,8).map(log=><div key={log.at}><strong>{log.weightKg} kg · {calculateBmi(log.weightKg,log.heightCm) ?? '—'} BMI</strong><span>{log.steps?.toLocaleString()||0} steps · {log.activityMinutes||0} active min</span></div>)}</div>}</aside></section>;
}
