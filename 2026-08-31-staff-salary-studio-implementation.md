# Staff Salary Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a native Staff Salary Studio in the existing Flask backoffice with staff master/KYC, attendance, leave, payroll, ledger, bulk salary payments, payslips and reports.

**Architecture:** Extend the current Flask/Flask-SQLAlchemy modular monolith additively. Keep pure payroll/attendance calculations in `staff_salary_core.py`, persistence and protected routes in `app.py`, and UI in focused Jinja/CSS/JS files while reusing the existing Tesla OS 27 shell and permission registry.

**Tech Stack:** Python 3, Flask, Flask-SQLAlchemy, PostgreSQL with SQLite-compatible tests, Jinja2, vanilla JavaScript, CSS, pytest/source-contract tests, existing AuditEvent/permission helpers.

**Spec:** `docs/superpowers/specs/2026-08-31-staff-salary-studio-design.md`

## Global Constraints

- Preserve every existing working Flask route, permission and secure POST behavior.
- Additive schema only; no `DROP TABLE`, `DROP COLUMN` or destructive rewrite.
- Use integer paise for all payroll/payment arithmetic.
- Never store restricted banking authentication factors.
- Staff Salary Studio module key is `staff_salary`; main endpoint is `staff_salary_studio`.
- Existing users without the new permission remain unchanged.
- Direct bank APIs are not activated without an identified/configured provider; V1 ships bank-batch export plus protected payment reconciliation.
- Biometric ingestion is vendor-neutral CSV/API normalization; vendor-specific device transport is not invented.

---

### Task 1: Payroll domain core

**Files:**
- Create: `staff_salary_core.py`
- Create: `tests/test_staff_salary_core.py`

**Interfaces:**
- Produces: `money_minor(value) -> int`, `mask_identifier(value, keep=4) -> str`, `staff_code(prefix, sequence) -> str`, `normalize_attendance_status(value) -> str`, `attendance_minutes(in_at,out_at) -> int`, `loss_of_pay_minor(monthly_gross_minor,payable_days,unpaid_days) -> int`, `calculate_payroll(snapshot) -> dict`, `transition_payroll_status(current,event) -> str`, `ledger_balance(entries) -> int`, `build_bank_batch_rows(items) -> list[dict]`.

- [ ] Write failing tests covering deterministic paise arithmetic, masking, staff-code formatting, attendance aliases, LOP, payroll earnings/deductions/net, legal/illegal payroll transitions, ledger balance and bank rows.
- [ ] Run `pytest -q tests/test_staff_salary_core.py` and verify failure because the module does not exist.
- [ ] Implement the pure helpers with no Flask/database imports.
- [ ] Rerun the test and verify pass.
- [ ] Commit `feat: add staff payroll domain core`.

### Task 2: Additive staff/payroll schema and models

**Files:**
- Modify: `app.py`
- Create: `migrations/staff_salary_v1.sql`
- Create: `tests/test_staff_salary_models.py`

**Interfaces:**
- Consumes: Task 1 helpers.
- Produces SQLAlchemy models named exactly `StaffMember`, `StaffDocument`, `StaffBankAccount`, `StaffSalaryStructure`, `StaffAttendanceEvent`, `StaffAttendanceDay`, `StaffLeaveType`, `StaffLeaveBalance`, `StaffLeaveRequest`, `StaffPayrollPeriod`, `StaffPayrollItem`, `StaffPayrollAdjustment`, `StaffLedgerEntry`, `StaffSalaryPaymentBatch`, `StaffSalaryPayment`.

- [ ] Write source-contract tests asserting all models/critical columns and non-destructive migration creation statements.
- [ ] Run `pytest -q tests/test_staff_salary_models.py` and verify failure.
- [ ] Add models to `app.py` using indexed foreign keys and timestamps consistent with the existing codebase.
- [ ] Add `migrations/staff_salary_v1.sql` with `CREATE TABLE IF NOT EXISTS` and indexes; no destructive statements.
- [ ] Rerun model tests and migration parse checks.
- [ ] Commit `feat: add staff salary persistence model`.

### Task 3: Permission, registry, Dock and icon integration

**Files:**
- Modify: `app.py`
- Modify: `templates/_application_groups.html`
- Modify: `templates/_livenza_symbols.html`
- Modify: `templates/base.html`
- Create: `tests/test_staff_salary_shell.py`

**Interfaces:**
- Produces `MODULES['staff_salary']`, registry entry endpoint `staff_salary_studio`, symbol `staff_salary`, Finance launcher card, lightweight launcher/Dock/command item, and full command palette item.

- [ ] Write failing source tests for module key, registry metadata, permission gating, symbol, launcher, Dock and command palette.
- [ ] Run `pytest -q tests/test_staff_salary_shell.py` and verify failure.
- [ ] Add the module/registry entry and visual metadata.
- [ ] Add the staff/payroll SVG symbol.
- [ ] Add Staff Salary Studio to Finance & Utilities plus lightweight shell surfaces.
- [ ] Rerun shell tests.
- [ ] Commit `feat: register staff salary studio`.

### Task 4: Staff master, photograph, KYC and salary structure

**Files:**
- Modify: `app.py`
- Create: `templates/staff_salary.html`
- Create: `templates/staff_salary_staff_edit.html`
- Create: `static/staff_salary.css`
- Create: `static/staff_salary.js`
- Create: `tests/test_staff_salary_staff_routes.py`

