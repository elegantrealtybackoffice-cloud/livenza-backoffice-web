# Livenza Life Operations Cloud — Web 1.5.7

Web 1.5.7 refines the persistent mascot and header identity, and makes display rotation reliable on television, signage and video-wall browsers.

## Bottom-docked frameless mascot

- The mascot is reduced to a compact companion and fixed at the bottom-right of authenticated pages.
- Its translucent rectangular nudge has been removed, leaving the character, two light sparkles and a small LIVE/weather chip.
- The supplied light-background mascot artwork is blended and softly masked so it reads as a clean character rather than a rectangular image.
- Clicking the mascot still opens the complete weather, forecast, live operations and motivational quote panel to the left.
- On phones the mascot becomes smaller again, while the detail panel opens above it using the available viewport height.

## Minimal header L effect

- The L mark remains stable and transparent inside the compact header.
- The former conic ring, circular halo and white badge treatment are suppressed.
- Two tiny blue light points orbit independently at slow speeds, giving the logo a restrained AI signal without making the identity look playful or crowded.
- Reduced-motion preferences stop both points.

## Television and video-wall rotation

- Rotation dimensions use the browser's measured visual viewport, with `innerWidth`/`innerHeight` and physical screen fallbacks.
- 90°, 180° and 270° remain applied after entering or leaving fullscreen and after resizing the display.
- Portrait and landscape attempt the native Screen Orientation API in fullscreen, then fall back to a CSS view when the API is unavailable.
- Standard, WebKit, Mozilla and Microsoft fullscreen variants are handled.
- Browsers that do not expose or permit native fullscreen receive a reversible theatre-mode fallback that fills the browser viewport.
- The Display menu shows whether the current orientation is using native screen orientation or browser-safe mode.

## Deployment

No database migration is required. Deploy the package normally, confirm `/version` returns `Web 1.5.7`, then test each display angle and fullscreen state on the actual television or video-wall browser.
