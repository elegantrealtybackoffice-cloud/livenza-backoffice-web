import hashlib
import hmac
import mimetypes
from pathlib import Path

LANDLORD_CORE_FIELDS=(
    'profile_name','party_type','full_legal_name','entity_legal_name','primary_mobile','email','city','state','country','verification_status','tags'
)
TENANT_CORE_FIELDS=(
    'profile_name','party_type','full_legal_name','corporate_legal_name','primary_mobile','email','city','state','country','verification_status','tags'
)

LANDLORD_AGREEMENT_MAP={
    'full_legal_name':'landlord_name','father_spouse_name':'landlord_father','entity_legal_name':'landlord_entity',
    'primary_address':'landlord_address','primary_id_type':'landlord_id_type','primary_id_number':'landlord_id_no',
    'pan':'landlord_pan','primary_mobile':'landlord_mobile','email':'landlord_email','authorized_signatory':'authorized_signatory',
}
TENANT_AGREEMENT_MAP={
    'full_legal_name':'tenant_name','father_spouse_name':'tenant_father','dob':'tenant_dob','permanent_address':'tenant_address',
    'primary_id_type':'tenant_id_type','primary_id_number':'tenant_id_no','primary_mobile':'tenant_mobile','whatsapp':'tenant_whatsapp',
    'email':'tenant_email','emergency_contact1':'emergency_contact1','emergency_contact2':'emergency_contact2',
    'corporate_legal_name':'corporate_name','billing_address':'corporate_address','gstin':'corporate_gstin','corporate_pan':'corporate_pan',
    'authorized_representative':'corporate_representative','authorized_representative_designation':'corporate_designation',
}

MASTER_FIELD_SET={
    'landlord':(
        'profile_name','party_type','full_legal_name','entity_legal_name','father_spouse_name',
        'dob_or_incorporation_date','nationality','primary_mobile','alternate_mobile','whatsapp',
        'email','alternate_email','primary_address','permanent_address','registered_office',
        'correspondence_address','billing_address','city','state','country','pin_code',
        'primary_id_type','primary_id_number','aadhaar','pan','passport_number','passport_country',
        'passport_issue_date','passport_expiry_date','driving_licence','voter_or_other_id','gstin',
        'cin_llpin_registration','tan','authorized_signatory','authorized_signatory_designation',
        'authority_reference','authority_expiry_date','bank_beneficiary_name','bank_name','bank_branch',
        'bank_account','bank_account_type','ifsc','upi_id','preferred_payment_mode',
        'verification_status','last_verified_date','tags','notes'
    ),
    'tenant':(
        'profile_name','party_type','full_legal_name','corporate_legal_name','father_spouse_name',
        'mother_name','guardian_name','dob','gender','nationality','occupation_or_course','job_title',
        'employer_college_company','employee_student_id','primary_mobile','alternate_mobile','whatsapp',
        'email','alternate_email','emergency_contact1','emergency_contact1_relationship',
        'emergency_contact2','emergency_contact2_relationship','permanent_address','current_address',
        'work_address','billing_address','city','state','country','pin_code','primary_id_type',
        'primary_id_number','aadhaar','pan','passport_number','passport_country','passport_issue_date',
        'passport_expiry_date','driving_licence','other_government_id','visa_number','visa_type',
        'visa_issue_date','visa_expiry_date','frro_reference','frro_status','c_form_reference',
        'foreign_compliance_notes','gstin','corporate_pan','cin_llpin','authorized_representative',
        'authorized_representative_designation','bank_beneficiary_name','bank_name','bank_account','ifsc',
        'upi_id','preferred_refund_payment_mode','verification_status','last_verified_date','tags','notes'
    ),
}

SENSITIVE_FIELDS={
    'landlord':{'primary_id_number','aadhaar','pan','passport_number','driving_licence','voter_or_other_id','gstin','cin_llpin_registration','tan','bank_account','ifsc','upi_id'},
    'tenant':{'primary_id_number','aadhaar','pan','passport_number','driving_licence','other_government_id','visa_number','frro_reference','c_form_reference','gstin','corporate_pan','cin_llpin','bank_account','ifsc','upi_id'},
}