**Interfaces:**
- Produces: `GET /staff-salary`, `GET|POST /staff-salary/staff/new`, `GET|POST /staff-salary/staff/<id>`, `POST /staff-salary/staff/<id>/salary-structure`, `POST /staff-salary/staff/<id>/document`, protected by `permission_required('staff_salary')`.

- [ ] Write failing route/source tests for permission decorators, photograph input, KYC/bank/salary fields and masked list output.
- [ ] Run focused tests and verify failure.
- [ ] Implement suite dashboard context and staff CRUD with server-side validation and unique staff-code generation.
- [ ] Save photograph as bounded data URI for V1, validating image MIME/size; store KYC documents using existing protected/encrypted document patterns rather than public static files.
- [ ] Implement bank and salary-structure saves with masked display helpers.
- [ ] Create responsive Jinja screens using existing application-window patterns.
- [ ] Rerun tests plus Jinja parse.
- [ ] Commit `feat: add staff onboarding and salary structure`.

### Task 5: Attendance import and leave engine

**Files:**
- Modify: `app.py`
- Modify: `templates/staff_salary.html`
- Modify: `static/staff_salary.js`
- Create: `tests/test_staff_salary_attendance_leave.py`

**Interfaces:**
- Produces: `POST /staff-salary/attendance/import`, `POST /staff-salary/attendance/manual`, `POST /staff-salary/leave-types`, `POST /staff-salary/leave`, `POST /staff-salary/leave/<id>/status`.

- [ ] Write failing tests for CSV header validation, duplicate external event IDs, daily summary derivation, leave balance arithmetic and audit calls.
- [ ] Implement CSV parser accepting `staff_code,timestamp,event_type,external_id` plus normalized aliases.
- [ ] Upsert raw events idempotently and derive affected staff/day summaries.
- [ ] Implement manual correction and leave request/approval/rejection with AuditEvent records.
- [ ] Render Attendance and Leave tabs with entitlement/used/pending/remaining data.
- [ ] Rerun focused tests.
- [ ] Commit `feat: add attendance and leave workflows`.

### Task 6: Payroll calculation, locking and ledger

**Files:**
- Modify: `app.py`
- Modify: `templates/staff_salary.html`
- Create: `templates/staff_salary_payslip.html`
- Create: `tests/test_staff_salary_payroll.py`

**Interfaces:**
- Produces: `POST /staff-salary/payroll/period`, `POST /staff-salary/payroll/<id>/calculate`, `POST /staff-salary/payroll/<id>/status`, `GET /staff-salary/payroll/<id>/payslip/<staff_id>`, `GET /staff-salary/ledger/<staff_id>`.

- [ ] Write failing tests for period state guards, salary snapshot storage, LOP feed from attendance/leave, item totals, locking immutability and ledger posting.
- [ ] Implement period creation and calculation from active staff/salary structures.
- [ ] Snapshot earnings/deductions into `StaffPayrollItem` so later master-data edits do not mutate history.
- [ ] Post salary-credit ledger entries on approval and prevent duplicate posts.
- [ ] Implement printable payslip and ledger drill-down.
- [ ] Rerun focused tests.
- [ ] Commit `feat: add payroll and staff ledger`.

### Task 7: Salary payment batches, reports and reconciliation

**Files:**
- Modify: `app.py`
- Modify: `templates/staff_salary.html`
- Create: `tests/test_staff_salary_payments_reports.py`

**Interfaces:**
- Produces: `POST /staff-salary/payments/batch`, `GET /staff-salary/payments/batch/<id>.csv`, `POST /staff-salary/payments/<id>/mark-paid`, `GET /staff-salary/reports/<kind>.csv`.

- [ ] Write failing tests requiring approved-period guard, bank-detail guard, batch total equality, CSV columns, idempotent mark-paid behavior and report permissions.
- [ ] Implement batch creation from approved unpaid payroll items.
- [ ] Generate UTF-8 CSV columns `Staff Code,Employee,Account Holder,Account Number,IFSC,Amount,Reference`.
- [ ] Implement Admin-protected mark-paid transaction with reference, paid timestamp, payroll-state progression and ledger debit.
- [ ] Add reports for staff, attendance and payroll registers.
- [ ] Rerun focused tests.
- [ ] Commit `feat: add salary payments and reports`.

### Task 8: Regression, packaging and deployment gates

**Files:**
- Modify: `README.md`
- Modify: `VERIFY_DEPLOY.txt`
- Create: `STAFF_SALARY_STUDIO_AUDIT.md`

**Interfaces:**
- Produces a deployable complete source package and update-only package.

- [ ] Run all Staff Salary Studio tests.
- [ ] Run `python -m py_compile app.py staff_salary_core.py`.
- [ ] Parse every Jinja template with the configured Jinja environment/source test strategy.
- [ ] Run existing Hotfix 8/9/10 and Livenza admin permission/view regression tests.
- [ ] Update README suite list, migration order and deployment checks.
- [ ] Add staging checks: apply `migrations/staff_salary_v1.sql`, grant permission, create test staff, import sample attendance, approve leave, calculate/approve payroll, export bank CSV, mark one payment paid, verify ledger/payslip, verify unauthorized user is denied.
- [ ] Package complete source and update-only ZIP with SHA-256 manifest.
- [ ] Commit `release: staff salary studio v1`.
