# Tesla OS 27 — macOS 27 UI Reference

This implementation reference was derived from the user-supplied **Apple macOS 27 UI Kit.sketch** package. It records the design measurements and behavior translated into Tesla OS 27. It does **not** redistribute Apple font files or other extracted proprietary font binaries.

## Kit Coverage Reviewed

The Sketch package contains **37 pages, 285 shared layer styles and 67 shared text styles**. The complete page inventory is: Library Preview; Colors; Materials; Alerts; Buttons; Color Wells; Combo Boxes; Dialogs; Disclosure Controls; Forms; Group Boxes; Image Wells; Menu Bar and Dock; Menus; Notifications; Pointers; Pop-up and Pull-down Buttons; Popovers; Progress Indicators; Scrollbars; Search Fields; Segmented Controls; Sidebars; Sliders; Steppers; Text Fields; Titlebars and Toolbars; Checkboxes; Radio Buttons; Switches; Tooltips; Windows; Change Log; and Kit, plus separator pages.

The implementation pass mapped the pages most relevant to the Livenza shell directly and used the remaining control pages to validate state, sizing, focus and light/dark conventions.

### macOS 27.0.1 kit change-log rules incorporated

The supplied kit’s June 23, 2026 **27.0.1** change log confirms several rules that directly affect this build:

- Materials were updated for light/dark Liquid Glass and new vibrant text colors.
- Dock glass and app-icon layout were updated, and running-app indicator dots were added.
- Notification corner radius changed from 16 pt to **20 pt**.
- Sidebars were extended **edge-to-edge**, rebuilt for resizability and gained tinted symbols.
- Search fields and text fields removed the old “over-glass” variants; form content should therefore remain more opaque/readable.
- Window corner radius for regular windows changed to **16 pt**.
- Toolbar architecture is named Unified Compact Toolbar / Unified Toolbar / Expanded Toolbar, with updated grouped-control metrics and inactive states.
- Menu sizing is expressed as `.mini`, `.small` and `.regular` control sizes rather than arbitrary point-size labels.

## Core Geometry

| Component | macOS 27 kit measurement | Tesla OS 27 use |
| --- | ---: | --- |
| Menu bar | 1000 × 34 | Desktop menu bar is 34 px high |
| Apple/logo menu item | 33 × 24 | Livenza desktop mark uses the same compact control rhythm |
| Standard menu item | ~53 × 24 | Desktop menu targets use 24 px internal row rhythm |
| Dock | 1107 × 58 | Dock height token is 58 px |
| Dock item slot | 36 × 47 | Suite icon footprint follows the compact Dock cadence |
| Source app icon | 72 × 72 | Artwork is rendered down into the Dock slot |
| Notification | 344 × 78 | Home widget width token is 344 px |
| Sidebar | 256 px wide | Application sidebar token is 256 px |
| Sidebar Large row | 40 px | Used for emphasized navigation |
| Sidebar Medium row | 32 px | Default navigation rhythm |
| Sidebar Small row | 24 px | Compact navigation rhythm |
| Menu width | 160 px | Compact popover/menu baseline |
| Regular menu row | 24 px | Main menu item height |
| Small menu row | 22 px | Compact menu variant |
| Mini menu row | 19 px | Dense menu variant |
| Side-by-side alert | 260 × 170 | Compact confirmation/dialog target |
| Stacked alert | 260 × 238 | Vertical-action alert target |
| Alert button | 228 × 28 | Alert action control scale |
| Popover | 230 × 230 | Standard compact popover target |
| XL toolbar control | 36 px high | Large toolbar mode |
| XL search | 159 × 36 | Large toolbar search baseline |
| Medium toolbar control | 24 px high | Standard compact toolbar mode |
| Medium search | 149 × 24 | Compact toolbar search baseline |
| XL icon control | 28 × 28 | Large toolbar icon button |
| Medium icon control | 20 × 20 | Compact toolbar icon button |
| Example application window | 840 × 400 | Window proportion reference |
| Window background with sidebar | 600 × 300 | Content/sidebar proportion reference |
| Utility panel | 280 × 400 | Inspector/utility panel reference |

## Typography Scale

The kit’s shared text styles establish the hierarchy below. Tesla OS uses the native system-font stack so the browser selects the appropriate installed platform font; no Apple font binaries are bundled or redistributed.

| Style | Size / line height |
| --- | ---: |
| Large Title | 26 / 32 |
| Title 1 | 22 / 26 |
| Title 2 | 17 / 22 |
| Title 3 | 15 / 20 |
| Headline | 13 / 16, bold |
| Body | 13 / 16 |
| Callout | 12 / 15 |
| Subheadline | 11 / 14 |
| Footnote / Caption | 10 / 13 |

