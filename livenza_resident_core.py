"""Pure resident-service policy and workflow helpers.

No Flask/SQLAlchemy imports: these rules are reusable from API, admin and tests.
"""
from __future__ import annotations

import json

ALLOWED_CAPABILITIES = ('notices', 'maintenance', 'leave', 'late_entry', 'guest', 'food')
DEFAULT_CAPABILITIES = ('notices', 'maintenance')


def normalize_capabilities(value) -> tuple[str, ...]:
    if value is None or value == '':
        return DEFAULT_CAPABILITIES
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
            value = decoded if isinstance(decoded, (list, tuple, set)) else [value]
        except Exception:
            value = [part.strip() for part in value.split(',') if part.strip()]
    if not isinstance(value, (list, tuple, set)):
        return DEFAULT_CAPABILITIES
    selected = {str(item or '').strip().lower() for item in value}
    return tuple(capability for capability in ALLOWED_CAPABILITIES if capability in selected)


def capability_enabled(value, capability: str) -> bool:
    return str(capability or '').strip().lower() in normalize_capabilities(value)


_REQUEST_TRANSITIONS = {
    'submitted': {'approve': 'approved', 'reject': 'rejected', 'cancel': 'cancelled'},
    'approved': {'cancel': 'cancelled'},
    'rejected': {},
    'cancelled': {},
}


def transition_resident_request(status: str, event: str) -> str:
    current = str(status or '').strip().lower()
    action = str(event or '').strip().lower()
    target = _REQUEST_TRANSITIONS.get(current, {}).get(action)
    if not target:
        raise ValueError(f'Invalid resident request transition: {current} -> {action}')
    return target
