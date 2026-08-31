UNIT_TYPES = ("building", "wing", "floor", "unit", "room", "bed")
ALLOWED_CHILDREN = {
    None: {"building", "wing", "floor", "unit", "room", "bed"},
    "building": {"wing", "floor", "unit", "room"},
    "wing": {"floor", "unit", "room"},
    "floor": {"unit", "room"},
    "unit": {"room", "bed"},
    "room": {"bed"},
    "bed": set(),
}


def validate_unit_type(unit_type: str) -> str:
    value = (unit_type or "").strip().lower()
    if value not in UNIT_TYPES:
        raise ValueError("unsupported inventory unit type")
    return value


def can_parent(parent_type, child_type: str) -> bool:
    child = validate_unit_type(child_type)
    parent = None if parent_type is None else validate_unit_type(parent_type)
    return child in ALLOWED_CHILDREN[parent]


def availability_state(total_allocatable: int, unavailable: int) -> str:
    total = max(int(total_allocatable), 0)
    blocked = min(max(int(unavailable), 0), total)
    free = total - blocked
    if free <= 0:
        return "sold_out"
    if total >= 4 and free <= max(1, total // 4):
        return "limited"
    return "available"
