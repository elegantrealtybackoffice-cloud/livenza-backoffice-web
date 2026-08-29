import pytest
from livenza_inventory_core import validate_unit_type, can_parent, availability_state


def test_inventory_hierarchy_rules():
    assert can_parent(None, "building")
    assert can_parent("building", "floor")
    assert can_parent("floor", "room")
    assert can_parent("room", "bed")
    assert not can_parent("bed", "room")


def test_invalid_inventory_unit_is_rejected():
    with pytest.raises(ValueError):
        validate_unit_type("desk")


def test_availability_state_is_derived_from_allocatable_count():
    assert availability_state(10, 10) == "sold_out"
    assert availability_state(10, 9) == "limited"
    assert availability_state(10, 3) == "available"


def test_availability_state_clamps_negative_values():
    assert availability_state(-1, 0) == "sold_out"
    assert availability_state(4, -3) == "available"
