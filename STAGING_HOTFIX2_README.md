# Livenza.life Staging Hotfix 2 — Seed Test Data

Temporary staging-only helper for Render Free staging validation.

## What it adds

- Admin-only route: `/admin/livenza/staging/seed`
- Route returns 404 unless `LIVENZA_ENV=staging`
- Requires the confirmation phrase `SEED STAGING`
- Idempotently seeds clearly labelled staging data:
  - Jaipur student stay: `[STAGING] Oasis Residency Jaipur`
  - Gurugram corporate/short stay: `[STAGING] Corporate Stay Sector 38`
  - Room categories, allocatable inventory units and rate plans
  - One Store product: `[STAGING] Livenza Move-In Tee`
- Does not create customers, OTPs, payments or secrets.

## Temporary

Remove this route/module/template/test before merging the staging branch into production `main`.
