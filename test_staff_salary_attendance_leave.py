from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.py').read_text(encoding='utf-8')
TPL=(ROOT/'templates'/'staff_salary.html').read_text(encoding='utf-8')


def test_attendance_routes_and_csv_contract():
    assert "@app.route('/staff-salary/attendance/import',methods=['POST'])" in APP
    assert "@app.route('/staff-salary/attendance/manual',methods=['POST'])" in APP
    for header in ['staff_code','timestamp','event_type','external_id']:
        assert header in APP
    assert 'normalize_attendance_status' in APP
    assert 'StaffAttendanceEvent.query.filter_by(external_id=external_id)' in APP
    assert 'def _staff_rebuild_attendance_day(' in APP


def test_manual_attendance_and_leave_actions_are_audited():
    for action in ['attendance_imported','attendance_manual_correction','leave_type_saved','leave_requested','leave_approved','leave_rejected']:
        assert action in APP
    assert "module='staff_salary'" in APP


def test_leave_routes_and_balance_arithmetic_exist():
    assert "@app.route('/staff-salary/leave-types',methods=['POST'])" in APP
    assert "@app.route('/staff-salary/leave',methods=['POST'])" in APP
    assert "@app.route('/staff-salary/leave/<int:leave_id>/status',methods=['POST'])" in APP
    assert 'pending_units' in APP and 'used_units' in APP and 'entitled_units' in APP
    assert 'def _staff_leave_balance(' in APP


def test_attendance_and_leave_tabs_have_working_forms():
    for action in ['staff_salary_attendance_import','staff_salary_attendance_manual','staff_salary_leave_type_save','staff_salary_leave_request']:
        assert f"url_for('{action}'" in TPL
    assert 'name="attendance_file"' in TPL
    assert 'name="leave_type_id"' in TPL
    assert 'name="decision"' in TPL

def test_vendor_neutral_biometric_webhook_supports_automatic_feed():
    assert "@app.route('/webhooks/staff-attendance',methods=['POST'])" in APP
    assert "STAFF_ATTENDANCE_WEBHOOK_TOKEN" in APP
    assert "X-Livenza-Webhook-Token" in APP
    assert 'def _staff_ingest_attendance_record(' in APP
    assert "source='biometric_api'" in APP