DOCUMENT_CATEGORIES={
    'profile_photo':'Profile photo','signature_seal':'Signature / seal','aadhaar_front':'Aadhaar front',
    'aadhaar_back':'Aadhaar back','pan':'PAN','passport':'Passport','driving_licence':'Driving licence',
    'other_government_id':'Other government ID','gst_certificate':'GST certificate',
    'incorporation_entity_document':'Incorporation / LLP / partnership / trust document',
    'cancelled_cheque_bank_proof':'Cancelled cheque / bank proof',
    'ownership_authority_proof':'Ownership / title / authority proof',
    'authorization_board_resolution':'Authorization letter / board resolution',
    'visa_frro_foreign_compliance':'Visa / FRRO / foreign-national compliance',
    'student_employee_id':'Student / employee ID','admission_employment_proof':'Admission / employment proof',
    'miscellaneous':'Miscellaneous supporting document',
}

PROHIBITED_AUTH_KEYS=('bank_password','upi_pin','card_pin','cvv','otp','captcha','session_cookie','browser_cookie')
_ALLOWED_EXTENSIONS={'.pdf','jpg','.jpg','.jpeg','.png','.webp','.heic','.heif','.tif','.tiff'}
_MIME_BY_EXT={
    '.pdf':'application/pdf','.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp',
    '.heic':'image/heic','.heif':'image/heif','.tif':'image/tiff','.tiff':'image/tiff'
}
_NORMALIZED_ID_FIELDS={'primary_id_number','aadhaar','pan','passport_number','driving_licence','voter_or_other_id','other_government_id','visa_number','frro_reference','c_form_reference','gstin','corporate_pan','cin_llpin','cin_llpin_registration','tan','bank_account','ifsc'}


def _kind(kind):
    value=str(kind or '').strip().lower()
    if value not in MASTER_FIELD_SET:
        raise ValueError('Master kind must be landlord or tenant.')
    return value


def _clean_identifier(value):
    return ''.join(ch for ch in str(value or '').upper() if ch.isalnum())


def normalize_master_payload(kind:str,supplied:dict)->dict:
    kind=_kind(kind)
    supplied=supplied or {}
    for key in supplied:
        normalized=str(key or '').strip().lower()
        if any(blocked in normalized for blocked in PROHIBITED_AUTH_KEYS):
            raise ValueError('Authentication secrets are not permitted in Landlord/Tenant Master.')
    allowed=set(MASTER_FIELD_SET[kind])
    result={}
    for key in MASTER_FIELD_SET[kind]:
        value=supplied.get(key,'')
        if isinstance(value,(list,tuple,set)):
            value=', '.join(str(x).strip() for x in value if str(x).strip())
        value=str(value or '').strip()
        if key in _NORMALIZED_ID_FIELDS:
            value=_clean_identifier(value)
        result[key]=value
    if not result.get('party_type'):
        result['party_type']='individual'
    if not result.get('country'):
        result['country']='India'
    if not result.get('verification_status'):
        result['verification_status']='unverified'
    searchable=[]
    for key in MASTER_FIELD_SET[kind]:
        if key in SENSITIVE_FIELDS[kind] or key in {'notes'}:
            continue
        value=result.get(key,'')
        if value:
            searchable.append(value)
    result['search_text']=' '.join(searchable).strip()
    return result


def mask_identifier(value:str)->str:
    value=str(value or '')
    if not value:
        return ''
    visible=value[-4:]
    return '•'*max(4,len(value)-len(visible))+visible


def master_display_payload(kind:str,payload:dict)->dict:
    kind=_kind(kind)
    shown=dict(payload or {})
    for field in SENSITIVE_FIELDS[kind]:
        value=str(shown.get(field) or '')
        if not value: continue
        if field in {'pan','corporate_pan'}:
            shown[field]='••••••'+value[-5:]
        else:
            shown[field]=mask_identifier(value)
    return shown


def safe_master_summary(kind:str,row,payload:dict|None=None)->dict:
    kind=_kind(kind)
    get=lambda name,default='': getattr(row,name,default) if row is not None else default
    return {
        'id':get('id',None),'master_code':get('master_code',''),'profile_name':get('profile_name',''),
        'party_type':get('party_type',''),'legal_name':get('legal_name',''),'primary_mobile':get('primary_mobile',''),
        'email':get('email',''),'city':get('city',''),'state':get('state',''),'country':get('country','India'),
        'verification_status':get('verification_status','unverified'),'tags':get('tags',''),'active':bool(get('active',True)),
    }


