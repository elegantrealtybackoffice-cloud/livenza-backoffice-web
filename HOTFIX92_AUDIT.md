# Hotfix 9.2 Audit — Bright Settings + Persistent Interactive Dock

**Product:** Tesla OS 27  
**Version:** 27.0.1  
**Build:** 27A101  
**Audit date:** 2026-08-27

## Scope

Hotfix 9.2 is a bounded continuation of the verified Hotfix 9.1 interface. It addresses the Desktop & Dock / System Settings behavior seen in the deployed UI without changing business data, permissions, Flask workflow semantics or provider integrations.

## Root causes corrected

1. **Stale dark appearance migration** — Hotfix 9.1 defaulted new users to Light, but still merged `appearance.mode` from the older v1.9 / v27.0.1 local preference namespaces. A previously stored dark value could therefore make the current Settings detail canvas appear graphite/purple even though the new default was Light.
2. **Dock hidden on direct application routes** — a Hotfix 9 route-specific CSS rule suppressed the Dock outside Home. That conflicted with the persistent-Dock interaction requirement and meant Desktop & Dock controls could have no immediately visible target while the user was in Settings.
3. **Incomplete Dock magnification** — the proximity algorithm changed scale only. The expected vertical lift was not applied, so hover feedback was flatter than the intended macOS-style spatial response.
4. **Magnification toggle residual transform** — disabling magnification while the pointer was already over the Dock could leave an existing inline scale until pointer exit.
5. **Route bottom safe area** — restoring the Dock exposed a later 24px route padding override that could allow long application content to scroll behind the fixed Dock.

## Implemented behavior

- New local preference namespace: `livenza.settings.v2702`.
- Older v190/v2701 preferences still migrate, but legacy `appearance.mode` is intentionally discarded once so Hotfix 9.2 starts in the bright Light appearance. A user can explicitly select Dark again afterward and that choice persists in the v2702 namespace.
- Light appearance explicitly sets native `color-scheme: light` for consistent browser form controls.
- The global Dock remains available on signed-in direct application routes as well as Home.
- Direct-route content reserves `calc(var(--mac-dock-height) + 36px)` at the bottom so the persistent Dock never covers page content.
- Dock magnification now combines proximity scale with up to 13px of vertical lift.
- Turning magnification off immediately clears active Dock scale/lift transforms.
- Desktop & Dock Settings copy now states that changes apply instantly on every signed-in page.

## Verification

Source verification on the Hotfix 9.2 working tree:

- Hotfix 8 + 9 + 9.1 + 9.2 contract suite: **68/68 passed**.
- Python source compilation: **passed**.
- Production JavaScript syntax: **passed for every `static/*.js` file**.
- Jinja parsing: **73/73 templates passed**.
- CSS brace/token sanity: **passed**.

Focused Chromium render of the actual `system_settings.html` / Desktop & Dock pane at **1440×900** after the final Settings/Dock visual changes confirmed:

- appearance: `light`;
- application canvas: `rgb(245, 248, 252)`;
- Settings detail: `rgb(245, 245, 247)`;
- Settings card: translucent white `rgba(255, 255, 255, 0.92)`;
- Dock: visible `display:flex`, 58px high.

The full inherited Hotfix 9 multi-scenario Playwright jobs were also attempted in this packaging environment, but the Playwright driver transport timed out / terminated with `EPIPE` before completing. This is recorded as an environment/tooling limitation rather than a pass. The unchanged Hotfix 9.1 baseline had previously completed its 48 shell scenarios and 26 real-template scenarios successfully; Hotfix 9.2 additionally uses focused source contracts and the targeted actual-Settings Chromium render for the modified paths.

## Deployment limitation

The packaging environment does not authenticate into the production `backoffice.livenza.life` database/provider session. After upload, follow `VERIFY_DEPLOY.txt` and specifically test the Desktop & Dock controls in the real signed-in browser session.
