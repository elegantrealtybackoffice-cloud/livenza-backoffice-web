'use client';

import { useEffect } from 'react';

export function PwaBoot() {
  useEffect(() => {
    if (!('serviceWorker' in navigator)) return;
    const register = () => { void navigator.serviceWorker.register('/fit-sw.js', { scope: '/fit' }); };
    if (document.readyState === 'complete') register();
    else window.addEventListener('load', register, { once: true });
    return () => window.removeEventListener('load', register);
  }, []);
  return null;
}
