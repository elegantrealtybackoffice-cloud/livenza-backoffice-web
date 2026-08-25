# Livenza Back Office Web 1.5.11

Web 1.5.11 restores the website rotation tab to the authenticated top header.

## Rotation menu

- Automatic browser orientation
- Portrait workspace
- Landscape workspace
- 90° clockwise rotation
- 180° rotation
- 270° counter-clockwise rotation
- Browser Full Screen with a safe theatre fallback

The button remains compact in the white translucent header, becomes icon-only at narrower desktop and mobile widths, and hides with other right-side controls when the header contracts on scroll.

The selected display mode is stored locally, survives in-place page navigation and is reapplied after fullscreen or viewport changes. The menu supports keyboard Arrow/Home/End navigation, Escape closing and outside-click dismissal.

No database migration is required.
