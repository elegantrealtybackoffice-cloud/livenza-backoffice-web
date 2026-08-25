import copy
from letterhead_core import validate_structured_content, normalize_document_family

CLASSIFIER_TERMS = {
    'residence_certificate': ('residence certificate','residing certificate','proof of residence','residence proof'),
    'rent_confirmation': ('rent confirmation','rent letter'),
    'no_dues': ('no dues','no-dues'),
    'payment_confirmation': ('payment confirmation','receipt confirmation'),
    'accommodation_letter': ('accommodation letter','admission letter'),
    'appointment_letter': ('appointment letter',),
    'experience_letter': ('experience letter',),
    'salary_letter': ('salary letter',),
    'vendor_service': ('vendor letter','service letter'),
    'noc': ('noc','no objection certificate'),
    'authorization_letter': ('authorization letter','authority letter'),
    'formal_notice': ('legal notice','formal notice'),
    'corporate_letter': ('corporate letter',),
}
REWRITE_ACTIONS={'make_formal','shorten','improve_legal_tone','translate_hindi','rewrite_parent','rewrite_corporate'}
COMMON_REQUIRED={'date','property_or_entity'}
FAMILY_REQUIRED={
    'residence_certificate': {'full_name','date','property_or_entity'},
    'rent_confirmation': {'full_name','date','property_or_entity'},
    'no_dues': {'full_name','date','property_or_entity'},
    'payment_confirmation': {'full_name','date','property_or_entity'},
    'accommodation_letter': {'full_name','date','property_or_entity'},
    'appointment_letter': {'full_name','date','property_or_entity'},
    'experience_letter': {'full_name','date','property_or_entity'},
    'salary_letter': {'full_name','date','property_or_entity'},
    'vendor_service': {'full_name','date','property_or_entity'},
    'noc': {'full_name','date','property_or_entity'},
    'authorization_letter': {'full_name','date','property_or_entity'},
    'formal_notice': {'full_name','date','property_or_entity'},
    'corporate_letter': {'date','property_or_entity'},
    'custom': {'date','property_or_entity'},
}

def classify_request(text):
    low=' '.join(str(text or '').lower().split())
    for family,terms in CLASSIFIER_TERMS.items():
        if any(term in low for term in terms): return family
    return 'custom'

def required_fields_for_family(family):
    return set(FAMILY_REQUIRED.get(normalize_document_family(family), COMMON_REQUIRED))

def missing_required_fields(family,facts):
    facts=facts or {}
    return sorted(k for k in required_fields_for_family(family) if facts.get(k) in (None,'',[]))

def build_ai_draft_request(request_text,family,minimized_sources,allowed_attachment_ids=None,extra_facts=None):
    return {
        'request_text':str(request_text or '')[:6000],
        'document_family':normalize_document_family(family),
        'sources':list(minimized_sources or []),
        'allowed_source_ids':[f"{x.get('kind')}:{x.get('record_id')}" for x in (minimized_sources or [])],
        'allowed_attachment_ids':sorted(set(str(x) for x in (allowed_attachment_ids or set()))),
        'user_facts':dict(extra_facts or {}),
        'response_contract':{
            'keys':['document_family','title','date','addressee','subject','body_sections','property_or_entity','signatory_requirements','source_record_ids','suggested_attachment_ids','source_summary']
        },
    }

def parse_structured_draft(payload,allowed_source_ids,allowed_attachment_ids=None):
    if not isinstance(payload,dict): raise ValueError('AI draft must be an object.')
    out=copy.deepcopy(payload)
    source_ids=[str(x) for x in out.get('source_record_ids',[]) if str(x)]
    unknown=set(source_ids)-set(str(x) for x in (allowed_source_ids or set()))
    if unknown: raise ValueError('Draft contains an unauthorized source reference.')
    attachment_ids=[str(x) for x in out.get('suggested_attachment_ids',[]) if str(x)]
    allowed_attachments=set(str(x) for x in (allowed_attachment_ids or set()))
    if set(attachment_ids)-allowed_attachments: raise ValueError('Draft contains an unauthorized attachment reference.')
    errors=validate_structured_content(out)
    if errors: raise ValueError('Draft is missing or has invalid fields: '+', '.join(errors))
    out['document_family']=normalize_document_family(out.get('document_family'))
    out['source_record_ids']=source_ids
    out['suggested_attachment_ids']=attachment_ids
    out['source_summary']=[str(x)[:500] for x in out.get('source_summary',[]) if str(x).strip()][:20]
    out.pop('template_version_id',None); out.pop('signature_asset_id',None)
    return out

def rewrite_action(content,action,ai_client):
    if action not in REWRITE_ACTIONS: raise ValueError('Unknown rewrite action.')
    original=copy.deepcopy(content or {})
    blocks=original.get('body_sections') or []
    rewritten=ai_client.rewrite_blocks(copy.deepcopy(blocks),action)
    if not isinstance(rewritten,list): raise ValueError('Rewrite did not return body sections.')
    original['body_sections']=rewritten
    return original

def deterministic_draft(family,facts,request_text=''):
    family=normalize_document_family(family); full_name=facts.get('full_name') or facts.get('name') or 'the concerned person'
    property_or_entity=facts.get('property_or_entity') or facts.get('property_name') or 'Livenza Life'
    date=facts.get('date') or ''
    titles={
        'residence_certificate':'Residence Certificate','no_dues':'No Dues Certificate','rent_confirmation':'Rent Confirmation',
        'payment_confirmation':'Payment Confirmation','experience_letter':'Experience Letter','appointment_letter':'Appointment Letter',
        'salary_letter':'Salary Letter','noc':'No Objection Certificate','authorization_letter':'Authorization Letter',
        'formal_notice':'Formal Notice','accommodation_letter':'Accommodation Letter','corporate_letter':'Corporate Letter','custom':'Official Letter',
    }
    title=titles.get(family,'Official Letter')
    body=f"This is to confirm that {full_name} is associated with {property_or_entity}."
    if facts.get('room_no'): body+=f" The relevant room/unit is {facts['room_no']}."
    return {'document_family':family,'title':title,'date':date,'addressee':'To Whom It May Concern','subject':title,'body_sections':[{'type':'paragraph','text':body}], 'property_or_entity':property_or_entity,'signatory_requirements':{'role':'Authorized Signatory'},'source_record_ids':facts.get('source_record_ids',[]),'suggested_attachment_ids':[],'source_summary':facts.get('source_summary',[])}
