# Livenza Back Office Web 1.4.5

UI refinement and deployment-safe polish release.

## Changes
- Footer credit is explicitly rendered on every normal page: **Created by Rishabh Kothari**.
- Footer retains Livenza Life LLP copyright and Head Office address.
- Every native select/option control is forced into `color-scheme: light`, with white menu background and black/navy text to prevent Windows/Edge black-on-black dropdowns.
- Custom popovers and menus are locked to the same white/black/navy palette.
- Top navigation is rebuilt into fixed lanes: Brand | application tabs | View | account controls.
- Application tabs never wrap haphazardly; on smaller displays they become a neat horizontal scrolling row.
- Full Screen + Rotate are consolidated into a separate **View** pull-down.
- Active application tab gets a clean white/navy state.
- Adds progressive cross-page View Transitions, intersection-based content reveals, title transitions, footer motion and refined glass interactions.
- Keeps fullscreen stability and fullscreen-safe navigation from v1.4.4.
- CSS/JS cache key bumped to 1.4.5.

## Deploy
Upload the contents of the DIRECT ROOT FILES package to the root of the existing `livenza-backoffice-web` GitHub repository, replace matching files, and commit to `main`.

Verify `/version` returns `Web 1.4.5` after Render redeploys.
