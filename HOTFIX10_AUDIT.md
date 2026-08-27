# Hotfix 10 Audit — Lightweight Shell + Refined Settings + Livenza Identity + Deployment Cache Fix

**Product:** Tesla OS 27  
**Version:** 27.0.1  
**Build:** 27A101  
**Release:** Hotfix 10 Light Shell  
**Asset revision:** `27A101-H10L-20260827E`  
**Audit date:** 2026-08-27

## Why this Hotfix exists

Screenshots from the deployed host showed that earlier Hotfix 10 ZIPs could still look almost identical to the previous release: the old desktop composition could remain visible, the Dock changes could fail to appear, and menus could feel heavy. Root-cause analysis found two independent issues:

1. Home still inherited large runtime/presentation bundles that were unnecessary for an idle desktop.
2. Static assets are served with a one-year immutable cache policy, while earlier hotfix URLs were versioned only with the unchanged OS version `27.0.1`. A browser/CDN could therefore legally reuse old CSS/JS after a new ZIP was uploaded.

Hotfix 10 fixes both at the source. It does not depend on asking users to clear browser cache.

## Lightweight Home architecture

Home is now a dedicated lightweight shell:

- `static/home_light.css`
- `static/home_light.js`

The dashboard no longer loads the large `legacy_modules.css`, `macos27_system.css`, `app.js` or `tv_compat.js` bundles. The fast dashboard template context also skips settings/companion preference reads that are not needed to paint Home.

Measured source sizes in this release are approximately:

- `home_light.css`: 13 KB
- `home_light.js`: 5 KB

compared with the avoided Home bundles:

- `legacy_modules.css`: ~305 KB
- `app.js`: ~101 KB
- `tv_compat.js`: ~9 KB
- `macos27_system.css`: ~129 KB

The suite-specific heavy code is still retained for the application routes that need it.

## Visible Home contract

The actual Jinja Home template now renders:

- the Livenza.life · LIVE ELEVATED. scenic wallpaper;
- the approved horizontal Livenza wordmark in the top menu bar;
- functional Suites / View / Window / Help controls;
- seven curated Dock shortcuts — Suites, Agreement Studio, Rooms, Queries, Reviews, Banking and System Settings — subject to relevant permissions;
- Widgets hidden on initial load and opened only from the top-bar control;
- a compact Livenza Companion at the lower-right immediately above the Dock rather than in the middle of the wallpaper;
- no idle weather or operations polling;
- local menu/drawer interaction without waiting for a network request.

Dock proximity motion uses requestAnimationFrame/GPU transforms and respects Reduced Motion / low-capability behavior.

## Lightweight System Settings

System Settings has a dedicated `settings_light.css` path and avoids the legacy module stylesheet, general `app.js` runtime and TV compatibility script.

The actual `system_settings.html` Desktop & Dock template was rendered after the final CSS refinement. The final render confirms:

- bright white detail canvas;
- clear sidebar and title hierarchy;
- Dock Size on its own control row;
- Magnification and Auto-Hide as separate 58 px rows with proper macOS-style switches;
- no text bunching;
- no horizontal overflow;
- persistent curated Dock beneath the Settings window.

The lightweight Settings layer also explicitly defines form grids, option grids, wallpaper cards, switches, range/value rows, action controls, status cards and responsive layouts so other panes do not fall back to browser-default flow.

## Deployment-cache correction

Hotfix 10 introduces the unique static revision:

`27A101-H10L-20260827E`

Changes:

- versioned static template URLs use `?rev={{ asset_revision }}` instead of the unchanged OS version;
- `/version` reports the hotfix label and asset revision;
- responses include `X-Livenza-Revision`, `X-Livenza-Hotfix` and the existing build header;
- Home/Settings HTML includes `data-build-revision`;
- the default scenic wallpaper uses the revision-specific filename `static/wallpapers/livenza_life_live_elevated_h10l.jpg` so an immutable image cache cannot reuse an older file under the same URL.

A deployed host is not considered verified until these fingerprints are visible. Full steps are in `VERIFY_DEPLOY.txt`.

## Livenza identity system

The approved three-logo package remains the source of truth:

- `static/brand/livenza_wordmark_tagline.png` — formal/authentication/Agreement/Letterhead identity;
- `static/brand/livenza_wordmark.png` — horizontal UI wordmark;
- `static/brand/livenza_life_mark.png` — compact `.life` mark for PWA/favicon/system identity.

The UI palette remains deep navy `#061A3A`, emerald `#35D05B` and cyan `#10C8CF`, with bright professional working surfaces. Agreement and Letterhead PDF defaults use the approved logo while a configured custom Letterhead logo continues to take precedence.

## Default wallpaper

