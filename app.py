import os, io, csv, json, hashlib, datetime, urllib.parse, html, base64, re, secrets, uuid
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy import func, or_
from dateutil.relativedelta import relativedelta
import requests
import qrcode
from PIL import Image as PILImage
from zoneinfo import ZoneInfo

from agreement_core import PRESETS, DEFAULTS, FIELDS, FORMAT_PROFILES, build_agreement_text, build_agreement_text_hindi

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-this-secret-before-production')
raw_db = os.getenv('DATABASE_URL', '')
if raw_db.startswith('postgres://'):
    raw_db = raw_db.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = raw_db or ('sqlite:///' + os.path.join(BASE_DIR, 'instance', 'livenza_web.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_UPLOAD_MB','55')) * 1024 * 1024
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
if os.getenv('FORCE_HTTPS', '1') == '1':
    app.config['SESSION_COOKIE_SECURE'] = True

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)
    role = db.Column(db.String(30), default='manager')
    full_name = db.Column(db.String(180), default='')
    photo_data_uri = db.Column(db.Text, default='')
    aadhaar_last4 = db.Column(db.String(4), default='')
    aadhaar_name = db.Column(db.String(180), default='')
    aadhaar_verification_status = db.Column(db.String(40), default='Not verified')
    aadhaar_verification_method = db.Column(db.String(80), default='')
    aadhaar_verification_ref = db.Column(db.String(180), default='')
    aadhaar_verified_at = db.Column(db.DateTime, nullable=True)
    permissions_json = db.Column(db.Text, default='[]')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    code = db.Column(db.String(30), default='')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Agreement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    preset = db.Column(db.String(120), default='Strong Residential - 11 Months')
    data_json = db.Column(db.Text, nullable=False, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    @property
    def data(self):
        try: return json.loads(self.data_json or '{}')
        except Exception: return {}

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(120), default='')
    property_name = db.Column(db.String(180), default='')
    premises = db.Column(db.Text, default='')
    room_no = db.Column(db.String(60), nullable=False)
    room_type = db.Column(db.String(120), default='')
    capacity = db.Column(db.String(30), default='')
    standard_tariff = db.Column(db.String(60), default='')
    status_override = db.Column(db.String(40), default='')
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('property_name','room_no', name='uq_room_property'),)

class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_name = db.Column(db.String(180), default='')
    tenant_mobile = db.Column(db.String(40), default='')
    tenant_whatsapp = db.Column(db.String(40), default='')
    tenant_email = db.Column(db.String(180), default='')
    tenant_id_type = db.Column(db.String(40), default='')
    tenant_id_no = db.Column(db.String(100), default='')
    city = db.Column(db.String(120), default='')
    property_name = db.Column(db.String(180), default='')
    premises = db.Column(db.Text, default='')
    room_unit_no = db.Column(db.String(60), default='')
    room_type = db.Column(db.String(120), default='')
    tariff = db.Column(db.String(60), default='')
    security_deposit = db.Column(db.String(60), default='')
    joining_date = db.Column(db.String(40), default='')
    leaving_date = db.Column(db.String(40), default='')
    status = db.Column(db.String(40), default='Occupied')
    agreement_id = db.Column(db.Integer, db.ForeignKey('agreement.id'), nullable=True)
    agreement_reference = db.Column(db.String(120), default='')
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(180), default='')
    business_type = db.Column(db.String(120), default='')
    experience = db.Column(db.Text, default='')
    output = db.Column(db.Text, default='')
    language = db.Column(db.String(40), default='English')
    google_review_url = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class FoodOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), default='Direct')
    order_id = db.Column(db.String(120), default='')
    outlet = db.Column(db.String(180), default='')
    customer = db.Column(db.String(180), default='')
    order_time = db.Column(db.String(60), default='')
    status = db.Column(db.String(50), default='New')
    payment_mode = db.Column(db.String(50), default='')
    gross = db.Column(db.Float, default=0)
    commission = db.Column(db.Float, default=0)
    fees = db.Column(db.Float, default=0)
    taxes = db.Column(db.Float, default=0)
    net = db.Column(db.Float, default=0)
    settlement_status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class VideoAsset(db.Model):
    __tablename__ = 'video_asset'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(220), default='', nullable=False)
    media_type = db.Column(db.String(20), default='video', nullable=False)
    storage_path = db.Column(db.Text, default='')
    public_url = db.Column(db.Text, default='', nullable=False)
    mime_type = db.Column(db.String(120), default='')
    file_size = db.Column(db.BigInteger, default=0)
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class VideoScreen(db.Model):
    __tablename__ = 'video_screen'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    player_token = db.Column(db.String(180), nullable=False, unique=True)
    city = db.Column(db.String(120), default='')
    location_name = db.Column(db.String(220), default='')
    device_label = db.Column(db.String(180), default='')
    current_asset_id = db.Column(db.Integer, db.ForeignKey('video_asset.id'), nullable=True)
    playlist_json = db.Column(db.Text, default='[]')
    rotation_degrees = db.Column(db.Integer, default=0)
    fit_mode = db.Column(db.String(20), default='contain')
    loop_media = db.Column(db.Boolean, default=True)
    muted = db.Column(db.Boolean, default=True)
    enabled = db.Column(db.Boolean, default=True)
    slide_duration_seconds = db.Column(db.Integer, default=10)
    last_seen_at = db.Column(db.DateTime, nullable=True)
    last_ip = db.Column(db.String(120), default='')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class FestiveSession(db.Model):
    __tablename__ = 'festive_session'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), default='Festive Takeover', nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('video_asset.id'), nullable=True)
    active = db.Column(db.Boolean, default=False)
    started_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, default='')

class QueryLead(db.Model):
    __tablename__ = 'query_lead'
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(60), default='Manual')
    external_id = db.Column(db.String(180), default='')
    city = db.Column(db.String(120), default='')
    property_name = db.Column(db.String(180), default='')
    customer_name = db.Column(db.String(180), default='')
    mobile = db.Column(db.String(40), default='')
    whatsapp = db.Column(db.String(40), default='')
    email = db.Column(db.String(180), default='')
    query_text = db.Column(db.Text, default='')
    budget = db.Column(db.String(80), default='')
    move_in_date = db.Column(db.String(40), default='')
    stay_type = db.Column(db.String(80), default='')
    status = db.Column(db.String(40), default='Live')
    heat = db.Column(db.String(20), default='Warm')
    score = db.Column(db.Integer, default=50)
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    next_follow_up = db.Column(db.String(60), default='')
    notes = db.Column(db.Text, default='')
    raw_json = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class QueryTemplate(db.Model):
    __tablename__ = 'query_template'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(60), default='General')
    message = db.Column(db.Text, default='')
    whatsapp_template_name = db.Column(db.String(160), default='')
    sources_json = db.Column(db.Text, default='[]')
    statuses_json = db.Column(db.Text, default='[]')
    auto_send = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class QueryActivity(db.Model):
    __tablename__ = 'query_activity'
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('query_lead.id'), nullable=False)
    action = db.Column(db.String(80), default='Update')
    details = db.Column(db.Text, default='')
    actor_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Setting(db.Model):
    key = db.Column(db.String(120), primary_key=True)
    value = db.Column(db.Text, default='')


def setting(key, default=''):
    row = db.session.get(Setting, key)
    return row.value if row else default

def set_setting(key, value):
    row = db.session.get(Setting, key)
    if row: row.value = value
    else: db.session.add(Setting(key=key, value=value))
    db.session.commit()



MODULES = {
    'agreements': 'Agreement Studio',
    'rooms': 'Room Status & Tenants',
    'reviews': 'Google Review Generator',
    'food': 'Food Delivery Hub',
    'rentok': 'Livenza Billing Suite',
    'queries': 'Live Queries Manager',
    'video_wall': 'Video Wall Studio',
}

BASE_REQUIRED_AGREEMENT_FIELDS = []

AGREEMENT_GROUPS = [
    ('Agreement Format, Execution & Stamp Details', [x[0] for x in FIELDS[0:22]]),
    ('Landlord / Lessor / Management', [x[0] for x in FIELDS[22:32]]),
    ('Tenant / Lessee / Licensee / Guest', [x[0] for x in FIELDS[32:43]]),
    ('Corporate Client / Sponsor', [x[0] for x in FIELDS[43:51]]),
    ('Property, City & Financial Terms', ['city'] + [x[0] for x in FIELDS[51:75]]),
    ('Operations, Access, Services & Special Terms', [x[0] for x in FIELDS[75:88]]),
    ('Operating Model & Foreign Client Compliance', [x[0] for x in FIELDS[88:110]]),
    ('Licences, Verification & Regulatory References', [x[0] for x in FIELDS[110:120]]),
    ('Witnesses & Execution', [x[0] for x in FIELDS[120:122]]),
]


def user_permissions(user=None):
    user = user or current_user()
    if not user:
        return set()
    if (user.role or '').lower() == 'admin':
        return set(MODULES)
    try:
        vals = json.loads(user.permissions_json or '[]')
        return {x for x in vals if x in MODULES}
    except Exception:
        return set()


def can_access(module, user=None):
    if module not in MODULES:
        return False
    return module in user_permissions(user)


