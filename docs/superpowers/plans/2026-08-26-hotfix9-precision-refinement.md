# Tesla OS 27 Hotfix 9 Precision Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Suites launcher and all functional suite interiors into a vibrant, highly aligned Liquid-Glass-inspired browser OS while preserving working Livenza routes, permissions, data workflows and Hotfix 8 window management.

**Architecture:** Keep `static/macos27_system.css` and `static/macos27_shell.js` as the sole authoritative shell/theme layer. Rework launcher markup in `_application_groups.html` around compact app cards that derive visual identity from the application registry; keep suite interiors light and readable with family-specific semantic accents. Add contract and Chromium audits before each production change and remove, rather than override, obsolete legacy launcher styling.

**Tech Stack:** Flask/Jinja, vanilla CSS, vanilla JavaScript, Python unittest, Playwright/Chromium.

**Spec:** Approved Hotfix 9 Precision UI/UX Refinement Brief in the active conversation; Apple macOS 27 UI reference at `MACOS27_UI_REFERENCE.md`.

## Global Constraints

- Tesla OS name/version/build remain `Tesla OS 27`, `27.0.1`, `27A101`.
- Preserve all existing backend routes, database models, permissions and integrations.
- No separate `hotfix9.css`; authoritative changes belong in `static/macos27_system.css`.
- No dummy Dock apps, tabs, menu commands or launcher tiles.
- No default personal-photo wallpaper; custom user-selected wallpaper remains supported.
- Default desktop body typography remains 13px/16px and macOS 27 shell geometry remains 34px menu bar, 58px Dock, 36px Dock icons, 16px windows, 256px sidebars and 344px widgets.
- Reduced Motion must disable spatial/decorative animations while preserving state clarity.

---

### Task 1: Hotfix 9 Contract Gate

**Files:**
- Create: `tests/test_hotfix9_visual_contracts.py`
- Modify: none
- Test: `tests/test_hotfix9_visual_contracts.py`

**Interfaces:**
- Consumes: existing launcher markup, shell CSS/JS and Livenza registry.
- Produces: failing requirements for compact launcher cards, category identities, light suite surfaces, no broken words, curated wallpaper defaults and motion states.

- [ ] **Step 1: Write failing tests** that require `.suite-launch-card`, `.suite-launch-icon`, `.suite-launch-title`, `data-category-tone`, `word-break:normal`, a light launcher material, light suite surface tokens, no `AUTHORIZED APP`, no launcher media photos, compact account footer and reduced-motion coverage.
- [ ] **Step 2: Run tests and verify RED** with `python -m unittest tests.test_hotfix9_visual_contracts -v`; expected failures reference missing Hotfix 9 selectors/markup.
- [ ] **Step 3: Do not change production code in this task.**

### Task 2: Suites Launcher Markup and Functional Metadata

**Files:**
- Modify: `templates/_application_groups.html`
- Modify: `templates/base.html`
- Modify: `app.py`
- Test: `tests/test_hotfix9_visual_contracts.py`

**Interfaces:**
- Consumes: `LIVENZA_APP_REGISTRY`, `ui_app_available(endpoint)` and Jinja icon macro.
- Produces: `ui_app_meta(endpoint)` context helper and launcher tiles with `data-app-family`, `data-app-accent`, `data-app-accent2`.

- [ ] **Step 1: Run Task 1 tests to confirm RED remains.**
- [ ] **Step 2: Add `ui_app_meta(endpoint)`** returning a registry dict and expose it in the context processor without changing availability rules.
- [ ] **Step 3: Rewrite launcher branch of `app_item()`** as a compact card containing only icon, title, 1 concise description, optional status/launch affordance; remove media image and `AUTHORIZED APP` label.
- [ ] **Step 4: Add category-tone metadata** to Core, Operations, Finance, Communication, Connections and Administration tabs/panels.
- [ ] **Step 5: Change Suites footer** to a compact identity/control row; keep Logout functional.
- [ ] **Step 6: Run contracts and verify relevant markup tests pass.**

