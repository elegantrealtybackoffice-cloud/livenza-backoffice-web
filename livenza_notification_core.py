"""Pure transactional-notification formatting and delivery orchestration."""
from __future__ import annotations

import re

EVENT_TEMPLATES = {
    'booking.confirmed': ('Booking confirmed', 'Your Livenza booking {booking_id} is confirmed.'),
    'reservation.expiring': ('Reservation expiring', 'Your Livenza reservation {booking_id} is nearing expiry.'),
    'payment.received': ('Payment received', 'We received your payment for {reference}.'),
    'payment.due': ('Payment due', 'A payment is due for {reference}.'),
    'order.confirmed': ('Order confirmed', 'Your Livenza.store order {order_id} is confirmed.'),
    'order.shipped': ('Order shipped', 'Your Livenza.store order {order_id} has shipped.'),
    'support.updated': ('Support update', 'Your Livenza support ticket {ticket_id} was updated.'),
    'reward.earned': ('Livenza+ reward', 'You earned Livenza+ points from {reference}.'),
    'movein.approaching': ('Move-in approaching', 'Your Livenza move-in for {booking_id} is approaching.'),
}


class DeliveryResult:
    __slots__=('channel','status','destination_masked','provider_reference','error_code')
    def __init__(self, channel, status, destination_masked='', provider_reference='', error_code=''):
        self.channel=channel; self.status=status; self.destination_masked=destination_masked
        self.provider_reference=provider_reference; self.error_code=error_code


def _value(customer, key):
    if isinstance(customer, dict):
        return customer.get(key) or ''
    return getattr(customer, key, '') or ''


def mask_destination(value: str) -> str:
    raw=str(value or '').strip()
    if not raw: return ''
    if '@' in raw:
        local, domain=raw.split('@',1)
        prefix=(local[:1] if local else '')
        return f"{prefix}•••@{domain}"[:180]
    digits=''.join(ch for ch in raw if ch.isdigit())
    return ('•'*max(len(digits)-2,4)+digits[-2:])[:180] if digits else '••••'


def sanitize_error_code(value: str) -> str:
    text=str(value or '').strip().lower()
    if not text: return ''
    if any(term in text for term in ('token','secret','password','authorization','cookie','credential')):
        return 'provider_error'
    safe=re.sub(r'[^a-z0-9_.-]+','_',text).strip('_')[:80]
    return safe or 'provider_error'


class _SafeFormat(dict):
    def __missing__(self,key): return 'your Livenza account'


def dispatch_notification(event_name, customer, context, channels, providers):
    if event_name not in EVENT_TEMPLATES:
        raise ValueError('Unsupported notification event.')
    subject_template, body_template=EVENT_TEMPLATES[event_name]
    context=_SafeFormat({str(k):str(v) for k,v in (context or {}).items() if v is not None})
    subject=subject_template.format_map(context); body=body_template.format_map(context)
    providers=providers or {}; results=[]
    for channel in channels or []:
        if channel not in {'email','whatsapp'}:
            results.append(DeliveryResult(channel,'skipped','','','unsupported_channel')); continue
        destination=_value(customer,'primary_email' if channel=='email' else 'primary_mobile')
        masked=mask_destination(destination)
        if not destination:
            results.append(DeliveryResult(channel,'skipped',masked,'','missing_destination')); continue
        provider=providers.get(channel)
        if not provider:
            results.append(DeliveryResult(channel,'skipped',masked,'','integration_not_configured')); continue
        try:
            raw=provider(destination,subject,body) or {}
        except Exception:
            raw={'accepted':False,'error_code':'provider_exception'}
        accepted=bool(raw.get('accepted'))
        results.append(DeliveryResult(
            channel,'sent' if accepted else 'failed',masked,
            str(raw.get('reference') or '')[:180] if accepted else '',
            '' if accepted else sanitize_error_code(raw.get('error_code') or 'provider_error'),
        ))
    return results
