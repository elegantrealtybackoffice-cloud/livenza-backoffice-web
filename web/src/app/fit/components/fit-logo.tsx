import Image from 'next/image';
import styles from '../fit.module.css';

export function FitLogo() {
  return (
    <div className={styles.logoWrap} aria-label="livenza.fit">
      <Image src="/brand/livenza-fit-logo.png" alt="livenza.fit" width={280} height={85} priority className={styles.logo} />
      <span className={styles.logoTag}>FITNESS OS</span>
    </div>
  );
}
