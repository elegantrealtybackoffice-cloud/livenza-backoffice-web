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


JVVNL_COVERAGE_CITIES=(
    'Jaipur','Dausa','Alwar','Dholpur','Bundi','Baran','Jhalawar',
    'Sawai Madhopur','Tonk','Karauli'
)

def electricity_city_choices(city_rows,providers):
    """Build a de-duplicated Electricity Studio city/coverage list.

    Real City rows keep their database id. Provider coverage and known JVVNL districts
    are selectable virtual names and are resolved to a City row when a connection is saved.
    """
    by_label={}
    for row in city_rows or []:
        label=str(getattr(row,'name','') or '').strip()
        if label:
            by_label.setdefault(label.lower(),{'label':label,'value':f'id:{getattr(row,"id","")}', 'source':'city'})
    for provider in providers or []:
        label=str(getattr(provider,'city','') or '').strip()
        if label and label.lower() not in by_label:
            by_label[label.lower()]={'label':label,'value':f'name:{label}','source':'provider'}
        name=str(getattr(provider,'name','') or '').upper()
        if 'JVVNL' in name or 'JAIPUR VIDYUT VITRAN' in name:
            for city in JVVNL_COVERAGE_CITIES:
                by_label.setdefault(city.lower(),{'label':city,'value':f'name:{city}','source':'jvvnl'})
    return sorted(by_label.values(),key=lambda item:item['label'].lower())
