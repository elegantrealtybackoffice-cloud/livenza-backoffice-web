"""Pure referral helpers for Livenza+.

Referral rewards are deliberately gated to verified qualifying sources; clicks and
claims never award points on their own.
"""
from __future__ import annotations

import hashlib
import re


def normalize_referral_code(value: str) -> str:
    return re.sub(r'[^A-Z0-9]', '', str(value or '').upper())[:24]


def referral_code_for_seed(seed: str) -> str:
    digest = hashlib.sha256(str(seed or '').encode('utf-8')).hexdigest().upper()
    return f'LIV{digest[:7]}'


def referral_source_qualifies(source_type: str, payment_status: str) -> bool:
    return str(source_type or '').strip().lower() == 'booking' and str(payment_status or '').strip().lower() == 'paid'
