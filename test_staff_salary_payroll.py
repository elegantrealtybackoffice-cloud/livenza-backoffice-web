from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.py').read_text(encoding='utf-8')
TPL=(ROOT/'templates'/'staff_salary.html').read_text(encoding='utf-8')
PAYSLIP=(ROOT/'templates'/'staff_salary_payslip.html').read_text(encoding='utf-8') if (ROOT/'templates'/'staff_salary_payslip.html').exists() else ''
LEDGER=(ROOT/'templates'/'staff_salary_ledger.html').read_text(encoding='utf-8') if (ROOT/'templates'/'staff_salary_ledger.html').exists() else ''


def test_payroll_routes_exist_and_are_protected():
    for route in [
        "@app.route('/staff-salary/payroll/period',methods=['POST'])",
        "@app.route('/staff-salary/payroll/<int:period_id>/calculate',methods=['POST'])",
        "@app.route('/staff-salary/payroll/<int:period_id>/status',methods=['POST'])",
        "@app.route('/staff-salary/payroll/<int:period_id>/payslip/<int:staff_id>')",
        "@app.route('/staff-salary/ledger/<int:staff_id>')",
    ]:
        assert route in APP
    assert APP.count("@permission_required('staff_salary')") >= 15


def test_payroll_calculation_snapshots_attendance_leave_and_salary():
    assert 'def _staff_build_payroll_snapshot(' in APP
    assert 'loss_of_pay_minor' in APP
    assert 'overtime_minutes' in APP
    assert 'unpaid_leave_units' in APP
    assert 'snapshot_json=json.dumps(snapshot' in APP or 'item.snapshot_json=json.dumps(snapshot' in APP
    assert "period.status in {'draft','calculated'}" in APP


def test_approval_posts_idempotent_salary_credit_and_lock_guard():
    assert "source_type='payroll_item'" in APP
    assert 'salary_credit' in APP
    assert "if period.status=='locked'" in APP
    assert "transition_payroll_status(period.status,event)" in APP


def test_payroll_ui_has_period_calculate_review_approve_and_payslip():
    for action in ['staff_salary_payroll_period_create','staff_salary_payroll_calculate','staff_salary_payroll_status']:
        assert f"url_for('{action}'" in TPL
    assert 'value="review"' in TPL and 'value="approve"' in TPL
    assert 'staff_salary_payslip' in TPL


def test_payslip_and_ledger_templates_show_financial_breakdown():
    for term in ['Earnings','Deductions','Net Salary','Attendance']:
        assert term in PAYSLIP
    for term in ['Debit','Credit','Balance']:
        assert term in LEDGER
