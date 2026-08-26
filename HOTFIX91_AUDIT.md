# Hotfix 9.1 Audit — Marquee Removal + Vibrant Suite Materials

Tesla OS 27 · Version 27.0.1 · Build 27A101

## Scope

Hotfix 9.1 is a bounded refinement on the verified Hotfix 9 single-window design system. It removes the legacy operational marquee/status strip from every frontend surface and its runtime polling path, eliminates hidden ticker spacing dependencies, makes the normal application appearance bright by default instead of inheriting Windows/browser dark mode, and strengthens suite-specific colour materials while keeping one shared application-window language.

## Marquee/status-strip removal

Removed from:

- `templates/base.html` global shell markup.
- `static/app.js` `/api/marquee` polling, resize work and animation rendering.
- `static/tv_compat.js` drawer positioning dependency.
- `static/macos27_shell.js` Control Centre and Focus preferences/classes.
- System Settings → Automations marquee builder.
- System Settings → Control Centre live-status toggle.
- System Settings → Focus live-status toggle.
- `app.py` marquee endpoint, data builder, Moneycontrol quote helper/cache, runtime template context and server settings keys.
- Authoritative and legacy CSS ticker geometry/animation selectors and ticker-height spacing dependencies.

The protected companion weather/operations panel remains independent and continues to provide live operational information when enabled.

## Appearance and colour corrections

- New/default appearance remains Light and no longer auto-switches application canvases to black because the host OS/browser is dark.
- Explicit Dark remains available as an intentional user selection and now uses layered graphite/blue-gray materials rather than near-black slabs.
- Shared suite cards use more visible, still restrained colour-mixed materials.
- Electricity uses an amber/orange/mint utility palette with distinct Saved Connections, Current Records, Attention and Providers stat accents.
- Banking, Rooms/Residents, Queries, Communications, Documents and Settings retain the Hotfix 9 common geometry but receive richer tertiary accent support.
- Direct application routes retain the common 52px glass titlebar and desktop-only Dock remains hidden.

## Verification

Final source verification completed on the exact working tree used for packaging:

- Hotfix 8 + Hotfix 9 + Hotfix 9.1 contracts: **62/62 passed**.
- Python source compilation: passed.
- Production JavaScript syntax: passed for all files in `static/*.js`.
- Jinja templates parsed: **73/73**.
- Hotfix 9 multi-resolution Chromium shell audit: **48 scenarios, 0 failures**, repeated after the final production changes.
- Real-template Chromium audit: **26 scenarios, 0 failures**, repeated after the final production changes.
- Viewports include 1920×1080, 1600×900, 1440×900, 1366×768, 1280×720 and 1152×720 in the shell audit, plus 1440×900 and 1152×720 for the real-template suite audit.
- Source scan confirms no marquee/ticker implementation remains in `templates/`, `static/` or runtime application code.

## Environment limitation

The packaging sandbox does not authenticate into the production `backoffice.livenza.life` database/provider environment. The browser audits render the production shell and real Jinja suite templates deterministically in Chromium. After deployment, follow `VERIFY_DEPLOY.txt` for live role, database, PDF and integration checks.
