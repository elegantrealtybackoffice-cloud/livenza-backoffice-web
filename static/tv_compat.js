(function () {
  'use strict';
  var activeDrawer = null;
  var activeOpener = null;
  var closeTimer = null;

  function byId(id) { return document.getElementById(id); }
  function toArray(nodes) { return Array.prototype.slice.call(nodes || []); }
  function focusables(root) {
    if (!root) return [];
    return toArray(root.querySelectorAll('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])')).filter(function (node) {
      return !node.hidden && node.getAttribute('aria-hidden') !== 'true';
    });
  }
  function drawerTop() {
    var header = document.querySelector('.showcase-header');
    var marquee = byId('liveOperationsMarquee');
    var bottom = 0;
    if (header && header.getBoundingClientRect) bottom = Math.max(bottom, header.getBoundingClientRect().bottom || 0);
    if (marquee && marquee.getBoundingClientRect) bottom = Math.max(bottom, marquee.getBoundingClientRect().bottom || 0);
    return Math.max(72, Math.ceil(bottom + 8));
  }
  function positionDrawers() {
    var top = drawerTop();
    var backdrop = byId('appsMenuBackdrop');
    var drawers = document.querySelectorAll('.side-drawer');
    var i;
    if (backdrop) backdrop.style.top = top + 'px';
    for (i = 0; i < drawers.length; i += 1) drawers[i].style.top = top + 'px';
  }
  function setExpanded(opener, open) {
    if (!opener) return;
    opener.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (opener.classList) opener.classList.toggle('active', open);
  }
  function hideBackdrop() {
    var backdrop = byId('appsMenuBackdrop');
    if (!backdrop) return;
    backdrop.classList.remove('open');
    window.setTimeout(function () {
      if (!activeDrawer) backdrop.hidden = true;
    }, 220);
  }
  function closeDrawer(restoreFocus) {
    var drawer = activeDrawer;
    var opener = activeOpener;
    if (!drawer) return;
    window.clearTimeout(closeTimer);
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
    setExpanded(opener, false);
    activeDrawer = null;
    activeOpener = null;
    document.body.classList.remove('side-drawer-open');
    document.body.classList.remove('apps-drawer-open');
    hideBackdrop();
    closeTimer = window.setTimeout(function () {
      if (drawer.getAttribute('aria-hidden') === 'true') drawer.hidden = true;
    }, 240);
    if (restoreFocus && opener && opener.focus) opener.focus();
  }
  function openDrawer(drawer, opener) {
    var backdrop = byId('appsMenuBackdrop');
    var first;
    if (!drawer || !opener) return;
    if (activeDrawer && activeDrawer !== drawer) closeDrawer(false);
    window.clearTimeout(closeTimer);
    positionDrawers();
    drawer.hidden = false;
    drawer.setAttribute('aria-hidden', 'false');
    if (backdrop) {
      backdrop.hidden = false;
      window.setTimeout(function () { backdrop.classList.add('open'); }, 0);
    }
    activeDrawer = drawer;
    activeOpener = opener;
    setExpanded(opener, true);
    document.body.classList.add('side-drawer-open');
    if (drawer.id === 'appsDrawer') document.body.classList.add('apps-drawer-open');
    window.setTimeout(function () {
      drawer.classList.add('open');
      first = focusables(drawer)[0];
      if (first && first.focus) first.focus();
    }, 0);
  }
  function toggleDrawer(opener) {
    var target = opener ? opener.getAttribute('data-drawer-target') : '';
    var drawer = target ? byId(target) : null;
    if (!drawer) return;
    if (activeDrawer === drawer && drawer.classList.contains('open')) closeDrawer(true);
    else openDrawer(drawer, opener);
  }
  function panelFor(name) {
    return document.querySelector('[data-tv-panel="' + name + '"]');
  }
  function tabsInGroup(group) {
    return toArray(document.querySelectorAll('[data-tv-tab][data-tv-group="' + group + '"]'));
  }
  function activateTab(tab, focusPanel) {
    var group;
    var target;
    var tabs;
    var panels;
    var i;
    var active;
    var panel;
    if (!tab) return;
    group = tab.getAttribute('data-tv-group') || 'default';
    target = tab.getAttribute('data-tv-target') || tab.getAttribute('data-tv-tab');
    tabs = tabsInGroup(group);
    panels = document.querySelectorAll('[data-tv-panel][data-tv-group="' + group + '"]');
    for (i = 0; i < tabs.length; i += 1) {
      active = tabs[i] === tab;
      tabs[i].setAttribute('aria-selected', active ? 'true' : 'false');
      tabs[i].setAttribute('tabindex', active ? '0' : '-1');
      if (tabs[i].classList) tabs[i].classList.toggle('active', active);
    }
    for (i = 0; i < panels.length; i += 1) {
      active = panels[i].getAttribute('data-tv-panel') === target;
      panels[i].hidden = !active;
      if (panels[i].classList) panels[i].classList.toggle('active', active);
    }
    panel = panelFor(target);
    if (focusPanel && panel) {
      var next = focusables(panel)[0];
      if (next && next.focus) next.focus();
    }
  }
  function initTabs() {
    var groups = {};
    var tabs = document.querySelectorAll('[data-tv-tab]');
    var i;
    var group;
    var selected;
    for (i = 0; i < tabs.length; i += 1) {
      group = tabs[i].getAttribute('data-tv-group') || 'default';
      if (!groups[group]) groups[group] = [];
      groups[group].push(tabs[i]);
    }
    for (group in groups) {
      if (Object.prototype.hasOwnProperty.call(groups, group)) {
        selected = null;
        for (i = 0; i < groups[group].length; i += 1) {
          if (groups[group][i].getAttribute('aria-selected') === 'true' || groups[group][i].classList.contains('active')) {
            selected = groups[group][i];
            break;
          }
        }
        activateTab(selected || groups[group][0], false);
      }
    }
  }
  function moveTabFocus(tab, key) {
    var group = tab.getAttribute('data-tv-group') || 'default';
    var tabs = tabsInGroup(group);
    var index = tabs.indexOf ? tabs.indexOf(tab) : -1;
    var next;
    if (index < 0) return;
    if (key === 'Home') next = 0;
    else if (key === 'End') next = tabs.length - 1;
    else if (key === 'ArrowRight' || key === 'ArrowDown') next = (index + 1) % tabs.length;
    else next = (index - 1 + tabs.length) % tabs.length;
    if (tabs[next] && tabs[next].focus) tabs[next].focus();
    activateTab(tabs[next], false);
  }
  function keyName(event) {
    if (event.key) return event.key;
    if (event.keyCode === 13) return 'Enter';
    if (event.keyCode === 32) return ' ';
    if (event.keyCode === 27) return 'Escape';
    if (event.keyCode === 8) return 'Backspace';
    if (event.keyCode === 37) return 'ArrowLeft';
    if (event.keyCode === 38) return 'ArrowUp';
    if (event.keyCode === 39) return 'ArrowRight';
    if (event.keyCode === 40) return 'ArrowDown';
    if (event.keyCode === 36) return 'Home';
    if (event.keyCode === 35) return 'End';
    if (event.keyCode === 9) return 'Tab';
    return '';
  }
  function trapDrawerTab(event) {
    var nodes;
    var first;
    var last;
    if (!activeDrawer) return false;
    nodes = focusables(activeDrawer);
    if (!nodes.length) return false;
    first = nodes[0];
    last = nodes[nodes.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
      return true;
    }
    if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
      return true;
    }
    return false;
  }
  document.addEventListener('click', function (event) {
    var opener = event.target.closest ? event.target.closest('[data-drawer-target]') : null;
    var close = event.target.closest ? event.target.closest('[data-drawer-close]') : null;
    var tab = event.target.closest ? event.target.closest('[data-tv-tab]') : null;
    var link;
    if (opener) {
      event.preventDefault();
      toggleDrawer(opener);
      return;
    }
    if (close || event.target === byId('appsMenuBackdrop')) {
      event.preventDefault();
      closeDrawer(true);
      return;
    }
    if (tab) {
      activateTab(tab, false);
      return;
    }
    if (activeDrawer && event.target.closest) {
      link = event.target.closest('a[href]');
      if (link && activeDrawer.contains(link)) closeDrawer(false);
    }
  });
  document.addEventListener('keydown', function (event) {
    var key = keyName(event);
    var tab = event.target && event.target.closest ? event.target.closest('[data-tv-tab]') : null;
    if (key === 'Tab' && trapDrawerTab(event)) return;
    if ((key === 'Escape' || key === 'Backspace') && activeDrawer) {
      if (key === 'Backspace' && event.target && /INPUT|TEXTAREA/.test(event.target.tagName)) return;
      event.preventDefault();
      closeDrawer(true);
      return;
    }
    if (!tab) return;
    if (key === 'Enter' || key === ' ') {
      event.preventDefault();
      activateTab(tab, false);
      return;
    }
    if (key === 'ArrowLeft' || key === 'ArrowRight' || key === 'ArrowUp' || key === 'ArrowDown' || key === 'Home' || key === 'End') {
      event.preventDefault();
      moveTabFocus(tab, key);
    }
  });
  window.addEventListener('resize', positionDrawers);
  window.addEventListener('scroll', function () { if (activeDrawer) positionDrawers(); });
  initTabs();
  positionDrawers();
  window.LivenzaTvCompatReady = true;
}());
