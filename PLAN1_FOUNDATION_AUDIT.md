# Livenza.life V1 — Plan 1 Foundation Audit

Date: 2026-08-27
Baseline: Tesla OS 27 v27.0.1 Build 27A101 HOTFIX10 Navigation Failsafe Dock Refinement Rev D

## Implemented

- Separate consumer `Customer` identity model; existing staff `User` model retained.
- Customer mobile identity, OTP challenge, hashed session, and address models.
- Stay property, room category, and hierarchical inventory-unit models.
- Additive migration: `migrations/livenza_v1_foundation.sql`.
- Pure mobile/email normalization, OTP hashing, session-token hashing helpers.
- Pure inventory hierarchy and availability-state helpers.
- `/api/v1` blueprint with customer OTP request/verify/logout/me endpoints.
- OTP request throttling and five-attempt verification limit.
- Test OTP exposure restricted to explicit local/dev/test environments.
- HttpOnly customer session cookie with deployment-configured Secure flag and SameSite=Lax.
- OTP delivery adapter reuses the existing Integration Center-backed WhatsApp Cloud configuration.
- Public city/property/detail API, restricted to active + public stay properties.
- Availability API for active allocatable inventory; booking/hold subtraction remains Plan 3.
- README environment-variable and staging-migration procedure.
- Approved Plan 1 and platform specification copied into `docs/superpowers/`.

## Fresh verification performed in this workspace

### New portable foundation suite

Command family: `pytest` over the eight new Plan 1 test modules.

Result: **31 passed, 10 skipped**.

The 10 skipped tests are runtime Flask/SQLAlchemy tests. They are present in the package and automatically activate in an environment with project dependencies installed.

### Existing back-office regression contracts

Two batches covering HOTFIX8, HOTFIX9/9.1/9.2 and HOTFIX10 contracts.

Result: **121 passed, 0 failed**.

### Source compilation

`python -m py_compile app.py livenza_customer_core.py livenza_inventory_core.py livenza_api_v1.py`

Result: exit code 0.

### Migration compatibility parse

The additive foundation migration was executed against an in-memory SQLite compatibility database.

Result: all **8 new tables** created successfully and the migration contains no `DROP TABLE` or `DROP COLUMN` statements.

## Not verified in this sandbox

The sandbox has no network access and no installed Flask/Flask-SQLAlchemy runtime. `pip install -r requirements.txt` was attempted and failed because package download/name resolution is unavailable.

Therefore the following Plan 1 completion gates remain for staging:

1. Import/start the complete Flask application with `requirements.txt` installed.
2. Run the 10 runtime tests in the Plan 1 suite.
3. Apply `migrations/livenza_v1_foundation.sql` to staging PostgreSQL.
4. Smoke-test staff login and existing suites against staging.
5. Configure a test/staging WhatsApp provider and verify OTP delivery end-to-end.
6. Verify `/api/v1/cities`, `/api/v1/properties`, `/api/v1/availability`, OTP verification, `/api/v1/me`, and logout on staging.
7. Confirm production HTTPS sets the customer cookie `Secure` attribute.

Plan 2 should not receive production traffic until these staging gates pass.
