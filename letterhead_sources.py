from dataclasses import dataclass

SENSITIVE_FIELDS = {
    'aadhaar','aadhar','pan','passport','passport_number','visa','visa_number','account_number',
    'bank_account','upi','upi_id','ifsc','cvv','pin','otp','password','secret','api_key',
}

@dataclass(frozen=True)
class SourceCandidate:
    kind: str
    record_id: str
    display_label: str
    facts: dict
    protected_document_ids: list[str]

def _candidate(kind, row):
    rid=str(row.get('id',''))
    label=str(row.get('display_label') or row.get('name') or f'{kind.title()} {rid}')
    facts=row.get('facts') if isinstance(row.get('facts'),dict) else {k:v for k,v in row.items() if k not in {'allowed','id','name','display_label','protected_document_ids'}}
    docs=row.get('protected_document_ids') if isinstance(row.get('protected_document_ids'),list) else []
    return SourceCandidate(kind=kind,record_id=rid,display_label=label,facts=facts,protected_document_ids=[str(x) for x in docs])

def resolve_sources(actor, query, loaders):
    found=[]
    for kind,loader in (loaders or {}).items():
        try: rows=loader(query or {}) or []
        except Exception: rows=[]
        for row in rows:
            if not isinstance(row,dict) or row.get('allowed') is not True: continue
            found.append(_candidate(str(kind),row))
    return found

def _masked(value):
    text=str(value or '')
    if len(text)<=4: return '*'*len(text)
    return ('X' * max(4,len(text)-4)) + text[-4:]

def minimize_for_ai(candidate, requested_fields):
    requested={str(x) for x in (requested_fields or set())}
    facts={}
    for key,value in (candidate.facts or {}).items():
        if key not in requested: continue
        if key.lower() in SENSITIVE_FIELDS:
            facts[key]=_masked(value)
        else:
            facts[key]=value
    return {'kind':candidate.kind,'record_id':candidate.record_id,'display_label':candidate.display_label,'facts':facts}

def can_access_protected_source(actor, source_kind, source_id, permission_checker):
    try: return bool(permission_checker(actor,str(source_kind),str(source_id)))
    except Exception: return False
