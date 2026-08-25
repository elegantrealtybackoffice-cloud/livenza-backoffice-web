import re

DOCUMENT_TRANSITIONS = {
    "draft": {"review_required"},
    "review_required": {"draft", "approved"},
    "approved": {"finalized"},
    "finalized": {"revised"},
    "revised": set(),
}
TEMPLATE_TRANSITIONS = {
    "draft": {"submitted"},
    "submitted": {"draft", "published"},
    "published": {"superseded", "archived"},
    "superseded": {"archived"},
    "archived": set(),
}
REQUIRED_CONTENT_KEYS = {"title", "date", "addressee", "subject", "body_sections", "property_or_entity"}
ALLOWED_BLOCK_TYPES = {"paragraph", "heading", "bullet_list", "numbered_list", "table", "page_break"}
ALLOWED_ALIGNMENTS = {"left", "center", "right", "justify"}
SENSITIVE_AUDIT_KEYWORDS = {
    "aadhaar", "aadhar", "pan", "passport", "visa", "account_number", "bank_account",
    "cvv", "pin", "otp", "password", "secret", "api_key",
}
FAMILY_CODES = {
    "residence_certificate": "RESCERT", "rent_confirmation": "RENT", "no_dues": "NODUES",
    "payment_confirmation": "PAYCONF", "admission_letter": "ADMISSION", "appointment_letter": "APPT",
    "experience_letter": "EXP", "salary_letter": "SAL", "vendor_letter": "VENDOR", "noc": "NOC",
    "authorization_letter": "AUTH", "property_communication": "PROP", "legal_notice": "NOTICE",
    "corporate_letter": "CORP", "custom": "CUSTOM",
}

def normalize_document_family(value):
    value = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    aliases = {"residence": "residence_certificate", "residence_certificate": "residence_certificate", "no_dues_certificate": "no_dues"}
    return aliases.get(value, value if value in FAMILY_CODES else "custom")

def _clean_token(value, fallback="GENERAL"):
    token = re.sub(r"[^A-Z0-9]+", "", str(value or "").upper())
    return token[:20] or fallback

def build_reference_prefix(property_or_entity, document_family, fiscal_year):
    family = normalize_document_family(document_family)
    return f"LIV/{_clean_token(property_or_entity)}/{FAMILY_CODES.get(family,'CUSTOM')}/{str(fiscal_year).strip()}"

def format_reference_number(prefix, sequence, revision_no=0):
    base = f"{str(prefix).rstrip('/')}/{int(sequence):04d}"
    return f"{base}-R{int(revision_no)}" if int(revision_no or 0) > 0 else base

def can_transition_document(current, target):
    return target in DOCUMENT_TRANSITIONS.get(str(current or ""), set())

def can_transition_template(current, target, is_admin=False):
    current, target = str(current or ""), str(target or "")
    if target not in TEMPLATE_TRANSITIONS.get(current, set()):
        return False
    if current == "submitted" and target == "published" and not is_admin:
        return False
    return True

def _normalize_runs(block):
    if "runs" not in block and isinstance(block.get("text"), str):
        block["runs"] = [{"text": block.get("text", ""), "bold": False, "italic": False, "underline": False}]
    runs = block.get("runs")
    if runs is not None and not isinstance(runs, list):
        raise ValueError("runs")
    return block

def validate_structured_content(content):
    if not isinstance(content, dict):
        return sorted(REQUIRED_CONTENT_KEYS)
    errors = []
    for key in REQUIRED_CONTENT_KEYS:
        val = content.get(key)
        if key == "body_sections":
            if not isinstance(val, list) or not val:
                errors.append(key)
        elif val is None or str(val).strip() == "":
            errors.append(key)
    blocks = content.get("body_sections") if isinstance(content.get("body_sections"), list) else []
    for i, raw in enumerate(blocks):
        if not isinstance(raw, dict) or raw.get("type") not in ALLOWED_BLOCK_TYPES:
            errors.append(f"body_sections[{i}].type"); continue
        if raw.get("align", "left") not in ALLOWED_ALIGNMENTS:
            errors.append(f"body_sections[{i}].align")
        if raw.get("type") in {"paragraph", "heading"}:
            try: _normalize_runs(raw)
            except ValueError: errors.append(f"body_sections[{i}].runs")
        if raw.get("type") in {"bullet_list", "numbered_list"} and not isinstance(raw.get("items"), list):
            errors.append(f"body_sections[{i}].items")
        if raw.get("type") == "table" and not isinstance(raw.get("rows"), list):
            errors.append(f"body_sections[{i}].rows")
    return sorted(set(errors))

def audit_safe_metadata(values):
    if not isinstance(values, dict):
        return {}
    out = {}
    for key, value in values.items():
        low = str(key).lower()
        out[key] = "[REDACTED]" if any(word in low for word in SENSITIVE_AUDIT_KEYWORDS) else value
    return out
