# Livenza Backoffice UI + Performance Hardening Audit

Date: 2026-08-31
Scope: shared Tesla OS 27 shell and Staff Salary Studio readability/navigation performance.

## Root causes corrected

1. **Theme/CSS specificity conflict**
   - Global macOS dark-mode rules could override suite-local light surfaces.
   - Result: low-contrast or invisible labels, dark controls inside light cards, and inconsistent form colors.
   - Added `static/ui_integrity.css` as the final shared integrity layer with theme-safe surfaces, form controls, labels, focus states, overflow protection, and Staff Salary responsive form layout.

2. **Repeated database-backed settings/context work on every suite switch**
   - `setting()` performed repeated lookups during a single navigation path.
   - Dock visibility checks rebuilt permission/provider state repeatedly.
   - Added short TTL settings caching with write invalidation and consolidated Dock availability evaluation.

3. **Heavy partial-window rendering**
   - Desktop partial navigation still constructed the full global shell context and duplicate shell chrome.
   - Partial requests now use lightweight context and omit duplicate Dock/drawers/command-palette/global scripts while retaining suite-specific assets.

4. **Dock hover request storms**
   - Every pointer-over could immediately prefetch a suite.
   - Hover prefetch is now delayed/debounced; keyboard focus remains immediate.

5. **Excess nested blur/repaint cost**
   - Content cards/forms inherited multiple backdrop filters.
   - Shared content surfaces now avoid nested backdrop blur while the main macOS chrome keeps its glass treatment.

## Files changed

- `app.py`
- `base.html`
- `templates/base.html`
- `static/macos27_shell.js`
- `static/ui_integrity.css` (new)
- `tests/test_ui_performance_hardening.py` (new regression tests)

## Deployment notes

- No database migration is required.
- No Supabase schema change is required.
- No new environment variable is required.
- Copy this update over the current repository while preserving paths, commit, push, and allow Render auto-deploy.
- Do not remove any existing suites or files.
