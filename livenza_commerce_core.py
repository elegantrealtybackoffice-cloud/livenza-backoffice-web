"""Pure commerce rules for Livenza.store V1."""

ORDER_TRANSITIONS = {
    ('placed', 'payment_paid'): 'confirmed',
    ('placed', 'cancel'): 'cancelled',
    ('confirmed', 'pack'): 'packed',
    ('confirmed', 'cancel'): 'cancelled',
    ('packed', 'ship'): 'shipped',
    ('packed', 'cancel'): 'cancelled',
    ('shipped', 'deliver'): 'delivered',
    ('delivered', 'return'): 'returned',
}


def available_stock(stock_on_hand, stock_reserved):
    return max(int(stock_on_hand or 0) - int(stock_reserved or 0), 0)


def validate_quantity(quantity, available):
    quantity = int(quantity)
    available = max(int(available or 0), 0)
    if quantity < 1:
        raise ValueError('Quantity must be at least 1.')
    if quantity > available:
        raise ValueError('Requested quantity is not available.')
    return quantity


def calculate_order_totals(lines, discount_minor=0, delivery_minor=0):
    subtotal = sum(int(unit_price) * int(quantity) for unit_price, quantity in lines)
    discount = max(int(discount_minor or 0), 0)
    delivery = max(int(delivery_minor or 0), 0)
    total = max(subtotal - discount + delivery, 0)
    return {
        'subtotal_minor': subtotal,
        'discount_minor': discount,
        'delivery_minor': delivery,
        'total_minor': total,
    }


def transition_order(current_status, event):
    try:
        return ORDER_TRANSITIONS[(str(current_status), str(event))]
    except KeyError as exc:
        raise ValueError(f'Invalid order transition: {current_status} + {event}') from exc
