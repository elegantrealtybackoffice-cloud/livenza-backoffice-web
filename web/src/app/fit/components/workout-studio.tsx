'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { EXERCISES } from '@/lib/fit/exercises';
import { clampRepSeconds, estimateCalories, workoutDurationSeconds } from '@/lib/fit/engine';
import { STORAGE_KEYS, serializeWorkoutRecord, type WorkoutRecord } from '@/lib/fit/storage';
import { ExerciseArt } from './exercise-art';
import { getFitWorkouts, syncFitWorkout } from '@/lib/api';
import styles from '../fit.module.css';

type Status = 'idle' | 'running' | 'paused' | 'resting' | 'done';

function readHistory(): WorkoutRecord[] {
  if (typeof window === 'undefined') return [];
  try { return JSON.parse(localStorage.getItem(STORAGE_KEYS.workoutHistory) || '[]'); } catch { return []; }
}

export function WorkoutStudio({ selectedId }: { selectedId?: string }) {
  const first = EXERCISES.find((item) => item.id === selectedId) ?? EXERCISES[0];
  const [exerciseId, setExerciseId] = useState(first.id);
  const exercise = useMemo(() => EXERCISES.find((item) => item.id === exerciseId) ?? EXERCISES[0], [exerciseId]);
  const [sets, setSets] = useState(exercise.defaults.sets);
  const [reps, setReps] = useState(exercise.defaults.reps);
  const [repSeconds, setRepSeconds] = useState(exercise.defaults.repSeconds);
  const [restSeconds, setRestSeconds] = useState(exercise.defaults.restSeconds);
  const [currentSet, setCurrentSet] = useState(1);
  const [currentRep, setCurrentRep] = useState(0);
  const [restRemaining, setRestRemaining] = useState(0);
  const [status, setStatus] = useState<Status>('idle');
  const [voiceOn, setVoiceOn] = useState(true);
  const [beepOn, setBeepOn] = useState(true);
  const [history, setHistory] = useState<WorkoutRecord[]>([]);
  const startedAt = useRef<number | null>(null);

  useEffect(() => {
    const local=readHistory();
    setHistory(local);
    void getFitWorkouts().then((remote)=>{
      const mapped=remote.map((item)=>serializeWorkoutRecord({exerciseId:item.exercise_id,exerciseName:item.exercise_name,reps:item.reps,sets:item.sets,repSeconds:item.rep_seconds,durationSeconds:item.duration_seconds,completedAt:item.completed_at}));
      const byKey=new Map([...local,...mapped].map((item)=>[`${item.exerciseId}:${item.completedAt}`,item]));
      const merged=[...byKey.values()].sort((a,b)=>b.completedAt.localeCompare(a.completedAt)).slice(0,30);
      localStorage.setItem(STORAGE_KEYS.workoutHistory,JSON.stringify(merged));
      setHistory(merged);
    }).catch(()=>undefined);
  }, []);
  useEffect(() => {
    if (!selectedId) return;
    const next = EXERCISES.find((item) => item.id === selectedId);
    if (next) selectExercise(next.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  function selectExercise(id: string) {
    const next = EXERCISES.find((item) => item.id === id) ?? EXERCISES[0];
    if (status === 'running' || status === 'resting') return;
    setExerciseId(next.id);
    setSets(next.defaults.sets); setReps(next.defaults.reps); setRepSeconds(next.defaults.repSeconds); setRestSeconds(next.defaults.restSeconds);
    setCurrentSet(1); setCurrentRep(0); setStatus('idle');
  }

  function speak(value: number | string) {
    if (!voiceOn || typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    const utterance = new SpeechSynthesisUtterance(String(value));
    utterance.rate = 1.05; utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  }

  function beep() {
    if (!beepOn || typeof window === 'undefined') return;
    try {
      const AudioContextCtor = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!AudioContextCtor) return;
      const ctx = new AudioContextCtor();
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();
      oscillator.frequency.value = 640; gain.gain.value = 0.04;
      oscillator.connect(gain); gain.connect(ctx.destination); oscillator.start(); oscillator.stop(ctx.currentTime + 0.07);
    } catch { /* visual counter still works */ }
  }

  function saveCompletion() {
    const durationSeconds = startedAt.current ? (Date.now() - startedAt.current) / 1000 : workoutDurationSeconds({ sets, reps, repSeconds, restSeconds });
    const record = serializeWorkoutRecord({ exerciseId: exercise.id, exerciseName: exercise.name, reps, sets, repSeconds, durationSeconds, completedAt: new Date().toISOString() });
    const next = [record, ...readHistory()].slice(0, 30);
    localStorage.setItem(STORAGE_KEYS.workoutHistory, JSON.stringify(next));
    setHistory(next);
    void syncFitWorkout({
      client_record_id:`web:${record.exerciseId}:${record.completedAt}`,
      exercise_id:record.exerciseId,exercise_name:record.exerciseName,sets:record.sets,reps:record.reps,
      rep_seconds:record.repSeconds,duration_seconds:record.durationSeconds,estimated_calories:estimatedCalories,
      source:'livenza_fit_web',completed_at:record.completedAt,
    }).catch(()=>undefined);
  }

  useEffect(() => {
    if (status !== 'running') return;
    const delay = clampRepSeconds(repSeconds) * 1000;
    const timer = window.setTimeout(() => {
      const nextRep = currentRep + 1;
      setCurrentRep(nextRep); beep(); speak(nextRep);
      if (nextRep >= reps) {
        if (currentSet < sets) {
          setRestRemaining(Math.max(0, Math.round(restSeconds)));
          setStatus(restSeconds > 0 ? 'resting' : 'running');
          if (restSeconds <= 0) { setCurrentSet((value) => value + 1); setCurrentRep(0); }
        } else {
          setStatus('done'); saveCompletion(); speak('Complete');
        }
      }
    }, delay);
    return () => window.clearTimeout(timer);
    // deliberate timer state machine dependencies
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, currentRep, currentSet, reps, sets, repSeconds, restSeconds]);

  useEffect(() => {
    if (status !== 'resting') return;
    if (restRemaining <= 0) {
      setCurrentSet((value) => value + 1); setCurrentRep(0); setStatus('running'); speak('Go'); return;
    }
    const timer = window.setTimeout(() => setRestRemaining((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, restRemaining]);

  function start() {
    window.speechSynthesis?.cancel();
    setCurrentSet(1); setCurrentRep(0); setStatus('running'); startedAt.current = Date.now(); speak('Start');
  }

  function stop() {
    window.speechSynthesis?.cancel();
    setStatus('idle'); setCurrentSet(1); setCurrentRep(0); setRestRemaining(0); startedAt.current = null;
  }

  const total = workoutDurationSeconds({ sets, reps, repSeconds, restSeconds });
  const estimatedCalories = estimateCalories(exercise.met, 70, total / 60);

  return (
    <section className={styles.workspaceGrid}>
      <div className={`${styles.panel} ${styles.counterPanel}`}>
        <div className={styles.panelHeader}><div><span className={styles.eyebrow}>SMART COUNTER</span><h2>Workout Studio</h2></div><span className={styles.statusPill}>{status}</span></div>
        <div className={styles.exerciseSelectorRow}>
          <label><span>Exercise</span><select value={exerciseId} onChange={(event: React.ChangeEvent<HTMLSelectElement>) => selectExercise(event.target.value)} disabled={status === 'running' || status === 'resting'}>{EXERCISES.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        </div>
        <div className={styles.counterStage}>
          <ExerciseArt pose={exercise.illustration.pose} label={exercise.name} />
          <div className={styles.counterReadout}>
            <span className={styles.counterLabel}>{status === 'resting' ? 'REST' : `SET ${currentSet} / ${sets}`}</span>
            <strong>{status === 'resting' ? restRemaining : currentRep}</strong>
            <span>{status === 'resting' ? 'seconds' : `/ ${reps} reps`}</span>
          </div>
        </div>
        <div className={styles.controlsGrid}>
          <label>Sets<input type="number" min="1" max="8" value={sets} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSets(Math.max(1, Math.min(8, Number(e.target.value))))} disabled={status !== 'idle' && status !== 'done'} /></label>
          <label>Reps<input type="number" min="1" max="150" value={reps} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setReps(Math.max(1, Math.min(150, Number(e.target.value))))} disabled={status !== 'idle' && status !== 'done'} /></label>
          <label>Sec / rep<input type="number" min="0.5" max="15" step="0.5" value={repSeconds} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRepSeconds(clampRepSeconds(Number(e.target.value)))} disabled={status === 'running'} /></label>
          <label>Rest sec<input type="number" min="0" max="300" value={restSeconds} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRestSeconds(Math.max(0, Math.min(300, Number(e.target.value))))} disabled={status !== 'idle' && status !== 'done'} /></label>
        </div>
        <div className={styles.switchRow}>
          <label><input type="checkbox" checked={voiceOn} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setVoiceOn(e.target.checked)} /> Voice count</label>
          <label><input type="checkbox" checked={beepOn} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setBeepOn(e.target.checked)} /> Rep beep</label>
          <span>≈ {Math.ceil(total / 60)} min · ~{estimatedCalories} kcal @ 70 kg</span>
        </div>
        <div className={styles.actionRow}>
          {(status === 'idle' || status === 'done') && <button className={styles.primaryButton} onClick={start}>Start workout</button>}
          {status === 'running' && <button className={styles.secondaryButton} onClick={() => { setStatus('paused'); window.speechSynthesis?.cancel(); }}>Pause</button>}
          {status === 'paused' && <button className={styles.primaryButton} onClick={() => setStatus('running')}>Resume</button>}
          {status !== 'idle' && <button className={styles.ghostButton} onClick={stop}>Stop</button>}
        </div>
        <p className={styles.safetyNote}>Technique first. Stop for sharp pain, faintness, chest pain, or unusual breathlessness. Presets are general starting points, not medical advice.</p>
      </div>

      <aside className={styles.stack}>
        <div className={styles.panel}><span className={styles.eyebrow}>METHOD</span><h3>{exercise.name}</h3><p className={styles.muted}>{exercise.overview}</p><ol className={styles.coachSteps}>{exercise.steps.map((step) => <li key={step}>{step}</li>)}</ol><div className={styles.warningBox}><strong>Common mistakes</strong>{exercise.mistakes.map((item) => <span key={item}>• {item}</span>)}</div></div>
        <div className={styles.panel}><span className={styles.eyebrow}>RECENT</span><h3>Workout history</h3>{history.length === 0 ? <p className={styles.muted}>Finish a workout and it will appear here.</p> : <div className={styles.historyList}>{history.slice(0,5).map((item) => <div key={item.completedAt}><strong>{item.exerciseName}</strong><span>{item.sets} × {item.reps} · {item.repSeconds}s/rep</span></div>)}</div>}</div>
      </aside>
    </section>
  );
}
