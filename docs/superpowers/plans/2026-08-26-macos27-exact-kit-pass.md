# macOS 27 Exact Kit Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the approximate Hotfix 5 macOS styling with the exact geometry, typography, material, focus, state, Dock, widget, and motion behavior extracted from the supplied Apple macOS 27 UI Kit.

**Architecture:** Keep the existing Flask routes, templates, and application behavior intact. Consolidate the macOS 27 translation in `static/desktop_v2701.css` and `static/desktop_v2701.js`, with narrowly scoped template hooks where needed; extend the UI contract tests to lock exact kit metrics and motion/accessibility behavior. The new exact-kit layer remains the last-loaded UI layer so older warm-neutral styles cannot leak through.

**Tech Stack:** Flask/Jinja templates, CSS, vanilla JavaScript, Python `unittest` contract tests.

**Spec:** `MACOS27_UI_REFERENCE.md`

## Global Constraints

- Keep Tesla OS name/version `27` / `27.0.1` unchanged.
- Do not alter backend routes, authentication, business logic, agreements data, or integrations behavior.
- Use system font fallbacks; do not redistribute Apple font files.
- Use exact extracted kit metrics: 34px menu bar, 58px Dock, 36px Dock icon, 4px running dot, 16px window radius, 52px unified toolbar, 40px compact toolbar, 77px expanded toolbar, 256px sidebar, 344px notification/widget width, 20px notification radius, 26px alert radius, 24px regular menu rows, 13/16 body typography.
- Preserve reduced-motion support and keyboard focus visibility.

---

### Task 1: Lock exact kit metrics and state tokens

**Files:**
- Modify: `tests/test_macos_desktop_ui.py`
- Modify: `static/desktop_v2701.css`

**Interfaces:**
- Consumes: existing CSS custom properties in `:root`.
- Produces: exact geometry/material/focus tokens used by all later tasks.

- [ ] **Step 1: Write failing tests for missing exact metrics**

Add assertions for Dock icon/running dot, unified/compact/expanded toolbars, alert radius, focus rings, regular control height, and notification/widget width.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_macos_desktop_ui -v`
Expected: FAIL because the new exact tokens are not all declared.

- [ ] **Step 3: Add exact tokens and shared states**

Declare exact kit values in `:root`, including `--mac-dock-icon:36px`, `--mac-dock-running-dot:4px`, `--mac-toolbar-unified-height:52px`, `--mac-toolbar-compact-height:40px`, `--mac-toolbar-expanded-height:77px`, `--mac-alert-radius:26px`, `--mac-control-regular:24px`, and focus ring colors/sizes.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_macos_desktop_ui -v`
Expected: PASS for exact-token tests.

### Task 2: Rebuild Dock geometry and pointer-distance magnification

**Files:**
- Modify: `tests/test_macos_desktop_ui.py`
- Modify: `static/desktop_v2701.css`
- Modify: `static/desktop_v2701.js`

**Interfaces:**
- Consumes: `.mac-dock`, `.mac-dock-item`, `--dock-scale`.
- Produces: 58px Dock, 36px app icons, 45px stride, 4px running dots, pointer-distance magnification with reduced-motion fallback.

- [ ] **Step 1: Write failing tests for Dock algorithm hooks**

Assert JS includes pointer-distance scaling of adjacent icons, clamped influence, and reduced-motion bypass; assert CSS uses exact icon and dot variables.

- [ ] **Step 2: Run the Dock tests and observe failure**

Run: `python -m unittest tests.test_macos_desktop_ui.MacDesktopUiContractTests.test_exact_dock_geometry_and_motion -v`
Expected: FAIL before new implementation.

- [ ] **Step 3: Implement exact Dock sizing and motion**

Use 36px icon boxes and 45px center stride. Compute magnification from pointer distance with a smooth falloff affecting the hovered and neighboring icons; keep running dots visually stationary and remove transforms under `prefers-reduced-motion`.

- [ ] **Step 4: Run Dock test and full UI suite**

Run: `python -m unittest tests.test_macos_desktop_ui -v`
Expected: PASS.

### Task 3: Exact menu bar, widgets, notifications, and transient materials

**Files:**
- Modify: `tests/test_macos_desktop_ui.py`
- Modify: `static/desktop_v2701.css`
- Modify: `templates/dashboard.html`

