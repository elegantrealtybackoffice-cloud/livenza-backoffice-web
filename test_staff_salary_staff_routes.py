from pathlib import Path
ROOT=Path(__file__).resolve().parent
APP=(ROOT/'app.py').read_text(encoding='utf-8')
MAIN=(ROOT/'templates'/'staff_salary.html').read_text(encoding='utf-8') if (ROOT/'templates'/'staff_salary.html').exists() else ''
EDIT=(ROOT/'templates'/'staff_salary_staff_edit.html').read_text(encoding='utf-8') if (ROOT/'templates'/'staff_salary_staff_edit.html').exists() else ''


def test_staff_salary_routes_are_permission_protected():
    for route in [
        "@app.route('/staff-salary')",
        "@app.route('/staff-salary/staff/new',methods=['GET','POST'])",
        "@app.route('/staff-salary/staff/<int:staff_id>',methods=['GET','POST'])",
        "@app.route('/staff-salary/staff/<int:staff_id>/salary-structure',methods=['POST'])",
        "@app.route('/staff-salary/staff/<int:staff_id>/document',methods=['POST'])",
    ]:
        assert route in APP
    assert APP.count("@permission_required('staff_salary')") >= 5


def test_staff_sensitive_helpers_encrypt_and_mask():
    assert 'def _staff_encrypt_text(' in APP
    assert 'encrypt_secret(' in APP
    assert 'def _staff_masked_member(' in APP
    assert 'aadhaar_masked' in APP and 'pan_masked' in APP and 'account_masked' in APP


def test_staff_form_requests_photo_kyc_bank_and_salary_fields():
    text=MAIN+EDIT
    for field in ['staff_photo','aadhaar_no','pan_no','account_number','ifsc','basic','hra','fixed_allowance','overtime_rate']:
        assert f'name="{field}"' in text
    assert 'accept="image/jpeg,image/png,image/webp"' in text


def test_staff_documents_are_encrypted_not_public_static_files():
    assert 'encrypt_blob(raw,_master_key())' in APP
    assert 'decrypt_blob(doc.encrypted_blob,doc.encrypted_nonce,_master_key())' in APP
    assert 'staff_document_download' in APP


def test_staff_main_screen_has_required_v1_tabs():
    assert 'data-staff-tab="{{key}}"' in MAIN
    for tab in ['dashboard','staff','attendance','leave','salary','payroll','ledger','payments','reports','settings']:
        assert f"('{tab}'," in MAIN
