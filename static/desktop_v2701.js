(() => {
  'use strict';

  const body = document.body;
  const dock = document.getElementById('macDock');

  const setDockScale = (event) => {
    if (!dock || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const x = event.clientX;
    dock.querySelectorAll('.mac-dock-item').forEach((item) => {
      const rect = item.getBoundingClientRect();
      const center = rect.left + rect.width / 2;
      const distance = Math.abs(x - center);
      const influence = Math.max(0, 1 - distance / 94);
      item.style.setProperty('--dock-scale', (1 + influence * 0.26).toFixed(3));
    });
  };

  const resetDockScale = () => {
    dock?.querySelectorAll('.mac-dock-item').forEach((item) => item.style.removeProperty('--dock-scale'));
  };

  if (dock) {
    dock.addEventListener('pointermove', setDockScale, {passive: true});
    dock.addEventListener('pointerleave', resetDockScale, {passive: true});
    dock.addEventListener('wheel', (event) => {
      if (Math.abs(event.deltaY) > Math.abs(event.deltaX) && dock.scrollWidth > dock.clientWidth) {
        dock.scrollLeft += event.deltaY;
        event.preventDefault();
      }
    }, {passive: false});
  }

  if (body?.dataset.page !== 'dashboard') return;

  const byId = (id) => document.getElementById(id);
  const homeCurrentTime = byId('homeCurrentTime');
  const homeCurrentDate = byId('homeCurrentDate');
  const homeDateNumber = byId('homeDateNumber');
  const homeDayName = byId('homeDayName');
  const homeWeatherTemperature = byId('homeWeatherTemperature');
  const homeWeatherCity = byId('homeWeatherCity');
  const homeWeatherCondition = byId('homeWeatherCondition');
  const homeWeatherRange = byId('homeWeatherRange');
  const operationPrimary = byId('homeOperationPrimary');
  const operationPrimaryValue = byId('homeOperationPrimaryValue');
  const operationSecondary = byId('homeOperationSecondary');
  const operationSecondaryValue = byId('homeOperationSecondaryValue');

  const updateClock = () => {
    const now = new Date();
    if (homeCurrentTime) homeCurrentTime.textContent = now.toLocaleTimeString([], {hour: 'numeric', minute: '2-digit'});
    if (homeCurrentDate) homeCurrentDate.textContent = now.toLocaleDateString([], {weekday: 'short', month: 'short', day: 'numeric'});
    if (homeDateNumber) homeDateNumber.textContent = String(now.getDate());
    if (homeDayName) homeDayName.textContent = now.toLocaleDateString([], {weekday: 'long'});
  };

  const renderPulse = (data) => {
    const weather = data?.weather || {};
    if (homeWeatherCity) homeWeatherCity.textContent = weather.city || 'Gurugram';
    if (homeWeatherTemperature) homeWeatherTemperature.textContent = Number.isFinite(Number(weather.temperature)) ? `${Math.round(Number(weather.temperature))}°` : '—°';
    if (homeWeatherCondition) homeWeatherCondition.textContent = weather.condition || 'Live weather unavailable';
    const today = Array.isArray(weather.forecast) ? weather.forecast[0] : null;
    if (homeWeatherRange) {
      const high = Number.isFinite(Number(today?.high)) ? `${Math.round(Number(today.high))}°` : '—°';
      const low = Number.isFinite(Number(today?.low)) ? `${Math.round(Number(today.low))}°` : '—°';
      homeWeatherRange.textContent = `H:${high}  L:${low}`;
    }

    const operations = Array.isArray(data?.operations) ? data.operations : [];
    const first = operations[0];
    const second = operations[1];
    if (first) {
      if (operationPrimary) operationPrimary.textContent = first.label || 'Live operations';
      if (operationPrimaryValue) operationPrimaryValue.textContent = `${first.value ?? '—'} · Live now`;
    }
    if (second) {
      if (operationSecondary) operationSecondary.textContent = second.label || 'Workspace';
      if (operationSecondaryValue) operationSecondaryValue.textContent = `${second.value ?? '—'} · Current status`;
    }
  };

  const loadHomePulse = async () => {
    try {
      const response = await fetch('/api/companion/pulse', {credentials: 'same-origin', headers: {Accept: 'application/json'}});
      const data = await response.json();
      if (!response.ok || !data?.ok) throw new Error(data?.error || 'Pulse unavailable');
      renderPulse(data);
    } catch (error) {
      if (homeWeatherCondition) homeWeatherCondition.textContent = 'Live weather will reconnect shortly';
      if (operationPrimaryValue) operationPrimaryValue.textContent = 'Live status reconnecting…';
    }
  };

  document.querySelectorAll('[data-home-companion-open]').forEach((control) => {
    control.addEventListener('click', () => {
      const companionButton = byId('mascotCompanionButton');
      if (companionButton) companionButton.click();
    });
  });

  updateClock();
  window.setInterval(updateClock, 30_000);
  loadHomePulse();
  window.setInterval(loadHomePulse, 120_000);
})();
