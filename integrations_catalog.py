"""Built-in third-party provider metadata and legacy v1.7.x compatibility descriptors."""
from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import urlparse

REQUIRED_FIELDS=('provider_key','display_name','category')
LEGACY_SOURCES={
    'openai': {'env_any':['OPENAI_API_KEY']},
    'whatsapp_cloud': {'env_all':['WHATSAPP_CLOUD_TOKEN','WHATSAPP_PHONE_NUMBER_ID']},
    'google_email': {'encrypted_setting':'google_oauth_token','env_all':['GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET']},
    'google_drive': {'encrypted_setting':'google_oauth_token','env_all':['GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET']},
    'bbps_electricity': {'env_any':['BBPS_PROVIDER_BASE_URL','BBPS_PROVIDER_CLIENT_ID','BBPS_PROVIDER_CLIENT_SECRET']},
    'payment_provider': {'env_any':['ELECTRICITY_PAYMENT_PROVIDER','ELECTRICITY_PAYMENT_PROVIDER_URL']},
    'webhooks': {'setting_any':['food_webhook_token','query_webhook_token'],'env_any':['META_VERIFY_TOKEN','GOOGLE_LEAD_WEBHOOK_SECRET']},
}

def _safe_url(value):
    value=str(value or '').strip()
    if not value: return ''
    p=urlparse(value)
    if p.scheme not in ('http','https') or not p.netloc: raise ValueError('Provider URL must use http:// or https://.')
    return value

def load_integration_catalog(path):
    rows=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(rows,list): raise ValueError('Integration catalog must be a JSON array.')
    seen=set(); out=[]
    for raw in rows:
        if not isinstance(raw,dict): raise ValueError('Each provider must be an object.')
        row=dict(raw)
        for field in REQUIRED_FIELDS:
            row[field]=str(row.get(field) or '').strip()
            if not row[field]: raise ValueError(f'Missing {field}.')
        key=row['provider_key'].lower()
        if key in seen: raise ValueError(f'Duplicate provider key: {key}')
        seen.add(key); row['provider_key']=key
        row['category']=row['category'].lower()
        row['workflow_module']=str(row.get('workflow_module') or 'integrations').strip()
        row['portal_url']=_safe_url(row.get('portal_url'))
        row['developer_url']=_safe_url(row.get('developer_url'))
        row['embed_mode']='inline' if str(row.get('embed_mode')).lower()=='inline' else 'external'
        caps=row.get('capabilities') or []
        row['capabilities']=[str(x).strip() for x in caps if str(x).strip()]
        out.append(row)
    return out

def seed_integration_providers(session, ProviderModel, rows):
    created=updated=0
    for row in rows:
        obj=ProviderModel.query.filter_by(provider_key=row['provider_key']).first()
        if not obj:
            obj=ProviderModel(provider_key=row['provider_key']); session.add(obj); created+=1
        else: updated+=1
        obj.display_name=row['display_name']; obj.category=row['category']; obj.workflow_module=row.get('workflow_module') or 'integrations'
        obj.portal_url=row.get('portal_url') or ''; obj.developer_url=row.get('developer_url') or ''; obj.embed_mode=row.get('embed_mode') or 'external'
        obj.capabilities_json=json.dumps(row.get('capabilities') or [],separators=(',',':')); obj.active=True
    session.commit()
    return {'created':created,'updated':updated}

def legacy_connection_status(provider_key, env=None, settings=None, db_state=None):
    env=env or {}; settings=settings or {}; db_state=db_state or {}; spec=LEGACY_SOURCES.get(provider_key,{})
    checks=[]
    if spec.get('env_any'):
        checks.append(any(bool(str(env.get(k) or '').strip()) for k in spec['env_any']))
    if spec.get('env_all'):
        checks.append(all(bool(str(env.get(k) or '').strip()) for k in spec['env_all']))
    if spec.get('setting_any'):
        checks.append(any(bool(str(settings.get(k) or '').strip()) for k in spec['setting_any']))
    if spec.get('encrypted_setting'):
        checks.append(bool(str(settings.get(spec['encrypted_setting']) or '').strip()))
    if provider_key in ('swiggy','zomato'):
        checks.append(bool(db_state.get('food_integrations')))
    configured=any(checks) if checks else bool(db_state.get(provider_key))
    return {'provider_key':provider_key,'configured':configured,'source':'legacy' if configured else 'none'}

def provider_workflow_url(provider, connection=None):
    def get(obj,key,default=''):
        if isinstance(obj,dict): return obj.get(key,default)
        return getattr(obj,key,default)
    config=get(connection or {},'nonsecret_config',{}) or {}
    if not config and connection is not None:
        raw=get(connection,'nonsecret_config_json','')
        try: config=json.loads(raw or '{}') if raw else {}
        except Exception: config={}
    candidate=(config.get('portal_url') if isinstance(config,dict) else '') or get(provider,'portal_url','')
    return _safe_url(candidate) if candidate else ''
