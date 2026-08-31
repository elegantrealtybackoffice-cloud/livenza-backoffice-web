-- Livenza Staff Salary Studio V1: additive staff, attendance, leave, payroll and payments schema.
BEGIN;

CREATE TABLE IF NOT EXISTS staff_member (
  id SERIAL PRIMARY KEY,
  staff_code VARCHAR(40) NOT NULL UNIQUE,
  full_name VARCHAR(180) NOT NULL,
  photo_data_uri TEXT NOT NULL DEFAULT '',
  father_spouse_name VARCHAR(180) NOT NULL DEFAULT '',
  dob DATE NULL,
  gender VARCHAR(40) NOT NULL DEFAULT '',
  mobile VARCHAR(40) NOT NULL DEFAULT '',
  alternate_mobile VARCHAR(40) NOT NULL DEFAULT '',
  email VARCHAR(220) NOT NULL DEFAULT '',
  current_address TEXT NOT NULL DEFAULT '',
  permanent_address TEXT NOT NULL DEFAULT '',
  emergency_name VARCHAR(180) NOT NULL DEFAULT '',
  emergency_mobile VARCHAR(40) NOT NULL DEFAULT '',
  aadhaar_no TEXT NOT NULL DEFAULT '', aadhaar_nonce VARCHAR(180) NOT NULL DEFAULT '', aadhaar_last4 VARCHAR(4) NOT NULL DEFAULT '',
  pan_no TEXT NOT NULL DEFAULT '', pan_nonce VARCHAR(180) NOT NULL DEFAULT '', pan_last4 VARCHAR(4) NOT NULL DEFAULT '',
  city_id INTEGER NULL REFERENCES city(id),
  property_name VARCHAR(180) NOT NULL DEFAULT '',
  designation VARCHAR(120) NOT NULL DEFAULT '', department VARCHAR(120) NOT NULL DEFAULT '', reporting_manager VARCHAR(180) NOT NULL DEFAULT '',
  joining_date DATE NULL, employment_type VARCHAR(40) NOT NULL DEFAULT 'full_time', shift_name VARCHAR(80) NOT NULL DEFAULT 'General', weekly_off VARCHAR(40) NOT NULL DEFAULT 'Sunday',
  probation_end_date DATE NULL, status VARCHAR(32) NOT NULL DEFAULT 'active', notes TEXT NOT NULL DEFAULT '',
  created_by_user_id INTEGER NULL REFERENCES "user"(id), created_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now()), updated_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now())
);
CREATE INDEX IF NOT EXISTS ix_staff_member_city_id ON staff_member(city_id); CREATE INDEX IF NOT EXISTS ix_staff_member_property_name ON staff_member(property_name); CREATE INDEX IF NOT EXISTS ix_staff_member_status ON staff_member(status);

CREATE TABLE IF NOT EXISTS staff_document (
  id SERIAL PRIMARY KEY, staff_id INTEGER NOT NULL REFERENCES staff_member(id), document_type VARCHAR(60) NOT NULL DEFAULT 'other', file_name VARCHAR(220) NOT NULL DEFAULT '', mime_type VARCHAR(120) NOT NULL DEFAULT 'application/octet-stream', encrypted_blob TEXT NOT NULL, encrypted_nonce VARCHAR(180) NOT NULL, verification_status VARCHAR(40) NOT NULL DEFAULT 'unverified', uploaded_by_user_id INTEGER NULL REFERENCES "user"(id), uploaded_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now())
); CREATE INDEX IF NOT EXISTS ix_staff_document_staff_id ON staff_document(staff_id);

CREATE TABLE IF NOT EXISTS staff_bank_account (
  id SERIAL PRIMARY KEY, staff_id INTEGER NOT NULL REFERENCES staff_member(id), account_holder VARCHAR(180) NOT NULL DEFAULT '', account_number TEXT NOT NULL DEFAULT '', account_nonce VARCHAR(180) NOT NULL DEFAULT '', account_last4 VARCHAR(4) NOT NULL DEFAULT '', ifsc VARCHAR(30) NOT NULL DEFAULT '', bank_name VARCHAR(160) NOT NULL DEFAULT '', branch_name VARCHAR(160) NOT NULL DEFAULT '', upi_id VARCHAR(180) NOT NULL DEFAULT '', preferred_method VARCHAR(32) NOT NULL DEFAULT 'bank_transfer', active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now()), updated_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now())
); CREATE INDEX IF NOT EXISTS ix_staff_bank_account_staff_id ON staff_bank_account(staff_id);

