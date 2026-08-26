(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const root = document.documentElement;
  const body = document.body;
  const PREF_KEY = 'livenza.settings.v2701';
  const OLD_PREF_KEY = 'livenza.systemSettings.v190';
  const CUSTOM_WALLPAPER_KEY = 'livenza.wallpaper.custom';
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');

  function safeParse(value) {
    try { return JSON.parse(value || '{}') || {}; } catch (_) { return {}; }
  }
  function readPreferences() {
    try {
      return {...safeParse(localStorage.getItem(OLD_PREF_KEY)), ...safeParse(localStorage.getItem(PREF_KEY))};
    } catch (_) { return {}; }
  }
  function writePreferences(prefs) {
    try { localStorage.setItem(PREF_KEY, JSON.stringify(prefs)); } catch (_) {}
  }
  const DEFAULT_PREFERENCES = {
    'appearance.mode':'light',
    'dock.size':'regular',
    'dock.magnification':true,
    'dock.autohide':false,
    'control.search':true,
    'control.companion':true,
    'control.display':true,
    'control.fullscreen':true,
    'focus.enabled':false,
    'focus.companion':true
  };
  let preferences = {...DEFAULT_PREFERENCES, ...readPreferences()};

  function setRootPreferenceClasses() {
    const mode = ['light', 'dark'].includes(preferences['appearance.mode']) ? preferences['appearance.mode'] : 'light';
    root.dataset.appearance = mode;
    root.classList.toggle('settings-increase-contrast', Boolean(preferences['appearance.contrast']));
    root.classList.toggle('settings-reduce-transparency', Boolean(preferences['appearance.reduceTransparency'] || preferences['accessibility.reduceTransparency']));
    root.classList.toggle('settings-reduce-motion', Boolean(preferences['accessibility.reduceMotion']));
    root.classList.toggle('settings-large-text', Boolean(preferences['accessibility.largeText']));
    const focusEnabled = Boolean(preferences['focus.enabled']);
    body.classList.toggle('settings-focus-mode', focusEnabled);
    body.classList.toggle('focus-hide-companion', focusEnabled && preferences['focus.companion'] !== false);
    body.classList.toggle('hide-control-search', preferences['control.search'] === false);
    body.classList.toggle('hide-control-companion', preferences['control.companion'] === false);
    body.classList.toggle('hide-control-display', preferences['control.display'] === false);
    body.classList.toggle('hide-control-fullscreen', preferences['control.fullscreen'] === false);
    root.dataset.dockSize = ['small','regular','large'].includes(preferences['dock.size']) ? preferences['dock.size'] : 'regular';
    root.classList.toggle('dock-autohide', Boolean(preferences['dock.autohide']));
  }

  function applyWallpaper(value, persist = true) {
    const allowed = new Set(['aurora', 'spectrum', 'sequoia', 'midnight', 'livenza-blue', 'violet-glass', 'ocean', 'sunrise', 'custom']);
    const desktop = $('.mac-desktop-home');
    const transitionLayer = $('#wallpaperTransitionLayer');
    if (desktop && transitionLayer && !reduceMotion.matches && !root.classList.contains('settings-reduce-motion')) {
      transitionLayer.style.backgroundImage = getComputedStyle(desktop).backgroundImage;
      transitionLayer.classList.remove('is-fading');
      transitionLayer.hidden = false;
      void transitionLayer.offsetWidth;
      transitionLayer.classList.add('is-fading');
      window.setTimeout(() => { transitionLayer.hidden = true; transitionLayer.classList.remove('is-fading'); transitionLayer.style.removeProperty('background-image'); }, 280);
    }
    let next = allowed.has(value) ? value : 'aurora';
    let custom = '';
    if (next === 'custom') {
      try { custom = localStorage.getItem(CUSTOM_WALLPAPER_KEY) || ''; } catch (_) {}
      if (!custom) next = 'aurora';
    }
    root.dataset.wallpaper = next;
    if (custom) root.style.setProperty('--user-wallpaper', `url("${custom.replace(/"/g, '%22')}")`);
    else if (next !== 'custom') root.style.removeProperty('--user-wallpaper');
    if (persist) {
      preferences['wallpaper.variant'] = next;
      writePreferences(preferences);
    }
    $$('[data-wallpaper-value]').forEach((choice) => {
      const selected = choice.dataset.wallpaperValue === next;
      choice.setAttribute('aria-checked', String(selected));
      choice.classList.toggle('selected', selected);
    });
    const preview = $('.wallpaper-custom');
    if (preview && custom) preview.style.backgroundImage = `url("${custom.replace(/"/g, '%22')}")`;
    return next;
  }

  async function resizeWallpaperFile(file) {
    if (!file || !file.type.startsWith('image/')) throw new Error('Choose a JPEG, PNG, WebP or AVIF image.');
    if (file.size > 18 * 1024 * 1024) throw new Error('Choose an image smaller than 18 MB.');
    const url = URL.createObjectURL(file);
    try {
      const image = await new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error('The selected image could not be read.'));
        img.src = url;
      });
      const maxSide = 2560;
      const scale = Math.min(1, maxSide / Math.max(image.naturalWidth || 1, image.naturalHeight || 1));
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
      canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
      const context = canvas.getContext('2d', {alpha: false});
      if (!context) throw new Error('Wallpaper processing is unavailable in this browser.');
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      let quality = .88;
      let data = canvas.toDataURL('image/jpeg', quality);
      while (data.length > 2_600_000 && quality > .54) {
        quality -= .08;
        data = canvas.toDataURL('image/jpeg', quality);
      }
      if (data.length > 3_200_000) throw new Error('This image is too large to save as a browser wallpaper.');
      return data;
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  setRootPreferenceClasses();
  applyWallpaper(preferences['wallpaper.variant'] || root.dataset.wallpaper || 'aurora', false);
  function applySharedSuiteDesign(scope) {
    if (!scope || body?.dataset.page === 'dashboard' && scope.id === 'appMain') return;
    scope.classList.add('app-standard-page');
    $$('.page-head', scope).forEach((node) => node.classList.add('app-standard-header'));
    $$('.page-head > div:first-child', scope).forEach((node) => node.classList.add('app-standard-heading'));
    $$('.page-head > .actions, .page-head-actions, .section-head > .actions, .letterhead-hero-actions', scope).forEach((node) => node.classList.add('app-standard-actions'));
    $$('.safe-tabs, .banking-subnav, .food-subnav, .letterhead-tabs', scope).forEach((node) => node.classList.add('app-standard-tabs'));
    $$('.section-head, .banking-panel-head, .query-sheet-head, .letterhead-page-head', scope).forEach((node) => node.classList.add('app-standard-section-head'));
    $$(`.liquid-card, .form-card, .table-card, .review-card, .banking-panel, .query-card, .master-card,
       .screen-card, .portal-card, .connection-card, .letterhead-card, .settings-card`, scope).forEach((node) => {
      if (!node.matches('.paper, .letterhead-review-paper, .letterhead-preview-paper')) node.classList.add('app-standard-card');
    });
    $$('.table-card, .provider-directory-table, .electricity-sheet-wrap, .query-sheet-wrap', scope).forEach((node) => node.classList.add('app-standard-table'));
    $$('form.bank-upload-form, form.reconcile-form, .form-card > form, form.form-grid', scope).forEach((node) => node.classList.add('app-standard-form'));
  }


  if (body?.dataset.page !== 'dashboard') applySharedSuiteDesign(document.getElementById('appMain'));

  /* ---------- Drawers ---------- */
  const backdrop = $('#appsMenuBackdrop');
  const drawers = $$('.apps-drawer');
  let drawerFocus = null;
  function setDrawer(drawer, open, restoreFocus = false) {
    if (!drawer) return;
    if (open) {
      drawers.forEach((other) => { if (other !== drawer) setDrawer(other, false); });
      drawerFocus = document.activeElement;
      drawer.hidden = false;
      drawer.setAttribute('aria-hidden', 'false');
      requestAnimationFrame(() => drawer.classList.add('is-open'));
      if (backdrop) {
        backdrop.hidden = false;
        requestAnimationFrame(() => backdrop.classList.add('is-open'));
      }
      $$(`[data-drawer-target="${drawer.id}"]`).forEach((trigger) => trigger.setAttribute('aria-expanded', 'true'));
    } else {
      drawer.classList.remove('is-open');
      drawer.setAttribute('aria-hidden', 'true');
      $$(`[data-drawer-target="${drawer.id}"]`).forEach((trigger) => trigger.setAttribute('aria-expanded', 'false'));
      window.setTimeout(() => { if (!drawer.classList.contains('is-open')) drawer.hidden = true; }, 280);
      if (!drawers.some((other) => other !== drawer && other.classList.contains('is-open')) && backdrop) {
        backdrop.classList.remove('is-open');
        window.setTimeout(() => { if (!backdrop.classList.contains('is-open')) backdrop.hidden = true; }, 180);
      }
      if (restoreFocus && drawerFocus?.focus) drawerFocus.focus();
    }
  }
  $$('[data-drawer-target]').forEach((trigger) => trigger.addEventListener('click', (event) => {
    const drawer = document.getElementById(trigger.dataset.drawerTarget);
    if (!drawer) return;
    event.preventDefault();
    setDrawer(drawer, !drawer.classList.contains('is-open'));
  }));
  $$('[data-drawer-close]').forEach((button) => button.addEventListener('click', () => setDrawer(button.closest('.apps-drawer'), false, true)));
  backdrop?.addEventListener('click', () => drawers.forEach((drawer) => setDrawer(drawer, false)));

  /* ---------- Command palette ---------- */
  const palette = $('#macCommandPalette');
  const commandSearch = $('#macGlobalSearch');
  const commandResults = $('#macCommandResults');
  let commandFocus = null;
  let commandIndex = 0;
  const visibleCommands = () => commandResults ? $$('[data-command-item]:not([hidden])', commandResults) : [];
  function setCommandIndex(index) {
    const items = visibleCommands();
    if (!items.length) return;
    commandIndex = Math.max(0, Math.min(index, items.length - 1));
    items.forEach((item, itemIndex) => item.classList.toggle('is-active', itemIndex === commandIndex));
    items[commandIndex]?.scrollIntoView({block: 'nearest'});
  }
  function filterCommands() {
    const query = (commandSearch?.value || '').trim().toLowerCase();
    $$('[data-command-item]', commandResults || document).forEach((item) => {
      const haystack = `${item.dataset.commandLabel || ''} ${item.dataset.commandKeywords || ''}`.toLowerCase();
      item.hidden = Boolean(query && !haystack.includes(query));
    });
    setCommandIndex(0);
  }
  function openPalette() {
    if (!palette) return;
    drawers.forEach((drawer) => setDrawer(drawer, false));
    commandFocus = document.activeElement;
    palette.hidden = false;
    palette.setAttribute('aria-hidden', 'false');
    requestAnimationFrame(() => palette.classList.add('is-open'));
    if (commandSearch) {
      commandSearch.value = '';
      filterCommands();
      requestAnimationFrame(() => commandSearch.focus());
    }
  }
  function closePalette(restore = true) {
    if (!palette) return;
    palette.classList.remove('is-open');
    palette.setAttribute('aria-hidden', 'true');
    window.setTimeout(() => { if (!palette.classList.contains('is-open')) palette.hidden = true; }, 220);
    if (restore && commandFocus?.focus) commandFocus.focus();
    commandFocus = null;
  }
  $$('[data-mac-command-open]').forEach((button) => button.addEventListener('click', openPalette));
  $('#macCommandClose')?.addEventListener('click', () => closePalette());
  palette?.addEventListener('click', (event) => { if (event.target === palette) closePalette(); });
  commandSearch?.addEventListener('input', filterCommands);
  commandSearch?.addEventListener('keydown', (event) => {
    const items = visibleCommands();
    if (event.key === 'ArrowDown') { event.preventDefault(); setCommandIndex(commandIndex + 1); }
    else if (event.key === 'ArrowUp') { event.preventDefault(); setCommandIndex(commandIndex - 1); }
    else if (event.key === 'Enter' && items[commandIndex]) { event.preventDefault(); items[commandIndex].click(); }
    else if (event.key === 'Escape') { event.preventDefault(); closePalette(); }
  });

  /* ---------- History / inspector ---------- */
  $('#macHistoryBack')?.addEventListener('click', () => history.length > 1 ? history.back() : location.assign('/'));
  $('#macHistoryForward')?.addEventListener('click', () => history.forward());
  $$('[data-route-window-action]').forEach((control) => control.addEventListener('click', (event) => {
    const action = control.dataset.routeWindowAction;
    if (action === 'reload') { event.preventDefault(); location.reload(); return; }
    if (action === 'minimize') {
      event.preventDefault();
      const home = control.dataset.routeHomeUrl || '/';
      if (history.length > 1 && document.referrer) {
        try { const ref = new URL(document.referrer); if (ref.origin === location.origin) { history.back(); return; } } catch (_) {}
      }
      location.assign(home);
    }
  }));
  const inspector = $('#macInspector');
  const inspectorTemplate = $('#macInspectorTemplate');
  const shellBody = $('.mac-shell-body');
  function closeInspector() {
    if (!inspector) return;
    inspector.hidden = true;
    inspector.setAttribute('aria-hidden', 'true');
    shellBody?.classList.remove('has-inspector');
  }
  if (inspector && inspectorTemplate) {
    const clone = inspectorTemplate.content.cloneNode(true);
    if ((clone.textContent || '').trim() || clone.querySelector('*')) {
      $('.mac-inspector-inner', inspector)?.append(clone);
      inspector.hidden = false;
      inspector.setAttribute('aria-hidden', 'false');
      shellBody?.classList.add('has-inspector');
    }
  }
  $('#macInspectorClose')?.addEventListener('click', closeInspector);

  /* ---------- Dock pointer-distance magnification ---------- */
  const dock = $('#macDock');
  const DOCK_INFLUENCE = 104;
  const DOCK_MAX_SCALE = 1.38;
  let dockCenters = [];
  let dockPointerX = 0;
  let dockFrame = 0;
  function cacheDockCenters() {
    if (!dock) return;
    dockCenters = $$('.mac-dock-item', dock).map((item) => {
      const rect = item.getBoundingClientRect();
      return {item, center: rect.left + rect.width / 2};
    });
  }
  function paintDock() {
    dockFrame = 0;
    if (!dock || reduceMotion.matches || root.classList.contains('settings-reduce-motion') || preferences['dock.magnification'] === false) return;
    for (const point of dockCenters) {
      const distance = Math.abs(dockPointerX - point.center);
      const influence = Math.max(0, 1 - distance / DOCK_INFLUENCE);
      const eased = influence * influence * (3 - 2 * influence);
      point.item.style.setProperty('--dock-scale', (1 + eased * (DOCK_MAX_SCALE - 1)).toFixed(3));
    }
  }
  function scheduleDock(event) {
    dockPointerX = event.clientX;
    if (!dockFrame) dockFrame = requestAnimationFrame(paintDock);
  }
  function resetDock() {
    if (dockFrame) cancelAnimationFrame(dockFrame);
    dockFrame = 0;
    $$('.mac-dock-item', dock || document).forEach((item) => item.style.removeProperty('--dock-scale'));
  }
  if (dock) {
    cacheDockCenters();
    dock.addEventListener('pointerenter', cacheDockCenters, {passive: true});
    dock.addEventListener('pointermove', scheduleDock, {passive: true});
    dock.addEventListener('pointerleave', resetDock, {passive: true});
    dock.addEventListener('wheel', (event) => {
      if (dock.scrollWidth > dock.clientWidth && Math.abs(event.deltaY) > Math.abs(event.deltaX)) {
        dock.scrollLeft += event.deltaY;
        event.preventDefault();
        cacheDockCenters();
      }
    }, {passive: false});
    new ResizeObserver(cacheDockCenters).observe(dock);
  }
  let dockHideTimer = 0;
  document.addEventListener('pointermove', (event) => {
    if (!dock || !root.classList.contains('dock-autohide')) return;
    if (event.clientY >= innerHeight - 10) {
      window.clearTimeout(dockHideTimer);
      dock.classList.add('dock-peek');
    } else if (!dock.matches(':hover')) {
      window.clearTimeout(dockHideTimer);
      dockHideTimer = window.setTimeout(() => dock.classList.remove('dock-peek'), 500);
    }
  }, {passive:true});
  dock?.addEventListener('pointerenter', () => { window.clearTimeout(dockHideTimer); dock.classList.add('dock-peek'); }, {passive:true});
  dock?.addEventListener('pointerleave', () => { if (root.classList.contains('dock-autohide')) dockHideTimer = window.setTimeout(() => dock.classList.remove('dock-peek'), 500); }, {passive:true});

  reduceMotion.addEventListener?.('change', () => { resetDock(); cacheDockCenters(); });

  function applyHomeWidgetPreferences() {
    $$('[data-home-widget]').forEach((widget) => {
      const key = widget.dataset.homeWidget;
      widget.hidden = preferences.widgets?.[key] === false;
    });
  }
  applyHomeWidgetPreferences();

  /* ---------- Settings ---------- */
  const settingsRoot = $('[data-system-settings]');
  function applyPreferenceControls() {
    setRootPreferenceClasses();
    settingsRoot?.querySelectorAll('[data-pref]').forEach((control) => {
      const key = control.dataset.pref;
      if (control.type === 'checkbox') control.checked = Boolean(preferences[key]);
      else if (preferences[key] != null) control.value = preferences[key];
    });
    settingsRoot?.querySelectorAll('[data-pref-button]').forEach((button) => {
      const selected = preferences[button.dataset.prefButton] === button.dataset.value;
      button.classList.toggle('selected', selected);
      button.setAttribute('aria-pressed', String(selected));
    });
    settingsRoot?.querySelectorAll('[data-widget-key]').forEach((card) => {
      const input = $('input[type="checkbox"]', card);
      if (input) input.checked = preferences.widgets?.[card.dataset.widgetKey] !== false;
    });
    applyWallpaper(preferences['wallpaper.variant'] || 'aurora', false);
  }
  if (settingsRoot) {
    const settingsSearch = $('#settingsSearch', settingsRoot);
    const navItems = $$('[data-settings-search]', settingsRoot);
    const navToggle = $('#settingsNavToggle', settingsRoot);
    const filterSettings = () => {
      const query = (settingsSearch?.value || '').trim().toLowerCase();
      navItems.forEach((item) => {
        const haystack = (item.dataset.settingsSearch || item.textContent || '').toLowerCase();
        item.hidden = Boolean(query && !haystack.includes(query));
      });
    };
    settingsSearch?.addEventListener('input', filterSettings);
    settingsSearch?.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') { settingsSearch.value = ''; filterSettings(); settingsSearch.blur(); }
    });
    const setSettingsNav = (open) => {
      settingsRoot.classList.toggle('settings-nav-open', Boolean(open));
      navToggle?.setAttribute('aria-expanded', String(Boolean(open)));
    };
    navToggle?.addEventListener('click', () => setSettingsNav(!settingsRoot.classList.contains('settings-nav-open')));
    navItems.forEach((item) => item.addEventListener('click', () => setSettingsNav(false)));

    settingsRoot.addEventListener('change', async (event) => {
      const pref = event.target.closest?.('[data-pref]');
      if (pref) {
        preferences[pref.dataset.pref] = pref.type === 'checkbox' ? pref.checked : pref.value;
        writePreferences(preferences);
        applyPreferenceControls();
        return;
      }
      const widget = event.target.closest?.('[data-widget-key]');
      if (widget && event.target.matches('input[type="checkbox"]')) {
        preferences.widgets = preferences.widgets || {};
        preferences.widgets[widget.dataset.widgetKey] = event.target.checked;
        writePreferences(preferences);
        applyHomeWidgetPreferences();
      }
      if (event.target.id === 'wallpaperCustomInput') {
        const status = $('#wallpaperStatus');
        const file = event.target.files?.[0];
        if (!file) return;
        if (status) status.textContent = 'Preparing wallpaper…';
        try {
          const data = await resizeWallpaperFile(file);
          localStorage.setItem(CUSTOM_WALLPAPER_KEY, data);
          preferences['wallpaper.variant'] = 'custom';
          writePreferences(preferences);
          applyWallpaper('custom', false);
          if (status) status.textContent = 'Custom wallpaper saved on this browser.';
        } catch (error) {
          if (status) status.textContent = error.message || 'Wallpaper could not be saved.';
        } finally {
          event.target.value = '';
        }
      }
    });

    settingsRoot.addEventListener('click', (event) => {
      const prefButton = event.target.closest?.('[data-pref-button]');
      if (prefButton) {
        preferences[prefButton.dataset.prefButton] = prefButton.dataset.value;
        writePreferences(preferences);
        applyPreferenceControls();
        return;
      }
      const wallpaper = event.target.closest?.('[data-wallpaper-value]');
      if (wallpaper) {
        const value = wallpaper.dataset.wallpaperValue;
        if (value === 'custom') {
          let custom = '';
          try { custom = localStorage.getItem(CUSTOM_WALLPAPER_KEY) || ''; } catch (_) {}
          if (!custom) { $('#wallpaperCustomInput')?.click(); return; }
        }
        applyWallpaper(value);
        return;
      }
      if (event.target.closest?.('[data-wallpaper-remove-custom]')) {
        try { localStorage.removeItem(CUSTOM_WALLPAPER_KEY); } catch (_) {}
        preferences['wallpaper.variant'] = 'aurora';
        writePreferences(preferences);
        applyWallpaper('aurora', false);
        const preview = $('.wallpaper-custom');
        if (preview) preview.style.removeProperty('background-image');
        const status = $('#wallpaperStatus');
        if (status) status.textContent = 'Custom wallpaper removed.';
        return;
      }
      if (event.target.closest?.('[data-reset-widgets]')) {
        preferences.widgets = {};
        writePreferences(preferences);
        applyPreferenceControls();
        applyHomeWidgetPreferences();
        return;
      }
      if (event.target.closest?.('[data-reset-local-prefs]')) {
        const widgets = preferences.widgets || {};
        preferences = {...DEFAULT_PREFERENCES, widgets, 'wallpaper.variant': preferences['wallpaper.variant'] || 'aurora'};
        writePreferences(preferences);
        applyPreferenceControls();
      }
    });
    applyPreferenceControls();
  }

  /* ---------- Desktop window manager ---------- */
  const desktopWindowHost = $('#desktopWindowLayer');
  const desktopHostEnabled = body.dataset.page === 'dashboard' && Boolean(desktopWindowHost);
  const desktopWindows = new Map();
  let activeWindowId = '';
  let windowZ = 120;
  let windowCascade = 0;
  const WINDOW_GEOMETRY_PREFIX = 'livenza.window.geometry.';

  function windowIdFor(endpoint) {
    return `livenza-window-${String(endpoint || 'app').replace(/[^a-z0-9_-]+/gi, '-').toLowerCase()}`;
  }
  function windowRecord(windowId) { return desktopWindows.get(windowId) || null; }
  function dockItemForEndpoint(endpoint) { return $(`[data-dock-app][data-app-endpoint="${CSS.escape(endpoint || '')}"]`); }
  function saveWindowGeometry(windowEl) {
    if (!windowEl || windowEl.classList.contains('is-maximized') || windowEl.classList.contains('is-minimized')) return;
    const geometry = {
      left: parseFloat(windowEl.style.left) || windowEl.offsetLeft,
      top: parseFloat(windowEl.style.top) || windowEl.offsetTop,
      width: parseFloat(windowEl.style.width) || windowEl.offsetWidth,
      height: parseFloat(windowEl.style.height) || windowEl.offsetHeight,
    };
    try { sessionStorage.setItem(WINDOW_GEOMETRY_PREFIX + windowEl.dataset.windowApp, JSON.stringify(geometry)); } catch (_) {}
  }
  function readWindowGeometry(endpoint) {
    try { return safeParse(sessionStorage.getItem(WINDOW_GEOMETRY_PREFIX + endpoint)); } catch (_) { return {}; }
  }
  function desktopSafeBounds() {
    const menuHeight = 34;
    const dockHeight = parseFloat(getComputedStyle(root).getPropertyValue('--mac-dock-height')) || 58;
    return {left: 10, top: menuHeight + 8, right: innerWidth - 10, bottom: innerHeight - dockHeight - 22};
  }
  function setWindowBounds(windowEl, geometry) {
    if (!windowEl) return;
    const safe = desktopSafeBounds();
    const minWidth = Math.min(560, Math.max(360, safe.right - safe.left));
    const minHeight = Math.min(360, Math.max(260, safe.bottom - safe.top));
    const width = Math.max(minWidth, Math.min(Number(geometry.width) || Math.min(1080, innerWidth * .72), safe.right - safe.left));
    const height = Math.max(minHeight, Math.min(Number(geometry.height) || Math.min(760, innerHeight * .74), safe.bottom - safe.top));
    const left = Math.max(safe.left, Math.min(Number(geometry.left) || safe.left + 30 + windowCascade * 24, safe.right - width));
    const top = Math.max(safe.top, Math.min(Number(geometry.top) || safe.top + 20 + windowCascade * 18, safe.bottom - height));
    windowEl.style.left = `${left}px`;
    windowEl.style.top = `${top}px`;
    windowEl.style.width = `${width}px`;
    windowEl.style.height = `${height}px`;
  }
  function updateDockWindowState(endpoint) {
    const dockItem = dockItemForEndpoint(endpoint);
    if (!dockItem) return;
    const record = [...desktopWindows.values()].find((item) => item.endpoint === endpoint);
    const open = Boolean(record?.el?.isConnected);
    const minimized = Boolean(record?.el?.classList.contains('is-minimized'));
    const active = Boolean(open && record.el.id === activeWindowId && !minimized);
    dockItem.classList.toggle('is-running', open);
    dockItem.classList.toggle('is-window-active', active);
    dockItem.setAttribute('aria-pressed', String(active));
  }
  function updateDesktopMenuContext(windowEl = null) {
    const label = $('#desktopActiveApp');
    if (label) label.textContent = windowEl?.dataset.windowTitle || 'Livenza Life';
    body?.classList.toggle('desktop-has-active-window', Boolean(windowEl));
    $$('[data-active-window-only]').forEach((item) => {
      item.hidden = !windowEl;
      item.setAttribute('aria-hidden', String(!windowEl));
    });
    $$('[data-window-menu-command="minimize-active"], [data-window-menu-command="zoom-active"], [data-window-menu-command="close-active"], [data-window-menu-command="reload-active"], [data-window-menu-command="open-full-page"]').forEach((item) => {
      item.disabled = !windowEl;
      item.setAttribute('aria-disabled', String(!windowEl));
    });
  }
  function focusAppWindow(windowId) {
    const record = windowRecord(windowId);
    const windowEl = record?.el;
    if (!windowEl || windowEl.classList.contains('is-minimized')) return;
    activeWindowId = windowId;
    windowZ += 1;
    desktopWindows.forEach((entry) => entry.el.classList.remove('is-active'));
    windowEl.classList.add('is-active');
    windowEl.style.zIndex = String(windowZ);
    desktopWindows.forEach((entry) => updateDockWindowState(entry.endpoint));
    updateDesktopMenuContext(windowEl);
  }
  function dockOriginFor(endpoint, windowEl) {
    const dockItem = dockItemForEndpoint(endpoint);
    if (!dockItem || !windowEl) return;
    const dockRect = dockItem.getBoundingClientRect();
    const windowRect = windowEl.getBoundingClientRect();
    windowEl.style.setProperty('--window-origin-x', `${dockRect.left + dockRect.width / 2 - (windowRect.left + windowRect.width / 2)}px`);
    windowEl.style.setProperty('--window-origin-y', `${dockRect.top + dockRect.height / 2 - (windowRect.top + windowRect.height / 2)}px`);
  }
  function minimizeAppWindow(windowId) {
    const record = windowRecord(windowId);
    const windowEl = record?.el;
    if (!windowEl || windowEl.classList.contains('is-minimized')) return;
    saveWindowGeometry(windowEl);
    dockOriginFor(record.endpoint, windowEl);
    windowEl.classList.add('is-minimizing');
    window.setTimeout(() => {
      windowEl.classList.remove('is-minimizing', 'is-active');
      windowEl.classList.add('is-minimized');
      windowEl.setAttribute('aria-hidden', 'true');
      if (activeWindowId === windowId) activeWindowId = '';
      updateDockWindowState(record.endpoint);
      const next = [...desktopWindows.values()].map((entry) => entry.el).filter((el) => !el.classList.contains('is-minimized')).sort((a,b) => Number(b.style.zIndex || 0) - Number(a.style.zIndex || 0))[0];
      if (next) focusAppWindow(next.id); else updateDesktopMenuContext(null);
    }, reduceMotion.matches || root.classList.contains('settings-reduce-motion') ? 0 : 240);
  }
  function restoreAppWindow(windowId) {
    const record = windowRecord(windowId);
    const windowEl = record?.el;
    if (!windowEl) return;
    if (windowEl.classList.contains('is-minimized')) {
      dockOriginFor(record.endpoint, windowEl);
      windowEl.classList.remove('is-minimized');
      windowEl.classList.add('is-restoring');
      windowEl.setAttribute('aria-hidden', 'false');
      window.setTimeout(() => windowEl.classList.remove('is-restoring'), reduceMotion.matches || root.classList.contains('settings-reduce-motion') ? 0 : 240);
    }
    focusAppWindow(windowId);
  }
  function maximizeAppWindow(windowId) {
    const record = windowRecord(windowId);
    const windowEl = record?.el;
    if (!windowEl) return;
    if (windowEl.classList.contains('is-minimized')) restoreAppWindow(windowId);
    if (windowEl.classList.contains('is-maximized')) {
      windowEl.classList.remove('is-maximized');
      const previous = safeParse(windowEl.dataset.restoreGeometry || '{}');
      setWindowBounds(windowEl, previous);
      windowEl.dataset.restoreGeometry = '';
    } else {
      const rect = windowEl.getBoundingClientRect();
      windowEl.dataset.restoreGeometry = JSON.stringify({left: rect.left, top: rect.top, width: rect.width, height: rect.height});
      const safe = desktopSafeBounds();
      windowEl.style.left = `${safe.left}px`;
      windowEl.style.top = `${safe.top}px`;
      windowEl.style.width = `${safe.right - safe.left}px`;
      windowEl.style.height = `${safe.bottom - safe.top}px`;
      windowEl.classList.add('is-maximized');
    }
    focusAppWindow(windowId);
  }
  function closeAppWindow(windowId) {
    const record = windowRecord(windowId);
    const windowEl = record?.el;
    if (!windowEl) return;
    saveWindowGeometry(windowEl);
    dockOriginFor(record.endpoint, windowEl);
    windowEl.classList.add('is-closing');
    const remove = () => {
      windowEl.remove();
      desktopWindows.delete(windowId);
      if (activeWindowId === windowId) activeWindowId = '';
      updateDockWindowState(record.endpoint);
      const next = [...desktopWindows.values()].map((entry) => entry.el).filter((el) => !el.classList.contains('is-minimized')).sort((a,b) => Number(b.style.zIndex || 0) - Number(a.style.zIndex || 0))[0];
      if (next) focusAppWindow(next.id); else updateDesktopMenuContext(null);
    };
    window.setTimeout(remove, reduceMotion.matches || root.classList.contains('settings-reduce-motion') ? 0 : 200);
  }

  async function ensureWindowAssets(doc, baseUrl = location.href) {
    const promises = [];
    doc.querySelectorAll('link[rel="stylesheet"][href]').forEach((link) => {
      let url;
      try { url = new URL(link.getAttribute('href'), baseUrl); } catch (_) { return; }
      if (url.origin !== location.origin) return;
      if ([...document.styleSheets].some((sheet) => sheet.href && new URL(sheet.href, location.href).href === url.href)) return;
      const node = document.createElement('link');
      node.rel = 'stylesheet'; node.href = url.href; node.dataset.windowAsset = '1';
      document.head.appendChild(node);
    });
    doc.querySelectorAll('script[src]').forEach((script) => {
      let url;
      try { url = new URL(script.getAttribute('src'), baseUrl); } catch (_) { return; }
      if (url.origin !== location.origin) return;
      if ([...document.scripts].some((node) => node.src === url.href)) return;
      promises.push(new Promise((resolve) => {
        const node = document.createElement('script');
        node.src = url.href; node.async = false; node.dataset.windowAsset = '1';
        node.addEventListener('load', resolve, {once:true});
        node.addEventListener('error', resolve, {once:true});
        document.body.appendChild(node);
      }));
    });
    await Promise.all(promises);
  }
  function windowScriptIsExecutable(script) {
    const type = String(script?.getAttribute?.('type') || '').trim().toLowerCase();
    return !type || type === 'text/javascript' || type === 'application/javascript' || type === 'module';
  }
  function windowMarkupWithoutExecutableScripts(sourceMain) {
    const clone = sourceMain.cloneNode(true);
    clone.querySelectorAll('script').forEach((script) => {
      if (script.hasAttribute('src') || windowScriptIsExecutable(script)) script.remove();
    });
    return clone.innerHTML;
  }
  async function executeWindowInlineScripts(sourceMain, target) {
    const scripts = [...sourceMain.querySelectorAll('script:not([src])')].filter(windowScriptIsExecutable);
    for (const source of scripts) {
      const node = document.createElement('script');
      const type = String(source.getAttribute('type') || '').trim();
      if (type) node.type = type;
      if (source.nonce) node.nonce = source.nonce;
      if (source.hasAttribute('nomodule')) node.noModule = true;
      node.dataset.windowInlineScript = '1';
      node.textContent = source.textContent || '';
      if (node.type === 'module') {
        await new Promise((resolve) => {
          node.addEventListener('load', resolve, {once:true});
          node.addEventListener('error', resolve, {once:true});
          target.appendChild(node);
          window.setTimeout(resolve, 1000);
        });
      } else {
        target.appendChild(node);
        node.remove();
      }
    }
  }

  async function loadWindowDocument(windowEl, url, pushHistory = true) {
    if (!windowEl) return false;
    const content = $('.mac-window-content', windowEl);
    content?.classList.add('mac-suite-surface');
    const titleLabel = $('.mac-window-title', windowEl);
    if (!content) return false;
    windowEl.classList.add('is-loading');
    try {
      const response = await fetch(url, {credentials:'same-origin', headers:{'X-Livenza-Partial':'1', 'Accept':'text/html'}});
      if (!response.ok) throw new Error(`App returned ${response.status}`);
      const type = response.headers.get('content-type') || '';
      if (type && !type.includes('text/html')) return false;
      const html = await response.text();
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const nextMain = doc.getElementById('appMain');
      if (!nextMain || doc.querySelector('.login-card')) return false;
      content.innerHTML = windowMarkupWithoutExecutableScripts(nextMain);
      applySharedSuiteDesign(content);
      await ensureWindowAssets(doc, url);
      await executeWindowInlineScripts(nextMain, content);
      const fetchedTitle = doc.querySelector('#macPageTitle')?.textContent?.trim() || doc.title?.split('·')[0]?.trim();
      if (fetchedTitle && titleLabel) titleLabel.textContent = fetchedTitle;
      windowEl.dataset.windowUrl = url;
      if (pushHistory) {
        const record = windowRecord(windowEl.id);
        if (record) {
          record.history = (record.history || []).slice(0, (record.historyIndex ?? -1) + 1);
          record.history.push(url);
          record.historyIndex = record.history.length - 1;
        }
      }
      window.LivenzaInitPage?.(content);
      window.dispatchEvent(new CustomEvent('livenza:content-swapped', {detail:{root:content, url, windowId:windowEl.id}}));
      return true;
    } catch (error) {
      console.warn('Desktop app window load failed', error);
      return false;
    } finally {
      windowEl.classList.remove('is-loading');
    }
  }

  function setupWindowPointerBehavior(windowEl) {
    const titlebar = $('.mac-window-titlebar', windowEl);
    let moveFrame = 0;
    let pendingMove = null;
    titlebar?.addEventListener('pointerdown', (event) => {
      if (event.button !== 0 || event.target.closest('[data-window-action]') || windowEl.classList.contains('is-maximized')) return;
      focusAppWindow(windowEl.id);
      const start = windowEl.getBoundingClientRect();
      const startX = event.clientX, startY = event.clientY;
      titlebar.setPointerCapture?.(event.pointerId);
      const paint = () => {
        moveFrame = 0;
        if (!pendingMove) return;
        const safe = desktopSafeBounds();
        const left = Math.max(safe.left, Math.min(start.left + pendingMove.x - startX, safe.right - start.width));
        const top = Math.max(safe.top, Math.min(start.top + pendingMove.y - startY, safe.bottom - 80));
        windowEl.style.left = `${left}px`; windowEl.style.top = `${top}px`;
      };
      const move = (moveEvent) => { pendingMove = {x:moveEvent.clientX, y:moveEvent.clientY}; if (!moveFrame) moveFrame = requestAnimationFrame(paint); };
      const end = () => {
        titlebar.removeEventListener('pointermove', move); titlebar.removeEventListener('pointerup', end); titlebar.removeEventListener('pointercancel', end);
        if (moveFrame) cancelAnimationFrame(moveFrame); moveFrame = 0; pendingMove = null; saveWindowGeometry(windowEl);
      };
      titlebar.addEventListener('pointermove', move); titlebar.addEventListener('pointerup', end); titlebar.addEventListener('pointercancel', end);
    });
    $$('.mac-window-resize-handle', windowEl).forEach((handle) => handle.addEventListener('pointerdown', (event) => {
      if (event.button !== 0 || windowEl.classList.contains('is-maximized')) return;
      event.preventDefault(); focusAppWindow(windowEl.id);
      const direction = handle.dataset.resize || 'se';
      const start = windowEl.getBoundingClientRect(); const startX = event.clientX, startY = event.clientY;
      handle.setPointerCapture?.(event.pointerId);
      let frame = 0, next = null;
      const paint = () => {
        frame = 0; if (!next) return;
        const safe = desktopSafeBounds();
        let left = start.left, top = start.top, width = start.width, height = start.height;
        const dx = next.x - startX, dy = next.y - startY;
        if (direction.includes('e')) width = Math.min(safe.right - start.left, Math.max(520, start.width + dx));
        if (direction.includes('s')) height = Math.min(safe.bottom - start.top, Math.max(320, start.height + dy));
        if (direction.includes('w')) { const proposed = Math.max(safe.left, Math.min(start.left + dx, start.right - 520)); width = start.right - proposed; left = proposed; }
        if (direction.includes('n')) { const proposed = Math.max(safe.top, Math.min(start.top + dy, start.bottom - 320)); height = start.bottom - proposed; top = proposed; }
        Object.assign(windowEl.style, {left:`${left}px`, top:`${top}px`, width:`${width}px`, height:`${height}px`});
      };
      const move = (moveEvent) => { next = {x:moveEvent.clientX, y:moveEvent.clientY}; if (!frame) frame = requestAnimationFrame(paint); };
      const end = () => { handle.removeEventListener('pointermove', move); handle.removeEventListener('pointerup', end); handle.removeEventListener('pointercancel', end); if (frame) cancelAnimationFrame(frame); frame=0; next=null; saveWindowGeometry(windowEl); };
      handle.addEventListener('pointermove', move); handle.addEventListener('pointerup', end); handle.addEventListener('pointercancel', end);
    }));
  }

  async function openAppWindow(meta) {
    if (!desktopHostEnabled || !meta?.endpoint || !meta?.url) return null;
    if (meta.endpoint === 'dashboard') {
      desktopWindows.forEach((entry) => { if (!entry.el.classList.contains('is-minimized')) minimizeAppWindow(entry.el.id); });
      updateDesktopMenuContext(null);
      return null;
    }
    const windowId = windowIdFor(meta.endpoint);
    const existing = windowRecord(windowId);
    if (existing?.el?.isConnected) { restoreAppWindow(windowId); return existing.el; }
    const windowEl = document.createElement('section');
    windowEl.id = windowId;
    windowEl.className = 'mac-app-window is-opening';
    windowEl.dataset.windowApp = meta.endpoint;
    windowEl.dataset.windowTitle = meta.title || 'Livenza';
    windowEl.dataset.windowUrl = meta.url;
    windowEl.dataset.windowTone = meta.tone || 'blue';
    windowEl.setAttribute('data-window-family', meta.family || 'productivity');
    windowEl.setAttribute('data-window-accent', meta.accent || '#0088ff');
    windowEl.setAttribute('data-window-accent2', meta.accent2 || '#6155f5');
    windowEl.style.setProperty('--suite-accent', meta.accent || '#0088ff');
    windowEl.style.setProperty('--suite-accent-2', meta.accent2 || '#6155f5');
    windowEl.tabIndex = -1;
    windowEl.innerHTML = `
      <header class="mac-window-titlebar">
        <div class="mac-window-controls" aria-label="Window controls">
          <button type="button" class="mac-window-control close" data-window-action="close" aria-label="Close"></button>
          <button type="button" class="mac-window-control minimize" data-window-action="minimize" aria-label="Minimise"></button>
          <button type="button" class="mac-window-control maximize" data-window-action="maximize" aria-label="Zoom"></button>
        </div>
        <div class="mac-window-title-identity"><span class="mac-window-mini-icon livenza-app-icon" data-app-icon="${String(meta.endpoint || '').replace(/[^a-z0-9_-]/gi,'')}"><span class="app-icon-backdrop"></span><span class="app-icon-glyph">${meta.iconMarkup || ''}</span><span class="app-icon-shine"></span></span><strong class="mac-window-title">${String(meta.title || 'Livenza').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]))}</strong></div>
        <div class="mac-window-title-actions"><button type="button" data-window-action="reload" aria-label="Reload app">↻</button><a href="${meta.url}" data-window-action="fullpage" aria-label="Open in full page">↗</a></div>
      </header>
      <div class="mac-window-content mac-suite-surface"><div class="mac-window-loading" role="status">Opening ${String(meta.title || 'app').replace(/[&<>]/g,'')}…</div></div>
      <i class="mac-window-resize-handle resize-n" data-resize="n"></i><i class="mac-window-resize-handle resize-e" data-resize="e"></i><i class="mac-window-resize-handle resize-s" data-resize="s"></i><i class="mac-window-resize-handle resize-w" data-resize="w"></i>
      <i class="mac-window-resize-handle resize-ne" data-resize="ne"></i><i class="mac-window-resize-handle resize-se" data-resize="se"></i><i class="mac-window-resize-handle resize-sw" data-resize="sw"></i><i class="mac-window-resize-handle resize-nw" data-resize="nw"></i>`;
    desktopWindowHost.appendChild(windowEl);
    windowCascade = (windowCascade + 1) % 8;
    setWindowBounds(windowEl, readWindowGeometry(meta.endpoint));
    desktopWindows.set(windowId, {el:windowEl, endpoint:meta.endpoint, title:meta.title || 'Livenza', url:meta.url, history:[], historyIndex:-1});
    setupWindowPointerBehavior(windowEl);
    dockOriginFor(meta.endpoint, windowEl);
    requestAnimationFrame(() => windowEl.classList.remove('is-opening'));
    focusAppWindow(windowId);
    updateDockWindowState(meta.endpoint);
    const loaded = await loadWindowDocument(windowEl, meta.url, true);
    if (!loaded) { closeAppWindow(windowId); location.assign(meta.url); return null; }
    return windowEl;
  }

  function shouldOpenInDesktopWindow(anchor) {
    if (!desktopHostEnabled || !anchor || !anchor.matches('[data-app-nav]')) return false;
    if (anchor.hasAttribute('download') || anchor.target === '_blank') return false;
    let url; try { url = new URL(anchor.href, location.href); } catch (_) { return false; }
    if (url.origin !== location.origin || /^\/(logout|api\/|static\/)/.test(url.pathname)) return false;
    if (/\.(pdf|zip|csv|xlsx?|docx?|png|jpe?g|webp)$/i.test(url.pathname)) return false;
    return true;
  }
  function appMetaForAnchor(anchor) {
    const url = new URL(anchor.href, location.href);
    let source = anchor.matches('[data-dock-app]') ? anchor : $$('[data-dock-app]').find((item) => {
      try { return new URL(item.href, location.href).pathname === url.pathname; } catch (_) { return false; }
    });
    const endpoint = anchor.dataset.appEndpoint || source?.dataset.appEndpoint || url.pathname.replace(/^\/+|\/+$/g, '').replace(/[^a-z0-9]+/gi, '_') || 'dashboard';
    const title = anchor.dataset.appTitle || source?.dataset.appTitle || anchor.querySelector('b')?.textContent?.trim() || anchor.getAttribute('aria-label') || anchor.title || 'Livenza';
    const iconSource = anchor.querySelector('.app-icon-glyph') || source?.querySelector('.app-icon-glyph');
    return {
      endpoint,
      url:url.href,
      title,
      tone:anchor.dataset.appTone || source?.dataset.appTone || 'blue',
      family:anchor.dataset.appFamily || source?.dataset.appFamily || 'productivity',
      accent:anchor.dataset.appAccent || source?.dataset.appAccent || '#0088ff',
      accent2:anchor.dataset.appAccent2 || source?.dataset.appAccent2 || '#6155f5',
      iconMarkup:iconSource?.innerHTML || ''
    };
  }

  if (desktopHostEnabled) {
    desktopWindowHost.addEventListener('pointerdown', (event) => {
      const windowEl = event.target.closest('.mac-app-window'); if (windowEl) focusAppWindow(windowEl.id);
    });
    desktopWindowHost.addEventListener('click', async (event) => {
      const control = event.target.closest('[data-window-action]');
      if (control) {
        const windowEl = control.closest('.mac-app-window'); if (!windowEl) return;
        const action = control.dataset.windowAction;
        if (action === 'close') closeAppWindow(windowEl.id);
        else if (action === 'minimize') minimizeAppWindow(windowEl.id);
        else if (action === 'maximize') maximizeAppWindow(windowEl.id);
        else if (action === 'reload') await loadWindowDocument(windowEl, windowEl.dataset.windowUrl, false);
        else if (action === 'fullpage') return;
        event.preventDefault(); return;
      }
      const anchor = event.target.closest('a[href]');
      if (!anchor || anchor.dataset.windowAction === 'fullpage' || anchor.hasAttribute('download') || anchor.target === '_blank') return;
      let url; try { url = new URL(anchor.href, location.href); } catch (_) { return; }
      if (url.origin !== location.origin || /^\/(logout|api\/|static\/)/.test(url.pathname) || /\.(pdf|zip|csv|xlsx?|docx?|png|jpe?g|webp)$/i.test(url.pathname)) return;
      const windowEl = anchor.closest('.mac-app-window');
      if (!windowEl || (url.hash && url.pathname === new URL(windowEl.dataset.windowUrl, location.href).pathname)) return;
      const targetDockItem = $$('[data-dock-app]').find((item) => {
        try { return new URL(item.href, location.href).pathname === url.pathname; } catch (_) { return false; }
      });
      if (targetDockItem?.dataset.appEndpoint && targetDockItem.dataset.appEndpoint !== windowEl.dataset.windowApp) {
        event.preventDefault();
        await openAppWindow(appMetaForAnchor(targetDockItem));
        return;
      }
      event.preventDefault();
      const ok = await loadWindowDocument(windowEl, url.href, true);
      if (!ok) location.assign(url.href);
    });
    document.addEventListener('click', async (event) => {
      const anchor = event.target.closest('[data-app-nav]');
      if (!shouldOpenInDesktopWindow(anchor)) return;
      event.preventDefault();
      drawers.forEach((drawer) => setDrawer(drawer, false));
      const meta = appMetaForAnchor(anchor);
      await openAppWindow(meta);
    }, true);
  }

  /* ---------- Contextual desktop menus ---------- */
  const desktopMenus = $$('[data-window-menu]');
  function closeDesktopMenus() {
    desktopMenus.forEach((menu) => { menu.hidden = true; menu.classList.remove('is-open'); });
    $$('[data-window-menu-trigger]').forEach((trigger) => trigger.setAttribute('aria-expanded', 'false'));
  }
  $$('[data-window-menu-trigger]').forEach((trigger) => trigger.addEventListener('click', (event) => {
    event.stopPropagation();
    const menu = $(`[data-window-menu="${trigger.dataset.windowMenuTrigger}"]`); if (!menu) return;
    const willOpen = menu.hidden;
    closeDesktopMenus();
    if (willOpen) {
      const rect = trigger.getBoundingClientRect();
      menu.style.left = `${Math.max(6, rect.left)}px`; menu.style.top = `${rect.bottom + 3}px`;
      menu.hidden = false; requestAnimationFrame(() => menu.classList.add('is-open'));
      trigger.setAttribute('aria-expanded', 'true');
    }
  }));
  document.addEventListener('click', (event) => { if (!event.target.closest('[data-window-menu], [data-window-menu-trigger]')) closeDesktopMenus(); });
  document.addEventListener('click', async (event) => {
    const command = event.target.closest('[data-window-menu-command]'); if (!command) return;
    const active = activeWindowId ? windowRecord(activeWindowId)?.el : null;
    const name = command.dataset.windowMenuCommand;
    if (name === 'toggle-widgets') body.classList.toggle('desktop-widgets-hidden');
    else if (name === 'show-desktop') desktopWindows.forEach((entry) => { if (!entry.el.classList.contains('is-minimized')) minimizeAppWindow(entry.el.id); });
    else if (name === 'minimize-active' && active) minimizeAppWindow(active.id);
    else if (name === 'zoom-active' && active) maximizeAppWindow(active.id);
    else if (name === 'close-active' && active) closeAppWindow(active.id);
    else if (name === 'reload-active' && active) await loadWindowDocument(active, active.dataset.windowUrl, false);
    else if (name === 'open-full-page' && active) location.assign(active.dataset.windowUrl);
    else if (name === 'bring-all-front') {
      desktopWindows.forEach((entry) => { if (entry.el.classList.contains('is-minimized')) restoreAppWindow(entry.el.id); });
      const last = [...desktopWindows.values()].pop()?.el; if (last) focusAppWindow(last.id);
    }
    closeDesktopMenus();
  });

  window.LivenzaWindowManager = {openAppWindow, focusAppWindow, minimizeAppWindow, restoreAppWindow, maximizeAppWindow, closeAppWindow, loadWindowDocument};


  /* ---------- Home desktop widgets ---------- */
  const isHome = body?.dataset.page === 'dashboard';
  if (isHome) {
    const byId = (id) => document.getElementById(id);
    const currentTime = byId('homeCurrentTime');
    const currentDate = byId('homeCurrentDate');
    const dateNumber = byId('homeDateNumber');
    const dayName = byId('homeDayName');
    const weatherTemperature = byId('homeWeatherTemperature');
    const weatherCity = byId('homeWeatherCity');
    const weatherCondition = byId('homeWeatherCondition');
    const weatherRange = byId('homeWeatherRange');
    const operationPrimary = byId('homeOperationPrimary');
    const operationPrimaryValue = byId('homeOperationPrimaryValue');
    const operationSecondary = byId('homeOperationSecondary');
    const operationSecondaryValue = byId('homeOperationSecondaryValue');
    let clockTimer = 0;

    function updateClock() {
      const now = new Date();
      if (currentTime) currentTime.textContent = now.toLocaleTimeString([], {hour: 'numeric', minute: '2-digit'});
      if (currentDate) currentDate.textContent = now.toLocaleDateString([], {weekday: 'short', month: 'short', day: 'numeric'});
      if (dateNumber) dateNumber.textContent = String(now.getDate());
      if (dayName) dayName.textContent = now.toLocaleDateString([], {weekday: 'long'});
    }
    function renderHomePulse(data) {
      const weather = data?.weather || {};
      if (weatherCity) weatherCity.textContent = weather.city || 'Gurugram';
      if (weatherTemperature) weatherTemperature.textContent = Number.isFinite(Number(weather.temperature)) ? `${Math.round(Number(weather.temperature))}°` : '—°';
      if (weatherCondition) weatherCondition.textContent = weather.condition || 'Live weather unavailable';
      const today = Array.isArray(weather.forecast) ? weather.forecast[0] : null;
      if (weatherRange) {
        const high = Number.isFinite(Number(today?.high)) ? `${Math.round(Number(today.high))}°` : '—°';
        const low = Number.isFinite(Number(today?.low)) ? `${Math.round(Number(today.low))}°` : '—°';
        weatherRange.textContent = `H:${high}  L:${low}`;
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
    }
    function startClock() {
      window.clearInterval(clockTimer);
      updateClock();
      if (!document.hidden) clockTimer = window.setInterval(updateClock, 30_000);
    }
    window.addEventListener('livenza:companion-pulse', (event) => renderHomePulse(event.detail));
    if (window.LivenzaCompanionPulse) renderHomePulse(window.LivenzaCompanionPulse);
    document.addEventListener('visibilitychange', startClock);
    startClock();
    $$('[data-home-companion-open]').forEach((control) => control.addEventListener('click', () => {
      if (window.LivenzaCompanion?.open) window.LivenzaCompanion.open('chat');
      else byId('mascotCompanionButton')?.click();
    }));
  }

  /* ---------- Global keys and restoration ---------- */
  document.addEventListener('keydown', (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      palette?.classList.contains('is-open') ? closePalette() : openPalette();
    } else if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'f' && settingsRoot) {
      const search = $('#settingsSearch', settingsRoot);
      if (search) { event.preventDefault(); search.focus(); search.select(); }
    } else if (event.key === 'Escape') {
      if (palette?.classList.contains('is-open')) closePalette();
      else {
        const openDrawer = drawers.find((drawer) => drawer.classList.contains('is-open'));
        if (openDrawer) setDrawer(openDrawer, false, true);
        else if (inspector && !inspector.hidden) closeInspector();
      }
    }
  });
  window.addEventListener('pageshow', () => {
    if (palette?.classList.contains('is-open')) closePalette(false);
    drawers.forEach((drawer) => setDrawer(drawer, false));
    cacheDockCenters();
  });

  window.LivenzaMacShell = {
    openPalette,
    closePalette,
    applyWallpaper,
    resizeWallpaperFile,
    getPreferences: () => ({...preferences})
  };
})();
