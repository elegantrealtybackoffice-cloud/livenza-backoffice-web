from pathlib import Path

ROOT=Path(__file__).resolve().parent
APP=(ROOT/'app.py').read_text(encoding='utf-8')
MIG=ROOT/'migrations'/'staff_salary_v1.sql'

MODELS={
    'StaffMember': ['staff_code','full_name','photo_data_uri','aadhaar_no','pan_no','designation','department','property_name','joining_date','employment_type','shift_name','weekly_off','status'],
    'StaffDocument': ['staff_id','document_type','file_name','encrypted_blob','verification_status','uploaded_by_user_id'],
    'StaffBankAccount': ['staff_id','account_holder','account_number','ifsc','bank_name','branch_name','upi_id','preferred_method','active'],
    'StaffSalaryStructure': ['staff_id','effective_from','basic_minor','hra_minor','fixed_allowance_minor','travel_allowance_minor','food_allowance_minor','mobile_allowance_minor','special_allowance_minor','overtime_rate_minor','statutory_deduction_minor','active'],
    'StaffAttendanceEvent': ['staff_id','event_at','event_type','source','external_id','device_name','created_by_user_id'],
    'StaffAttendanceDay': ['staff_id','work_date','first_in_at','last_out_at','worked_minutes','status','late_minutes','overtime_minutes','source_summary'],
    'StaffLeaveType': ['code','name','paid','annual_entitlement','active'],
    'StaffLeaveBalance': ['staff_id','leave_type_id','year','entitled_units','used_units','pending_units'],
    'StaffLeaveRequest': ['staff_id','leave_type_id','start_date','end_date','units','status','reason','reviewed_by_user_id'],
    'StaffPayrollPeriod': ['code','period_start','period_end','payable_days','status','calculated_at','approved_at','locked_at'],
    'StaffPayrollItem': ['payroll_period_id','staff_id','snapshot_json','gross_earnings_minor','total_deductions_minor','net_salary_minor','status'],
    'StaffPayrollAdjustment': ['staff_id','payroll_period_id','adjustment_type','amount_minor','description','created_by_user_id'],
    'StaffLedgerEntry': ['staff_id','entry_date','description','debit_minor','credit_minor','source_type','source_id','created_by_user_id'],
    'StaffSalaryPaymentBatch': ['payroll_period_id','batch_reference','status','total_minor','item_count','created_by_user_id'],
    'StaffSalaryPayment': ['batch_id','payroll_item_id','staff_id','amount_minor','status','bank_reference','paid_at'],
}


def test_all_staff_salary_models_and_columns_are_present():
    for model, columns in MODELS.items():
        marker=f'class {model}(db.Model):'
        assert marker in APP, model
        block=APP.split(marker,1)[1].split('\nclass ',1)[0]
        for column in columns:
            assert column in block, f'{model}.{column}'


def test_staff_salary_migration_is_additive():
    assert MIG.exists()
    text=MIG.read_text(encoding='utf-8')
    upper=text.upper()
    for table in [
        'staff_member','staff_document','staff_bank_account','staff_salary_structure',
        'staff_attendance_event','staff_attendance_day','staff_leave_type','staff_leave_balance',
        'staff_leave_request','staff_payroll_period','staff_payroll_item','staff_payroll_adjustment',
        'staff_ledger_entry','staff_salary_payment_batch','staff_salary_payment'
    ]:
        assert f'CREATE TABLE IF NOT EXISTS {table.upper()}' in upper
    assert 'DROP TABLE' not in upper
    assert 'DROP COLUMN' not in upper
