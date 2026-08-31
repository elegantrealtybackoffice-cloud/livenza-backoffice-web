from __future__ import annotations

import datetime as dt
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable, Mapping, Any


ATTENDANCE_ALIASES = {
    'p': 'present', 'present': 'present',
    'a': 'absent', 'absent': 'absent',
    'in': 'in', 'checkin': 'in', 'check-in': 'in', 'check in': 'in', 'punch in': 'in',
    'out': 'out', 'checkout': 'out', 'check-out': 'out', 'check out': 'out', 'punch out': 'out',
    'half': 'half_day', 'halfday': 'half_day', 'half-day': 'half_day', 'half day': 'half_day',
    'leave': 'leave', 'l': 'leave',
    'weekly off': 'weekly_off', 'weekly-off': 'weekly_off', 'weekly_off': 'weekly_off', 'wo': 'weekly_off',
    'holiday': 'holiday', 'h': 'holiday',
}

PAYROLL_TRANSITIONS = {
    ('draft', 'calculate'): 'calculated',
    ('calculated', 'review'): 'under_review',
    ('under_review', 'approve'): 'approved',
    ('approved', 'start_payment'): 'payment_processing',
    ('payment_processing', 'mark_paid'): 'paid',
    ('paid', 'lock'): 'locked',
    ('calculated', 'recalculate'): 'calculated',
    ('under_review', 'return_to_calculated'): 'calculated',
}

EARNING_KEYS = (
    'basic_minor', 'hra_minor', 'fixed_allowance_minor', 'travel_allowance_minor',
    'food_allowance_minor', 'mobile_allowance_minor', 'special_allowance_minor',
    'incentive_minor', 'overtime_minor', 'bonus_minor', 'arrears_minor',
)

DEDUCTION_KEYS = (
    'loss_of_pay_minor', 'advance_recovery_minor', 'loan_recovery_minor',
    'penalty_minor', 'statutory_deduction_minor', 'other_deduction_minor',
)


def money_minor(value: Any) -> int:
    """Convert rupee input to paise using decimal half-up rounding."""
    if value is None or value == '':
        return 0
    if isinstance(value, bool):
        raise ValueError('Boolean is not a money value')
    try:
        amount = Decimal(str(value).replace(',', '').strip())
    except (InvalidOperation, AttributeError):
        raise ValueError('Invalid money value') from None
    if not amount.is_finite():
        raise ValueError('Invalid money value')
    return int((amount * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def minor_to_rupees(value: int) -> str:
    value = int(value or 0)
    sign = '-' if value < 0 else ''
    value = abs(value)
    return f"{sign}{value // 100}.{value % 100:02d}"


def mask_identifier(value: Any, keep: int = 4) -> str:
    raw = ''.join(str(value or '').split())
    if not raw:
        return ''
    keep = max(0, int(keep))
    if len(raw) <= keep:
        return raw
    return '•' * (len(raw) - keep) + raw[-keep:]


def staff_code(prefix: str, sequence: int) -> str:
    prefix = '-'.join(part for part in str(prefix or 'LIV').strip().upper().replace('_', '-').split('-') if part)
    if not prefix:
        prefix = 'LIV'
    sequence = int(sequence)
    if sequence < 1:
        raise ValueError('Sequence must be positive')
    return f'{prefix}-{sequence:04d}'


def normalize_attendance_status(value: Any) -> str:
    key = ' '.join(str(value or '').strip().lower().replace('_', ' ').split())
    if key in ATTENDANCE_ALIASES:
        return ATTENDANCE_ALIASES[key]
    compact = key.replace(' ', '')
    if compact in ATTENDANCE_ALIASES:
        return ATTENDANCE_ALIASES[compact]
    raise ValueError(f'Unsupported attendance status: {value}')


def attendance_minutes(in_at: dt.datetime | None, out_at: dt.datetime | None) -> int:
    if not in_at or not out_at or out_at <= in_at:
        return 0
    return max(0, int((out_at - in_at).total_seconds() // 60))


def loss_of_pay_minor(monthly_gross_minor: int, payable_days: int, unpaid_days: float) -> int:
    payable_days = int(payable_days)
    if payable_days <= 0:
        raise ValueError('Payable days must be positive')
    gross = max(0, int(monthly_gross_minor or 0))
    unpaid = max(Decimal('0'), Decimal(str(unpaid_days or 0)))
    unpaid = min(unpaid, Decimal(payable_days))
    result = (Decimal(gross) * unpaid / Decimal(payable_days)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return int(result)


def calculate_payroll(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    earnings = {key: max(0, int(snapshot.get(key, 0) or 0)) for key in EARNING_KEYS}
    deductions = {key: max(0, int(snapshot.get(key, 0) or 0)) for key in DEDUCTION_KEYS}
    gross = sum(earnings.values())
    total_deductions = sum(deductions.values())
    net = max(0, gross - total_deductions)
    return {
        'earnings': earnings,
        'deductions': deductions,
        'gross_earnings_minor': gross,
        'total_deductions_minor': total_deductions,
        'net_salary_minor': net,
    }


def transition_payroll_status(current: str, event: str) -> str:
    key = (str(current or '').strip().lower(), str(event or '').strip().lower())
    if key not in PAYROLL_TRANSITIONS:
        raise ValueError(f'Illegal payroll transition: {key[0]} + {key[1]}')
    return PAYROLL_TRANSITIONS[key]


def ledger_balance(entries: Iterable[Mapping[str, Any]]) -> int:
    return sum(int(row.get('credit_minor', 0) or 0) - int(row.get('debit_minor', 0) or 0) for row in entries)


def build_bank_batch_rows(items: Iterable[Mapping[str, Any]]) -> list[dict[str, str]]:
    rows = []
    for item in items:
        amount_minor = max(0, int(item.get('amount_minor', 0) or 0))
        rows.append({
            'Staff Code': str(item.get('staff_code', '') or ''),
            'Employee': str(item.get('employee', '') or ''),
            'Account Holder': str(item.get('account_holder', '') or ''),
            'Account Number': str(item.get('account_number', '') or ''),
            'IFSC': str(item.get('ifsc', '') or '').upper(),
            'Amount': minor_to_rupees(amount_minor),
            'Reference': str(item.get('reference', '') or ''),
        })
    return rows