CREATE TABLE IF NOT EXISTS staff_salary_structure (
  id SERIAL PRIMARY KEY, staff_id INTEGER NOT NULL REFERENCES staff_member(id), effective_from DATE NOT NULL, basic_minor BIGINT NOT NULL DEFAULT 0, hra_minor BIGINT NOT NULL DEFAULT 0, fixed_allowance_minor BIGINT NOT NULL DEFAULT 0, travel_allowance_minor BIGINT NOT NULL DEFAULT 0, food_allowance_minor BIGINT NOT NULL DEFAULT 0, mobile_allowance_minor BIGINT NOT NULL DEFAULT 0, special_allowance_minor BIGINT NOT NULL DEFAULT 0, overtime_rate_minor BIGINT NOT NULL DEFAULT 0, statutory_deduction_minor BIGINT NOT NULL DEFAULT 0, notes TEXT NOT NULL DEFAULT '', active BOOLEAN NOT NULL DEFAULT TRUE, created_by_user_id INTEGER NULL REFERENCES "user"(id), created_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now()), CONSTRAINT uq_staff_salary_effective UNIQUE(staff_id,effective_from)
); CREATE INDEX IF NOT EXISTS ix_staff_salary_structure_staff_id ON staff_salary_structure(staff_id);

CREATE TABLE IF NOT EXISTS staff_attendance_event (
  id SERIAL PRIMARY KEY, staff_id INTEGER NOT NULL REFERENCES staff_member(id), event_at TIMESTAMP NOT NULL, event_type VARCHAR(24) NOT NULL, source VARCHAR(40) NOT NULL DEFAULT 'biometric', external_id VARCHAR(180) NULL, device_name VARCHAR(180) NOT NULL DEFAULT '', note VARCHAR(500) NOT NULL DEFAULT '', created_by_user_id INTEGER NULL REFERENCES "user"(id), created_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now())
); CREATE UNIQUE INDEX IF NOT EXISTS uq_staff_attendance_external_id ON staff_attendance_event(external_id); CREATE INDEX IF NOT EXISTS ix_staff_attendance_event_staff_id ON staff_attendance_event(staff_id); CREATE INDEX IF NOT EXISTS ix_staff_attendance_event_event_at ON staff_attendance_event(event_at);

CREATE TABLE IF NOT EXISTS staff_attendance_day (
  id SERIAL PRIMARY KEY, staff_id INTEGER NOT NULL REFERENCES staff_member(id), work_date DATE NOT NULL, first_in_at TIMESTAMP NULL, last_out_at TIMESTAMP NULL, worked_minutes INTEGER NOT NULL DEFAULT 0, status VARCHAR(24) NOT NULL DEFAULT 'absent', late_minutes INTEGER NOT NULL DEFAULT 0, overtime_minutes INTEGER NOT NULL DEFAULT 0, source_summary VARCHAR(180) NOT NULL DEFAULT '', updated_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now()), CONSTRAINT uq_staff_attendance_day UNIQUE(staff_id,work_date)
); CREATE INDEX IF NOT EXISTS ix_staff_attendance_day_work_date ON staff_attendance_day(work_date);

CREATE TABLE IF NOT EXISTS staff_leave_type (
  id SERIAL PRIMARY KEY, code VARCHAR(30) NOT NULL UNIQUE, name VARCHAR(120) NOT NULL, paid BOOLEAN NOT NULL DEFAULT TRUE, annual_entitlement DOUBLE PRECISION NOT NULL DEFAULT 0, active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now())
);
CREATE TABLE IF NOT EXISTS staff_leave_balance (
  id SERIAL PRIMARY KEY, staff_id INTEGER NOT NULL REFERENCES staff_member(id), leave_type_id INTEGER NOT NULL REFERENCES staff_leave_type(id), year INTEGER NOT NULL, entitled_units DOUBLE PRECISION NOT NULL DEFAULT 0, used_units DOUBLE PRECISION NOT NULL DEFAULT 0, pending_units DOUBLE PRECISION NOT NULL DEFAULT 0, updated_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now()), CONSTRAINT uq_staff_leave_balance UNIQUE(staff_id,leave_type_id,year)
);
CREATE TABLE IF NOT EXISTS staff_leave_request (
  id SERIAL PRIMARY KEY, staff_id INTEGER NOT NULL REFERENCES staff_member(id), leave_type_id INTEGER NOT NULL REFERENCES staff_leave_type(id), start_date DATE NOT NULL, end_date DATE NOT NULL, units DOUBLE PRECISION NOT NULL DEFAULT 1, status VARCHAR(24) NOT NULL DEFAULT 'submitted', reason VARCHAR(1000) NOT NULL DEFAULT '', review_note VARCHAR(1000) NOT NULL DEFAULT '', reviewed_by_user_id INTEGER NULL REFERENCES "user"(id), reviewed_at TIMESTAMP NULL, created_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now()), updated_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now())
); CREATE INDEX IF NOT EXISTS ix_staff_leave_request_status ON staff_leave_request(status);

