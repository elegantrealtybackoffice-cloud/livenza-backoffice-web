# Staff Salary Studio Design

## Status
Approved in chat on 2026-08-31. This spec converts the approved Staff Salary Studio direction into implementation constraints for the current Livenza Life / Tesla OS 27 codebase.

## Goal
Add a native Staff Salary Studio to `backoffice.livenza.life` for staff onboarding, photographs/KYC, biometric attendance ingestion, leave/allowance management, salary structures, monthly payroll calculation, staff ledger, payslips, and salary-payment batches while preserving all existing Flask routes and permissions.

## Architecture
Keep the existing Flask + Flask-SQLAlchemy modular-monolith backoffice. Add payroll domain logic in a focused `staff_salary_core.py`, additive SQLAlchemy models in `app.py`, additive SQL migration, Jinja templates, suite-specific CSS/JS, and source/domain tests. Do not create a second HR application or a microservice.

The suite key is `staff_salary`; its main endpoint is `staff_salary_studio`. It participates in existing `MODULES`, `permission_required()`, `LIVENZA_APP_REGISTRY`, launcher, Dock and command-palette rules.

## Scope

### Staff master
Each staff member has a generated immutable staff code, photograph, personal/contact/emergency fields, employment data, city/property label, manager/designation/department, joining/status/shift/weekly-off data, KYC references, bank details and salary structure.

Sensitive identifiers must be masked in normal UI. Aadhaar/PAN/bank account values are never rendered in full in list/dashboard views.

### Attendance
Attendance supports normalized `in`, `out`, `present`, `absent`, `half_day`, `leave`, `weekly_off`, `holiday` and manual correction events. A generic biometric import accepts CSV uploads now and leaves device-specific adapters replaceable later. Raw events are retained; daily summaries are derived records.

### Leave and holidays
Leave types include Casual, Sick, Earned/Paid, Unpaid, Comp Off, Maternity, Paternity and Emergency plus custom rows. Leave balances track entitlement, used and pending units by staff/year. Requests move through `submitted`, `approved`, `rejected`, `cancelled`.

### Salary structure and payroll
Monthly payroll uses integer paise internally. Earnings include basic, HRA, fixed allowances, incentives, overtime, bonus and arrears. Deductions include loss-of-pay, advances, loans, penalties, statutory deductions and adjustments.

Payroll periods move through `draft`, `calculated`, `under_review`, `approved`, `payment_processing`, `paid`, `locked`. Once locked, prior payroll items are immutable. Later changes become adjustments in a future period.

### Staff ledger
Ledger rows are double-purpose running staff account entries with `debit_minor`, `credit_minor`, source type/id and immutable creation metadata. Payroll credits salary payable; payment/advance/loan/deduction transactions post the opposite side as applicable.

### Salary payments
V1 must support downloadable bank bulk-payment CSV and a protected manual `mark paid` workflow that records bank reference and posts ledger entries. Direct bank API execution is allowed only behind a provider adapter and privileged approval; no bank password, UPI PIN, card PIN/CVV, OTP, CAPTCHA answer or banking session cookie may be stored.

### Payslips and reports
Generate printable HTML payslips from authoritative payroll items. Provide CSV exports for staff directory, attendance register, payroll register and bank payment batch.

## Permissions
- `staff_salary` controls entry to the suite.
- Admin retains universal module access through existing permission behavior.
- Sensitive payment actions additionally require Admin or a payroll capability encoded by explicit server-side checks; UI hiding alone is never authorization.
- Existing suites and existing users without `staff_salary` permission remain unchanged.

## UI
Use the existing Tesla OS 27 application shell. Add Staff Salary Studio to Finance & Utilities and the lightweight Home launcher/Dock/command palette. Use a professional staff/payroll icon added to the internal SVG symbol system; do not bundle Apple assets.

Main suite tabs: Dashboard, Staff, Attendance, Leave, Salary Structure, Payroll, Ledger, Payments, Reports, Settings.

## Data model
Create additive tables:

- `staff_member`
- `staff_document`
- `staff_bank_account`
- `staff_salary_structure`
- `staff_attendance_event`
- `staff_attendance_day`
- `staff_leave_type`
- `staff_leave_balance`
- `staff_leave_request`
- `staff_payroll_period`
- `staff_payroll_item`
- `staff_payroll_adjustment`
- `staff_ledger_entry`
- `staff_salary_payment_batch`
- `staff_salary_payment`

No destructive migration statements are allowed.

## Core invariants
1. Money uses paise integer helpers; no floating point arithmetic in payroll rules.
2. Staff code is unique and never reused.
3. KYC/bank identifiers are masked in list responses/templates.
4. Payroll item totals are deterministic from the stored snapshot used for that run.
5. A locked payroll period cannot be recalculated or edited.
6. Payment batch total must equal the sum of included approved payroll net amounts.
7. Marking a salary payment paid is idempotent by payment row and bank reference.
8. Manual attendance changes and privileged payroll/payment actions write audit events.
9. Existing `MODULES`, authentication, Settings, Banking, Vault and other suites remain operational.

## Error handling
- Reject malformed attendance imports with row-level validation summary; never partially commit invalid file rows unless the import explicitly identifies accepted/rejected counts.
- Reject payroll calculation when no active salary structure exists for a staff member selected in the run.
- Reject payment batch generation from non-approved payroll periods.
- Reject duplicate staff codes, duplicate attendance event external IDs, and duplicate payment references where scoped uniqueness applies.
- User-facing errors use existing Flask flash patterns; authorization failures remain server-side 403/permission redirects.

## Testing
Add pure domain tests for money, attendance normalization, leave calculation, payroll calculation, period transitions, ledger balance and bank batch serialization. Add source/model/migration tests, permission/route tests and Jinja/UI contract tests. Run the existing backoffice regression suites before packaging.

## Out of scope for V1
- Vendor-specific biometric SDK/network protocol without an identified device model/API.
- Live direct bank API transfer without a contracted bank API/provider configuration.
- Recruitment/appraisals/asset management/full-and-final settlement beyond the data hooks required by payroll.
