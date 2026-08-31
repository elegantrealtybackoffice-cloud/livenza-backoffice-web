# Staff Salary Studio V1 — Release Audit

**Product:** Livenza Tesla OS 27 Backoffice  
**Module:** Staff Salary Studio  
**Module key:** `staff_salary`  
**Primary route:** `/staff-salary`  
**Release date:** 2026-08-31

## Delivered scope

- Permission-aware Staff Salary Studio in Finance & Utilities, with launcher/Dock/command-palette integration.
- Staff registration with photograph, identity/contact/employment details and property/location assignment.
- Aadhaar, PAN and bank account number encrypted at rest; masked list/report presentation.
- Encrypted staff-document upload/download for PDF/JPG/PNG/WebP.
- Effective-dated salary structures with integer-paise storage and calculation.
- Vendor-neutral attendance ingestion through CSV and the token-protected `/webhooks/staff-attendance` automatic feed, with deterministic duplicate protection, manual audited corrections and daily summaries.
- Leave types, annual allowance, pending/used balances and approval/rejection workflow.
- Payroll periods, attendance/unpaid-leave loss-of-pay, overtime, adjustment hooks, immutable salary snapshots, review/approval/paid/locked states.
- Printable payslips and per-staff running ledger.
- Approved-payroll bank batch generation, UTF-8 bank CSV export, Admin-only payment reconciliation and UTR/reference capture.
- Staff, attendance and payroll CSV reports.

## Security controls

- Existing server-side `permission_required('staff_salary')` authorization remains authoritative for the suite.
- Admin authorization is additionally required to create/export full bank-account salary batches and to mark salary payments paid.
- Staff documents are encrypted through the existing Livenza Vault AES-GCM helpers and are never written to public static storage.
- Directory/report surfaces use masked Aadhaar, PAN and bank account values.
- Restricted banking authentication factors are not part of the schema or forms.
- Sensitive/manual/payroll/payment actions write to the existing AuditEvent system.
- Locked payroll is immutable; approved salary ledger credits and paid ledger debits are idempotent by source record.

## Integration boundaries

- Biometric V1 normalizes CSV/API-style event data; it does not invent a vendor SDK/device transport without an identified device provider.
- Salary payment V1 exports bank-upload CSV and reconciles bank references. Direct bank-server transfer APIs remain disabled until a contracted/configured provider and its authorization model are available.

## Database

Apply additive migration:

`migrations/staff_salary_v1.sql`

The migration creates staff, encrypted document/bank, salary structure, attendance, leave, payroll, ledger and payment tables. It contains no DROP statements.

## Sample connector payload

A ready CSV example is included at `docs/samples/staff_attendance_import_sample.csv`. The same event fields can be posted as JSON to `/webhooks/staff-attendance`.

## Verification evidence

See the final release response and `VERIFY_DEPLOY.txt` for the exact local regression results and staging acceptance sequence. Runtime writes, PostgreSQL migration execution, biometric hardware transport and real bank transfer behavior require staging/production credentials and therefore must be verified after deployment.

## Production database deployment — 2026-08-31

- Applied `staff_salary_v1` to Supabase project `livenza-backoffice`.
- Applied `staff_salary_v1_indexes` to cover new foreign-key joins flagged by the Supabase performance advisor.
- Verified all 15 Staff Salary tables exist with RLS enabled and no public policies, matching the backoffice server-side/default-deny database pattern.
- Application-code deployment still requires the updated source to be committed to the connected GitHub repository / Render service.

## Deployment-session verification

- Production Supabase migration `staff_salary_v1`: applied successfully.
- Production Supabase migration `staff_salary_v1_indexes`: applied successfully.
- Verified all 15 Staff Salary tables have RLS enabled.
- Fresh package regression: `497 passed, 25 skipped`.
- Fresh `python -m py_compile app.py staff_salary_core.py`: passed.
- GitHub/Render application push was not executed because this chat session has no authenticated GitHub/Render connector or deployment credential.
