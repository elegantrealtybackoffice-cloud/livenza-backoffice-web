import datetime as dt
import pytest

from staff_salary_core import (
    money_minor, mask_identifier, staff_code, normalize_attendance_status,
    attendance_minutes, loss_of_pay_minor, calculate_payroll,
    transition_payroll_status, ledger_balance, build_bank_batch_rows,
)


def test_money_minor_uses_deterministic_paise_rounding():
    assert money_minor('24500') == 2450000
    assert money_minor('24500.50') == 2450050
    assert money_minor(0) == 0
    assert money_minor('') == 0
    with pytest.raises(ValueError):
        money_minor('abc')


def test_mask_identifier_and_staff_code():
    assert mask_identifier('123456789012') == '••••••••9012'
    assert mask_identifier('ABCDE1234F') == '••••••234F'
    assert mask_identifier('1234') == '1234'
    assert staff_code('LIV-JPR', 1) == 'LIV-JPR-0001'
    assert staff_code(' liv-jpr ', 87) == 'LIV-JPR-0087'


def test_attendance_normalization_and_minutes():
    assert normalize_attendance_status('P') == 'present'
    assert normalize_attendance_status('check-in') == 'in'
    assert normalize_attendance_status('CHECK OUT') == 'out'
    assert normalize_attendance_status('half day') == 'half_day'
    with pytest.raises(ValueError):
        normalize_attendance_status('teleport')
    assert attendance_minutes(dt.datetime(2026,8,31,9), dt.datetime(2026,8,31,18,15)) == 555
    assert attendance_minutes(None, dt.datetime(2026,8,31,18,15)) == 0


def test_loss_of_pay_is_pro_rata_and_bounded():
    assert loss_of_pay_minor(3000000, 30, 2) == 200000
    assert loss_of_pay_minor(3000000, 30, 0) == 0
    assert loss_of_pay_minor(3000000, 30, 45) == 3000000
    with pytest.raises(ValueError):
        loss_of_pay_minor(3000000, 0, 1)


def test_calculate_payroll_returns_snapshot_totals():
    result = calculate_payroll({
        'basic_minor': 1500000,
        'hra_minor': 500000,
        'fixed_allowance_minor': 250000,
        'travel_allowance_minor': 50000,
        'food_allowance_minor': 50000,
        'mobile_allowance_minor': 25000,
        'special_allowance_minor': 125000,
        'incentive_minor': 100000,
        'overtime_minor': 75000,
        'bonus_minor': 50000,
        'arrears_minor': 25000,
        'loss_of_pay_minor': 100000,
        'advance_recovery_minor': 50000,
        'loan_recovery_minor': 25000,
        'penalty_minor': 10000,
        'statutory_deduction_minor': 60000,
        'other_deduction_minor': 5000,
    })
    assert result['gross_earnings_minor'] == 2750000
    assert result['total_deductions_minor'] == 250000
    assert result['net_salary_minor'] == 2500000
    assert result['earnings']['basic_minor'] == 1500000


def test_payroll_status_machine_rejects_illegal_transitions():
    assert transition_payroll_status('draft','calculate') == 'calculated'
    assert transition_payroll_status('calculated','review') == 'under_review'
    assert transition_payroll_status('under_review','approve') == 'approved'
    assert transition_payroll_status('approved','start_payment') == 'payment_processing'
    assert transition_payroll_status('payment_processing','mark_paid') == 'paid'
    assert transition_payroll_status('paid','lock') == 'locked'
    with pytest.raises(ValueError):
        transition_payroll_status('locked','calculate')


def test_ledger_balance_and_bank_batch_rows():
    entries=[
        {'debit_minor':0,'credit_minor':2800000},
        {'debit_minor':500000,'credit_minor':0},
        {'debit_minor':2300000,'credit_minor':0},
    ]
    assert ledger_balance(entries) == 0
    rows=build_bank_batch_rows([{
        'staff_code':'LIV-JPR-0001','employee':'Asha','account_holder':'Asha',
        'account_number':'1234567890','ifsc':'PUNB0406400','amount_minor':2450050,
        'reference':'SAL-2026-08-0001'
    }])
    assert rows == [{
        'Staff Code':'LIV-JPR-0001','Employee':'Asha','Account Holder':'Asha',
        'Account Number':'1234567890','IFSC':'PUNB0406400','Amount':'24500.50',
        'Reference':'SAL-2026-08-0001'
    }]