def permission_required(module):
    def outer(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            if not session.get('uid'):
                return redirect(url_for('login', next=request.path))
            u = current_user()
            if not u or not u.active:
                session.clear()
                return redirect(url_for('login'))
            if not can_access(module, u):
                flash(f'Your account does not have access to {MODULES[module]}.', 'danger')
                return redirect(url_for('dashboard'))
            return fn(*a, **kw)
        return wrapper
    return outer


def admin_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not session.get('uid'):
            return redirect(url_for('login', next=request.path))
        u=current_user()
        if not u or not u.active or (u.role or '').lower()!='admin':
            abort(403)
        return fn(*a, **kw)
    return wrapper


def agreement_required_fields(preset_name, data):
    # Web 1.3.2: every Agreement Studio field is optional.
    return set()


def field_label_map():
    m={x[0]:x[1] for x in FIELDS}
    m['city']='City'
    return m


def missing_agreement_fields(preset_name, data):
    # Compatibility hook: no Agreement Studio fields are mandatory.
    return []


def normalize_whatsapp_number(value):
    raw=''.join(ch for ch in (value or '') if ch.isdigit())
    if len(raw)==10:
        raw='91'+raw
    return raw if 8 <= len(raw) <= 15 else ''


def share_serializer():
    return URLSafeTimedSerializer(app.config['SECRET_KEY'], salt='livenza-agreement-share-v1')

def image_data_uri(file_storage):
    if not file_storage or not getattr(file_storage, 'filename', ''):
        return ''
    try:
        img=PILImage.open(file_storage.stream).convert('RGB')
        img.thumbnail((640,640))
        buf=io.BytesIO(); img.save(buf,format='JPEG',quality=84,optimize=True)
        if buf.tell()>900000:
            img.thumbnail((420,420)); buf=io.BytesIO(); img.save(buf,format='JPEG',quality=76,optimize=True)
        return 'data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode('ascii')
    except Exception:
        return ''

def masked_aadhaar(last4):
    d=''.join(ch for ch in (last4 or '') if ch.isdigit())[-4:]
    return f'XXXX XXXX {d}' if len(d)==4 else ''

def _extract_json_object(text_value):
    raw=(text_value or '').strip()
    raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw,flags=re.I|re.S).strip()
    try:
        value=json.loads(raw)
        return value if isinstance(value,dict) else {}
    except Exception:
        m=re.search(r'\{.*\}',raw,re.S)
        if not m: return {}
        try:
            value=json.loads(m.group(0)); return value if isinstance(value,dict) else {}
        except Exception:
            return {}


def _normalize_aadhaar_extract(value):
    value=value if isinstance(value,dict) else {}
    out={}
    def clean(k,limit=800):
        return str(value.get(k,'') or '').strip()[:limit]
    out['tenant_name']=clean('name',180)
    out['tenant_father']=clean('father_or_spouse',180)
    out['tenant_dob']=clean('date_of_birth',40)
    out['tenant_address']=clean('address',1000)
    digits=''.join(ch for ch in clean('aadhaar_number',40) if ch.isdigit())
    if len(digits)==12:
        out['tenant_id_no']=f'{digits[:4]} {digits[4:8]} {digits[8:]}'
    else:
        out['tenant_id_no']=''
    out['tenant_id_type']='Aadhaar'
    out['gender']=clean('gender',30)
    return out


def _parse_aadhaar_text_fallback(raw_text):
    txt='\n'.join(x.strip() for x in (raw_text or '').splitlines() if x.strip())
    result={'name':'','father_or_spouse':'','date_of_birth':'','gender':'','address':'','aadhaar_number':''}
    m=re.search(r'(?<!\d)(\d{4})\s*(\d{4})\s*(\d{4})(?!\d)',txt)
    if m: result['aadhaar_number']=' '.join(m.groups())
    m=re.search(r'(?:DOB|Date\s*of\s*Birth|YOB)\s*[:\-/]?\s*([0-3]?\d[\-/][01]?\d[\-/]\d{4}|\d{4})',txt,re.I)
    if m: result['date_of_birth']=m.group(1)
    m=re.search(r'\b(Male|Female|Transgender)\b',txt,re.I)
    if m: result['gender']=m.group(1).title()
    m=re.search(r'(?:S/O|D/O|W/O|C/O)\s*[:\-]?\s*([^\n,]+)',txt,re.I)
    if m: result['father_or_spouse']=m.group(1).strip()
    m=re.search(r'(?:Address|पता)\s*[:\-]\s*(.+?)(?=(?:\n\s*\d{4}\s*\d{4}\s*\d{4}|\Z))',txt,re.I|re.S)
    if m: result['address']=' '.join(m.group(1).split())[:1000]
    # Name heuristic: a short human-name line immediately preceding DOB/gender.
    lines=[x.strip() for x in txt.splitlines() if x.strip()]
    dob_idx=next((i for i,x in enumerate(lines) if re.search(r'\b(?:DOB|Date\s*of\s*Birth|YOB)\b',x,re.I)),None)
    if dob_idx is not None:
        for cand in reversed(lines[max(0,dob_idx-4):dob_idx]):
            if 2 <= len(cand) <= 80 and not re.search(r'Government|भारत|UIDAI|Aadhaar|Enrollment|VID|Male|Female|Address',cand,re.I) and not re.search(r'\d{4}',cand):
                result['name']=cand; break
    return _normalize_aadhaar_extract(result)


def _aadhaar_ai_extract(file_bytes, filename, mimetype):
    key=os.getenv('OPENAI_API_KEY','').strip()
    if not key:
        return {}, 'AI extraction is not configured on this server.'
    from openai import OpenAI
    client=OpenAI(api_key=key)
    prompt=(
        'Extract identity fields from this Indian Aadhaar document for tenant-form autofill. '
        'Return ONLY strict JSON with keys: name, father_or_spouse, date_of_birth, gender, address, aadhaar_number. '
        'Use empty strings when a field is not clearly visible. Do not guess. Preserve the Aadhaar number only if all 12 digits are clearly legible. '
        'Do not add commentary. This extraction is not an authenticity verification.'
    )
    content=[{'type':'input_text','text':prompt}]
    if mimetype=='application/pdf' or filename.lower().endswith('.pdf'):
        content.append({'type':'input_file','filename':filename or 'aadhaar.pdf','file_data':base64.b64encode(file_bytes).decode('ascii')})
    else:
        mt=mimetype if mimetype in ('image/jpeg','image/png','image/webp') else 'image/jpeg'
        content.append({'type':'input_image','image_url':f'data:{mt};base64,'+base64.b64encode(file_bytes).decode('ascii'),'detail':'high'})
    resp=client.responses.create(
        model=os.getenv('OPENAI_AADHAAR_MODEL',os.getenv('OPENAI_REVIEW_MODEL','gpt-5.6-luna')),
        input=[{'role':'user','content':content}],
    )
    obj=_extract_json_object(getattr(resp,'output_text',''))
    return _normalize_aadhaar_extract(obj), '' if obj else 'The document could not be read reliably.'

def query_log(q, action, details='', actor=None):
    db.session.add(QueryActivity(query_id=q.id,action=action,details=details,actor_user_id=(actor.id if actor else None)))

def wa_number(value):
    return normalize_whatsapp_number(value)

def whatsapp_cloud_configured():
    return bool(os.getenv('WHATSAPP_CLOUD_TOKEN','').strip() and os.getenv('WHATSAPP_PHONE_NUMBER_ID','').strip())

def whatsapp_cloud_text(to, body):
    to=wa_number(to)
    token=os.getenv('WHATSAPP_CLOUD_TOKEN','').strip(); pid=os.getenv('WHATSAPP_PHONE_NUMBER_ID','').strip()
    if not (to and token and pid): return False, 'WhatsApp Cloud API is not configured.'
    ver=os.getenv('WHATSAPP_GRAPH_VERSION','v23.0')
    r=requests.post(f'https://graph.facebook.com/{ver}/{pid}/messages',headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},json={'messaging_product':'whatsapp','to':to,'type':'text','text':{'body':body,'preview_url':False}},timeout=25)
    return r.ok, (r.text[:800] if not r.ok else 'Sent')

def whatsapp_cloud_template(to, template_name, language='en'):
    to=wa_number(to); token=os.getenv('WHATSAPP_CLOUD_TOKEN','').strip(); pid=os.getenv('WHATSAPP_PHONE_NUMBER_ID','').strip()
    if not (to and token and pid and template_name): return False, 'Cloud API/template not configured.'
    ver=os.getenv('WHATSAPP_GRAPH_VERSION','v23.0')
    payload={'messaging_product':'whatsapp','to':to,'type':'template','template':{'name':template_name,'language':{'code':language}}}
    r=requests.post(f'https://graph.facebook.com/{ver}/{pid}/messages',headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},json=payload,timeout=25)
    return r.ok, (r.text[:800] if not r.ok else 'Sent')

