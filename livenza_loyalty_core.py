"""Pure append-only loyalty arithmetic for Livenza+ V1."""


def balance(entries):
    total = 0
    for direction, points in entries:
        value = max(int(points or 0), 0)
        if str(direction) == 'credit':
            total += value
        elif str(direction) == 'debit':
            total -= value
    return total


def points_for_paid_amount(amount_minor, points_per_100_inr=1):
    amount_minor = max(int(amount_minor or 0), 0)
    rate = max(int(points_per_100_inr or 0), 0)
    return (amount_minor // 10000) * rate