def identifier_lookup_hash(value:str,master_key:str)->str:
    clean=_clean_identifier(value)
    if not clean:
        return ''
    key=hashlib.sha256((str(master_key or '')+'|livenza-master-lookup-v1').encode('utf-8')).digest()
    return hmac.new(key,clean.encode('utf-8'),hashlib.sha256).hexdigest()


def identifier_lookup_hashes(kind:str,payload:dict,master_key:str)->list[str]:
    kind=_kind(kind)
    values=[]
    for field in sorted(SENSITIVE_FIELDS[kind]):
        value=(payload or {}).get(field,'')
        hashed=identifier_lookup_hash(value,master_key)
        if hashed and hashed not in values:
            values.append(hashed)
    return values


def validate_master_document(filename:str,mime_type:str,size:int)->tuple[str,str]:
    if int(size or 0)>20*1024*1024:
        raise ValueError('Master documents must be 20 MB or smaller.')
    ext=Path(str(filename or '')).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise ValueError('Unsupported master document type.')
    normalized=_MIME_BY_EXT.get(ext) or mimetypes.types_map.get(ext) or 'application/octet-stream'
    supplied=(mime_type or '').lower().strip()
    if supplied and supplied not in {normalized,'application/octet-stream'} and not (normalized.startswith('image/') and supplied.startswith('image/')):
        raise ValueError('Document MIME type does not match its file extension.')
    return ext,normalized



def parse_annexure_ids(value)->list[int]:
    """Return unique positive document ids in the order supplied."""
    if isinstance(value,(list,tuple,set)):
        parts=value
    else:
        parts=str(value or '').split(',')
    result=[]
    seen=set()
    for part in parts:
        try:
            number=int(str(part).strip())
        except (TypeError,ValueError):
            continue
        if number<=0 or number in seen:
            continue
        seen.add(number);result.append(number)
    return result

def legacy_profile_to_master(kind:str,name:str,fields:dict)->dict:
    kind=_kind(kind); fields=fields or {}
    if kind=='landlord':
        supplied={
            'profile_name':name,'full_legal_name':fields.get('landlord_name',''),'father_spouse_name':fields.get('landlord_father',''),
            'entity_legal_name':fields.get('landlord_entity',''),'primary_address':fields.get('landlord_address',''),
            'primary_id_type':fields.get('landlord_id_type',''),'primary_id_number':fields.get('landlord_id_no',''),
            'pan':fields.get('landlord_pan',''),'primary_mobile':fields.get('landlord_mobile',''),'email':fields.get('landlord_email',''),
            'authorized_signatory':fields.get('authorized_signatory',''),
        }
    else:
        supplied={
            'profile_name':name,'full_legal_name':fields.get('tenant_name',''),'father_spouse_name':fields.get('tenant_father',''),
            'dob':fields.get('tenant_dob',''),'permanent_address':fields.get('tenant_address',''),
            'primary_id_type':fields.get('tenant_id_type',''),'primary_id_number':fields.get('tenant_id_no',''),
            'primary_mobile':fields.get('tenant_mobile',''),'whatsapp':fields.get('tenant_whatsapp',''),'email':fields.get('tenant_email',''),
            'emergency_contact1':fields.get('emergency_contact1',''),'emergency_contact2':fields.get('emergency_contact2',''),
        }
    return normalize_master_payload(kind,supplied)


def apply_master_mapping(kind:str,payload:dict,agreement_data:dict,replace:bool=False)->tuple[dict,list[str]]:
    kind=_kind(kind)
    mapping=LANDLORD_AGREEMENT_MAP if kind=='landlord' else TENANT_AGREEMENT_MAP
    merged=dict(agreement_data or {}); changed=[]
    for master_key,agreement_key in mapping.items():
        value=str((payload or {}).get(master_key) or '').strip()
        if not value:
            continue
        if replace or not str(merged.get(agreement_key) or '').strip():
            merged[agreement_key]=value; changed.append(agreement_key)
    return merged,changed
