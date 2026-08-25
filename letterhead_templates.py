import json
from datetime import date

SCOPE_KEYS = ("roles", "properties", "entities", "document_families")

def next_template_version_no(existing_versions):
    vals=[]
    for value in existing_versions or []:
        try: vals.append(int(value))
        except Exception: pass
    return (max(vals) + 1) if vals else 1

def _scope(value):
    if isinstance(value, dict): data=value
    else:
        try: data=json.loads(value or '{}')
        except Exception: data={}
    if not isinstance(data, dict): data={}
    return {key: [str(v) for v in data.get(key, []) if str(v).strip()] if isinstance(data.get(key, []), list) else [] for key in SCOPE_KEYS}

def _admin(actor):
    return bool(getattr(actor, 'is_admin', False) or str(getattr(actor, 'role', '')).lower() == 'admin')

def _matches(scope, actor, context):
    context=context or {}
    role=str(getattr(actor,'role','') or context.get('role',''))
    dimensions={
        'roles': role,
        'properties': str(context.get('property','') or context.get('property_ref','')),
        'entities': str(context.get('entity','') or context.get('entity_ref','')),
        'document_families': str(context.get('document_family','')),
    }
    for key,value in dimensions.items():
        allowed=scope.get(key,[])
        if allowed and value not in allowed:
            return False
    return True

def template_is_usable(template_version, actor, context):
    if not template_version or getattr(template_version,'lifecycle_state','') != 'published':
        return False
    return _matches(_scope(getattr(template_version,'scope_json','{}')), actor, context)

def signature_is_usable(signature_asset, actor, context, on_date=None):
    if not signature_asset or not bool(getattr(signature_asset,'is_active',False)) or getattr(signature_asset,'revoked_at',None):
        return False
    on_date=on_date or date.today()
    effective=getattr(signature_asset,'effective_date',None); expires=getattr(signature_asset,'expires_at',None)
    if effective and on_date < effective: return False
    if expires and on_date > expires: return False
    return _matches(_scope(getattr(signature_asset,'scope_json','{}')), actor, context)

def starter_template_definitions():
    base_layout={
        'page_size':'A4','margins_mm':{'top':38,'right':18,'bottom':24,'left':18},
        'header':{'brand':'Livenza Life','show_logo':True},
        'footer':{'text':'Livenza Life LLP','page_numbers':True},
        'typography':{'body_font':'Helvetica','body_size':10.5,'heading_font':'Helvetica-Bold'},
        'watermark':'','signature_anchor':'bottom-right',
    }
    rows=[
        ('livenza-general','General Livenza Life LLP Letterhead','custom'),
        ('student-residence-certificate','Student Residence Certificate','residence_certificate'),
        ('corporate-stay','Corporate Stay Letterhead','corporate_letter'),
        ('property-communication','Property-specific Communication','property_communication'),
        ('hr-employment','HR / Employment correspondence','employment'),
        ('vendor-supplier','Vendor / Supplier correspondence','vendor_service'),
        ('formal-notice-noc','Formal Notice / NOC','formal_notice'),
        ('payment-no-dues','Payment / No-Dues confirmation','no_dues'),
    ]
    return [{'slug':slug,'name':name,'document_family':family,'layout':json.loads(json.dumps(base_layout))} for slug,name,family in rows]

def validate_template_asset(filename, mime_type, size_bytes):
    allowed={'image/png','image/jpeg','image/webp','image/svg+xml','application/pdf'}
    if mime_type not in allowed: raise ValueError('Unsupported template asset type.')
    if int(size_bytes or 0) <= 0 or int(size_bytes) > 8*1024*1024: raise ValueError('Template asset must be between 1 byte and 8 MB.')
    return True
