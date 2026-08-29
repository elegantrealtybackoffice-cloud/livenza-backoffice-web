# Livenza.life V1 Staging Runbook

This runbook is the mandatory rehearsal before any `livenza.life` production routing change. Staging must use a separate PostgreSQL database and non-production provider credentials.

## Deployment order

1. **Backup / restore point.** Snapshot the staging PostgreSQL database and record the restoration identifier before changing code or schema.
2. **Deploy compatible backend code first.** Deploy the Plan 5 backend while keeping public consumer traffic on the existing route. Confirm `/health` still returns 200 and staff can sign in to the back-office.
3. **Apply additive migrations in order.** Apply Plan 1 `migrations/livenza_v1_foundation.sql`, then Plan 3 `migrations/livenza_v1_booking_payments.sql`, Plan 4 `migrations/livenza_v1_store_loyalty.sql`, and Plan 5 `migrations/livenza_v1_admin_migration.sql`. Plan 2 adds the consumer web but no database migration.
4. **Seed controlled fixtures through admin.** Create at least two test properties, room categories, allocatable inventory units, rate plans, and two public Store products with variants/stock. Do not seed by editing production tables manually.
5. **Configure Razorpay Test Mode.** Set test-mode key/secret and webhook secret, keep `LIVENZA_ENV=staging`, and configure the staging webhook at `/api/v1/payments/webhooks/razorpay`.
6. **Configure staging integrations.** Configure test email/Google, WhatsApp, and private/public storage through the existing Integrations Center/environment contracts. Use staging-only buckets and recipients.
7. **Deploy the Next.js staging web.** Set `LIVENZA_API_ORIGIN=https://api-staging.livenza.life` and `LIVENZA_SITE_URL=https://staging.livenza.life`.
8. **Run backend regression tests.** Run the complete Python suite in the real Flask/PostgreSQL environment.
9. **Run Playwright.** Run discovery, booking, Store, and `release.spec.ts` against staging. Razorpay Test Mode must exercise signed webhook confirmation.
10. **Manual staff access check.** Verify manager accounts without `customers`, `stays_admin`, `store_admin`, or `content` cannot open those modules. Verify authorized accounts can see only intended operational data.
11. **Run the legacy migration dry-run.** `python scripts/livenza_migrate_legacy.py --source legacy_backoffice --dry-run --strict`. Resolve every conflict before `--apply` is considered.
12. **Run smoke and post-deploy verification.** Use `scripts/livenza_smoke.py` and `scripts/livenza_postdeploy_verify.py` with staging URLs. Store `LIVENZA_POSTDEPLOY_TOKEN` only in the staging secret manager/environment.

## Acceptance journeys

### Stay journey
`Homepage → Stays → Property → Room → OTP → Hold → Booking → Razorpay Test Mode → signed webhook → confirmation → My Livenza → receipt → back-office booking → inventory reconciled`

### Store journey
`Same Livenza ID → Store → product → cart → checkout → Razorpay Test Mode → signed webhook → My Orders → Livenza+ → back-office order → stock reconciled`

## Seven release gates — staging sign-off

Leave these unchecked until the corresponding evidence is attached to the staging release record.

- [ ] **Brand** — approved Livenza visual system is consistent on homepage, Stays, Store, booking, My Livenza, and responsive breakpoints.
- [ ] **Functional** — no dead primary navigation, booking, checkout, account, or back-office controls.
- [ ] **Commercial** — one stay booking and one Store order complete end-to-end in Razorpay Test Mode.
- [ ] **Data** — consumer actions reconcile to the same booking/order/customer/inventory records visible in back-office.
- [ ] **Payments** — raw-body webhook verification, event-id deduplication, failed-payment release, and refund-result recording are verified.
- [ ] **Responsive** — phone 390×844, tablet 768×1024, desktop 1440×900, keyboard navigation, and reduced motion pass.
- [ ] **Performance** — production Next.js build/bundle check and smoke response timing pass without blocking interaction.

## Required commands

```bash
python -m pytest -q
python scripts/livenza_smoke.py --base-url https://staging.livenza.life --api-url https://api-staging.livenza.life
python scripts/livenza_migrate_legacy.py --source legacy_backoffice --dry-run --strict
cd web
npm ci
npm run lint
npm run build
npm run check:bundle
PLAYWRIGHT_BASE_URL=https://staging.livenza.life npm run test:e2e
```

Do not sign off production until all seven boxes are checked from staging evidence.
