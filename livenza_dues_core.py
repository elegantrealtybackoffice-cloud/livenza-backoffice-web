"""Pure tenant-dues helpers shared by My Livenza and admin workflows."""
from __future__ import annotations


def outstanding_minor(amount_minor: int, allocated_minor: int) -> int:
    amount=max(int(amount_minor or 0),0)
    allocated=max(int(allocated_minor or 0),0)
    return max(amount-allocated,0)


def due_status(amount_minor: int, allocated_minor: int) -> str:
    amount=max(int(amount_minor or 0),0)
    allocated=max(int(allocated_minor or 0),0)
    if amount <= 0 or allocated >= amount:
        return 'paid'
    if allocated > 0:
        return 'part_paid'
    return 'open'
