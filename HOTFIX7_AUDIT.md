# Hotfix 7 Browser-OS Audit Record

## Automated source gates
- Python unittest discovery: 38 tests, 0 failures, 0 errors.
- Python compilation: project top-level `.py` files compile successfully.
- JavaScript syntax: `static/macos27_shell.js` and `static/app.js` pass `node --check`.
- Jinja parse: 73 templates parse successfully.

## Chromium shell audit
Real Chromium via Playwright is used against a deterministic in-memory fixture that injects the production `macos27_system.css` and `macos27_shell.js`.

Viewports: 1440×900 and 1152×720.

Checks include:
- 34 px menu bar, 58 px Dock, 36 px idle icons, 344 px widgets, 16 px window radius, 40 px compact window titlebar and 4 px running dots.
- No page-level horizontal or vertical overflow and no widget/Dock intersection.
- Representative text overflow/legibility.
- Wallpaper rendering and compact responsive layout.
- Pointer-distance Dock magnification without changing Dock height.
- App window open/focus/running-state, pointer drag/resize safe bounds, maximise/minimise/restore, multi-window focus/close.
- Contextual menu materialisation and active-window-only File menu.
- Same-origin mounted-page inline script execution after dynamic content load.
- Reduced Motion behaviour.

The final Chromium audit is run twice consecutively after the last production-code fix and must return `ok: true` both times.

## Environment limitation
The packaging sandbox does not include Flask, and its browser policy cannot exercise an authenticated `https://backoffice.livenza.life` session. The browser audit therefore validates the production shell code and deterministic app-window fixture, not live server/database/provider behaviour. `VERIFY_DEPLOY.txt` contains the required post-deployment acceptance checks.
