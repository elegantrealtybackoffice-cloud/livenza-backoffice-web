# Tesla OS 27 Hotfix 8 Suite Visual System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Upgrade the verified Hotfix 7 browser-OS shell so every functional Livenza suite has visible app artwork, a distinct colour identity, polished macOS-style window interiors, spatial motion, clean text alignment, and no extra lag.

**Architecture:** Preserve the existing Flask routes and window manager. Add one authoritative suite identity registry to the existing application registry, render an original icon layer through the existing Livenza SVG symbols, and implement suite-specific colour/motion through `macos27_system.css` using `data-window-app`/`data-page` instead of adding another stylesheet. Improve the existing window manager and browser fixture rather than creating parallel navigation code.

**Tech Stack:** Flask/Jinja templates, vanilla JavaScript, CSS, Chromium headless audits, Python unittest/static contract checks.

**Spec:** Approved Hotfix 8 refinement brief and approved sub-window amendment from 2026-08-26.

## Global Constraints

- Keep Tesla OS 27 / version 27.0.1 naming.
- Do not change working backend data models, routes, permissions, agreement logic, billing logic, or integration credentials.
- Dock must show only routes returned by `ui_app_available`.
- Do not copy Apple application artwork or redistribute Apple fonts/assets.
- Use exact macOS 27 geometry already documented in `MACOS27_UI_REFERENCE.md`.
- Do not add another global CSS override file; extend/refactor `static/macos27_system.css`.
- Respect `prefers-reduced-motion` and existing user motion settings.
- Preserve Hotfix 7 wallpaper, window lifecycle, and functional-only rules.

---

### Task 1: Visual Contracts
- Create `tests/test_hotfix8_visual_contracts.py` validating visible glyph rules, semantic app identities, suite accents, window motion, and no new global stylesheet.
- Run tests and confirm RED on Hotfix 7 baseline.
- Implement the minimum source changes required by later tasks.

### Task 2: App Icon System
- Modify `_application_groups.html` to emit endpoint-aware app icon markup.
- Extend `_livenza_symbols.html` only with original Livenza vector symbols where needed.
- Refine Dock/drawer/suggestion icon CSS so every icon has a legible glyph and unique application identity.
- Test icon visibility and endpoint mapping.

### Task 3: Suite Colour Identity
- Extend `LIVENZA_APP_REGISTRY` with `family`, `accent`, and `accent2` metadata without changing route availability.
- Pass metadata through Dock/window attributes.
- Add semantic accent tokens for every functional suite and apply them to titlebars, headers, selection states, badges, tables, cards, and empty states.
- Keep workspace surfaces readable rather than fully saturated.

### Task 4: Application Interior Refinement
- Normalize `page-head`, `section-head`, cards, forms, tables, tabs, badges, list rows, sidebars and empty states inside managed windows.
- Add per-suite presentation for Agreements, Rooms/Residents, Queries, Reviews, Video Wall, Food, Billing, Banking, Electricity, WhatsApp, Email, Drive, Letterhead, Settings and master-data pages.
- Audit text baseline, padding, wrapping and overflow.

### Task 5: Motion and Window Polish
- Refine opening/minimizing/restoring/focus transitions and content reveal.
- Use requestAnimationFrame/cached geometry for Dock effects only.
- Add restrained sidebar/tab/card/row transitions.
- Verify Reduced Motion removes spatial movement.

### Task 6: Performance and Legacy Cleanup
- Remove redundant presentation imports/classes where safe.
- Avoid large backdrop-filter content areas and expensive perpetual effects.
- Confirm polling/timers remain visibility-aware.
- Run CSS/JS size and duplicate-rule audit.

### Task 7: Chromium Visual Audit
- Build deterministic fixture using production CSS/JS.
- Capture desktop, Dock hover, a productivity window, finance window, creative window, Settings, overlapping windows at 1920x1080, 1440x900, 1366x768, 1152x720.
- Fail on overflow/collisions/missing glyphs/blank icons.

### Task 8: Final Verification and Packaging
- Run full source contracts, Python compile, JS syntax, Jinja parse, Chromium audits twice.
- Create complete ZIP and <=100-file split ZIPs.
- Verify archive integrity, manifest, checksums and deployment notes before delivery.
