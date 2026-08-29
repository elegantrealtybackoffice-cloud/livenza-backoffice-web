from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
API=(ROOT/'livenza_api_v1.py').read_text(encoding='utf-8')
CHECKOUT=(ROOT/'web/src/components/store/checkout-view.tsx').read_text(encoding='utf-8')
BOOKING=(ROOT/'web/src/components/booking/booking-wizard.tsx').read_text(encoding='utf-8')


def _block(name): return API.split(f'def {name}(',1)[1].split('\n    @api.',1)[0]


def test_delivery_options_route_is_owner_derived_from_confirmed_current_stay():
    assert '/me/delivery-options' in API
    block=_block('my_delivery_options')
    helper=_block('_eligible_property_room_delivery')
    assert 'session_for_request()' in block
    for text in ['StayBooking.customer_id == customer_id','StayBooking.status == "confirmed"','LIVENZA_INTERNAL_DELIVERY_PROPERTIES','StayBookingItem','StayInventoryUnit']:
        assert text in API
    assert 'payload.get("property"' not in block and 'payload.get("room"' not in block


def test_order_rejects_self_asserted_property_room_delivery():
    block=_block('create_store_order')
    assert '_eligible_property_room_delivery' in block
    assert 'invalid_delivery_option' in block


def test_move_in_kit_booking_addon_is_sourced_from_store_variant():
    catalog=_block('_booking_addon_catalog')
    booking=_block('create_booking')
    assert 'booking_addon_code' in catalog
    assert 'source_variant_id' in catalog
    assert 'source_product_id' in catalog
    assert 'source_variant_id' in booking
    assert 'metadata_json' in booking


def test_checkout_can_render_backend_delivery_options():
    assert 'getDeliveryOptions' in CHECKOUT
    assert 'property_room' in CHECKOUT
    assert 'Deliver to my Livenza property' in CHECKOUT


def test_booking_wizard_can_surface_move_in_kit_as_normal_server_addon():
    assert 'getBookingAddons' in BOOKING
    assert 'move_in_kit' not in BOOKING or 'selectedAddons' in BOOKING
