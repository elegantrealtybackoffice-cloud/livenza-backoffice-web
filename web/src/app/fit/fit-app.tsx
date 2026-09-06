'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { EXERCISES } from '@/lib/fit/exercises';
import { calculateBmi } from '@/lib/fit/engine';
import { STORAGE_KEYS } from '@/lib/fit/storage';
import { verifyPin, type PinCredential } from '@/lib/fit/pin';
import { FitLogo } from './components/fit-logo';
import { WorkoutStudio } from './components/workout-studio';
import { ExerciseLibrary } from './components/exercise-library';
import { HealthDashboard } from './components/health-dashboard';
import { MusicStudio } from './components/music-studio';
import { IntegrationsPanel } from './components/integrations-panel';
import { PlansPanel } from './components/plans-panel';
import { ProfilePanel } from './components/profile-panel';
import { LivePanel } from './components/live-panel';
import { PwaBoot } from './components/pwa-boot';
import styles from './fit.module.css';

type Tab='Today'|'Workout'|'Exercises'|'Plans'|'Health'|'Music'|'Live'|'Wearables'|'Profile';
const tabs: {label:Tab;icon:string}[]=[{label:'Today',icon:'⌂'},{label:'Workout',icon:'▶'},{label:'Exercises',icon:'◫'},{label:'Plans',icon:'▦'},{label:'Health',icon:'♥'},{label:'Music',icon:'♫'},{label:'Live',icon:'●'},{label:'Wearables',icon:'⌁'},{label:'Profile',icon:'◉'}];

function TodayPanel({start}:{start:(id?:string)=>void}){
  const [summary,setSummary]=useState({workouts:0,weight:0,height:0,steps:0});
  useEffect(()=>{try{const workouts=JSON.parse(localStorage.getItem(STORAGE_KEYS.workoutHistory)||'[]');const health=JSON.parse(localStorage.getItem(STORAGE_KEYS.healthLogs)||'[]');const latest=health[0]||{};setSummary({workouts:workouts.length,weight:latest.weightKg||0,height:latest.heightCm||0,steps:latest.steps||0});}catch{}},[]);
  const bmi=summary.weight&&summary.height?calculateBmi(summary.weight,summary.height):null;
  return <><section className={styles.hero}><div><span className={styles.eyebrow}>TRAIN · TRACK · RECOVER</span><h1>Your fitness,<br/><em>in one place.</em></h1><p>Offline counters and coaching when you need focus. Connected health, music, video and live sessions when you’re online.</p><div className={styles.actionRow}><button className={styles.primaryButton} onClick={()=>start('push-up')}>Start Push-Ups</button><button className={styles.secondaryButton} onClick={()=>start('jumping-jack')}>150 Jumping Jacks</button></div></div><div className={styles.heroDial}><span>READY</span><strong>92</strong><small>training score*</small></div></section><section className={styles.metricStrip}><div><span>Workouts saved</span><strong>{summary.workouts}</strong><small>on this device</small></div><div><span>Steps</span><strong>{summary.steps.toLocaleString()}</strong><small>latest log</small></div><div><span>BMI</span><strong>{bmi??'—'}</strong><small>latest local log</small></div><div><span>Exercise library</span><strong>{EXERCISES.length}</strong><small>coached movements</small></div></section><section className={styles.todayGrid}><article className={styles.panel}><span className={styles.eyebrow}>QUICK START</span><h2>Move now</h2><div className={styles.quickGrid}>{['push-up','bodyweight-squat','jumping-jack','forearm-plank'].map(id=>{const ex=EXERCISES.find(e=>e.id===id)!;return <button key={id} onClick={()=>start(id)}><strong>{ex.name}</strong><span>{ex.defaults.sets} × {ex.defaults.reps} · {ex.defaults.repSeconds}s/rep</span></button>})}</div></article><article className={styles.panel}><span className={styles.eyebrow}>CONNECTED MODE</span><h2>One health view</h2><p>Health Connect, Samsung Health, Apple Health/Watch and Fitbit are designed as permission-based adapters. Livenza.fit shows only what you authorize.</p><div className={styles.miniBars}><i style={{height:'45%'}}/><i style={{height:'62%'}}/><i style={{height:'55%'}}/><i style={{height:'84%'}}/><i style={{height:'72%'}}/><i style={{height:'92%'}}/><i style={{height:'68%'}}/></div><small>*Demo readiness score in this patch; production score needs real recovery/activity data.</small></article></section></>;
}

function LockScreen({onUnlock}:{onUnlock:()=>void}){const[pin,setPin]=useState('');const[error,setError]=useState('');async function unlock(){try{const raw=localStorage.getItem(STORAGE_KEYS.pinCredential);if(!raw){onUnlock();return;}const ok=await verifyPin(pin,JSON.parse(raw) as PinCredential);if(ok){setPin('');onUnlock();}else setError('Incorrect PIN');}catch{setError('Unable to verify local PIN.');}}return <div className={styles.lockScreen}><div className={styles.lockCard}><FitLogo/><span className={styles.eyebrow}>DEVICE LOCKED</span><h2>Welcome back</h2><p>Enter your Livenza.fit PIN.</p><input autoFocus type="password" inputMode="numeric" value={pin} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setPin(e.target.value.replace(/\D/g,'').slice(0,8))} onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>)=>{if(e.key==='Enter')void unlock();}} placeholder="••••"/><button className={styles.primaryButton} onClick={()=>void unlock()}>Unlock</button>{error&&<span className={styles.errorText}>{error}</span>}</div></div>}

export function FitApp(){
  const[tab,setTab]=useState<Tab>('Today'); const[selectedId,setSelectedId]=useState<string|undefined>(undefined); const[locked,setLocked]=useState(false); const[hasPin,setHasPin]=useState(false);
  useEffect(()=>{const hp=Boolean(localStorage.getItem(STORAGE_KEYS.pinCredential));setHasPin(hp);setLocked(hp);},[]);
  const start=useCallback((id?:string)=>{if(id)setSelectedId(id);setTab('Workout');},[]);
  const body=useMemo(()=>{switch(tab){case'Today':return <TodayPanel start={start}/>;case'Workout':return <WorkoutStudio selectedId={selectedId}/>;case'Exercises':return <ExerciseLibrary onStart={start}/>;case'Plans':return <PlansPanel onStart={()=>start('bodyweight-squat')}/>;case'Health':return <HealthDashboard/>;case'Music':return <MusicStudio/>;case'Live':return <LivePanel/>;case'Wearables':return <IntegrationsPanel/>;case'Profile':return <ProfilePanel onLock={()=>setLocked(true)} onSecurityChange={setHasPin}/>;}},[tab,selectedId,start]);
  if(locked)return <main className={styles.appShell}><LockScreen onUnlock={()=>setLocked(false)}/></main>;
  return <main className={styles.appShell} data-brand="fit"><PwaBoot/><header className={styles.topbar}><FitLogo/><div className={styles.topActions}><span className={styles.onlineDot}/> <span>Offline-ready</span>{hasPin&&<button onClick={()=>setLocked(true)}>Lock</button>}</div></header><div className={styles.appBody}><nav className={styles.sideNav} aria-label="Livenza Fit"><span className={styles.navCaption}>FITNESS</span>{tabs.map(item=><button key={item.label} className={tab===item.label?styles.navActive:styles.navButton} onClick={()=>setTab(item.label)}><i>{item.icon}</i><span>{item.label}</span></button>)}</nav><div className={styles.content}>{body}</div></div><footer className={styles.fitFooter}>livenza.fit · live elevated · offline when you need it, connected when you want it</footer></main>;
}
