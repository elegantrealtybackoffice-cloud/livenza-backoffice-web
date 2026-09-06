'use client';
import styles from '../fit.module.css';
const plans=[
  {name:'Foundation 3×',level:'Beginner',days:'Mon · Wed · Fri',sessions:['Squat + Push-Up','Row + Glute Bridge','Lunge + Core'],copy:'Three balanced full-body days with generous recovery.'},
  {name:'Strength 4×',level:'Intermediate',days:'Mon · Tue · Thu · Sat',sessions:['Upper Push','Lower Strength','Upper Pull','Lower + Core'],copy:'Upper/lower split with progressive rep targets.'},
  {name:'Condition 5×',level:'Intermediate',days:'5 flexible days',sessions:['Strength','Intervals','Mobility','Strength','Cardio'],copy:'Mixed strength, conditioning and mobility for general fitness.'},
  {name:'Move Daily',level:'All levels',days:'Daily 15–25 min',sessions:['Mobility','Walk/Cardio','Core','Recovery'],copy:'Low-friction daily movement with intensity managed across the week.'},
];
export function PlansPanel({onStart}:{onStart:()=>void}){return <section className={styles.panel}><div className={styles.panelHeader}><div><span className={styles.eyebrow}>PROGRAMS</span><h2>Training Plans</h2></div><button className={styles.primaryButton} onClick={onStart}>Quick start workout</button></div><div className={styles.planGrid}>{plans.map(plan=><article key={plan.name} className={styles.planCard}><span className={styles.cardMeta}>{plan.level}</span><h3>{plan.name}</h3><p>{plan.copy}</p><strong>{plan.days}</strong><ul className={styles.cleanList}>{plan.sessions.map(s=><li key={s}>{s}</li>)}</ul><button className={styles.secondaryButton} onClick={onStart}>Use plan</button></article>)}</div></section>}
