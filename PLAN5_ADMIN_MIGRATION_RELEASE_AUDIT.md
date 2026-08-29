# Livenza.life V1 — Plan 5 Admin, Migration & Release Hardening Audit

## Scope

Plan 5 extends the existing Flask/Jinja back-office with unified Livenza operational admin, Content Studio, secure object storage access, event-driven transactional notifications, explicit legacy mapping/migration tooling, production configuration guards, smoke/E2E release checks, and staging/production runbooks.

## Implemented

- Explicit back-office permissions: `customers`, `stays_admin`, `store_admin`, `content`.
- Unified operational admin for customers, properties, bookings, Store orders, and support.
- Privileged booking/order/stock/refund/content actions with allow-listed audit metadata.
- Content Studio with draft/published separation and public published-only `/api/v1/content/...` API.
- Public/private storage adapters; owner-scoped document download returns a short-lived signed URL rather than raw object keys.
- Public property media serialization without exposing storage keys.
- Transactional notification registry for booking/payment/order/support/reward/move-in events.
- Notification providers reuse existing Google/WhatsApp integration configuration and record masked delivery outcomes independently of commercial transactions.
- Deterministic `LegacyEntityMap` migration logic and `--dry-run`/`--apply` tooling. Display names are never used as identity evidence.
- Production environment validation blocks test auth, default secrets, SQLite, Razorpay test stubs/missing live credentials, insecure HTTP, or missing private storage.
- `/api/v1/health`, smoke script, responsive/keyboard/reduced-motion/metadata Playwright release spec, and usable consumer 404.
- Staff-only post-deploy booking/order reconciliation endpoint protected by a constant-time bearer-token comparison and returning no customer PII.
- Staging and production runbooks with migration order, rollback points, Razorpay checks, and the seven release gates.

## Fresh verification completed in this workspace

- Plan 5 tests: **39 passed, 0 failed**.
- Full repository pytest suite: **314 passed, 13 skipped, 0 failed**.
- Legacy HOTFIX8/9/10 regression subset: **121 passed, 0 failed** (also included in the full suite).
- Python source compilation: passed.
- Jinja parsing: **64 templates parsed successfully**.
- Offline TypeScript check: passed with `tsc -p web/tsconfig.offline.json --noEmit`.
- Migration compatibility sequence (Plan 1 → Plan 3 → Plan 4 → Plan 5): passed in an in-memory SQLite compatibility parse/execution check; required Plan 5 tables were created.
- Browser-source secret scan: passed for `web/src` and `web/scripts`; no Razorpay key secret/webhook secret, WhatsApp token, Supabase service-role key, or post-deploy token names are referenced by browser source. The Playwright booking test intentionally reads the webhook secret in the Node test runner, not in browser code.
- Plan 5 diff against the exact Plan 4 snapshot before audit/checksum metadata: **31 added, 10 modified, 0 deleted**.

## Runtime/staging gates NOT verified in this sandbox

These remain mandatory before merge to `main` or production routing:

1. Real Flask runtime tests with project dependencies installed.
2. PostgreSQL migration execution and inventory/stock concurrency behavior.
3. `npm ci`, ESLint, real `next build`, bundle-budget check.
4. Playwright discovery/booking/store/release suites against deployed staging.
5. Razorpay Test Mode order + signed webhook end-to-end confirmation.
6. Real Google email, WhatsApp, and private/public storage provider delivery/access.
7. Legacy migration dry-run against a staging copy of the real database.
8. Seven staging release gates signed off in `docs/runbooks/livenza-v1-staging.md`.

Plan 5 code is therefore a **staging-ready implementation checkpoint**, not a production sign-off.
