"""Pure domain helpers for My Livenza tenant onboarding.

This module intentionally has no Flask/SQLAlchemy dependency so tenancy rules can
be reused and tested without booting the web application.
"""
from __future__ import annotations

import datetime

TENANCY_TYPES = ('student', 'corporate', 'ota_short_stay', 'long_term')

_TENANCY_ALIASES = {
    'student': 'student',
    'hostel': 'student',
    'student_housing': 'student',
    'corporate': 'corporate',
    'company': 'corporate',
    'short_stay': 'ota_short_stay',
    'short-stay': 'ota_short_stay',
    'ota': 'ota_short_stay',
    'airbnb': 'ota_short_stay',
    'hotel': 'ota_short_stay',
    'ota_short_stay': 'ota_short_stay',
    'long_term': 'long_term',
    'long-term': 'long_term',
    'residential': 'long_term',
    'rental': 'long_term',
}

_COMMON_FIELDS = (
    'full_name',
    'permanent_address',
    'emergency_contact_name',
    'emergency_contact_mobile',
)

_REQUIRED_FIELDS = {
    'student': _COMMON_FIELDS + (
        'date_of_birth',
        'guardian_name',
        'guardian_mobile',
        'institute_name',
    ),
    'corporate': _COMMON_FIELDS + (
        'employer_name',
        'employee_id',
    ),
    'ota_short_stay': _COMMON_FIELDS,
    'long_term': _COMMON_FIELDS + (
        'date_of_birth',
    ),
}


def normalize_tenancy_type(value: str) -> str:
    key = str(value or '').strip().lower().replace(' ', '_')
    normalized = _TENANCY_ALIASES.get(key)
    if not normalized:
        raise ValueError(f'Unsupported tenancy type: {value!r}')
    return normalized


def required_profile_fields(tenancy_type: str) -> tuple[str, ...]:
    return _REQUIRED_FIELDS[normalize_tenancy_type(tenancy_type)]


def missing_profile_fields(tenancy_type: str, payload: dict | None) -> tuple[str, ...]:
    data = payload if isinstance(payload, dict) else {}
    return tuple(field for field in required_profile_fields(tenancy_type) if not str(data.get(field) or '').strip())


def onboarding_next_step(*, profile_complete: bool, documents_complete: bool,
                         documents_verified: bool, agreement_generated: bool,
                         agreement_accepted: bool) -> str:
    if not profile_complete:
        return 'profile'
    if not documents_complete:
        return 'documents'
    if not documents_verified:
        return 'verification'
    if not agreement_generated:
        return 'agreement'
    if not agreement_accepted:
        return 'agreement_acceptance'
    return 'complete'

_REQUIRED_DOCUMENT_TYPES = {
    'student': ('government_id', 'student_id'),
    'corporate': ('government_id', 'corporate_id'),
    'ota_short_stay': ('government_id',),
    'long_term': ('government_id',),
}

def required_document_types(tenancy_type: str) -> tuple[str, ...]:
    return _REQUIRED_DOCUMENT_TYPES[normalize_tenancy_type(tenancy_type)]

def mask_government_identifier(value: str) -> str:
    raw = ''.join(ch for ch in str(value or '').strip() if ch.isalnum())
    if not raw:
        return ''
    if raw.isdigit() and len(raw) >= 4:
        return f'•••• •••• {raw[-4:]}'
    keep = raw[-5:] if len(raw) >= 5 else raw[-4:]
    return ('•' * max(len(raw) - len(keep), 4)) + keep

_AGREEMENT_PRESETS = {
    'student': 'Student Accommodation',
    'corporate': 'Corporate / Serviced Stay',
    'ota_short_stay': 'OTA Commercial Hosting Rights',
    'long_term': 'Strong Residential - 11 Months',
}

_AGREEMENT_TYPES = {
    'student': 'Comprehensive Rental Agreement',
    'corporate': 'Corporate Stay / Serviced Accommodation Agreement',
    'ota_short_stay': 'Commercial Hosting / OTA Agreement',
    'long_term': 'Comprehensive Rental Agreement',
}