The Livenza.life · LIVE ELEVATED. scenic wallpaper is the first-run/reset default. The source image was cropped free of generated preview chrome so Tesla OS supplies its own menu bar and Dock. Wallpaper Fill/Fit/Stretch/Center, position and zoom preferences remain supported.

## Automated verification scope

The release gate covers:

- complete Python unit/source regression suite, including inherited Hotfix 8/9/9.1/9.2 contracts and current Hotfix 10 light-shell contracts;
- Python source compilation;
- every production JavaScript file under `static/` with `node --check`;
- every Jinja template parse;
- CSS structure/brace validation;
- Hotfix 10 lightweight Chromium audit at 1920×1080 and 1366×768;
- focused Settings Chromium render;
- actual Jinja Home render;
- actual Jinja Desktop & Dock Settings render after final styling.

The lightweight Home browser audit specifically asserts seven Dock items, widgets hidden on load, immediate View-menu click execution below the fixture threshold, lower-right Companion geometry, on-demand panel behavior and no horizontal overflow.

## Production limitation

The packaged source can be deterministically exercised in Chromium, but a ZIP test is not proof that a remote server has deployed it. The main-site verification therefore starts with `/version`, response headers and actual Network asset URLs. If the revision fingerprint is absent, the server/CDN is still serving an older release regardless of what files were uploaded.

Protected database writes, provider integrations and role-specific production data remain mandatory live checks after deployment.

## Compatibility / non-goals

- No agreement/legal semantics are changed.
- No production database reset is required.
- Historical migrations remain intact.
- Existing permissions and server-side authorization remain authoritative.
- Heavy suite runtimes are not deleted; they are simply not booted on idle Home/Settings when unnecessary.
- Apple proprietary font files or artwork are not bundled.

## Deployment-survival audit — revision B
A second package-level audit found a cache class that source/UI tests alone could miss: browser-visible logos, favicons, PWA icons and other static images could be referenced without a Hotfix revision while `/static/*` responses were marked immutable for one year. On a device that had previously loaded an earlier Hotfix 10, those files could remain stale even when the new ZIP was correctly deployed.

Revision `27A101-H10L-20260827E` closes this gap:
- every literal template `url_for('static', ...)` is cache-busted with the current asset revision;
- only `/static/*?rev=<current revision>` receives one-year immutable caching; unversioned static requests must revalidate;
- PWA 192/512 icons use Hotfix-specific filenames;
- the CSS-embedded compact Livenza mark uses a Hotfix-specific filename;
- package audit found zero missing static references, zero missing literal template includes/renders, zero missing literal `url_for` endpoints, zero case-collision paths and zero whitespace/non-ASCII deployment paths.

Fresh verification after these changes: 108/108 contracts pass; Python compilation passes; 9/9 production JavaScript files pass syntax validation; 73/73 Jinja templates parse; 6/6 CSS files pass structural validation; Hotfix 10 light-shell, focused runtime, brand desktop/mobile and Livenza default-wallpaper Chromium audits all pass.

## Hotfix 10 Dock refinement — Revision C

Revision C refines the deployed lightweight Home shell without reintroducing the legacy UI bundles. The Dock now uses a restrained macOS-like translucent navy glass material, original Livenza suite squircles with explicit SVG stroke rendering, suite-specific gradients, a visual separator before Settings, matching active dots, and requestAnimationFrame pointer-field magnification using transform-only scale/lift. The same Livenza symbol stroke contract is applied to the lightweight Settings Dock.

The change also fixes the browser fallback that could render inline Livenza SVG symbols as flat black fills when the lightweight shell did not define stroke/fill semantics.


## Revision D navigation recovery

Revision D hardens Home navigation against partial uploads, stale JavaScript and CDN mismatches. Suites controls are real links to `/?suites=1` and the server renders the Suites drawer open when that query flag is present, while `home_light.js` progressively enhances the same links into the normal instant drawer. Dock application entries remain ordinary anchors, so Agreements, Rooms, Queries, Reviews, Banking and Settings do not depend on JavaScript for navigation. A Home runtime-ready marker/watchdog makes missing or stale Home JavaScript observable.

## Revision E — interaction recovery for partial deployments

**Deployment revision:** `27A101-H10L-20260827E`

A production interaction failure was traced to progressive-enhancement handlers canceling real fallback links before confirming that their matching target UI existed. In a partial/mismatched deploy (for example new `home_light.js` with an older `base.html`), this could make Suites, View, Window, Help, Widgets and Search appear completely dead.

Revision E binds/intercepts these controls only when the corresponding drawer, popover, widget stack, companion panel or command palette is present. Otherwise the browser follows the real server `href` normally. Dock application launchers remain ordinary links.

Verification includes a dedicated partial-deployment source contract and a Chromium fixture that intentionally omits the target UI while loading the new Home runtime; fallback clicks must remain uncancelled.