CREATE TABLE IF NOT EXISTS staff_payroll_period (
  id SERIAL PRIMARY KEY, code VARCHAR(32) NOT NULL UNIQUE, period_start DATE NOT NULL, period_end DATE NOT NULL, payable_days INTEGER NOT NULL DEFAULT 30, status VARCHAR(32) NOT NULL DEFAULT 'draft', calculated_at TIMESTAMP NULL, approved_at TIMESTAMP NULL, locked_at TIMESTAMP NULL, created_by_user_id INTEGER NULL REFERENCES "user"(id), created_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now())
);
CREATE TABLE IF NOT EXISTS staff_payroll_item (
  id SERIAL PRIMARY KEY, payroll_period_id INTEGER NOT NULL REFERENCES staff_payroll_period(id), staff_id INTEGER NOT NULL REFERENCES staff_member(id), snapshot_json TEXT NOT NULL DEFAULT '{}', gross_earnings_minor BIGINT NOT NULL DEFAULT 0, total_deductions_minor BIGINT NOT NULL DEFAULT 0, net_salary_minor BIGINT NOT NULL DEFAULT 0, status VARCHAR(24) NOT NULL DEFAULT 'calculated', paid_minor BIGINT NOT NULL DEFAULT 0, created_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now()), updated_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now()), CONSTRAINT uq_staff_payroll_item UNIQUE(payroll_period_id,staff_id)
);
CREATE TABLE IF NOT EXISTS staff_payroll_adjustment (
  id SERIAL PRIMARY KEY, staff_id INTEGER NOT NULL REFERENCES staff_member(id), payroll_period_id INTEGER NULL REFERENCES staff_payroll_period(id), adjustment_type VARCHAR(40) NOT NULL DEFAULT 'other', amount_minor BIGINT NOT NULL DEFAULT 0, description VARCHAR(500) NOT NULL DEFAULT '', applied BOOLEAN NOT NULL DEFAULT FALSE, created_by_user_id INTEGER NULL REFERENCES "user"(id), created_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now())
);
CREATE TABLE IF NOT EXISTS staff_ledger_entry (
  id SERIAL PRIMARY KEY, staff_id INTEGER NOT NULL REFERENCES staff_member(id), entry_date DATE NOT NULL DEFAULT CURRENT_DATE, description VARCHAR(500) NOT NULL DEFAULT '', debit_minor BIGINT NOT NULL DEFAULT 0, credit_minor BIGINT NOT NULL DEFAULT 0, source_type VARCHAR(60) NOT NULL DEFAULT '', source_id INTEGER NULL, created_by_user_id INTEGER NULL REFERENCES "user"(id), created_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now())
); CREATE INDEX IF NOT EXISTS ix_staff_ledger_entry_staff_id ON staff_ledger_entry(staff_id);

CREATE TABLE IF NOT EXISTS staff_salary_payment_batch (
  id SERIAL PRIMARY KEY, payroll_period_id INTEGER NOT NULL REFERENCES staff_payroll_period(id), batch_reference VARCHAR(80) NOT NULL UNIQUE, status VARCHAR(24) NOT NULL DEFAULT 'created', total_minor BIGINT NOT NULL DEFAULT 0, item_count INTEGER NOT NULL DEFAULT 0, created_by_user_id INTEGER NULL REFERENCES "user"(id), created_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now()), completed_at TIMESTAMP NULL
);
CREATE TABLE IF NOT EXISTS staff_salary_payment (
  id SERIAL PRIMARY KEY, batch_id INTEGER NOT NULL REFERENCES staff_salary_payment_batch(id), payroll_item_id INTEGER NOT NULL UNIQUE REFERENCES staff_payroll_item(id), staff_id INTEGER NOT NULL REFERENCES staff_member(id), amount_minor BIGINT NOT NULL DEFAULT 0, status VARCHAR(24) NOT NULL DEFAULT 'pending', bank_reference VARCHAR(180) NOT NULL DEFAULT '', paid_at TIMESTAMP NULL, created_at TIMESTAMP NOT NULL DEFAULT timezone('utc', now())
); CREATE INDEX IF NOT EXISTS ix_staff_salary_payment_staff_id ON staff_salary_payment(staff_id);

-- Supabase public-schema hardening: server-side Flask uses the database connection,
-- while Data API roles remain default-deny unless explicit policies are added later.
ALTER TABLE staff_member ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_document ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_bank_account ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_salary_structure ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_attendance_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_attendance_day ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_leave_type ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_leave_balance ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_leave_request ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_payroll_period ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_payroll_item ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_payroll_adjustment ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_ledger_entry ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_salary_payment_batch ENABLE ROW LEVEL SECURITY;
ALTER TABLE staff_salary_payment ENABLE ROW LEVEL SECURITY;

COMMIT;
