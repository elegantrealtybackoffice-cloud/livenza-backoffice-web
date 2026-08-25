import json
from urllib.parse import urlparse

REQUIRED_PROVIDER_KEYS={
    'name','state','city','official_website_url','official_payment_url','official_login_url','identifier_types','bbps_biller_id','supports_bbps_fetch','supports_bbps_payment','embedding_mode','workflow_mode'
}

def safe_official_url(value:str)->str:
    value=(value or '').strip()
    try:
        parsed=urlparse(value)
        return value if parsed.scheme in ('http','https') and parsed.hostname else ''
    except Exception: return ''

def load_seed_providers(path:str):
    with open(path,'r',encoding='utf-8') as f: rows=json.load(f)
    if not isinstance(rows,list): raise ValueError('Electricity provider seed must be a JSON list.')
    output=[]
    for row in rows:
        missing=REQUIRED_PROVIDER_KEYS-set(row)
        if missing: raise ValueError(f'Provider seed row is missing: {sorted(missing)}')
        row=dict(row)
        for key in ('official_website_url','official_payment_url','official_login_url'): row[key]=safe_official_url(row.get(key,''))
        if row.get('workflow_mode') not in {'bbps','portal','upload_only','hybrid'}: raise ValueError('Invalid workflow mode.')
        if row.get('embedding_mode') not in {'inline','external','none'}: raise ValueError('Invalid embedding mode.')
        output.append(row)
    return output

def seed_electricity_providers(db_session, provider_model, seed_rows):
    inserted=0
    for row in seed_rows:
        exists=provider_model.query.filter_by(name=row['name'],state=row['state'],city=row['city']).first()
        if exists: continue
        obj=provider_model(
            name=row['name'],state=row['state'],city=row['city'],official_website_url=row['official_website_url'],official_payment_url=row['official_payment_url'],official_login_url=row['official_login_url'],identifier_types_json=json.dumps(row['identifier_types']),bbps_biller_id=row['bbps_biller_id'],supports_bbps_fetch=bool(row['supports_bbps_fetch']),supports_bbps_payment=bool(row['supports_bbps_payment']),embedding_mode=row['embedding_mode'],workflow_mode=row['workflow_mode'],active=True
        )
        db_session.add(obj); inserted+=1
    if inserted: db_session.commit()
    return inserted
