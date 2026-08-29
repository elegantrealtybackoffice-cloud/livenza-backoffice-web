from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/'app.py').read_text(encoding='utf-8')
CORE=ROOT/'livenza_admin_core.py'


def load_core():
    spec=importlib.util.spec_from_file_location('livenza_admin_core',CORE)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def test_audit_meta_strips_secrets_and_kyc():
    core=load_core()
    out=core.audit_meta({'amount_minor':50000,'password':'x','otp':'123456','aadhaar':'1234','booking_id':7,'reason':'customer request'})
    assert out['amount_minor']==50000 and out['booking_id']==7 and out['reason']=='customer request'
    assert 'password' not in out and 'otp' not in out and 'aadhaar' not in out


def test_privileged_routes_are_permission_guarded_and_audited():
    contracts=[
        ('/admin/livenza/bookings/<int:booking_id>/cancel', "@permission_required('stays_admin')", 'booking.cancel'),
        ('/admin/livenza/payments/<int:payment_id>/refund-state', '@admin_required', 'payment.refund_state'),
        ('/admin/livenza/store/orders/<int:order_id>/status', "@permission_required('store_admin')", 'order.status'),
        ('/admin/livenza/store/variants/<int:variant_id>/stock', "@permission_required('store_admin')", 'variant.stock_adjust'),
        ('/admin/livenza/content/<int:content_id>/publish', "@permission_required('content')", 'content.publish'),
    ]
    for route, guard, action in contracts:
        assert route in APP
        block=APP.split(route,1)[1][:1800]
        assert guard in block
        assert action in block
        assert 'record_audit(' in block


def test_stock_adjustment_never_allows_stock_below_reserved():
    assert 'stock_reserved' in APP.split("/admin/livenza/store/variants/<int:variant_id>/stock",1)[1][:1600]
    assert 'abort(400)' in APP.split("/admin/livenza/store/variants/<int:variant_id>/stock",1)[1][:1600]
