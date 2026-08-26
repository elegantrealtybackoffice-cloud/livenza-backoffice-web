(function () {
  'use strict';
  var root = document.documentElement;
  var nav = window.navigator || {};
  var result = {
    profile: 'medium',
    webgl: false,
    maxTextureSize: 0,
    hardwareConcurrency: Number(nav.hardwareConcurrency || 0),
    deviceMemory: Number(nav.deviceMemory || 0),
    frameTime: 0,
    tvHint: false,
    modernReady: false
  };
  var ua = String(nav.userAgent || '');
  var frameSamplerStarted = false;

  function removeProfileFlags() {
    root.classList.remove('capability-high');
    root.classList.remove('capability-medium');
    root.classList.remove('low-capability');
  }
  function emitReady() {
    var event;
    var detail = {
      profile: result.profile,
      webgl: result.webgl,
      maxTextureSize: result.maxTextureSize,
      hardwareConcurrency: result.hardwareConcurrency,
      deviceMemory: result.deviceMemory,
      frameTime: result.frameTime,
      tvHint: result.tvHint
    };
    try {
      event = document.createEvent('CustomEvent');
      event.initCustomEvent('livenza:capability-ready', false, false, detail);
      document.dispatchEvent(event);
    } catch (err) {
      try {
        event = document.createEvent('Event');
        event.initEvent('livenza:capability-ready', false, false);
        event.detail = detail;
        document.dispatchEvent(event);
      } catch (ignored) {}
    }
  }
  function applyProfile(profile, emit) {
    result.profile = profile;
    removeProfileFlags();
    if (profile === 'low') root.classList.add('low-capability');
    else root.classList.add('capability-' + profile);
    if (result.tvHint || profile === 'low') root.classList.add('tv-performance');
    else root.classList.remove('tv-performance');
    if (emit !== false) emitReady();
  }
  function inspectWebGL() {
    var canvas;
    var gl;
    try {
      canvas = document.createElement('canvas');
      gl = canvas.getContext('webgl2', { failIfMajorPerformanceCaveat: true }) || canvas.getContext('webgl', { failIfMajorPerformanceCaveat: true }) || canvas.getContext('experimental-webgl');
      if (!gl) return;
      result.webgl = true;
      result.maxTextureSize = Number(gl.getParameter(gl.MAX_TEXTURE_SIZE) || 0);
      var lose = gl.getExtension && gl.getExtension('WEBGL_lose_context');
      if (lose && lose.loseContext) lose.loseContext();
    } catch (err) {
      result.webgl = false;
      result.maxTextureSize = 0;
    }
  }
  function classifyBase() {
    // WebGL is now informational. The default Livenza companion and core UI
    // are lightweight DOM/CSS, so a missing GPU context must not downgrade the
    // entire site into low-capability mode.
    var severe = false;
    var moderate = false;
    if (result.hardwareConcurrency && result.hardwareConcurrency <= 2) severe = true;
    else if (result.hardwareConcurrency && result.hardwareConcurrency < 4) moderate = true;
    if (result.deviceMemory && result.deviceMemory <= 2) severe = true;
    else if (result.deviceMemory && result.deviceMemory < 4) moderate = true;
    if (severe) return 'low';
    if (!moderate && ((result.hardwareConcurrency && result.hardwareConcurrency >= 8) || (result.deviceMemory && result.deviceMemory >= 8))) return 'high';
    return 'medium';
  }
  function finishFrameSample(ms, callback) {
    result.frameTime = Math.round(ms * 10) / 10;
    if (ms > 35) applyProfile('low');
    else if (ms > 22 && result.profile === 'high') applyProfile('medium');
    else emitReady();
    if (callback) callback(result.frameTime);
  }
  function sampleFrameTime(callback) {
    var raf = window.requestAnimationFrame || function (fn) { return window.setTimeout(function () { fn(new Date().getTime()); }, 16); };
    var frames = [];
    var last = 0;
    var count = 0;
    function step(ts) {
      if (last) frames.push(ts - last);
      last = ts;
      count += 1;
      if (count < 12) {
        raf(step);
        return;
      }
      var sum = 0;
      var i;
      for (i = 0; i < frames.length; i += 1) sum += frames[i];
      finishFrameSample(frames.length ? sum / frames.length : 16, callback);
    }
    raf(step);
  }

  result.tvHint = /SmartTV|Tizen|Web0S|WebOS|NetCast|HbbTV|Viera|BRAVIA|AFTB|TV Safari|SMART-TV/i.test(ua);
  inspectWebGL();
  applyProfile(classifyBase(), false);
  window.LivenzaCapability = result;
  window.LivenzaCapability.sampleFrameTime = sampleFrameTime;
  emitReady();

  if (!frameSamplerStarted) {
    frameSamplerStarted = true;
    sampleFrameTime();
  }
  window.setTimeout(function () {
    result.modernReady = window.LivenzaModernReady === true;
    if (!result.modernReady) applyProfile('low');
  }, 3200);
}());
