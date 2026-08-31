import csv, io, json, re
from copy import copy
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from dateutil import parser as date_parser
import requests

PAYMENT_TRANSITIONS={
    ('initiated','provider_pending'):'pending',
    ('initiated','provider_confirmed'):'confirmed',
    ('initiated','provider_failed'):'failed',
    ('pending','provider_confirmed'):'confirmed',
    ('pending','provider_failed'):'failed',
    ('pending','manual_review'):'manual_confirmation_required',
    ('manual_confirmation_required','admin_confirmed'):'confirmed',
    ('manual_confirmation_required','admin_rejected'):'failed',
}

COMMON_ALIASES={
    'bill_number':['bill_number','billNumber','bill no','bill no.','bill number'],
    'bill_date':['bill_date','billDate','bill date'],
    'due_date':['due_date','dueDate','due date','payment due date'],
    'bill_month':['bill_month','billMonth','bill period','billing month','billing period'],
    'total_due_amount':['total_due_amount','amount','amount_due','amountDue','net payable','total amount','current amount','bill amount'],
    'current_charges':['current_charges','currentCharges','current charges'],
    'arrears_amount':['arrears_amount','arrears','outstanding arrears'],
    'late_fee_amount':['late_fee_amount','late fee','lpsc','surcharge','late payment surcharge'],
    'units_consumed':['units_consumed','units','consumption','units consumed'],
    'meter_number':['meter_number','meterNo','meter no','meter number'],
    'previous_reading':['previous_reading','previous reading','prev reading'],
    'current_reading':['current_reading','current reading'],
    'consumer_name':['consumer_name','consumerName','consumer name','name'],
    'identifier_primary':['identifier_primary','k no','k number','consumer no','consumer number','ca no','account no','account number'],
}

def _pick(payload,aliases):
    lowered={str(k).strip().lower():v for k,v in (payload or {}).items()}
    for alias in aliases:
        if alias in payload: return payload.get(alias)
        key=str(alias).strip().lower()
        if key in lowered: return lowered[key]
    return ''

def _money(value):
    if value in (None,''): return '0.00'
    raw=re.sub(r'[^0-9.\-]','',str(value).replace(',',''))
    try: return f'{Decimal(raw):.2f}'
    except (InvalidOperation,ValueError): return '0.00'

def _number(value):
    if value in (None,''): return ''
    raw=re.sub(r'[^0-9.\-]','',str(value).replace(',',''))
    try:
        d=Decimal(raw); return format(d.normalize(),'f')
    except Exception: return ''

def _date(value):
    if not value: return ''
    if isinstance(value,date): return value.isoformat()
    try: return date_parser.parse(str(value),dayfirst=True,fuzzy=True).date().isoformat()
    except Exception: return ''

def normalize_bill_payload(payload:dict)->dict:
    payload=payload or {}
    out={}
    for field,aliases in COMMON_ALIASES.items(): out[field]=_pick(payload,aliases)
    for field in ('total_due_amount','current_charges','arrears_amount','late_fee_amount'): out[field]=_money(out[field])
    for field in ('units_consumed','previous_reading','current_reading'): out[field]=_number(out[field])
    for field in ('bill_date','due_date'): out[field]=_date(out[field])
    for field in ('bill_number','bill_month','meter_number','consumer_name','identifier_primary'): out[field]=str(out[field] or '').strip()
    return out

def bill_dedupe_key(provider_id:int, connection_id:int, bill_number:str, bill_month:str)->str:
    bill_number=(bill_number or '').strip(); bill_month=(bill_month or '').strip()
    return f'{provider_id}:{connection_id}:bill:{bill_number}' if bill_number else f'{provider_id}:{connection_id}:month:{bill_month or "unknown"}'

def reminder_status(due_date,paid:bool,pending:bool,today=None,days_before=5):
    today=today or date.today()
    if paid: return 'paid','success'
    if pending: return 'payment_pending_confirmation','warning'
    if not due_date: return 'unpaid','info'
    if isinstance(due_date,str):
        try: due_date=date_parser.parse(due_date).date()
        except Exception: return 'unpaid','info'
    delta=(due_date-today).days
    if delta<0: return 'overdue','danger'
    if delta==0: return 'due_today','danger'
    if delta<=max(0,int(days_before or 0)): return 'due_soon','warning'
    return 'unpaid','info'