The interface avoids oversized web-dashboard typography. Text hierarchy comes from weight, spacing and contrast before increasing size.

## System Color Language

The kit uses the macOS semantic system-color family rather than a monochrome beige palette. Tesla OS maps the same design idea into its own CSS variables:

- Blue: primary interactive/action accent
- Violet/indigo: AI and premium Livenza functions
- Green: success/live/healthy states
- Orange/yellow: attention and operational warnings
- Cyan/teal: information and connected-service states
- Pink/red: high-attention and destructive states

For label hierarchy, the light appearance uses approximately 85% black for primary labels, 50% for secondary labels and 25% for tertiary labels. Dark appearance follows the corresponding white-label hierarchy.

## Liquid Glass Translation

The Sketch Materials page uses custom glass materials with different optical treatments based on surface purpose. Tesla OS follows the hierarchy rather than applying one generic blur everywhere.

### Dock
- Very light optical blur and distortion.
- Multiple neutral translucent layers.
- Strong inner edge highlights and subtle shadows.
- The wallpaper remains clearly visible and colorful through/around the Dock.

### Notifications / widgets
- Moderate blur (kit material around 15 px).
- Low distortion.
- Soft outer shadow and bright edge treatment.
- High-contrast foreground content remains readable.

### Menus
- Stronger blur (kit material around 20 px).
- Reduced saturation under the menu surface.
- More pronounced shadow than notifications.
- Selection and iconography stay crisp.

### Large regular glass surfaces
- Strong blur (kit material around 30 px), increased saturation and deeper shadow.
- Used sparingly for navigational/transient surfaces, not every content card.

### Sidebars and windows
- Active sidebar surfaces are light/translucent, while the main window/content surface is substantially more opaque and readable.
- This is the key rule used to remove the previous washed-out beige-on-beige appearance.

## Desktop Composition

Home is treated as an operating-system desktop rather than a conventional dashboard page:

1. A slim 34 px menu bar at the top.
2. A vibrant wallpaper as the desktop/content backdrop.
3. A compact right-side stack of operational widgets using the 344 px notification/widget cadence.
4. A persistent bottom Dock containing the authorized Suite applications individually.
5. The Livenza Companion remains a secondary assistant layer rather than the dominant visual object.

## Dock Behavior

- Dock remains fixed while the page scrolls.
- Each authorized Suite appears as its own application icon.
- Active page gets an indicator dot.
- Pointer proximity produces restrained magnification rather than a large bounce on every item.
- Horizontal overflow remains possible on narrower desktops without destroying icon sizing.
- The Suites launcher is retained as an additional app-grid entry point, not the sole way to launch modules.

## Menus, Alerts and Widgets

- Menus use compact 24 px row rhythm and logical separators.
- Right-side widgets follow notification geometry instead of generic large dashboard cards.
- Alerts should remain compact and task-focused rather than occupying large modal panels.
- Toolbars group related controls and avoid giving every icon a large independent pill background.

## Accessibility and Readability

- Primary content is not placed on heavily transparent surfaces.
- Primary text uses strong semantic contrast.
- Secondary/tertiary text is visibly subordinate but not faded into the background.
- Focus, hover, active and selected states remain distinguishable without relying on color alone.
- Reduced-motion preferences disable nonessential Dock and glass animation.
- Responsive rules reduce density on small screens rather than shrinking type below the kit hierarchy.

## Files Implementing This Pass

- `templates/base.html`
- `templates/dashboard.html`
- `templates/_application_groups.html`
- `static/desktop_v2701.css`
- `static/desktop_v2701.js`
- `static/livenza_liquid_wallpaper.webp`
- `tests/test_macos_desktop_ui.py`

The existing backend routes, permissions, authentication, agreements, masters, billing, banking, electricity, communications, integrations and Letterhead workflows are intentionally left intact.

## Hotfix 6 implementation lock

The exact-kit implementation now uses these extracted values as CSS contracts: menu bar 34px; Dock 58px; app icon 36px; icon center stride 45px; running dot 4px; window radius 16px; unified toolbar 52px; compact toolbar 40px; expanded toolbar 77px; sidebar 256px; notification/widget width 344px; notification radius 20px; alert radius 26px; regular menu/control row 24px; body type 13/16.

Focus is represented as the extracted two-ring treatment: a 1px inner ring using `rgba(0,136,255,.15)` plus a 3.5px outer ring using `rgba(0,136,255,.25)`. The web motion layer intentionally does not label its duration/easing values as exact Apple internals because the Sketch kit defines visual states, geometry, and material appearance rather than system runtime animation constants.