### Task 3: Liquid Glass Suites Launcher CSS

**Files:**
- Modify: `static/macos27_system.css`
- Modify: `static/legacy_modules.css` only to delete superseded launcher rules if they still win.
- Test: `tests/test_hotfix9_visual_contracts.py`

**Interfaces:**
- Consumes: Hotfix 9 launcher classes and category metadata.
- Produces: polished light/translucent launcher with aligned tabs and responsive card grid.

- [ ] **Step 1: Add a failing CSS contract** for launcher background, grid min-width, no broken words and tab geometry.
- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Implement `.suites-launcher` Liquid Glass material** using translucent light surface, blur/saturation, inner edge highlight and restrained shadow independent of OS auto-dark preference unless the user explicitly selected dark appearance.
- [ ] **Step 4: Implement category tabs** at 26–28px high with icon size 14–16px, baseline alignment, no ordinary-width wrapping, horizontal scrolling under constrained width and category-specific selected accent.
- [ ] **Step 5: Implement responsive `.suite-launch-grid` and `.suite-launch-card`** with 220–260px minimum cards, 18–20px radius, 16–18px padding, 56px app icons, two-line descriptions and normal word breaking.
- [ ] **Step 6: Remove conflicting legacy launcher/card rules instead of adding `!important` where deletion is sufficient.**
- [ ] **Step 7: Run contracts and verify GREEN.**

### Task 4: Vibrant Light Suite Canvas and Typography

**Files:**
- Modify: `static/macos27_system.css`
- Test: `tests/test_hotfix9_visual_contracts.py`

**Interfaces:**
- Consumes: window `data-window-family`/accent tokens set by `macos27_shell.js`.
- Produces: family-specific light suite surfaces for productivity, occupancy, pipeline, reputation, creative, hospitality, finance, utilities, communication, documents and system.

- [ ] **Step 1: Add failing contracts** for `--suite-canvas`, `--suite-card`, family tint variables, global `word-break:normal`, 13px/16px content typography and readable dark labels on light default suite surfaces.
- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Implement suite canvas tokens** with off-white/light-tinted working surfaces; use colour in sidebars, selections, cards, chips, metrics and charts rather than black full-window backgrounds.
- [ ] **Step 4: Normalize headings, labels, tabs, cards, buttons, forms and table cells** to the approved font scale and 4/8/12/16/20/24/32 spacing rhythm.
- [ ] **Step 5: Add zero-broken-word policy** for app titles/headings while allowing controlled description wrapping.
- [ ] **Step 6: Add family-specific card/canvas accents** for Agreements, Rooms/Residents, Queries, Billing/Banking/Electricity, Food, WhatsApp/Email/Drive, Reviews/Video Wall/Letterhead and Settings.
- [ ] **Step 7: Run contracts and verify GREEN.**

### Task 5: Motion, Window Polish and Interaction Restraint

**Files:**
- Modify: `static/macos27_system.css`
- Modify: `static/macos27_shell.js`
- Test: `tests/test_hotfix9_visual_contracts.py`

**Interfaces:**
- Consumes: existing window lifecycle and requestAnimationFrame Dock proximity system.
- Produces: distinct press, menu, tab, card, window and reduced-motion timing behavior.

- [ ] **Step 1: Add failing motion contracts** for card lift <=3px, launcher materialisation, tab fill transition, active-window elevation and reduced-motion cancellation.
- [ ] **Step 2: Verify RED.**
- [ ] **Step 3: Refine launcher open/close animation** to short scale/opacity/materialisation from its trigger rather than generic drawer sliding.
- [ ] **Step 4: Refine card hover** to 1–3px lift with shadow/accent change and pressed compression.
- [ ] **Step 5: Preserve requestAnimationFrame Dock proximity animation** and eliminate any new per-pointer geometry reads.
- [ ] **Step 6: Verify Reduced Motion removes launcher/window spatial motion.**
- [ ] **Step 7: Run contracts and verify GREEN.**

