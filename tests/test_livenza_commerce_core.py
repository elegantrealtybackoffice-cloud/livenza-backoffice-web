import pytest
from livenza_commerce_core import available_stock, validate_quantity, calculate_order_totals, transition_order


def test_available_stock_never_negative():
    assert available_stock(5, 2) == 3
    assert available_stock(2, 5) == 0


def test_validate_quantity_rejects_invalid_or_unavailable_quantity():
    assert validate_quantity(2, 3) == 2
    with pytest.raises(ValueError):
        validate_quantity(0, 3)
    with pytest.raises(ValueError):
        validate_quantity(4, 3)


def test_totals_use_integer_minor_units():
    totals = calculate_order_totals([(129900, 2), (69900, 1)], discount_minor=10000, delivery_minor=0)
    assert totals == {'subtotal_minor': 329700, 'discount_minor': 10000, 'delivery_minor': 0, 'total_minor': 319700}


def test_order_state_machine_rejects_skips():
    assert transition_order('placed', 'payment_paid') == 'confirmed'
    assert transition_order('confirmed', 'pack') == 'packed'
    assert transition_order('packed', 'ship') == 'shipped'
    assert transition_order('shipped', 'deliver') == 'delivered'
    assert transition_order('delivered', 'return') == 'returned'
    with pytest.raises(ValueError):
        transition_order('placed', 'deliver')
