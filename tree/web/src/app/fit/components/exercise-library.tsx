'use client';

import { useMemo, useState } from 'react';
import { EXERCISES, EXERCISE_CATEGORIES, type ExerciseCategory } from '@/lib/fit/exercises';
import { ExerciseArt } from './exercise-art';
import styles from '../fit.module.css';

export function ExerciseLibrary({ onStart }: { onStart: (id: string) => void }) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<'All' | ExerciseCategory>('All');
  const [selectedId, setSelectedId] = useState(EXERCISES[0].id);
  const selected = EXERCISES.find((item) => item.id === selectedId) ?? EXERCISES[0];
  const filtered = useMemo(() => EXERCISES.filter((item) => (category === 'All' || item.category === category) && `${item.name} ${item.targets.join(' ')} ${item.equipment}`.toLowerCase().includes(query.toLowerCase())), [query, category]);

  return <section className={styles.libraryLayout}>
    <div className={styles.panel}>
      <div className={styles.panelHeader}><div><span className={styles.eyebrow}>36 COACHED MOVEMENTS</span><h2>Exercise Library</h2></div><input className={styles.searchInput} value={query} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setQuery(e.target.value)} placeholder="Search exercise, muscle or equipment" /></div>
      <div className={styles.chipRow}><button className={category==='All'?styles.chipActive:styles.chip} onClick={()=>setCategory('All')}>All</button>{EXERCISE_CATEGORIES.map((item)=><button key={item} className={category===item?styles.chipActive:styles.chip} onClick={()=>setCategory(item)}>{item}</button>)}</div>
      <div className={styles.exerciseGrid}>{filtered.map((item)=><button key={item.id} className={`${styles.exerciseCard} ${selectedId===item.id?styles.exerciseCardActive:''}`} onClick={()=>setSelectedId(item.id)}><ExerciseArt pose={item.illustration.pose} label={item.name}/><span className={styles.cardMeta}>{item.category} · {item.difficulty}</span><strong>{item.name}</strong><small>{item.targets.join(' · ')}</small><span className={styles.presetLine}>{item.defaults.sets} sets × {item.defaults.reps} · {item.defaults.repSeconds}s/rep</span></button>)}</div>
    </div>
    <aside className={`${styles.panel} ${styles.detailPanel}`}><ExerciseArt pose={selected.illustration.pose} label={selected.name}/><span className={styles.eyebrow}>{selected.category} · {selected.difficulty}</span><h2>{selected.name}</h2><p>{selected.overview}</p><div className={styles.detailFacts}><span><b>Targets</b>{selected.targets.join(', ')}</span><span><b>Equipment</b>{selected.equipment}</span><span><b>Preset</b>{selected.defaults.sets} × {selected.defaults.reps}</span><span><b>Rest</b>{selected.defaults.restSeconds}s</span></div><h3>How to do it</h3><ol className={styles.coachSteps}>{selected.steps.map((step)=><li key={step}>{step}</li>)}</ol><h3>Avoid</h3><ul className={styles.cleanList}>{selected.mistakes.map((item)=><li key={item}>{item}</li>)}</ul><div className={styles.safetyNote}>{selected.safety}</div><button className={styles.primaryButton} onClick={()=>onStart(selected.id)}>Start with counter</button></aside>
  </section>;
}
