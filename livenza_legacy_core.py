"""Deterministic legacy-to-Livenza mapping rules."""
from __future__ import annotations


def _unique_ids(values):
    return sorted({int(v) for v in (values or []) if v is not None})


def resolve_customer_action(mapped_customer_id=None, mobile_matches=None, email_matches=None, display_name_matches=None):
    """Decide link/create/conflict. Display names are intentionally ignored as identity evidence."""
    if mapped_customer_id is not None:
        return {'action':'link','customer_id':int(mapped_customer_id),'reason':'existing_mapping'}
    mobile=_unique_ids(mobile_matches); email=_unique_ids(email_matches)
    candidates=sorted(set(mobile+email))
    if len(candidates)>1:
        return {'action':'conflict','customer_ids':candidates,'reason':'identity_conflict'}
    if len(candidates)==1:
        return {'action':'link','customer_id':candidates[0],'reason':'verified_identity'}
    return {'action':'create','reason':'no_verified_identity_match'}


def room_source_key(property_name, room_no):
    prop=' '.join(str(property_name or '').strip().lower().split())
    room=' '.join(str(room_no or '').strip().lower().split())
    if not prop or not room:
        raise ValueError('Property name and room number are required.')
    return f'{prop}|{room}'
