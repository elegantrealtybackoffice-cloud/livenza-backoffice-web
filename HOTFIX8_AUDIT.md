# Hotfix 8 macOS 27 Suite-Polish Audit Record

Tesla OS 27 · Version 27.0.1 · Build 27A101

Hotfix 8 extends the verified browser-OS shell into the application suites themselves. The pass focuses on functional Dock artwork, suite-specific colour identity, readable macOS-style sub-window surfaces, restrained motion, richer wallpaper choices, alignment fixes, and reduced hidden-tab work without changing the authoritative business/backend workflows.

## Visual-system scope

- Functional Dock applications use explicit SVG symbols and per-suite accent pairs; blank/generic placeholder tiles are rejected by tests.
- Managed windows receive `data-window-family`, accent and secondary-accent identity from the application registry.
- Suite families cover productivity, occupancy, pipeline, reputation, creative, hospitality, finance, utilities, communication, documents and system workflows.
- Core applications have explicit visual mappings for Agreements, Rooms, Residents, Queries, Reviews, Video Wall, Food, Billing, Banking, Electricity, WhatsApp, Email, Drive, Letterhead and Settings.
- Sub-window surfaces use restrained family colour washes while preserving high-contrast content cards, tables and forms.
- Finance/stat values use tabular numerals and non-wrapping value lines; key widget/date typography was browser-audited for clipping.
- Settings includes eight original built-in wallpaper variants (`aurora`, `spectrum`, `sequoia`, `midnight`, `livenza-blue`, `violet-glass`, `ocean`, `sunrise`) plus the existing custom-wallpaper workflow.
- Mascot temperature-chip clutter is removed; the assistant remains outside Dock/widget collision zones.

## Motion and performance changes

- Suite-content reveal is a short, restrained materialization and is disabled under Reduced Motion.
- Dock/application icon transitions preserve the Hotfix 7 requestAnimationFrame proximity behavior.
- Footer-clock scheduling now uses visibility-aware timeouts rather than an always-running 1-second interval.
- Video Wall state/heartbeat polling now pauses when the player document is hidden and resumes once visible, avoiding duplicate hidden-tab intervals.
- Retired presentation assets from older shell/theme generations remain removed. The final base shell loads the retained module compatibility stylesheet plus the authoritative `macos27_system.css` layer, with route-scoped Letterhead CSS only where required.

## Automated verification

Fresh verification on the exact Hotfix 8 source tree:

- `26/26` Hotfix 8 Python source-contract tests pass.
- Python compileall passes for the application source.
- Every production JavaScript file in `static/` passes `node --check`.
- `73/73` Jinja templates parse successfully.
- Chromium/Playwright visual audit covers `24` scenarios per run across 1920×1080, 1440×900, 1366×768 and 1152×720, including Agreements, Banking, Creative/Letterhead, Settings, overlapping windows and Reduced Motion.
- The 24-scenario Chromium audit passes twice consecutively after the final production-code change.
- Browser checks include 58px Dock geometry, 344px desktop widget geometry, safe-window bounds, no page overflow, no Dock/widget collision, nonblank Dock SVG artwork, key-text clipping, suite-window colour treatments and Reduced Motion suppression.
- Source scan contains only one remaining `setInterval` in the desktop clock implementation, and it is explicitly started/stopped by document visibility state.

## Environment limitation

The packaging sandbox does not have Flask installed and cannot authenticate into the deployed `backoffice.livenza.life` instance. The automated browser audit therefore exercises the actual Hotfix 8 production CSS/SVG/application-window design through a deterministic Chromium fixture rather than claiming a remote authenticated production-session certification. Server-backed writes, provider integrations, database state and deployment-specific behavior must be rechecked after upload using `VERIFY_DEPLOY.txt`.
