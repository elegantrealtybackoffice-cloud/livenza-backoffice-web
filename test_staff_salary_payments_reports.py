from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.py').read_text(encoding='utf-8')
TPL=(ROOT/'templates'/'staff_salary.html').read_text(encoding='utf-8')


def test_payment_and_report_routes_exist():
    for route in [
        "@app.route('/staff-salary/payments/batch',methods=['POST'])",
        "@app.route('/staff-salary/payments/batch/<int:batch_id>.csv')",
        "@app.route('/staff-salary/payments/<int:payment_id>/mark-paid',methods=['POST'])",
        "@app.route('/staff-salary/reports/<kind>.csv')",
    ]:
        assert route in APP


def test_batch_requires_approved_period_and_complete_bank_details():
    assert "period.status!='approved'" in APP
    assert 'bank_detail_errors' in APP
    assert '_staff_decrypt_text(bank.account_number,bank.account_nonce)' in APP
    assert 'batch.total_minor=sum(' in APP
    assert 'batch.item_count=len(' in APP


def test_bank_csv_contract_and_payment_idempotency():
    for column in ['Staff Code','Employee','Account Holder','Account Number','IFSC','Amount','Reference']:
        assert column in APP
    assert 'build_bank_batch_rows' in APP
    assert "if payment.status=='paid'" in APP
    assert "source_type='salary_payment'" in APP
    assert 'bank_reference' in APP


def test_mark_paid_is_admin_protected_and_reports_are_module_protected():
    marker="def staff_salary_payment_mark_paid(payment_id):"
    pos=APP.index(marker)
    before=APP[max(0,pos-250):pos]
    assert '@admin_required' in before
    report_pos=APP.index('def staff_salary_report(kind):')
    assert "@permission_required('staff_salary')" in APP[report_pos-200:report_pos]


def test_payment_and_report_ui_has_live_actions():
    for action in ['staff_salary_payment_batch_create','staff_salary_payment_batch_csv','staff_salary_payment_mark_paid','staff_salary_report']:
        assert f"url_for('{action}'" in TPL
    assert 'name="bank_reference"' in TPL
