from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MY=ROOT/'web/src/components/my/my-dashboard.tsx'
ACCOUNT=ROOT/'web/src/app/account/page.tsx'
API=(ROOT/'web/src/lib/api.ts').read_text(encoding='utf-8')


def test_account_page_has_real_otp_login_not_plan_handoff_copy():
    assert ACCOUNT.exists()
    text=ACCOUNT.read_text(encoding='utf-8')
    assert 'arrives with the booking flow in Plan 3' not in text
    assert 'OtpLogin' in text


def test_my_dashboard_is_contextual_and_does_not_fake_a_stay():
    assert MY.exists()
    text=MY.read_text(encoding='utf-8')
    assert 'stays.length > 0' in text
    assert 'No active stay yet' in text
    assert 'CURRENT STAY' in text


def test_my_livenza_api_client_functions_exist():
    for fn in ['getMyStays','getMyPayments','getMyDocuments','getMySupport','createSupportTicket','patchMyProfile']:
        assert f'function {fn}' in API or f' {fn}(' in API


def test_my_pages_exist():
    for rel in ['web/src/app/my/page.tsx','web/src/app/my/stay/page.tsx','web/src/app/my/payments/page.tsx','web/src/app/my/documents/page.tsx','web/src/app/my/support/page.tsx']:
        assert (ROOT/rel).exists(), rel