def transition_payment_status(current:str,event:str)->str:
    key=((current or '').strip(),(event or '').strip())
    if key not in PAYMENT_TRANSITIONS: raise ValueError(f'Invalid payment transition: {key[0]} + {key[1]}')
    return PAYMENT_TRANSITIONS[key]

def build_electricity_csv(rows):
    rows=list(rows or []); headers=list(rows[0].keys()) if rows else ['City','Property','Provider','Total Due','Status']
    buf=io.StringIO(); writer=csv.DictWriter(buf,fieldnames=headers,extrasaction='ignore'); writer.writeheader(); writer.writerows(rows)
    return ('\ufeff'+buf.getvalue()).encode('utf-8')

def build_electricity_xlsx(rows):
    from openpyxl import Workbook
    rows=list(rows or []); headers=list(rows[0].keys()) if rows else ['City','Property','Provider','Total Due','Status']
    wb=Workbook(); ws=wb.active; ws.title='Electricity Bill Register'; ws.append(headers)
    for row in rows: ws.append([row.get(h,'') for h in headers])
    for cell in ws[1]:
        font=copy(cell.font); font.bold=True; cell.font=font
    ws.freeze_panes='A2'; ws.auto_filter.ref=ws.dimensions
    buf=io.BytesIO(); wb.save(buf); return buf.getvalue()


def _nested_bill_payload(data):
    """Find a likely bill-details object in a JSON response without logging secrets."""
    if not isinstance(data,dict):
        return {}
    priority=('bill','billDetails','bill_details','billdetail','data','payload','response','result')
    for key in priority:
        value=data.get(key)
        if isinstance(value,dict):
            nested=_nested_bill_payload(value)
            if nested:
                return nested
    billish={'amount','amountDue','amount_due','total_due_amount','dueDate','due_date','billNumber','bill_number','consumerName','consumer_name','meterNo','meter_number'}
    if billish.intersection(data.keys()):
        return data
    for value in data.values():
        if isinstance(value,dict):
            nested=_nested_bill_payload(value)
            if nested:
                return nested
    return {}

def fetch_bill_from_billdesk(connection,provider,config,http=requests):
    """Fetch a current utility bill through an authorised BillDesk/Bharat Connect merchant API.

    The exact production URL/header names are supplied by BillDesk onboarding and therefore
    remain configuration-driven. The public Instapay web form is intentionally not scraped.
    """
    def get(obj,key,default=''):
        return obj.get(key,default) if isinstance(obj,dict) else getattr(obj,key,default)
    cfg=config or {}
    fetch_url=str(cfg.get('fetch_url') or '').strip()
    client_id=str(cfg.get('client_id') or '').strip()
    client_secret=str(cfg.get('client_secret') or '').strip()
    api_key=str(cfg.get('api_key') or '').strip()
    merchant_id=str(cfg.get('merchant_id') or '').strip()
    biller_id=str(cfg.get('biller_id') or get(provider,'bbps_biller_id','') or '').strip()
    if not fetch_url or not client_id or not client_secret:
        return {'ok':False,'status':'integration_not_configured','bill':{},'message':'BillDesk API is not connected. Add the BillDesk merchant bill-fetch endpoint and credentials in Render/Livenza Vault.','raw_meta':{'integration':'billdesk'}}
    if not fetch_url.lower().startswith('https://'):
        return {'ok':False,'status':'integration_not_configured','bill':{},'message':'BillDesk bill-fetch endpoint must use HTTPS.','raw_meta':{'integration':'billdesk'}}
    identifier=str(get(connection,'identifier_primary','') or '').strip()
    if not identifier:
        return {'ok':False,'status':'invalid_identifier','bill':{},'message':'A saved K Number / consumer identifier is required before fetching the bill.','raw_meta':{'integration':'billdesk'}}
    payload={
        'biller_id':biller_id,
        'consumer_identifier':identifier,
        'identifier_type':str(get(connection,'identifier_primary_type','K_NO') or 'K_NO'),
        'secondary_identifier':str(get(connection,'identifier_secondary','') or ''),
    }
    if merchant_id:
        payload['merchant_id']=merchant_id
    headers={'Content-Type':'application/json','Accept':'application/json'}
    client_id_header=str(cfg.get('client_id_header') or 'X-Client-Id').strip() or 'X-Client-Id'
    headers[client_id_header]=client_id
    auth_header=str(cfg.get('auth_header') or 'Authorization').strip() or 'Authorization'
    auth_prefix=str(cfg.get('auth_prefix') if cfg.get('auth_prefix') is not None else 'Bearer').strip()
    headers[auth_header]=(f'{auth_prefix} {client_secret}'.strip() if auth_prefix else client_secret)
    if api_key:
        api_key_header=str(cfg.get('api_key_header') or 'X-API-Key').strip() or 'X-API-Key'
        headers[api_key_header]=api_key
    try:
        response=http.post(fetch_url,json=payload,headers=headers,timeout=int(cfg.get('timeout') or 30))
        if not getattr(response,'ok',False):
            return {'ok':False,'status':'failed','bill':{},'message':f'BillDesk bill fetch returned HTTP {getattr(response,"status_code",0)}.','raw_meta':{'integration':'billdesk','http_status':getattr(response,'status_code',0)}}
        data=response.json() if hasattr(response,'json') else {}
        source=_nested_bill_payload(data)
        if not source:
            return {'ok':False,'status':'invalid_response','bill':{},'message':'BillDesk returned a response but no bill details were found.','raw_meta':{'integration':'billdesk','http_status':getattr(response,'status_code',200)}}
        bill=normalize_bill_payload(source)
        if not bill.get('identifier_primary'):
            bill['identifier_primary']=identifier
        return {'ok':True,'status':'successful','bill':bill,'message':'Current bill fetched automatically through BillDesk / Bharat Connect.','raw_meta':{'integration':'billdesk','http_status':getattr(response,'status_code',200)}}
    except Exception as exc:
        return {'ok':False,'status':'failed','bill':{},'message':f'BillDesk bill fetch failed: {str(exc)[:140]}','raw_meta':{'integration':'billdesk'}}

