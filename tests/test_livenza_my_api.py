from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
API=(ROOT/'livenza_api_v1.py').read_text(encoding='utf-8')
APP=(ROOT/'app.py').read_text(encoding='utf-8')


def test_my_livenza_routes_exist():
    for route in ['/me/stays','/me/payments','/me/documents','/me/support']:
        assert route in API
    assert '@api.patch("/me/profile")' in API
    assert '@api.post("/me/support")' in API


def test_every_my_query_is_scoped_to_authenticated_customer():
    for fn in ['my_stays','my_payments','my_documents','my_support']:
        block=API.split(f'def {fn}():',1)[1].split('\n    @api.',1)[0]
        assert 'session_for_request()' in block
        assert 'customer_id=customer.id' in block or 'customer.id' in block
        assert 'request.args.get("customer' not in block


def test_support_creation_has_stable_categories_and_limits():
    block=API.split('def create_support_ticket():',1)[1].split('\n    @api.',1)[0]
    for category in ['stay','payment','store','account','other']:
        assert f'"{category}"' in block
    assert 'len(subject) > 180' in block
    assert 'len(description) > 5000' in block


def test_profile_patch_does_not_allow_mobile_or_customer_id_reassignment():
    block=API.split('def patch_me_profile():',1)[1].split('\n    @api.',1)[0]
    assert 'primary_mobile' not in block
    assert 'customer_id' not in block
    assert 'full_name' in block and 'primary_email' in block


def test_api_registration_injects_document_and_support_models():
    assert "'CustomerDocument': CustomerDocument" in APP
    assert "'SupportTicket': SupportTicket" in APP
