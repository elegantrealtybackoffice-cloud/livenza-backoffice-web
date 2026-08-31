-- Livenza Staff Salary Studio V1 performance follow-up.
-- Cover foreign keys that are not already the leading column of a unique/index constraint.
BEGIN;
CREATE INDEX IF NOT EXISTS ix_staff_member_created_by_user_id ON staff_member(created_by_user_id);
CREATE INDEX IF NOT EXISTS ix_staff_document_uploaded_by_user_id ON staff_document(uploaded_by_user_id);
CREATE INDEX IF NOT EXISTS ix_staff_salary_structure_created_by_user_id ON staff_salary_structure(created_by_user_id);
CREATE INDEX IF NOT EXISTS ix_staff_attendance_event_created_by_user_id ON staff_attendance_event(created_by_user_id);
CREATE INDEX IF NOT EXISTS ix_staff_leave_balance_leave_type_id ON staff_leave_balance(leave_type_id);
CREATE INDEX IF NOT EXISTS ix_staff_leave_request_staff_id ON staff_leave_request(staff_id);
CREATE INDEX IF NOT EXISTS ix_staff_leave_request_leave_type_id ON staff_leave_request(leave_type_id);
CREATE INDEX IF NOT EXISTS ix_staff_leave_request_reviewed_by_user_id ON staff_leave_request(reviewed_by_user_id);
CREATE INDEX IF NOT EXISTS ix_staff_payroll_period_created_by_user_id ON staff_payroll_period(created_by_user_id);
CREATE INDEX IF NOT EXISTS ix_staff_payroll_item_staff_id ON staff_payroll_item(staff_id);
CREATE INDEX IF NOT EXISTS ix_staff_payroll_adjustment_staff_id ON staff_payroll_adjustment(staff_id);
CREATE INDEX IF NOT EXISTS ix_staff_payroll_adjustment_payroll_period_id ON staff_payroll_adjustment(payroll_period_id);
CREATE INDEX IF NOT EXISTS ix_staff_payroll_adjustment_created_by_user_id ON staff_payroll_adjustment(created_by_user_id);
CREATE INDEX IF NOT EXISTS ix_staff_ledger_entry_created_by_user_id ON staff_ledger_entry(created_by_user_id);
CREATE INDEX IF NOT EXISTS ix_staff_salary_payment_batch_payroll_period_id ON staff_salary_payment_batch(payroll_period_id);
CREATE INDEX IF NOT EXISTS ix_staff_salary_payment_batch_created_by_user_id ON staff_salary_payment_batch(created_by_user_id);
CREATE INDEX IF NOT EXISTS ix_staff_salary_payment_batch_id ON staff_salary_payment(batch_id);
COMMIT;