def fetch_bill_from_provider(connection,provider,config,http=requests):
    def get(obj,key,default=''):
        return obj.get(key,default) if isinstance(obj,dict) else getattr(obj,key,default)
    if not get(provider,'supports_bbps_fetch',False):
        return {'ok':False,'status':'unsupported','bill':{},'message':'Automated bill fetch is not enabled for this provider.','raw_meta':{}}
    base=(config or {}).get('base_url','').strip(); client_id=(config or {}).get('client_id','').strip(); secret=(config or {}).get('client_secret','').strip()
    if not (base and client_id and secret):
        return {'ok':False,'status':'manual_action_required','bill':{},'message':'Authorized Bharat Connect / BBPS provider configuration is not complete.','raw_meta':{}}
    if not base.lower().startswith(('https://','http://')):
        return {'ok':False,'status':'manual_action_required','bill':{},'message':'The configured bill-fetch provider URL is invalid.','raw_meta':{}}
    payload={
        'biller_id':get(provider,'bbps_biller_id',''),
        'consumer_identifier':get(connection,'identifier_primary',''),
        'identifier_type':get(connection,'identifier_primary_type','CONSUMER_NO'),
        'secondary_identifier':get(connection,'identifier_secondary',''),
    }
    headers={'X-Client-Id':client_id,'Authorization':f'Bearer {secret}','Content-Type':'application/json'}
    fetch_path=str((config or {}).get('fetch_path') or '/bill-fetch').strip() or '/bill-fetch'
    if not fetch_path.startswith('/'): fetch_path='/'+fetch_path
    try:
        response=http.post(base.rstrip('/')+fetch_path,json=payload,headers=headers,timeout=30)
        if not getattr(response,'ok',False):
            return {'ok':False,'status':'failed','bill':{},'message':f'Bill fetch provider returned HTTP {getattr(response,"status_code",0)}.','raw_meta':{}}
        data=response.json() if hasattr(response,'json') else {}
        source=data.get('bill') if isinstance(data,dict) and isinstance(data.get('bill'),dict) else data
        bill=normalize_bill_payload(source if isinstance(source,dict) else {})
        return {'ok':True,'status':'successful','bill':bill,'message':'Current bill fetched successfully.','raw_meta':{'provider_response_status':getattr(response,'status_code',200)}}
    except Exception as exc:
        return {'ok':False,'status':'failed','bill':{},'message':f'Bill fetch failed: {str(exc)[:160]}','raw_meta':{}}
