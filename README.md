# Livenza Back Office Web 1.4.3

Stability and visual polish release.

## Changes
- Footer now clearly shows `Created by Rishabh Kothari`, Livenza Life LLP copyright, Head Office address, live date/time and build version.
- Apple-inspired system typography using the native Apple/system font stack, tighter display letter spacing and Apple-like heading weights.
- More liquid-glass motion: page entrance, aurora drift, glass spotlight, card lift, icon float, button sheen and a subtle navigation progress transition.
- Rotate menu rebuilt as a global fixed liquid-glass popover so it cannot be clipped by the top navigation.
- Rotate modes: Auto, Portrait, Landscape, 90°, 180° and 270°. Fullscreen still attempts native device orientation lock where the browser supports it.
- Database navigation resilience added for Render + Supabase Session Pooler: pre-ping, connection recycling, timeout controls and failed-request rollback cleanup.
- Removed duplicated admin route decorator.
- Cache-busting updated to 1.4.3.

## Deploy
Upload the contents of the ROOT UPLOAD zip to the root of the existing GitHub repository, replacing matching files. Commit to `main` and allow Render to redeploy.

Verify `/version` returns `Web 1.4.3` after deployment.