def agreement_preset_for_tenancy(tenancy_type: str) -> str:
    return _AGREEMENT_PRESETS[normalize_tenancy_type(tenancy_type)]


def _minor_to_rupees(value) -> str:
    try:
        return f'{int(value or 0) / 100:.2f}'
    except (TypeError, ValueError):
        return '0.00'


def agreement_payload_for_onboarding(onboarding, customer, booking, property_row, rate_plan, unit,
                                     *, legal_entity_name: str = 'Livenza Life LLP',
                                     legal_address: str = '') -> dict:
    tenancy_type = normalize_tenancy_type(getattr(onboarding, 'tenancy_type', ''))
    profile = getattr(onboarding, 'profile', {}) or {}
    if not isinstance(profile, dict):
        profile = {}
    property_name = str(getattr(property_row, 'name', '') or '').strip()
    area = str(getattr(property_row, 'area', '') or '').strip()
    city = str(getattr(property_row, 'city', '') or '').strip()
    premises = ', '.join(part for part in (property_name, area, city) if part)
    unit_name = str(getattr(unit, 'display_name', '') or getattr(unit, 'code', '') or '').strip()
    purpose = str(profile.get('purpose_of_stay') or '').strip()
    if tenancy_type == 'student':
        institute = str(profile.get('institute_name') or '').strip()
        purpose = purpose or (f'Student accommodation while attending {institute}' if institute else 'Student accommodation')
    elif tenancy_type == 'corporate':
        employer = str(profile.get('employer_name') or '').strip()
        purpose = purpose or (f'Corporate accommodation for assignment with {employer}' if employer else 'Corporate accommodation')
    elif tenancy_type == 'ota_short_stay':
        purpose = purpose or 'Short-stay accommodation'
    else:
        purpose = purpose or 'Residential accommodation'

    payload = {
        'agreement_template': agreement_preset_for_tenancy(tenancy_type),
        'agreement_type': _AGREEMENT_TYPES[tenancy_type],
        'agreement_reference': str(getattr(booking, 'public_id', '') or getattr(onboarding, 'public_id', '') or ''),
        'agreement_date': datetime.date.today().isoformat(),
        'place_of_execution': city,
        'start_date': getattr(getattr(booking, 'start_date', None), 'isoformat', lambda: '')(),
        'end_date': getattr(getattr(booking, 'end_date', None), 'isoformat', lambda: '')(),
        'landlord_entity': str(legal_entity_name or 'Livenza Life LLP').strip(),
        'landlord_address': str(legal_address or '').strip(),
        'tenant_name': str(profile.get('full_name') or getattr(customer, 'full_name', '') or '').strip(),
        'tenant_father': str(profile.get('father_name') or profile.get('guardian_name') or '').strip(),
        'tenant_dob': str(profile.get('date_of_birth') or '').strip(),
        'tenant_address': str(profile.get('permanent_address') or '').strip(),
        'tenant_mobile': str(getattr(customer, 'primary_mobile', '') or '').strip(),
        'tenant_whatsapp': str(getattr(customer, 'primary_mobile', '') or '').strip(),
        'tenant_email': str(getattr(customer, 'primary_email', '') or '').strip(),
        'property_name': property_name,
        'premises': premises,
        'room_unit_no': unit_name,
        'monthly_rent': _minor_to_rupees(getattr(rate_plan, 'amount_minor', 0)),
        'security_deposit': _minor_to_rupees(getattr(rate_plan, 'security_deposit_minor', 0)),
        'purpose': purpose,
    }
    if tenancy_type == 'corporate':
        payload.update({
            'corporate_name': str(profile.get('employer_name') or '').strip(),
            'corporate_gstin': str(profile.get('company_gst') or '').strip(),
            'authorized_signatory': str(profile.get('employer_contact_name') or '').strip(),
            'corporate_mobile': str(profile.get('employer_contact_mobile') or '').strip(),
            'corporate_address': str(profile.get('employer_address') or '').strip(),
        })
    return payload