def generate_empty_rooms_pdf_bytes():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=36,rightMargin=36,topMargin=42,bottomMargin=42)
    styles=getSampleStyleSheet(); story=[Paragraph('LIVENZA LIFE - VACANT ROOMS STATUS',styles['Title']),Paragraph(datetime.datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%d %b %Y, %I:%M %p IST'),styles['Normal']),Spacer(1,12)]
    rows=[['City','Property','Room','Type','Tariff','Status']]
    for r in Room.query.order_by(Room.city,Room.property_name,Room.room_no):
        st=room_status(r)
        if st=='Vacant': rows.append([r.city,r.property_name,r.room_no,r.room_type,r.standard_tariff,st])
    if len(rows)==1: rows.append(['-','-','-','-','-','No vacant rooms'])
    t=Table(rows,repeatRows=1,colWidths=[65,110,45,85,70,65]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#5c34d6')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.4,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP')]))
    story.append(t); doc.build(story); buf.seek(0); return buf

def whatsapp_upload_pdf(pdf_bytes, filename):
    token=os.getenv('WHATSAPP_CLOUD_TOKEN','').strip(); pid=os.getenv('WHATSAPP_PHONE_NUMBER_ID','').strip(); ver=os.getenv('WHATSAPP_GRAPH_VERSION','v23.0')
    if not (token and pid): return None
    r=requests.post(f'https://graph.facebook.com/{ver}/{pid}/media',headers={'Authorization':f'Bearer {token}'},data={'messaging_product':'whatsapp'},files={'file':(filename,pdf_bytes.getvalue(),'application/pdf')},timeout=30)
    return (r.json().get('id') if r.ok else None)

def whatsapp_send_document(to, media_id, filename, caption=''):
    token=os.getenv('WHATSAPP_CLOUD_TOKEN','').strip(); pid=os.getenv('WHATSAPP_PHONE_NUMBER_ID','').strip(); ver=os.getenv('WHATSAPP_GRAPH_VERSION','v23.0'); to=wa_number(to)
    if not (token and pid and to and media_id): return False
    payload={'messaging_product':'whatsapp','to':to,'type':'document','document':{'id':media_id,'filename':filename,'caption':caption[:1024]}}
    return requests.post(f'https://graph.facebook.com/{ver}/{pid}/messages',headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},json=payload,timeout=25).ok

def normalize_query_payload(source, payload):
    flat={}
    if isinstance(payload,dict):
        flat.update(payload)
        for row in payload.get('user_column_data',[]) or []:
            key=(row.get('column_name') or row.get('column_id') or '').lower(); val=row.get('string_value') or row.get('column_value') or ''
            if key: flat[key]=val
        for row in payload.get('field_data',[]) or []:
            key=(row.get('name') or '').lower(); vals=row.get('values') or []; flat[key]=(vals[0] if vals else '')
    def pick(*keys):
        for k in keys:
            v=flat.get(k)
            if v not in (None,''): return str(v)
        return ''
    return dict(source=source.title(),external_id=pick('lead_id','id','external_id','leadgen_id'),customer_name=pick('full_name','name','customer_name'),mobile=pick('phone_number','phone','mobile'),whatsapp=pick('whatsapp','phone_number','phone','mobile'),email=pick('email','email_address'),query_text=pick('query','message','comments','notes','property_query'),city=pick('city'),property_name=pick('property','property_name','listing_name'),budget=pick('budget','travel_budget'),move_in_date=pick('move_in_date','arrival_date','check_in'),stay_type=pick('stay_type','accommodation_type'))

def auto_reply_for_query(q):
    candidates=QueryTemplate.query.filter_by(active=True,auto_send=True).order_by(QueryTemplate.id).all()
    for t in candidates:
        try: sources=json.loads(t.sources_json or '[]'); statuses=json.loads(t.statuses_json or '[]')
        except Exception: sources=statuses=[]
        if sources and q.source not in sources: continue
        if statuses and q.status not in statuses: continue
        number=q.whatsapp or q.mobile
        if t.whatsapp_template_name and whatsapp_cloud_configured(): ok,msg=whatsapp_cloud_template(number,t.whatsapp_template_name)
        elif whatsapp_cloud_configured(): ok,msg=whatsapp_cloud_text(number,t.message.format(name=q.customer_name or 'Guest',property=q.property_name or 'Livenza Life',city=q.city or ''))
        else: return False,'WhatsApp Cloud API not configured; query retained for manual reply.'
        query_log(q,'Auto WhatsApp',f'{t.name}: {msg}'); return ok,msg
    return False,'No matching auto-reply template.'


def _supabase_project_ref():
    explicit=os.getenv('SUPABASE_PROJECT_REF','').strip()
    if explicit: return explicit
    m=re.search(r'postgres\.([a-z0-9]+)[:@]', raw_db or '', re.I)
    if m: return m.group(1)
    m=re.search(r'db\.([a-z0-9]+)\.supabase\.co', raw_db or '', re.I)
    return m.group(1) if m else ''

def supabase_storage_configured():
    return bool(_supabase_project_ref() and os.getenv('SUPABASE_SERVICE_ROLE_KEY','').strip())

def upload_video_wall_media(file_storage):
    if not file_storage or not getattr(file_storage,'filename',''):
        return None, 'No media file selected.'
    project_ref=_supabase_project_ref(); key=os.getenv('SUPABASE_SERVICE_ROLE_KEY','').strip()
    if not (project_ref and key):
        return None, 'Supabase media upload is not configured. Add SUPABASE_SERVICE_ROLE_KEY in Render, or use an external media URL.'
    allowed={'video/mp4','video/webm','video/quicktime','image/jpeg','image/png','image/webp'}
    mime=(file_storage.mimetype or '').lower()
    if mime not in allowed:
        return None, 'Supported files: MP4, WebM, MOV, JPG, PNG and WebP.'
    file_storage.stream.seek(0,2); size=file_storage.stream.tell(); file_storage.stream.seek(0)
    max_bytes=int(os.getenv('VIDEO_WALL_MAX_MB','50'))*1024*1024
    if size>max_bytes:
        return None, f'File exceeds the configured {int(max_bytes/1024/1024)} MB limit. Compress the media or use an external/CDN URL.'
    ext=os.path.splitext(file_storage.filename)[1].lower() or ('.mp4' if mime.startswith('video/') else '.jpg')
    path=f"video-wall/{datetime.datetime.utcnow():%Y/%m}/{uuid.uuid4().hex}{ext}"
    base=f'https://{project_ref}.supabase.co'
    object_url=f"{base}/storage/v1/object/video-wall-media/{urllib.parse.quote(path,safe='/')}"
    headers={'Authorization':f'Bearer {key}','apikey':key,'Content-Type':mime,'x-upsert':'false'}
    try:
        data=file_storage.stream.read()
        r=requests.post(object_url,headers=headers,data=data,timeout=180)
        if not r.ok:
            return None, f'Supabase Storage upload failed ({r.status_code}): {r.text[:300]}'
        public=f"{base}/storage/v1/object/public/video-wall-media/{urllib.parse.quote(path,safe='/')}"
        return {'path':path,'url':public,'size':size,'mime':mime,'type':('image' if mime.startswith('image/') else 'video')}, ''
    except Exception as exc:
        return None, f'Upload failed: {exc}'

def active_festive_session():
    return FestiveSession.query.filter_by(active=True).order_by(FestiveSession.id.desc()).first()

def screen_is_online(screen):
    if not screen.last_seen_at: return False
    return (datetime.datetime.utcnow()-screen.last_seen_at).total_seconds() <= 90

def screen_player_state(screen):
    festive=active_festive_session()
    assets=[]
    if festive and festive.asset_id:
        a=db.session.get(VideoAsset,festive.asset_id)
        if a and a.active: assets=[a]
    else:
        try: ids=[int(x) for x in json.loads(screen.playlist_json or '[]') if str(x).isdigit()]
        except Exception: ids=[]
        if not ids and screen.current_asset_id: ids=[screen.current_asset_id]
        for aid in ids:
            a=db.session.get(VideoAsset,aid)
            if a and a.active: assets.append(a)
    def item(a): return {'id':a.id,'title':a.title,'url':a.public_url,'type':a.media_type,'mime':a.mime_type}
    return {
        'screen':{'id':screen.id,'name':screen.name,'city':screen.city,'location':screen.location_name,'enabled':bool(screen.enabled)},
        'asset':(item(assets[0]) if assets else None),
        'playlist':[item(a) for a in assets],
        'rotation':int(screen.rotation_degrees or 0),
        'fit':screen.fit_mode or 'contain',
        'loop':bool(screen.loop_media),
        'muted':bool(screen.muted),
        'slide_duration':max(3,int(screen.slide_duration_seconds or 10)),
        'festive':({'id':festive.id,'name':festive.name} if festive else None),
    }


def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if not session.get('uid'):
            return redirect(url_for('login', next=request.path))
        u=current_user()
        if not u or not u.active:
            session.clear()
            flash('This user account is inactive.', 'danger')
            return redirect(url_for('login'))
        return fn(*a, **kw)
    return wrapper


def current_user():
    return db.session.get(User, session.get('uid')) if session.get('uid') else None


def parse_date(v):
    if not v: return None
    for f in ('%Y-%m-%d','%d-%m-%Y','%d/%m/%Y'):
        try: return datetime.datetime.strptime(v, f).date()
        except Exception: pass
    return None


def room_status(room):
    if room.status_override in ('Maintenance','Blocked'): return room.status_override
    today = datetime.date.today()
    tenants = Tenant.query.filter_by(property_name=room.property_name, room_unit_no=room.room_no).order_by(Tenant.id.desc()).all()
    for t in tenants:
        j, l = parse_date(t.joining_date), parse_date(t.leaving_date)
        if t.status == 'Notice Given' and (not l or l >= today): return 'Notice Given'
        if j and j > today: return 'Upcoming'
        if (not j or j <= today) and (not l or l >= today) and t.status not in ('Vacated','Cancelled','Terminated'):
            return 'Occupied'
    return 'Vacant'


def sync_tenant_from_agreement(ag):
    d = ag.data
    if not (d.get('tenant_name') or d.get('room_unit_no')): return
    prop, room_no = d.get('property_name','').strip(), d.get('room_unit_no','').strip()
    if room_no:
        r = Room.query.filter_by(property_name=prop, room_no=room_no).first()
        if not r:
            r=Room(city=d.get('city',''), property_name=prop, premises=d.get('premises',''), room_no=room_no, room_type=d.get('room_type',''), capacity=d.get('occupancy_limit',''), standard_tariff=d.get('monthly_rent',''))
            db.session.add(r)
        else:
            if d.get('city'): r.city=d.get('city')
            if d.get('premises'): r.premises=d.get('premises')
            if d.get('room_type'): r.room_type=d.get('room_type')
            if d.get('monthly_rent'): r.standard_tariff=d.get('monthly_rent')
    t = Tenant.query.filter_by(agreement_id=ag.id).first()
    if not t: t=Tenant(agreement_id=ag.id); db.session.add(t)
    t.tenant_name=d.get('tenant_name',''); t.tenant_mobile=d.get('tenant_mobile',''); t.tenant_whatsapp=d.get('tenant_whatsapp') or d.get('tenant_mobile','')
    t.tenant_email=d.get('tenant_email',''); t.tenant_id_type=d.get('tenant_id_type',''); t.tenant_id_no=d.get('tenant_id_no','')
    t.city=d.get('city',''); t.property_name=prop; t.premises=d.get('premises',''); t.room_unit_no=room_no; t.room_type=d.get('room_type','')
    t.tariff=d.get('monthly_rent',''); t.security_deposit=d.get('security_deposit',''); t.joining_date=d.get('start_date',''); t.leaving_date=d.get('end_date','')
    t.agreement_reference=d.get('agreement_reference','')
    j,l=parse_date(t.joining_date), parse_date(t.leaving_date); today=datetime.date.today()
    t.status='Upcoming' if j and j>today else ('Vacated' if l and l<today else 'Occupied')
    db.session.commit()


def all_form_data(preset_name=None):
    preset_name = preset_name or request.form.get('agreement_template') or 'Strong Residential - 11 Months'
    d = dict(DEFAULTS)
    d.update(PRESETS.get(preset_name, {}))
    for key, *_ in FIELDS:
        if key in request.form:
            d[key]=request.form.get(key,'').strip()
    for key in request.form:
        if key not in d:
            d[key]=request.form.get(key,'').strip()
    d['agreement_template']=preset_name
    return d


@app.context_processor
def inject_common():
    return dict(
        current_user=current_user(), app_version='Web 1.4.2',
        can_access=can_access, module_labels=MODULES,
        is_admin=bool(current_user() and (current_user().role or '').lower()=='admin'), masked_aadhaar=masked_aadhaar
    )

@app.route('/health')
def health(): return jsonify(status='ok', service='livenza-back-office-web', version='1.4.1')

@app.after_request
def livenza_no_cache(response):
    # Back Office is an operational web app. During active deployment cycles we
    # deliberately prevent stale HTML/CSS/JS from masking a successful release.
    if request.path.startswith('/static/') or response.mimetype in ('text/html','text/css','application/javascript','text/javascript'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    response.headers['X-Livenza-Build'] = 'Web 1.4.2'
    return response

@app.route('/diagnostics')
def diagnostics():
    route_names = {rule.endpoint for rule in app.url_map.iter_rules()}
    checks = {
        'version': 'Web 1.4.2',
        'video_wall_route_loaded': 'video_wall' in route_names,
        'video_wall_player_loaded': 'wall_player' in route_names,
        'video_wall_template_exists': os.path.exists(os.path.join(BASE_DIR,'templates','video_wall.html')),
        'wall_player_template_exists': os.path.exists(os.path.join(BASE_DIR,'templates','wall_player.html')),
        'apple_theme_css_exists': os.path.exists(os.path.join(BASE_DIR,'static','style.css')),
        'billing_route_loaded': 'billing' in route_names,
    }
    try:
        checks['video_wall_tables_ready'] = db.session.execute(db.text("select count(*) from video_screen")).scalar() is not None
    except Exception as exc:
        checks['video_wall_tables_ready'] = False
        checks['database_error'] = str(exc)[:180]
        db.session.rollback()
    return jsonify(checks)

@app.route('/version')
def version(): return jsonify(version='Web 1.4.2', features=['liquid-glass','live-queries','identity','vacant-room-automation','pwa-icons','aadhaar-agreement-autofill','sticky-footer','optional-agreement-fields','apple-inspired-light-theme','video-wall-studio','multi-screen-player','festive-takeover','fullscreen-control','view-rotation-control','livenza-billing-suite','verified-deploy-marker','no-cache-assets','video-wall-diagnostics'])

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=User.query.filter_by(username=request.form.get('username','').strip()).first()
        if u and u.active and check_password_hash(u.password_hash, request.form.get('password','')):
            session.clear(); session['uid']=u.id
            return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Invalid login ID/password or inactive account.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

@app.route('/account', methods=['GET','POST'])
@login_required
def account():
    u=current_user()
    if request.method=='POST':
        if request.form.get('new_password'):
            u.password_hash=generate_password_hash(request.form['new_password'])
        if request.form.get('username'):
            u.username=request.form['username'].strip()
        if request.form.get('full_name') is not None:
            u.full_name=request.form.get('full_name','').strip()
        if request.files.get('photo') and request.files['photo'].filename:
            data=image_data_uri(request.files['photo'])
            if data: u.photo_data_uri=data
        last4=''.join(ch for ch in request.form.get('aadhaar_last4','') if ch.isdigit())[-4:]
        if last4: u.aadhaar_last4=last4
        if request.form.get('aadhaar_name') is not None: u.aadhaar_name=request.form.get('aadhaar_name','').strip()
        db.session.commit(); flash('Account updated.','success'); return redirect(url_for('account'))
    return render_template('account.html', user=u)

@app.route('/')
@login_required
def dashboard():
    rooms=Room.query.all(); statuses=[room_status(r) for r in rooms]
    stats={
        'agreements':Agreement.query.count(), 'tenants':Tenant.query.count(), 'rooms':len(rooms),
        'vacant':sum(1 for x in statuses if x=='Vacant'), 'orders':FoodOrder.query.count(), 'reviews':Review.query.count(), 'queries':QueryLead.query.count(), 'hot_queries':QueryLead.query.filter_by(heat='Hot').count(), 'screens':VideoScreen.query.count(), 'screens_online':sum(1 for x in VideoScreen.query.all() if screen_is_online(x))
    }
    agreements_all=Agreement.query.all()
    city_rows=[]
    for c in City.query.filter_by(active=True).order_by(City.name).all():
        city_rows.append({
            'name':c.name, 'code':c.code,
            'rooms':Room.query.filter_by(city=c.name).count(),
            'tenants':Tenant.query.filter_by(city=c.name).count(),
            'agreements':sum(1 for a in agreements_all if (a.data.get('city') or '').strip()==c.name)
        })
    return render_template('dashboard.html', stats=stats, cities=city_rows, permissions=user_permissions())

@app.route('/api/presets/<path:name>')
@permission_required('agreements')
def preset_api(name):
    profile=FORMAT_PROFILES.get(name, FORMAT_PROFILES.get('Strong Residential - 11 Months',{}))
    preview_data=dict(DEFAULTS); preview_data.update(PRESETS.get(name,{})); preview_data['agreement_template']=name
    return jsonify({
        'values':PRESETS.get(name,{}),
        'required':sorted(agreement_required_fields(name,preview_data)),
        'profile':{
            'title_en':profile.get('title_en',''), 'subtitle_en':profile.get('subtitle_en',''),
            'nature_en':profile.get('nature_en','')
        }
    })

def agreement_editor_context(ag=None, data=None):
    d=dict(DEFAULTS)
    if ag: d.update(ag.data)
    if data: d.update(data)
    if not ag and not data: d.update(PRESETS.get('Strong Residential - 11 Months',{}))
    fields={x[0]:x for x in FIELDS}
    fields['city']=('city','City','entry',None)
    city_names=[c.name for c in City.query.filter_by(active=True).order_by(City.name).all()]
    preset=d.get('agreement_template') or 'Strong Residential - 11 Months'
    profile=FORMAT_PROFILES.get(preset, FORMAT_PROFILES.get('Strong Residential - 11 Months',{}))
    return dict(ag=ag,d=d,presets=PRESETS,field_map=fields,groups=AGREEMENT_GROUPS,
                required_fields=agreement_required_fields(preset,d),city_names=city_names,preset_profile=profile)

@app.route('/agreements/aadhaar-extract', methods=['POST'])
@permission_required('agreements')
def agreement_aadhaar_extract():
    upload=request.files.get('aadhaar_file')
    if not upload or not upload.filename:
        return jsonify(ok=False,error='Choose an Aadhaar JPEG, PNG or PDF first.'),400
    filename=os.path.basename(upload.filename)
    ext=os.path.splitext(filename.lower())[1]
    if ext not in ('.jpg','.jpeg','.png','.pdf'):
        return jsonify(ok=False,error='Supported formats: JPG, JPEG, PNG and PDF.'),400
    raw=upload.read()
    if not raw:
        return jsonify(ok=False,error='The uploaded file is empty.'),400
    if len(raw)>10*1024*1024:
        return jsonify(ok=False,error='Aadhaar upload must be 10 MB or smaller.'),413
    mimetype=(upload.mimetype or '').lower()
    data={}; local_note=''
    # Text-based PDFs can be parsed locally first, without sending the file to an AI service.
    if ext=='.pdf':
        try:
            from pypdf import PdfReader
            reader=PdfReader(io.BytesIO(raw))
            pdf_text='\n'.join((page.extract_text() or '') for page in reader.pages[:4])
            if len(pdf_text.strip())>40:
                data=_parse_aadhaar_text_fallback(pdf_text)
                local_note='Text was extracted from the PDF locally.'
        except Exception:
            pass
    essential=sum(bool(data.get(k)) for k in ('tenant_name','tenant_dob','tenant_address','tenant_id_no'))
    if essential<3:
        try:
            ai_data,err=_aadhaar_ai_extract(raw,filename,mimetype or ('application/pdf' if ext=='.pdf' else 'image/jpeg'))
            if ai_data:
                for k,v in ai_data.items():
                    if v: data[k]=v
                local_note='Document read using the configured AI extraction service.'
            elif err and essential==0:
                return jsonify(ok=False,error=err),503
        except Exception as exc:
            if essential==0:
                return jsonify(ok=False,error='Could not extract Aadhaar details. Confirm the server AI key is configured or upload a text-based PDF.'),500
    if not any(data.get(k) for k in ('tenant_name','tenant_dob','tenant_address','tenant_id_no')):
        return jsonify(ok=False,error='No reliable Aadhaar fields were detected. Try a clearer scan or a PDF containing both sides.'),422
    return jsonify(ok=True,fields=data,note=local_note,warning='Autofill only — review the extracted details. This does not verify Aadhaar authenticity with UIDAI.')

@app.route('/agreements')
@permission_required('agreements')
def agreements(): return render_template('agreements.html', items=Agreement.query.order_by(Agreement.updated_at.desc()).all())

@app.route('/agreements/new', methods=['GET','POST'])
@app.route('/agreements/<int:aid>/edit', methods=['GET','POST'])
@permission_required('agreements')
def agreement_edit(aid=None):
    ag=db.session.get(Agreement,aid) if aid else None
    if request.method=='POST':
        preset=request.form.get('agreement_template') or 'Strong Residential - 11 Months'
        d=all_form_data(preset)
        if not ag:
            ag=Agreement(name='Agreement',preset=preset,data_json='{}'); db.session.add(ag); db.session.flush()
        ag.preset=preset; ag.data_json=json.dumps(d,ensure_ascii=False)
        ag.name=f"{d.get('tenant_name') or 'Agreement'} - {d.get('room_unit_no') or d.get('property_name') or ag.id}"
        db.session.commit(); sync_tenant_from_agreement(ag)
        flash(f'{preset} agreement saved. Preset-specific format and clauses have been applied.','success')
        return redirect(url_for('agreement_preview',aid=ag.id,lang=request.form.get('save_lang','en')))
    return render_template('agreement_edit.html', **agreement_editor_context(ag))

@app.route('/agreements/<int:aid>/preview')
@permission_required('agreements')
def agreement_preview(aid):
    ag=db.session.get(Agreement,aid) or abort(404); lang=request.args.get('lang','en')
    text=build_agreement_text_hindi(ag.data,[]) if lang=='hi' else build_agreement_text(ag.data,[])
    return render_template('agreement_preview.html',ag=ag,text=text,lang=lang)

def build_agreement_pdf_bytes(ag):
    from reportlab.lib.pagesizes import A4, legal, letter
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    d=ag.data
    ps={'A4':A4,'Legal':legal,'Letter':letter}.get(d.get('paper_size'),legal)
    def num(key,default):
        try:return float(d.get(key) or default)
        except:return float(default)
    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=ps,leftMargin=num('margin_left_mm',20)*mm,rightMargin=num('margin_right_mm',18)*mm,topMargin=num('margin_top_mm',16)*mm,bottomMargin=num('margin_bottom_mm',16)*mm)
    styles=getSampleStyleSheet()
    body=ParagraphStyle('AgreementBody',parent=styles['BodyText'],fontName='Times-Roman',fontSize=9.5,leading=14,spaceAfter=4)
    head=ParagraphStyle('AgreementHead',parent=styles['Heading3'],fontName='Times-Bold',fontSize=11,leading=14,spaceBefore=8,spaceAfter=5)
    title=ParagraphStyle('AgreementTitle',parent=styles['Title'],fontName='Times-Bold',fontSize=15,leading=18,alignment=TA_CENTER,spaceAfter=8)
    story=[]
    logo=os.path.join(BASE_DIR,'static','livenza_logo.png')
    if os.path.exists(logo):
        story += [Image(logo,width=38*mm,height=24*mm),Spacer(1,3*mm)]
    text=build_agreement_text(d,[])
    for line in text.splitlines():
        line=line.strip()
        if not line:
            story.append(Spacer(1,2.5*mm)); continue
        escaped=html.escape(line)
        if line.isupper() and len(line)<150:
            story.append(Paragraph(escaped, title if len(story)<8 else head))
        else:
            story.append(Paragraph(escaped,body))
    doc.build(story); buf.seek(0); return buf

@app.route('/agreements/<int:aid>/pdf')
@permission_required('agreements')
def agreement_pdf(aid):
    ag=db.session.get(Agreement,aid) or abort(404)
    return send_file(build_agreement_pdf_bytes(ag),mimetype='application/pdf',as_attachment=True,download_name=f"Livenza_Agreement_{ag.id}.pdf")

@app.route('/share/agreement/<token>.pdf')
def shared_agreement_pdf(token):
    try:
        payload=share_serializer().loads(token,max_age=7*24*3600)
        aid=int(payload.get('aid'))
    except (BadSignature,SignatureExpired,ValueError,TypeError):
        abort(404)
    ag=db.session.get(Agreement,aid) or abort(404)
    return send_file(build_agreement_pdf_bytes(ag),mimetype='application/pdf',as_attachment=True,download_name=f"Livenza_Agreement_{ag.id}.pdf")

@app.route('/agreements/<int:aid>/whatsapp')
@permission_required('agreements')
def agreement_whatsapp(aid):
    ag=db.session.get(Agreement,aid) or abort(404)
    d=ag.data; number=normalize_whatsapp_number(d.get('tenant_whatsapp') or d.get('tenant_mobile'))
    if not number:
        flash('A valid tenant WhatsApp number with country code is required before sharing the agreement.','danger')
        return redirect(url_for('agreement_edit',aid=aid))
    token=share_serializer().dumps({'aid':aid})
    share_url=url_for('shared_agreement_pdf',token=token,_external=True,_scheme='https')
    tenant=d.get('tenant_name') or 'Customer'
    message=f"Dear {tenant}, your Livenza agreement is ready. Download the PDF here: {share_url}\n\nThis secure link is valid for 7 days."
    return redirect(f"https://wa.me/{number}?text={urllib.parse.quote(message)}")

@app.route('/agreements/<int:aid>/delete', methods=['POST'])
@permission_required('agreements')
def agreement_delete(aid):
    ag=db.session.get(Agreement,aid) or abort(404)
    Tenant.query.filter_by(agreement_id=aid).update({'agreement_id':None}); db.session.delete(ag); db.session.commit(); flash('Agreement deleted.','success')
    return redirect(url_for('agreements'))

@app.route('/rooms', methods=['GET','POST'])
@permission_required('rooms')
def rooms():
    if request.method=='POST':
        rid=request.form.get('id'); r=db.session.get(Room,int(rid)) if rid else Room()
        if not rid: db.session.add(r)
        for k in ('city','property_name','premises','room_no','room_type','capacity','standard_tariff','status_override','notes'):
            setattr(r,k,request.form.get(k,'').strip())
        db.session.commit(); flash('Room saved.','success'); return redirect(url_for('rooms'))
    allrooms=Room.query.order_by(Room.city,Room.property_name,Room.room_no).all()
    room_rows=[]
    for r in allrooms:
        st=room_status(r); tenant=None
        if st!='Vacant': tenant=Tenant.query.filter_by(property_name=r.property_name,room_unit_no=r.room_no).order_by(Tenant.id.desc()).first()
        room_rows.append((r,st,tenant))
    return render_template('rooms.html', rows=room_rows, cities=City.query.filter_by(active=True).order_by(City.name).all())

@app.route('/tenants', methods=['GET','POST'])
@permission_required('rooms')
def tenants():
    if request.method=='POST':
        tid=request.form.get('id'); t=db.session.get(Tenant,int(tid)) if tid else Tenant()
        if not tid: db.session.add(t)
        for k in ('tenant_name','tenant_mobile','tenant_whatsapp','tenant_email','tenant_id_type','tenant_id_no','city','property_name','premises','room_unit_no','room_type','tariff','security_deposit','joining_date','leaving_date','status','agreement_reference','notes'):
            setattr(t,k,request.form.get(k,'').strip())
        if t.room_unit_no and not Room.query.filter_by(property_name=t.property_name,room_no=t.room_unit_no).first():
            db.session.add(Room(city=t.city,property_name=t.property_name,premises=t.premises,room_no=t.room_unit_no,room_type=t.room_type,standard_tariff=t.tariff))
        db.session.commit(); flash('Tenant saved.','success'); return redirect(url_for('tenants'))
    return render_template('tenants.html',items=Tenant.query.order_by(Tenant.updated_at.desc()).all(),cities=City.query.filter_by(active=True).order_by(City.name).all())

@app.route('/date-calculator', methods=['POST'])
@permission_required('agreements')
def date_calc():
    start=parse_date(request.form.get('start_date')); months=int(request.form.get('months') or 0); days=int(request.form.get('days') or 0)
    if not start: return jsonify(error='Invalid date'),400
    end=start+relativedelta(months=months)+datetime.timedelta(days=days)-datetime.timedelta(days=1)
    return jsonify(end_date=end.isoformat(), start_weekday=start.strftime('%A'), end_weekday=end.strftime('%A'), total_days=(end-start).days+1)

@app.route('/rooms/empty-report.pdf')
@permission_required('rooms')
def empty_rooms_pdf():
    return send_file(generate_empty_rooms_pdf_bytes(),mimetype='application/pdf',as_attachment=True,download_name=f"Livenza_Empty_Rooms_{datetime.date.today().isoformat()}.pdf")

@app.route('/jobs/vacant-room-report', methods=['GET','POST'])
def vacant_room_job():
    token=request.headers.get('X-Livenza-Job-Token') or request.args.get('token','')
    if not os.getenv('VACANT_REPORT_JOB_TOKEN') or token!=os.getenv('VACANT_REPORT_JOB_TOKEN'): abort(401)
    if setting('vacant_report_enabled','0')!='1': return jsonify(ok=True,skipped='disabled')
    now=datetime.datetime.now(ZoneInfo('Asia/Kolkata')); configured=setting('vacant_report_time','08:30')
    try:
        hh,mm=[int(x) for x in configured.split(':')[:2]]
    except Exception:
        hh,mm=8,30
    now_minutes=now.hour*60+now.minute; target_minutes=hh*60+mm
    if abs(now_minutes-target_minutes)>10:
        return jsonify(ok=True,skipped='not scheduled window',now=now.strftime('%H:%M'),scheduled=configured)
    if setting('vacant_report_last_sent','')==now.date().isoformat(): return jsonify(ok=True,skipped='already sent today')
    recipients=[x.strip() for x in setting('vacant_report_recipients','').split(',') if x.strip()]
    if not recipients: return jsonify(ok=False,error='No recipients configured'),400
    pdf=generate_empty_rooms_pdf_bytes(); filename=f'Livenza_Vacant_Rooms_{now.date().isoformat()}.pdf'; media_id=whatsapp_upload_pdf(pdf,filename)
    if not media_id: return jsonify(ok=False,error='WhatsApp Cloud API not configured or media upload failed'),503
    sent=[]
    for num in recipients:
        if whatsapp_send_document(num,media_id,filename,'Livenza Life daily vacant rooms status'): sent.append(num)
    if sent: set_setting('vacant_report_last_sent',now.date().isoformat())
    return jsonify(ok=True,sent=sent,total=len(recipients))


def offline_review(business, business_type, experience, tone, language):
    base=experience.strip() or f"The experience with {business or business_type or 'the business'} was smooth and professionally managed."
    if language=='Hindi':
        return [f"{business or 'यह स्थान'} में मेरा अनुभव अच्छा रहा। {base} सेवा सुव्यवस्थित थी और पूरी प्रक्रिया सहज लगी।", f"{business or 'यह व्यवसाय'} के साथ अनुभव संतोषजनक रहा। {base} टीम का व्यवहार सहयोगी और पेशेवर लगा।", f"कुल मिलाकर {business or 'यहाँ'} का अनुभव सकारात्मक रहा। {base} मैं वास्तविक अनुभव के आधार पर इसे अच्छा विकल्प मानता/मानती हूँ।"]
    return [f"I had a positive experience with {business or business_type}. {base} The process felt organized and professional throughout.", f"A smooth and dependable experience with {business or business_type}. {base} Communication was clear and the overall service was well managed.", f"Overall, my experience with {business or business_type} was very good. {base} I appreciated the professional approach and would consider using the service again."]


def normalize_google_review_url(value):
    value=(value or '').strip()
    if not value:
        return ''
    if not value.lower().startswith(('http://','https://')):
        value='https://' + value
    try:
        u=urllib.parse.urlparse(value)
    except Exception:
        return ''
    host=(u.hostname or '').lower()
    allowed=(
        host == 'g.page' or host.endswith('.g.page') or
        host == 'google.com' or host.endswith('.google.com') or
        host == 'google.co.in' or host.endswith('.google.co.in') or
        host == 'maps.app.goo.gl' or host.endswith('.maps.app.goo.gl')
    )
    if u.scheme not in ('http','https') or not host or not allowed:
        return ''
    return urllib.parse.urlunparse((u.scheme,u.netloc,u.path,u.params,u.query,u.fragment))

@app.route('/reviews/qr.png')
@permission_required('reviews')
def review_qr():
    review_url=normalize_google_review_url(request.args.get('url',''))
    if not review_url:
        abort(400, 'A valid Google Review URL is required.')
    qr=qrcode.QRCode(version=None,error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=10,border=3)
    qr.add_data(review_url); qr.make(fit=True)
    img=qr.make_image(fill_color='black',back_color='white')
    buf=io.BytesIO(); img.save(buf,format='PNG'); buf.seek(0)
    return send_file(buf,mimetype='image/png',download_name='Livenza_Google_Review_QR.png')

def online_reviews(form):
    key=os.getenv('OPENAI_API_KEY','').strip()
    if not key: return None
    from openai import OpenAI
    client=OpenAI(api_key=key)
    prompt=f"""Create exactly 3 distinct Google review drafts based ONLY on the genuine experience details below. Do not invent amenities, staff names, prices, dates, outcomes, or experiences not provided. Make them natural, useful, non-spammy, and different from each other. Business: {form.get('business_name','')}. Industry: {form.get('business_type','')}. Genuine experience: {form.get('experience','')}. Rating context: {form.get('rating','5')}/5. Tone: {form.get('tone','Professional')}. Vocabulary: {form.get('vocabulary','Natural')}. Language: {form.get('language','English')}. Length: {form.get('length','Medium')}. Return only the three reviews separated by a line containing exactly ---REVIEW---."""
    resp=client.responses.create(model=os.getenv('OPENAI_REVIEW_MODEL','gpt-5.6-luna'),input=prompt)
    parts=[p.strip() for p in resp.output_text.split('---REVIEW---') if p.strip()]
    return parts[:3] if parts else None

@app.route('/reviews', methods=['GET','POST'])
@permission_required('reviews')
def reviews():
    generated=[]
    review_url=setting('default_google_review_url','')
    form_data={}
    if request.method=='POST':
        form=request.form.to_dict(); form_data=form
        submitted_url=(form.get('google_review_url') or '').strip()
        review_url=normalize_google_review_url(submitted_url)
        if not review_url:
            flash('Google Business Review Link is mandatory. Paste the direct review-request link before generating reviews or QR codes.','danger')
            hist=Review.query.order_by(Review.created_at.desc()).limit(20).all()
            return render_template('reviews.html',generated=[],history=hist,review_url='',form_data=form_data),400
        if form.get('save_review_link')=='1':
            set_setting('default_google_review_url',review_url)
        try:
            generated=online_reviews(form) or offline_review(form.get('business_name',''),form.get('business_type',''),form.get('experience',''),form.get('tone',''),form.get('language','English'))
        except Exception as e:
            flash(f'Online AI unavailable; offline drafting used. ({e})','warning')
            generated=offline_review(form.get('business_name',''),form.get('business_type',''),form.get('experience',''),form.get('tone',''),form.get('language','English'))
        for out in generated:
            db.session.add(Review(business_name=form.get('business_name',''),business_type=form.get('business_type',''),experience=form.get('experience',''),output=out,language=form.get('language','English'),google_review_url=review_url))
        db.session.commit()
    hist=Review.query.order_by(Review.created_at.desc()).limit(20).all()
    return render_template('reviews.html',generated=generated,history=hist,review_url=review_url,form_data=form_data)

@app.route('/food', methods=['GET','POST'])
@permission_required('food')
def food():
    if request.method=='POST':
        f=request.form
        gross=float(f.get('gross') or 0); commission=float(f.get('commission') or 0); fees=float(f.get('fees') or 0); taxes=float(f.get('taxes') or 0)
        net=float(f.get('net') or (gross-commission-fees-taxes))
        db.session.add(FoodOrder(platform=f.get('platform','Direct'),order_id=f.get('order_id',''),outlet=f.get('outlet',''),customer=f.get('customer',''),order_time=f.get('order_time',''),status=f.get('status','New'),payment_mode=f.get('payment_mode',''),gross=gross,commission=commission,fees=fees,taxes=taxes,net=net,settlement_status=f.get('settlement_status','Pending')))
        db.session.commit(); flash('Order saved.','success'); return redirect(url_for('food'))
    items=FoodOrder.query.order_by(FoodOrder.created_at.desc()).all(); sums=db.session.query(func.sum(FoodOrder.gross),func.sum(FoodOrder.net)).first()
    return render_template('food.html',items=items,total_gross=sums[0] or 0,total_net=sums[1] or 0)

@app.route('/food/import', methods=['POST'])
@permission_required('food')
def food_import():
    file=request.files.get('file')
    if not file: flash('Choose a CSV file.','danger'); return redirect(url_for('food'))
    text=io.TextIOWrapper(file.stream,encoding='utf-8-sig'); reader=csv.DictReader(text); n=0
    for row in reader:
        def num(k):
            try:return float(row.get(k,0) or 0)
            except:return 0
        gross=num('gross'); commission=num('commission'); fees=num('fees'); taxes=num('taxes'); net=num('net') or gross-commission-fees-taxes
        db.session.add(FoodOrder(platform=row.get('platform','Direct'),order_id=row.get('order_id',''),outlet=row.get('outlet',''),customer=row.get('customer',''),order_time=row.get('order_time',''),status=row.get('status','New'),payment_mode=row.get('payment_mode',''),gross=gross,commission=commission,fees=fees,taxes=taxes,net=net,settlement_status=row.get('settlement_status','Pending'))); n+=1
    db.session.commit(); flash(f'Imported {n} orders.','success'); return redirect(url_for('food'))

@app.route('/webhooks/food/<platform>', methods=['POST'])
def food_webhook(platform):
    token=request.headers.get('X-Livenza-Webhook-Token','')
    if not setting('food_webhook_token') or token!=setting('food_webhook_token'): abort(401)
    payload=request.get_json(silent=True) or {}; gross=float(payload.get('gross') or payload.get('amount') or 0)
    db.session.add(FoodOrder(platform=platform.title(),order_id=str(payload.get('order_id','')),outlet=str(payload.get('outlet','')),customer=str(payload.get('customer','')),order_time=str(payload.get('order_time','')),status=str(payload.get('status','New')),payment_mode=str(payload.get('payment_mode','')),gross=gross,net=float(payload.get('net') or gross),settlement_status=str(payload.get('settlement_status','Pending')))); db.session.commit()
    return jsonify(ok=True)

@app.route('/queries', methods=['GET','POST'])
@permission_required('queries')
def queries():
    if request.method=='POST':
        f=request.form; q=QueryLead(source=f.get('source','Manual'),city=f.get('city',''),property_name=f.get('property_name',''),customer_name=f.get('customer_name',''),mobile=f.get('mobile',''),whatsapp=f.get('whatsapp','') or f.get('mobile',''),email=f.get('email',''),query_text=f.get('query_text',''),budget=f.get('budget',''),move_in_date=f.get('move_in_date',''),stay_type=f.get('stay_type',''),status=f.get('status','Live'),heat=f.get('heat','Warm'),score=int(f.get('score') or 50),next_follow_up=f.get('next_follow_up',''),notes=f.get('notes',''))
        au=f.get('assigned_user_id'); q.assigned_user_id=int(au) if au and au.isdigit() else None
        db.session.add(q); db.session.flush(); query_log(q,'Created','Manual query created',current_user()); db.session.commit(); flash('Query added to live queue.','success'); return redirect(url_for('queries'))
    status=request.args.get('status',''); heat=request.args.get('heat',''); source=request.args.get('source',''); term=request.args.get('q','').strip()
    qry=QueryLead.query
    if status: qry=qry.filter_by(status=status)
    if heat: qry=qry.filter_by(heat=heat)
    if source: qry=qry.filter_by(source=source)
    if term: qry=qry.filter(or_(QueryLead.customer_name.ilike(f'%{term}%'),QueryLead.mobile.ilike(f'%{term}%'),QueryLead.query_text.ilike(f'%{term}%'),QueryLead.property_name.ilike(f'%{term}%')))
    items=qry.order_by(QueryLead.updated_at.desc()).all()
    return render_template('queries.html',items=items,templates=QueryTemplate.query.filter_by(active=True).order_by(QueryTemplate.name).all(),users=User.query.filter_by(active=True).order_by(User.full_name,User.username).all(),cities=City.query.filter_by(active=True).order_by(City.name).all(),cloud_whatsapp=whatsapp_cloud_configured())

@app.route('/queries/<int:qid>/update',methods=['POST'])
@permission_required('queries')
def query_update(qid):
    q=db.session.get(QueryLead,qid) or abort(404); f=request.form
    for k in ('source','city','property_name','customer_name','mobile','whatsapp','email','query_text','budget','move_in_date','stay_type','status','heat','next_follow_up','notes'):
        if k in f: setattr(q,k,f.get(k,'').strip())
    try:q.score=max(0,min(100,int(f.get('score') or q.score or 0)))
    except Exception:pass
    au=f.get('assigned_user_id'); q.assigned_user_id=int(au) if au and au.isdigit() else None
    query_log(q,'Updated',f'Status {q.status}; heat {q.heat}',current_user()); db.session.commit(); flash('Query updated.','success'); return redirect(request.referrer or url_for('queries'))

@app.route('/queries/<int:qid>/whatsapp')
@permission_required('queries')
def query_whatsapp(qid):
    q=db.session.get(QueryLead,qid) or abort(404); tid=request.args.get('template'); t=db.session.get(QueryTemplate,int(tid)) if tid and tid.isdigit() else None
    msg=(t.message if t else setting('query_default_message','Dear {name}, thank you for contacting Livenza Life. Our team is reviewing your requirement and will assist you shortly.')).format(name=q.customer_name or 'Guest',property=q.property_name or 'Livenza Life',city=q.city or '')
    number=wa_number(q.whatsapp or q.mobile)
    if not number: flash('Query has no valid WhatsApp number.','danger'); return redirect(url_for('queries'))
    query_log(q,'WhatsApp opened',t.name if t else 'Default message',current_user()); db.session.commit()
    return redirect(f'https://wa.me/{number}?text={urllib.parse.quote(msg)}')

@app.route('/queries/<int:qid>/send-template/<int:tid>',methods=['POST'])
@permission_required('queries')
def query_send_template(qid,tid):
    q=db.session.get(QueryLead,qid) or abort(404); t=db.session.get(QueryTemplate,tid) or abort(404); number=q.whatsapp or q.mobile
    if t.whatsapp_template_name: ok,msg=whatsapp_cloud_template(number,t.whatsapp_template_name)
    else: ok,msg=whatsapp_cloud_text(number,t.message.format(name=q.customer_name or 'Guest',property=q.property_name or 'Livenza Life',city=q.city or ''))
    query_log(q,'WhatsApp template',f'{t.name}: {msg}',current_user()); db.session.commit(); flash(('Message sent.' if ok else msg),('success' if ok else 'warning')); return redirect(url_for('queries'))

@app.route('/queries/export.csv')
@permission_required('queries')
def query_export_csv():
    view=request.args.get('view','all').lower(); qry=QueryLead.query
    if view=='hot': qry=qry.filter_by(heat='Hot')
    elif view=='live': qry=qry.filter(QueryLead.status.in_(['New','Live','Follow-up']))
    rows=qry.order_by(QueryLead.updated_at.desc()).all(); buf=io.StringIO(); w=csv.writer(buf); w.writerow(['ID','Source','City','Property','Customer','Mobile','WhatsApp','Email','Status','Heat','Score','Budget','Move-in','Next Follow-up','Query','Notes'])
    for q in rows:w.writerow([q.id,q.source,q.city,q.property_name,q.customer_name,q.mobile,q.whatsapp,q.email,q.status,q.heat,q.score,q.budget,q.move_in_date,q.next_follow_up,q.query_text,q.notes])
    b=io.BytesIO(buf.getvalue().encode('utf-8-sig')); return send_file(b,mimetype='text/csv',as_attachment=True,download_name=f'Livenza_{view.title()}_Queries_{datetime.date.today()}.csv')

@app.route('/queries/report.pdf')
@permission_required('queries')
def query_report_pdf():
    from reportlab.lib.pagesizes import A4,landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
    view=request.args.get('view','live').lower(); qry=QueryLead.query
    if view=='hot': qry=qry.filter_by(heat='Hot')
    elif view=='live': qry=qry.filter(QueryLead.status.in_(['New','Live','Follow-up']))
    items=qry.order_by(QueryLead.updated_at.desc()).all(); buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=landscape(A4),leftMargin=24,rightMargin=24,topMargin=28,bottomMargin=28); styles=getSampleStyleSheet(); story=[Paragraph(f'LIVENZA LIFE - {view.upper()} QUERIES',styles['Title']),Paragraph(datetime.datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%d %b %Y %I:%M %p IST'),styles['Normal']),Spacer(1,10)]; rows=[['ID','Source','City','Customer','Mobile','Property','Status','Heat','Score','Follow-up']]
    for q in items:rows.append([q.id,q.source,q.city,q.customer_name,q.mobile,q.property_name,q.status,q.heat,q.score,q.next_follow_up])
    t=Table(rows,repeatRows=1,colWidths=[28,60,60,95,75,100,55,45,36,85]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#6d5dfc')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.35,colors.grey),('FONTSIZE',(0,0),(-1,-1),7.5),('VALIGN',(0,0),(-1,-1),'TOP')]));story.append(t);doc.build(story);buf.seek(0);return send_file(buf,mimetype='application/pdf',as_attachment=True,download_name=f'Livenza_{view.title()}_Queries.pdf')

def create_query_from_payload(source,payload):
    d=normalize_query_payload(source,payload); ext=d.get('external_id',''); existing=QueryLead.query.filter_by(source=d['source'],external_id=ext).first() if ext else None
    if existing:return existing,False
    q=QueryLead(**d,raw_json=json.dumps(payload,ensure_ascii=False)[:30000],status='Live',heat='Warm',score=55);db.session.add(q);db.session.flush();query_log(q,'Webhook received',source);auto_reply_for_query(q);db.session.commit();return q,True

@app.route('/webhooks/queries/<source>',methods=['POST'])
def query_webhook(source):
    expected=setting('query_webhook_token','') or os.getenv('QUERY_WEBHOOK_TOKEN',''); supplied=request.headers.get('X-Livenza-Webhook-Token') or request.args.get('token','')
    if not expected or supplied!=expected:abort(401)
    q,created=create_query_from_payload(source,request.get_json(silent=True) or {});return jsonify(ok=True,id=q.id,created=created)

@app.route('/webhooks/google/leads',methods=['POST'])
def google_lead_webhook():
    payload=request.get_json(silent=True) or {}; secret=os.getenv('GOOGLE_LEAD_WEBHOOK_SECRET',''); supplied=str(payload.get('google_key') or request.headers.get('X-Google-Key') or '')
    if secret and supplied!=secret:abort(401)
    q,created=create_query_from_payload('Google',payload);return jsonify(ok=True,id=q.id,created=created)

@app.route('/webhooks/meta/leads',methods=['GET','POST'])
def meta_lead_webhook():
    if request.method=='GET':
        if request.args.get('hub.verify_token')==os.getenv('META_VERIFY_TOKEN',''):return request.args.get('hub.challenge','')
        abort(403)
    payload=request.get_json(silent=True) or {}; token=os.getenv('META_PAGE_ACCESS_TOKEN',''); lead_payload=payload
    try:
        change=payload['entry'][0]['changes'][0]['value']; lead_id=change.get('leadgen_id')
        if lead_id and token:
            ver=os.getenv('META_GRAPH_VERSION','v23.0'); r=requests.get(f'https://graph.facebook.com/{ver}/{lead_id}',params={'access_token':token},timeout=20)
            if r.ok:lead_payload=r.json();lead_payload['leadgen_id']=lead_id
    except Exception:pass
    q,created=create_query_from_payload('Meta',lead_payload);return jsonify(ok=True,id=q.id,created=created)

@app.route('/admin/query-templates/save',methods=['POST'])
@admin_required
def query_template_save():
    tid=request.form.get('id');t=db.session.get(QueryTemplate,int(tid)) if tid else QueryTemplate();
    if not tid:db.session.add(t)
    t.name=request.form.get('name','').strip();t.category=request.form.get('category','General').strip();t.message=request.form.get('message','').strip();t.whatsapp_template_name=request.form.get('whatsapp_template_name','').strip();t.sources_json=json.dumps(request.form.getlist('sources'));t.statuses_json=json.dumps(request.form.getlist('statuses'));t.auto_send=request.form.get('auto_send')=='1';t.active=request.form.get('active')=='1';db.session.commit();flash('Query message template saved.','success');return redirect(url_for('admin_panel')+'#query-templates')

@app.route('/admin/query-templates/<int:tid>/delete',methods=['POST'])
@admin_required
def query_template_delete(tid):
    t=db.session.get(QueryTemplate,tid) or abort(404);db.session.delete(t);db.session.commit();flash('Template deleted.','success');return redirect(url_for('admin_panel')+'#query-templates')

@app.route('/admin/users/<int:uid>/aadhaar-verify',methods=['POST'])
@admin_required
def aadhaar_verify(uid):
    u=db.session.get(User,uid) or abort(404); endpoint=os.getenv('AADHAAR_AUTH_URL','').strip(); token=os.getenv('AADHAAR_AUTH_TOKEN','').strip()
    if not endpoint:
        flash('UIDAI/AUA-KUA authentication provider is not configured. Use UIDAI Paperless Offline e-KYC for offline verification or configure an authorized provider in Render.','warning');return redirect(url_for('admin_panel'))
    aadhaar_or_vid=request.form.get('aadhaar_or_vid','').strip(); otp=request.form.get('otp','').strip()
    try:
        r=requests.post(endpoint,headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},json={'aadhaar_or_vid':aadhaar_or_vid,'otp':otp,'reference':str(u.id)},timeout=30); data=r.json() if r.headers.get('content-type','').startswith('application/json') else {}; verified=bool(data.get('verified') or data.get('success'))
        u.aadhaar_verification_status='Verified' if verified else 'Verification failed';u.aadhaar_verification_method='Authorized AUA/KUA provider';u.aadhaar_verification_ref=str(data.get('reference') or data.get('txn_id') or '')[:180];u.aadhaar_verified_at=datetime.datetime.utcnow() if verified else None;db.session.commit();flash(('Aadhaar verification confirmed by configured provider.' if verified else 'Provider did not confirm Aadhaar verification.'),('success' if verified else 'danger'))
    except Exception as e:flash(f'Aadhaar provider error: {e}','danger')
    return redirect(url_for('admin_panel'))


@app.route('/video-wall')
@permission_required('video_wall')
def video_wall():
    screens=VideoScreen.query.order_by(VideoScreen.city,VideoScreen.location_name,VideoScreen.name).all()
    assets=VideoAsset.query.filter_by(active=True).order_by(VideoAsset.id.desc()).all()
    festive=active_festive_session()
    rows=[]
    for sc in screens:
        
        try: playlist_ids=[int(x) for x in json.loads(sc.playlist_json or '[]')]
        except Exception: playlist_ids=[]
        rows.append({'screen':sc,'online':screen_is_online(sc),'asset':db.session.get(VideoAsset,sc.current_asset_id) if sc.current_asset_id else None,'playlist_ids':playlist_ids,'player_url':url_for('wall_player',token=sc.player_token,_external=True)})
    return render_template('video_wall.html',screens=rows,assets=assets,festive=festive,cities=City.query.filter_by(active=True).order_by(City.name).all(),storage_ready=supabase_storage_configured())

@app.route('/video-wall/assets/upload',methods=['POST'])
@permission_required('video_wall')
def video_wall_asset_upload():
    title=request.form.get('title','').strip()
    external=request.form.get('external_url','').strip()
    if external:
        if not re.match(r'^https?://',external,re.I):
            flash('External media URL must start with http:// or https://','danger'); return redirect(url_for('video_wall'))
        lower=external.lower().split('?')[0]
        mtype='image' if lower.endswith(('.jpg','.jpeg','.png','.webp')) else 'video'
        asset=VideoAsset(title=title or os.path.basename(urllib.parse.urlparse(external).path) or 'External media',media_type=mtype,public_url=external,mime_type='',uploaded_by_user_id=current_user().id)
        db.session.add(asset); db.session.commit(); flash('External media added to the library.','success'); return redirect(url_for('video_wall'))
    f=request.files.get('media_file')
    info,err=upload_video_wall_media(f)
    if err:
        flash(err,'danger'); return redirect(url_for('video_wall'))
    asset=VideoAsset(title=title or f.filename,media_type=info['type'],storage_path=info['path'],public_url=info['url'],mime_type=info['mime'],file_size=info['size'],uploaded_by_user_id=current_user().id)
    db.session.add(asset); db.session.commit(); flash('Media uploaded and ready for screens.','success'); return redirect(url_for('video_wall'))

@app.route('/video-wall/assets/<int:asset_id>/toggle',methods=['POST'])
@permission_required('video_wall')
def video_wall_asset_toggle(asset_id):
    a=db.session.get(VideoAsset,asset_id) or abort(404); a.active=not a.active; db.session.commit(); flash('Media library updated.','success'); return redirect(url_for('video_wall'))

@app.route('/video-wall/screens/save',methods=['POST'])
@permission_required('video_wall')
def video_wall_screen_save():
    sid=request.form.get('id','').strip()
    sc=db.session.get(VideoScreen,int(sid)) if sid.isdigit() else None
    if not sc:
        sc=VideoScreen(name='Screen',player_token=secrets.token_urlsafe(28)); db.session.add(sc)
    sc.name=request.form.get('name','').strip() or sc.name or 'Screen'
    sc.city=request.form.get('city','').strip(); sc.location_name=request.form.get('location_name','').strip(); sc.device_label=request.form.get('device_label','').strip()
    aid=request.form.get('current_asset_id','').strip(); sc.current_asset_id=int(aid) if aid.isdigit() else None
    playlist=[]
    for raw in request.form.getlist('playlist_asset_ids'):
        if str(raw).isdigit() and int(raw) not in playlist: playlist.append(int(raw))
    if not playlist and sc.current_asset_id: playlist=[sc.current_asset_id]
    sc.playlist_json=json.dumps(playlist)
    if playlist: sc.current_asset_id=playlist[0]
    try: sc.rotation_degrees=int(float(request.form.get('rotation_degrees','0') or 0))%360
    except Exception: sc.rotation_degrees=0
    sc.fit_mode=request.form.get('fit_mode','contain') if request.form.get('fit_mode') in ('contain','cover','fill') else 'contain'
    sc.loop_media=request.form.get('loop_media')=='1'; sc.muted=request.form.get('muted')=='1'; sc.enabled=request.form.get('enabled')=='1'
    try: sc.slide_duration_seconds=max(3,min(3600,int(request.form.get('slide_duration_seconds','10') or 10)))
    except Exception: sc.slide_duration_seconds=10
    db.session.commit(); flash('TV / screen configuration saved.','success'); return redirect(url_for('video_wall'))

@app.route('/video-wall/screens/<int:sid>/delete',methods=['POST'])
@permission_required('video_wall')
def video_wall_screen_delete(sid):
    sc=db.session.get(VideoScreen,sid) or abort(404); db.session.delete(sc); db.session.commit(); flash('Screen removed.','success'); return redirect(url_for('video_wall'))

@app.route('/video-wall/festive/start',methods=['POST'])
@permission_required('video_wall')
def video_wall_festive_start():
    aid=request.form.get('asset_id','').strip()
    asset=db.session.get(VideoAsset,int(aid)) if aid.isdigit() else None
    if not asset:
        flash('Choose a festive commercial first.','danger'); return redirect(url_for('video_wall'))
    FestiveSession.query.filter_by(active=True).update({'active':False,'ended_at':datetime.datetime.utcnow()})
    fs=FestiveSession(name=request.form.get('name','').strip() or 'Festive Takeover',asset_id=asset.id,active=True,started_by_user_id=current_user().id,started_at=datetime.datetime.utcnow(),notes=request.form.get('notes','').strip())
    db.session.add(fs); db.session.commit(); flash('Festive takeover is LIVE on every enabled TV.','success'); return redirect(url_for('video_wall'))

@app.route('/video-wall/festive/stop',methods=['POST'])
@permission_required('video_wall')
def video_wall_festive_stop():
    for fs in FestiveSession.query.filter_by(active=True).all(): fs.active=False; fs.ended_at=datetime.datetime.utcnow()
    db.session.commit(); flash('Festive takeover stopped. Screens returned to their individual media.','success'); return redirect(url_for('video_wall'))

@app.route('/wall/<token>')
def wall_player(token):
    sc=VideoScreen.query.filter_by(player_token=token).first() or abort(404)
    return render_template('wall_player.html',screen=sc)

@app.route('/api/wall/<token>/state')
def wall_state(token):
    sc=VideoScreen.query.filter_by(player_token=token).first() or abort(404)
    return jsonify(screen_player_state(sc))

@app.route('/api/wall/<token>/heartbeat',methods=['POST'])
def wall_heartbeat(token):
    sc=VideoScreen.query.filter_by(player_token=token).first() or abort(404)
    sc.last_seen_at=datetime.datetime.utcnow(); sc.last_ip=(request.headers.get('X-Forwarded-For') or request.remote_addr or '')[:120]; db.session.commit()
    return jsonify(ok=True)

@app.route('/billing')
@permission_required('rentok')
def billing(): return render_template('rentok.html',url='https://manager.rentok.com/')

@app.route('/rentok')
def rentok_legacy():
    return redirect(url_for('billing'))

@app.route('/settings', methods=['GET','POST'])
@admin_required
def settings_page():
    keys=('food_webhook_token','whatsapp_recipient','empty_report_time','default_google_review_url','vacant_report_enabled','vacant_report_time','vacant_report_recipients','query_webhook_token')
    if request.method=='POST':
        for k in keys:
            if k in request.form:
                vals=request.form.getlist(k)
                val=(vals[-1] if vals else '').strip()
                if k=='default_google_review_url' and val:
                    val=normalize_google_review_url(val)
                    if not val:
                        flash('Default Google Review Link is invalid.','danger')
                        return redirect(url_for('settings_page'))
                set_setting(k,val)
        flash('Settings saved.','success'); return redirect(url_for('settings_page'))
    return render_template('settings.html',settings={k:setting(k) for k in keys})

@app.route('/admin')
@admin_required
def admin_panel():
    return render_template('admin.html', users=User.query.order_by(User.username).all(), cities=City.query.order_by(City.name).all(), modules=MODULES, query_templates=QueryTemplate.query.order_by(QueryTemplate.id.desc()).all(), aadhaar_provider_configured=bool(os.getenv('AADHAAR_AUTH_URL','').strip()))

@app.route('/admin/users/save', methods=['POST'])
@admin_required
def admin_user_save():
    uid=request.form.get('id')
    u=db.session.get(User,int(uid)) if uid else None
    username=request.form.get('username','').strip()
    if not username:
        flash('Login ID is required.','danger'); return redirect(url_for('admin_panel'))
    if not u:
        if User.query.filter_by(username=username).first():
            flash('That Login ID already exists.','danger'); return redirect(url_for('admin_panel'))
        password=request.form.get('password','')
        if len(password)<8:
            flash('A new user password must contain at least 8 characters.','danger'); return redirect(url_for('admin_panel'))
        u=User(username=username,password_hash=generate_password_hash(password)); db.session.add(u)
    else:
        other=User.query.filter(User.username==username,User.id!=u.id).first()
        if other:
            flash('That Login ID already exists.','danger'); return redirect(url_for('admin_panel'))
        u.username=username
        if request.form.get('password'):
            u.password_hash=generate_password_hash(request.form['password'])
    u.full_name=request.form.get('full_name','').strip()
    if request.files.get('photo') and request.files['photo'].filename:
        data=image_data_uri(request.files['photo'])
        if data: u.photo_data_uri=data
    last4=''.join(ch for ch in request.form.get('aadhaar_last4','') if ch.isdigit())[-4:]
    if last4: u.aadhaar_last4=last4
    if request.form.get('aadhaar_name') is not None: u.aadhaar_name=request.form.get('aadhaar_name','').strip()
    if request.form.get('aadhaar_verification_ref') is not None: u.aadhaar_verification_ref=request.form.get('aadhaar_verification_ref','').strip()
    u.role=request.form.get('role','manager') if request.form.get('role') in ('admin','manager') else 'manager'
    u.active=request.form.get('active')=='1'
    perms=[m for m in MODULES if request.form.get(f'perm_{m}')=='1']
    u.permissions_json=json.dumps(perms)
    db.session.commit(); flash('User access saved.','success'); return redirect(url_for('admin_panel'))

@app.route('/admin/users/<int:uid>/delete', methods=['POST'])
@admin_required
def admin_user_delete(uid):
    u=db.session.get(User,uid) or abort(404)
    if u.id==current_user().id:
        flash('You cannot delete the account currently signed in.','danger')
    else:
        db.session.delete(u); db.session.commit(); flash('User deleted.','success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/cities/save', methods=['POST'])
@admin_required
def admin_city_save():
    cid=request.form.get('id'); c=db.session.get(City,int(cid)) if cid else None
    name=request.form.get('name','').strip()
    if not name:
        flash('City name is required.','danger'); return redirect(url_for('admin_panel'))
    if not c:
        c=City.query.filter(func.lower(City.name)==name.lower()).first()
        if not c: c=City(name=name); db.session.add(c)
    else: c.name=name
    c.code=request.form.get('code','').strip().upper(); c.active=request.form.get('active')=='1'
    db.session.commit(); flash('City saved.','success'); return redirect(url_for('admin_panel'))

@app.route('/admin/cities/<int:cid>/delete', methods=['POST'])
@admin_required
def admin_city_delete(cid):
    c=db.session.get(City,cid) or abort(404); db.session.delete(c); db.session.commit(); flash('City removed.','success'); return redirect(url_for('admin_panel'))


def bootstrap():
    os.makedirs(os.path.join(BASE_DIR,'instance'),exist_ok=True)
    db.create_all()
    if User.query.count()==0:
        username=os.getenv('ADMIN_USERNAME','admin').strip() or 'admin'
        password=os.getenv('ADMIN_PASSWORD','')
        if not password:
            password='ChangeMeNow!2026'
            print('WARNING: ADMIN_PASSWORD was not set. Temporary password: ChangeMeNow!2026')
        db.session.add(User(username=username,password_hash=generate_password_hash(password),role='admin')); db.session.commit()

with app.app_context(): bootstrap()

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.getenv('PORT','5000')),debug=os.getenv('FLASK_DEBUG')=='1')
