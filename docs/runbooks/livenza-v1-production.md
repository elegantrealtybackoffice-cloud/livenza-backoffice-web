# Livenza.life V1 Production Runbook

Production launch is a controlled routing change after staging sign-off, not a ZIP upload directly to the live service.

## Pre-launch

1. **Verify backup.** Record the latest production PostgreSQL backup/restoration point and confirm restore access.
2. **Confirm staging sign-off.** All seven staging gates must be checked with evidence.
3. **Verify production secrets.** `LIVENZA_ENV=production`, secure random `SECRET_KEY`, PostgreSQL `DATABASE_URL`, HTTPS, Razorpay live key/secret/webhook secret, private storage, and production notification providers. `CUSTOMER_AUTH_TEST_MODE` and `RAZORPAY_TEST_STUB` must be `0`.

## Launch order

1. Deploy the migration-compatible Flask/backend code without changing public consumer routing.
2. Apply the **additive migrations** in Plan 1 → Plan 3 → Plan 4 → Plan 5 order. Do not drop legacy tables during V1 launch.
3. **Smoke back-office** login, System Settings, legacy suites, new Livenza Admin, database writes, and `/health` before public traffic moves.
4. Configure production private/public object storage, notification integrations, Razorpay live credentials and live webhook.
5. Deploy the consumer web with `LIVENZA_API_ORIGIN=https://api.livenza.life` and `LIVENZA_SITE_URL=https://livenza.life`.
6. Run the public smoke script and **post-deploy** verifier immediately.
7. When business/payment account readiness permits, perform one controlled low-value live Razorpay booking/order transaction. Never simulate a captured live payment from the browser.
8. Verify the same transaction in My Livenza, back-office, payment record, inventory/stock, and Livenza+ ledger.
9. Monitor application errors, payment/webhook logs, provider delivery failures, database load, and consumer performance through the launch window.

## Rollback points

- If the **consumer UI** fails while the backend remains healthy, **rollback consumer routing first** to the previous public site/deployment. Leave additive schema in place.
- If a backend regression appears before migrations are applied, roll back backend code immediately.
- After additive migrations, roll back backend code only to a version verified compatible with the new schema. Do not attempt destructive schema rollback during an incident.
- Payment/webhook failures: stop new consumer checkout traffic before changing credentials or webhook endpoints. Preserve provider event logs and processed-event IDs.
- Storage/notification failures must not roll back confirmed commercial state; disable the affected integration and remediate separately.

## Production verification commands

```bash
python scripts/livenza_smoke.py --base-url https://livenza.life --api-url https://api.livenza.life
python scripts/livenza_postdeploy_verify.py --base-url https://livenza.life --api-url https://api.livenza.life
```

For controlled booking/order reconciliation, pass `--booking-id` / `--order-id` and provide `LIVENZA_POSTDEPLOY_TOKEN` through the production secret environment only. Remove/rotate the verification token after launch validation.

## Razorpay checks

Confirm the live webhook URL, secret, allowed event types, `x-razorpay-event-id` deduplication, payment/order amounts, and that browser callbacks never set a payment to paid.
