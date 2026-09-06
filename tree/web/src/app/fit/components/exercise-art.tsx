import styles from '../fit.module.css';

export function ExerciseArt({ pose, label }: { pose: string; label: string }) {
  const isFloor = /push|plank|mountain|cobra|superman|bug|bicycle|cat|book|bridge/.test(pose);
  const isWide = /jack|fly|raise-side|skater/.test(pose);
  const isLunge = /lunge|hip-flexor/.test(pose);
  return (
    <div className={styles.exerciseArt} role="img" aria-label={`${label} exercise illustration`}>
      <svg viewBox="0 0 240 150" aria-hidden="true">
        <defs>
          <linearGradient id={`fit-${pose}`} x1="0" x2="1">
            <stop stopColor="#C7F000" />
            <stop offset="1" stopColor="#00C96B" />
          </linearGradient>
        </defs>
        <circle cx={isFloor ? 55 : 120} cy={isFloor ? 82 : 32} r="13" fill={`url(#fit-${pose})`} />
        {isFloor ? (
          <>
            <path d="M68 86 L112 93 L165 90" className={styles.artLine} />
            <path d="M103 93 L80 122 M112 93 L135 122" className={styles.artLine} />
            <path d="M162 90 L198 110 M162 90 L202 84" className={styles.artLine} />
            <path d="M78 126 H207" className={styles.artGround} />
          </>
        ) : isLunge ? (
          <>
            <path d="M120 46 L118 83" className={styles.artLine} />
            <path d="M118 58 L87 76 M118 58 L150 70" className={styles.artLine} />
            <path d="M118 83 L83 111 L56 113 M118 83 L150 105 L181 127" className={styles.artLine} />
          </>
        ) : (
          <>
            <path d="M120 46 L120 88" className={styles.artLine} />
            <path d={isWide ? 'M120 58 L72 55 M120 58 L168 55' : 'M120 58 L94 78 M120 58 L146 78'} className={styles.artLine} />
            <path d="M120 88 L96 128 M120 88 L144 128" className={styles.artLine} />
          </>
        )}
      </svg>
    </div>
  );
}
