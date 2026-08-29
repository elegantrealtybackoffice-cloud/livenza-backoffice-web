from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT/'web/src/app/stays/book/page.tsx'
WIZARD = ROOT/'web/src/components/booking/booking-wizard.tsx'
STATUS = ROOT/'web/src/components/booking/booking-status.tsx'
PAY = ROOT/'web/src/app/pay/[paymentId]/page.tsx'
API = (ROOT/'web/src/lib/api.ts').read_text(encoding='utf-8')
TYPES = (ROOT/'web/src/lib/types.ts').read_text(encoding='utf-8')
ANALYTICS = (ROOT/'web/src/lib/analytics.ts').read_text(encoding='utf-8')


def test_booking_handoff_is_replaced_by_real_wizard():
    assert BOOK.exists() and WIZARD.exists()
    text=BOOK.read_text(encoding='utf-8')
    assert 'BookingHandoff' not in text
    assert 'BookingWizard' in text


def test_wizard_covers_required_steps_and_guardian_rules():
    text=WIZARD.read_text(encoding='utf-8')
    for label in ['Stay','Sign in','Resident','Guardian','Add-ons','Summary','Payment']:
        assert label in text
    assert "stayType === 'student'" in text
    assert 'guardianName' in text and 'guardianMobile' in text
    assert 'stayType === \'corporate\'' in text or 'stayType !== \'student\'' in text


def test_reserve_mode_and_double_click_guard_are_explicit():
    text=WIZARD.read_text(encoding='utf-8')
    assert "bookingMode === 'reserve'" in text
    assert 'reservation_amount_minor' in text
    assert 'paymentPending' in text and 'disabled={paymentPending}' in text
    assert "track('booking_payment_start'" in text


def test_razorpay_is_lazy_loaded_only_in_payment_action():
    text=WIZARD.read_text(encoding='utf-8')
    assert 'https://checkout.razorpay.com/v1/checkout.js' in text
    assert 'loadRazorpay' in text
    assert '<Script' not in text


def test_booking_status_page_polls_backend_and_has_timeout_copy():
    assert STATUS.exists()
    text=STATUS.read_text(encoding='utf-8')
    assert 'getBooking' in text
    assert '60_000' in text or '60000' in text
    assert 'My Livenza' in text


def test_payment_page_and_api_types_exist():
    assert PAY.exists()
    for fragment in ['requestOtp','verifyOtp','createHold','createBooking','createPayment','getBooking','getPayment','createParentShare']:
        assert fragment in API
    for typename in ['RatePlan','InventoryHold','Booking','Payment']:
        assert f'export type {typename}' in TYPES
    assert "'booking_payment_start'" in ANALYTICS and "'booking_complete'" in ANALYTICS
