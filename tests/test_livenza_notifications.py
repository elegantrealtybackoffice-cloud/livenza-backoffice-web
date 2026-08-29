from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/'livenza_notification_core.py'
API=(ROOT/'livenza_api_v1.py').read_text(encoding='utf-8')
APP=(ROOT/'app.py').read_text(encoding='utf-8')
INTEGRATIONS=(ROOT/'livenza_integrations.py').read_text(encoding='utf-8')


def load_core():
    spec=importlib.util.spec_from_file_location('livenza_notification_core',CORE)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def test_unsupported_event_is_rejected():
    core=load_core()
    try: core.dispatch_notification('unknown.event',{'primary_mobile':'9999999999'}, {}, ['whatsapp'], {})
    except ValueError: pass
    else: raise AssertionError('unsupported event accepted')


def test_provider_failure_returns_sanitized_delivery_and_masks_destination():
    core=load_core()
    def broken(destination,subject,body):
        return {'accepted':False,'provider':'whatsapp_cloud','error_code':'HTTP 500 token=secret'}
    results=core.dispatch_notification('booking.confirmed',{'primary_mobile':'+919876543210'}, {'booking_id':'B1'}, ['whatsapp'], {'whatsapp':broken})
    assert len(results)==1
    result=results[0]
    assert result.status=='failed'
    assert '9876543210' not in result.destination_masked
    assert 'secret' not in result.error_code.lower()


def test_integrations_expose_text_email_and_whatsapp_adapters():
    assert 'def send_whatsapp_text' in INTEGRATIONS
    assert 'def send_google_email_text' in INTEGRATIONS


def test_api_injects_notification_callback_and_calls_after_payment_commit():
    assert 'notify=None' in API.split('def register_api_v1',1)[1][:220]
    webhook=API.split('def razorpay_webhook',1)[1][:4200]
    assert 'db.session.commit()' in webhook
    assert 'notify(' in webhook
    assert webhook.index('db.session.commit()') < webhook.rindex('notify(')


def test_app_persists_masked_notification_delivery():
    assert 'def send_livenza_transactional_notification' in APP
    block=APP.split('def send_livenza_transactional_notification',1)[1][:4500]
    assert 'NotificationDelivery(' in block
    assert 'destination_masked' in block
    assert 'provider_message_id' in block
