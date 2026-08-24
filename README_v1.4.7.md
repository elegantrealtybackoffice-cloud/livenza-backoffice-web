# Livenza Life Operations Cloud — Web 1.4.7

UI/UX and workflow refinement release.

## Changes
- Absolute light-theme lock across the application: white/soft-grey surfaces, black text, navy-blue accents.
- Agreement Studio accordions/preset panels/inputs are explicitly white; legacy dark styles cannot leak through.
- Fullscreen module navigation now swaps the main application content in-place so fullscreen stays active while moving between modules.
- Added Query Spreadsheet View (`/queries/sheet`) with direct cell editing, auto-save, row creation and search. It uses the existing `query_lead` table; no new database migration is required.
- Added an embedded Livenza Assistant near the footer for feature/workflow help. It works with a local built-in guide and can use `OPENAI_API_KEY` when available.
- Added a transparent Livenza easter egg with a subtle star interaction.
- Added touch ripples, reveal transitions, live ambient movement and restrained micro-interactions.
- Footer continues to show `Created by Rishabh Kothari` plus Livenza Life LLP copyright and Head Office.
- Static asset cache version bumped to 1.4.7.

## Deployment
Upload the package contents directly to the root of the existing `livenza-backoffice-web` repository, preserving `templates/` and `static/`. Commit to `main`; Render should auto-deploy.

Verify after deploy at `/version`: `Web 1.4.7`.

## Database
No Supabase migration is needed for this release. Query Spreadsheet View reads/writes the existing `query_lead` records.
