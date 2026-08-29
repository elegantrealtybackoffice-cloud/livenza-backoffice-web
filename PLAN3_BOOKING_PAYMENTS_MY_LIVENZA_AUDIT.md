# Livenza.life V1 — Plan 3 Booking, Payments & My Livenza Audit

## Scope
Plan 3 is an additive overlay on the verified Plan 2 consumer/stays discovery baseline. It adds transactional booking, inventory holds, parent-share payment continuation, Razorpay payment authority, receipts, and authenticated My Livenza customer surfaces without deleting any Plan 2 source file.

## Implemented
- Additive booking/payment/support/document/share-token data model and migration.
- Server-side inventory holds and booking state transitions.
- Availability that subtracts active overlapping holds and confirmed bookings.
- PostgreSQL allocation path with row locking (`FOR UPDATE SKIP LOCKED` through SQLAlchemy).
- Student guardian and corporate booking requirements.
- Server-authoritative booking add-on pricing.
- Secure parent-share URLs with hashed stored tokens and expiry.
- Parent Approve & Pay continuation using the payer's own authenticated identity while preserving booking ownership.
- Razorpay order creation adapter with secrets kept server-side.
- Raw-body Razorpay webhook HMAC verification, event-ID deduplication, and idempotent paid/failed transitions.
- Owner-scoped printable receipts.
- OTP account sign-in and My Livenza stays, payments, documents, support, and profile surfaces.
- Seven-step consumer booking UI and webhook-confirmed booking status polling.
- Real route-level E2E specification for test-mode booking + signed webhook confirmation.

## Fresh verification performed after final cleanup
- Plan 3 portable/source test suite: **59 passed, 2 skipped**.
- Plan 1/Plan 2 foundation/consumer regression suite: **52 passed, 10 skipped**.
- Existing HOTFIX8/9/10 regression suite: **121 passed**.
- Python compilation: PASS for `app.py`, `livenza_api_v1.py`, booking/payment/integration/receipt modules.
- Offline TypeScript: PASS with `npx tsc -p web/tsconfig.offline.json --noEmit`.
- Consumer route-source audit: PASS, 17 top-level/handoff routes.
- SQLite compatibility execution of foundation + Plan 3 migrations: PASS; all 10 Plan 3 tables created.
- Frontend secret-assignment scan: PASS.
- Plan 3 vs Plan 2 tree comparison before audit/checksum metadata: 39 added, 12 changed, 0 deleted (51-file overlay).

## Runtime/staging gates NOT verified in this sandbox
The following are deliberately **not** claimed as passing here:
- Flask/SQLAlchemy runtime tests (sandbox lacks the application runtime dependencies; 12 runtime tests are skipped across the fresh suites).
- Dependency-backed `npm test`, ESLint, `next build`, bundle-budget check, or Playwright execution (`npm install` could not complete in the network-restricted sandbox).
- PostgreSQL staging migration/row-lock concurrency behavior.
- Real Razorpay Test Mode checkout and provider-delivered webhook.
- WhatsApp OTP delivery through the configured production integration.
- Browser/device staging smoke tests.

These gates must be completed on staging before merging `livenza-life-v1` into production/main.

## Deployment order
1. Keep Plan 1 and Plan 2 commits already present on `livenza-life-v1`.
2. Overlay the Plan 3 update-only package onto the existing repository; do not delete the repository tree.
3. Commit and push Plan 3 to `livenza-life-v1` only.
4. Configure staging secrets outside Git.
5. Apply `migrations/livenza_v1_booking_payments.sql` to staging PostgreSQL.
6. Run the real Python/Flask test suite and consumer `npm ci && npm test && npm run lint && npm run build`.
7. Run Playwright booking journey with Razorpay test configuration and verify the webhook-driven confirmation.
8. Do not merge to `main` until the staging gates pass.
