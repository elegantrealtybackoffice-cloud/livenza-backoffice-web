# Plan 4 — Livenza.store + Livenza+ Verification Audit

## Scope
Plan 4 adds Store catalogue/cart/order/payment flows, resident-property delivery, Move-In Kit source traceability, My Livenza Store Orders, and append-only Livenza+ rewards. It is an additive overlay on the Plan 3 snapshot.

## Fresh verification evidence
- Plan 1–4 portable/source suite: `154 passed, 13 skipped`.
  - Skips are Flask/SQLAlchemy runtime tests because those dependencies are not installed in this sandbox.
- Legacy HOTFIX8/9/10 contracts: `121 passed`.
- Python source compilation: PASS for `app.py`, API/domain/payment/commerce/loyalty modules.
- Offline TypeScript: `tsc -p web/tsconfig.offline.json` PASS.
- Route source audit: PASS, 21 top-level/handoff routes.
- Plan 4 migration compatibility: PASS in SQLite parser/execution check; all six Store/Loyalty tables created.
- Frontend secret-source checks: PASS; no Razorpay key secret/webhook secret strings in `web/src`.
- Real Next.js production build: NOT VERIFIED in this sandbox. `npm run build` exits because the `next` package is not installed (`next: not found`).

## Security / transaction invariants implemented
- Cart and order prices are read only from `ProductVariant.price_minor`; client prices/discounts are ignored.
- PostgreSQL order path selects variants with `FOR UPDATE` before reserving final stock.
- `stock_reserved` increments in the same transaction as order creation.
- Payment provider creation failure rolls back the order and stock reservation.
- Failed Store payment releases reservation and cancels the unpaid order.
- Paid Store payment decrements `stock_on_hand` and `stock_reserved` once, then confirms the order.
- Razorpay webhook event IDs are deduplicated before payment source dispatch.
- Store order reads are customer-owner scoped.
- Property-room delivery is derived from confirmed current stays and configured property slugs; customers cannot self-assert room/property values.
- Move-In Kit booking metadata snapshots Store product/variant/SKU server-side and ignores arbitrary client metadata.
- Livenza+ is append-only and awards are idempotent by `(source_type, source_id, effect_key)`.

## Staging gates still required
1. Apply all Plan 1–4 migrations on staging PostgreSQL.
2. Run final-unit concurrent checkout test and verify only one reservation succeeds.
3. Configure Razorpay Test Mode and verify paid/failed/duplicate webhook paths end-to-end.
4. Install `web/` dependencies, run Vitest, ESLint, `next build`, bundle budget and Playwright Store E2E.
5. Publish a small real Store fixture catalogue and verify product/variant/stock behavior.
6. Verify resident room delivery with a real confirmed current stay and a non-eligible customer.
7. Verify Store payment and Stay payment each credit Livenza+ once and duplicate webhooks do not double-credit.

## Production status
This checkpoint is suitable for the `livenza-life-v1` staging branch. It is not approved for merge to `main` until the staging gates above pass.