**Interfaces:**
- Consumes: `.mac-desktop-menubar`, `.home-widget-stack`, `.home-widget`.
- Produces: 34px menu bar and 344px right-side widget/notification column using layered Liquid Glass.

- [ ] **Step 1: Write failing tests for desktop geometry/material classes**

Assert 34px menu bar, 344px widget width, 20px widget radius, 15px notification blur, and exact 24px menu-row styling.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m unittest tests.test_macos_desktop_ui -v`
Expected: FAIL on at least one new desktop geometry assertion.

- [ ] **Step 3: Implement exact desktop geometry and materials**

Use layered background, backdrop blur/saturation, inset highlights, subtle 1px glass edges and restrained shadows. Keep wallpaper vibrant and content readable.

- [ ] **Step 4: Run UI suite**

Run: `python -m unittest tests.test_macos_desktop_ui -v`
Expected: PASS.

### Task 4: Exact window, toolbar, sidebar, forms, menus, alerts, and focus states

**Files:**
- Modify: `tests/test_macos_desktop_ui.py`
- Modify: `static/desktop_v2701.css`

**Interfaces:**
- Consumes: existing shared shell classes (`.mac-workspace`, `.mac-toolbar`, sidebars, form controls, menus, dialogs).
- Produces: exact 16px windows, 52/40/77px toolbar variants, 256px sidebars, 24px regular controls/menu rows, 26px alerts, and two-ring macOS focus treatment.

- [ ] **Step 1: Write failing tests for exact app-shell states**

Assert selectors/tokens for unified compact expanded toolbars, sidebar width, alert radius, 24px controls, hover/pressed/focused/disabled selectors, and two focus-ring layers.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m unittest tests.test_macos_desktop_ui -v`
Expected: FAIL before state-system additions.

- [ ] **Step 3: Implement the shared exact-kit app shell**

Apply dense typography, exact control heights, active/inactive states, focus-visible rings, form field sizing, menu row sizing, window radii, and material separation between content and navigation/transient layers.

- [ ] **Step 4: Run full UI suite**

Run: `python -m unittest tests.test_macos_desktop_ui -v`
Expected: PASS.

### Task 5: Motion system and accessibility

**Files:**
- Modify: `tests/test_macos_desktop_ui.py`
- Modify: `static/desktop_v2701.css`
- Modify: `static/desktop_v2701.js`

**Interfaces:**
- Consumes: buttons, menus, popovers, widgets, alerts, Dock.
- Produces: brief spatially coherent motion, interruptible pointer interactions, and reduced-motion fallbacks.

- [ ] **Step 1: Write failing tests for motion contracts**

Assert CSS exposes motion duration/easing tokens, uses transform/opacity rather than layout animation for transient UI, and contains a reduced-motion block that removes Dock/transient transforms.

- [ ] **Step 2: Run tests and confirm failure**

Run: `python -m unittest tests.test_macos_desktop_ui -v`
Expected: FAIL before motion token/state updates.

- [ ] **Step 3: Implement the motion layer**

Add concise web approximations for press, hover, menu/popover materialization, notification entry, and Dock response. Do not claim these timings are private Apple constants; they are web implementation choices faithful to the kit/HIG behavior.

- [ ] **Step 4: Run UI suite**

Run: `python -m unittest tests.test_macos_desktop_ui -v`
Expected: PASS.

### Task 6: Version metadata, documentation, and package verification

**Files:**
- Modify: `README.md`
- Modify: `MACOS27_UI_REFERENCE.md`
- Modify: `app.py` only if UI feature metadata needs a Hotfix 6 marker.

**Interfaces:**
- Consumes: completed exact-kit implementation.
- Produces: deployment notes and package identity for Hotfix 6.

- [ ] **Step 1: Update docs and build metadata**

Document exact-kit pass, motion caveat, and deployment replacement order.

- [ ] **Step 2: Run all source checks**

Run: `python -m unittest discover -s tests -v`
Run: `python -m py_compile *.py`
Run: `node --check static/desktop_v2701.js`
Expected: all exit 0.

- [ ] **Step 3: Package the complete build and 100-file split archives**

Create one complete Hotfix 6 ZIP plus Part 01 with at most 100 files and Part 02 with the remainder.

- [ ] **Step 4: Verify archive integrity and file counts**

Run `unzip -t` on each archive and count members.
Expected: no archive errors; split parts respect the 100-file upload limit.
