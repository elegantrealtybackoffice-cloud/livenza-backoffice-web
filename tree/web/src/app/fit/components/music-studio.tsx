'use client';

import { useRef, useState } from 'react';
import styles from '../fit.module.css';

const moods = ['Warm-up Flow','Strength Mode','HIIT Energy','Run Tempo','Mobility Calm','Cooldown'];

export function MusicStudio() {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [trackName,setTrackName]=useState('No local track loaded');
  const [query,setQuery]=useState('');
  function load(event: React.ChangeEvent<HTMLInputElement>){ const file=event.target.files?.[0]; if(!file||!audioRef.current)return; audioRef.current.src=URL.createObjectURL(file); setTrackName(file.name); void audioRef.current.play(); }
  function openProvider(provider:'spotify'|'youtube'|'apple'){ const q=encodeURIComponent(query||'workout playlist'); const urls={spotify:`https://open.spotify.com/search/${q}`,youtube:`https://music.youtube.com/search?q=${q}`,apple:`https://music.apple.com/us/search?term=${q}`}; window.open(urls[provider],'_blank','noopener,noreferrer'); }
  return <section className={styles.workspaceGrid}><div className={styles.panel}><span className={styles.eyebrow}>OFFLINE PLAYER</span><h2>Music Studio</h2><div className={styles.nowPlaying}><div className={styles.albumOrb}>♪</div><div><small>NOW PLAYING</small><strong>{trackName}</strong><span>Local files remain available offline.</span></div></div><input type="file" accept="audio/*" onChange={load}/><audio ref={audioRef} controls className={styles.audioPlayer}/><p className={styles.muted}>During voice counting, browser speech is prioritized. A production media adapter can add automatic volume ducking where the provider permits it.</p><h3>Curated intents</h3><div className={styles.chipRow}>{moods.map(m=><button key={m} className={styles.chip} onClick={()=>setQuery(m)}>{m}</button>)}</div></div><aside className={styles.panel}><span className={styles.eyebrow}>ONLINE MUSIC</span><h3>Tell Livenza what to play</h3><input className={styles.searchInput} value={query} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setQuery(e.target.value)} placeholder="Song, artist or workout playlist"/><div className={styles.providerButtons}><button onClick={()=>openProvider('spotify')}>Search Spotify</button><button onClick={()=>openProvider('youtube')}>Search YouTube Music</button><button onClick={()=>openProvider('apple')}>Search Apple Music</button></div><p className={styles.safetyNote}>Full in-app streaming needs the user’s provider account plus each platform’s approved playback API/SDK. This build never bypasses provider subscriptions or permissions.</p></aside></section>;
}