### Task 6: Wallpaper and Home Polish

**Files:**
- Modify: `templates/settings/_wallpaper.html`
- Modify: `static/macos27_system.css`
- Modify: `static/macos27_shell.js` if default-selection logic needs adjustment.
- Test: `tests/test_hotfix9_visual_contracts.py`

**Interfaces:**
- Consumes: existing wallpaper persistence/local preference system.
- Produces: curated original Livenza abstract defaults; custom user images remain supported.

- [ ] **Step 1: Add failing test** that built-in presets are abstract/gradient Livenza variants and no personal-photo asset is used as a built-in/default choice.
- [ ] **Step 2: Verify RED if current markup still exposes personal-photo wallpaper.**
- [ ] **Step 3: Curate wallpaper labels/previews** and ensure custom upload is the only path to personal-photo wallpaper.
- [ ] **Step 4: Preserve first-paint preference restoration and crossfade.**
- [ ] **Step 5: Run contracts.**

### Task 7: Chromium Launcher and Suite Visual Audit

**Files:**
- Create: `tests/hotfix9_visual_fixture.html`
- Create: `tests/run_hotfix9_browser_audit.py`
- Test artifacts: `tests/audit_artifacts/hotfix9/`

**Interfaces:**
- Consumes: authoritative CSS and production-style launcher/window markup.
- Produces: browser evidence at 1920×1080, 1600×900, 1440×900, 1366×768, 1280×720 and 1152×720.

- [ ] **Step 1: Build fixture** with desktop, Suites launcher, Agreements, Banking, Queries, Letterhead, Settings and overlapping windows.
- [ ] **Step 2: Run audit and verify it catches any initial clipping/overflow issue.**
- [ ] **Step 3: Fix only production CSS/markup responsible for failures.**
- [ ] **Step 4: Audit** no page overflow, 58px Dock, 344px widgets where applicable, launcher bounds, card title wrapping, category tab alignment, no black suite canvas, key text clipping, safe window bounds and Reduced Motion.
- [ ] **Step 5: Capture screenshots for launcher and representative suite families.**
- [ ] **Step 6: Run the full Chromium audit twice consecutively after the final production change.**

### Task 8: Full Verification, Documentation and Packaging

**Files:**
- Create: `HOTFIX9_AUDIT.md`
- Modify: `README.md`
- Modify: `VERIFY_DEPLOY.txt`
- Modify: `UPLOAD_INSTRUCTIONS.txt`
- Package: `/mnt/data/Tesla_OS_27_v27.0.1_Build_27A101_COMPLETE_HOTFIX9_PRECISION_UI.zip`

**Interfaces:**
- Consumes: exact verified Hotfix 9 working tree.
- Produces: complete ZIP, <=100-file split ZIPs, manifest and SHA-256 checksums.

- [ ] **Step 1: Run all Hotfix 8 and Hotfix 9 unittest contracts.**
- [ ] **Step 2: Compile all Python with `python -m compileall -q .`.**
- [ ] **Step 3: Parse every Jinja template with a standalone Jinja environment.**
- [ ] **Step 4: Run `node --check` on every production JavaScript file and inline-script extractor checks where applicable.**
- [ ] **Step 5: Run Hotfix 9 Chromium audit twice.**
- [ ] **Step 6: Search for dummy controls, blank launcher icons, `AUTHORIZED APP`, unwanted broken-word rules and stale Hotfix 8 deployment copy.**
- [ ] **Step 7: Update audit/deployment docs with exact evidence and sandbox limitations.**
- [ ] **Step 8: Create deterministic complete ZIP and split at 100 files.**
- [ ] **Step 9: Run ZIP integrity, manifest reconstruction and SHA-256 verification.**
