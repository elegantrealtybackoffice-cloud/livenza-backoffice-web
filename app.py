import os, io, csv, json, hashlib, hmac, datetime, urllib.parse, html, base64, re, secrets, uuid
from email.message import EmailMessage
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy import func, or_, inspect
from dateutil.relativedelta import relativedelta
import requests
import qrcode
from PIL import Image as PILImage
from zoneinfo import ZoneInfo

from agreement_core import PRESETS, DEFAULTS, FIELDS, FORMAT_PROFILES, build_agreement_text, build_agreement_text_hindi

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_VERSION = 'Web 1.5.5'
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-this-secret-before-production')
raw_db = os.getenv('DATABASE_URL', '')
if raw_db.startswith('postgres://'):
    raw_db = raw_db.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = raw_db or ('sqlite:///' + os.path.join(BASE_DIR, 'instance', 'livenza_web.db'))
# Render + Supabase Session Pooler resilience. pool_pre_ping prevents the first
# navigation after an idle/stale pooled connection from throwing a transient 500.
if raw_db.startswith('postgresql'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 180,
        'pool_timeout': 20,
        'pool_size': 3,
        'max_overflow': 3,
        'pool_use_lifo': True,
    }
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
    pattern_hash = db.Column(db.Text, default='')
    webauthn_enabled = db.Column(db.Boolean, default=False)
    webauthn_enrolled_at = db.Column(db.DateTime, nullable=True)
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


class FoodIntegration(db.Model):
    __tablename__ = 'food_integration'
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(60), nullable=False, default='Other')
    display_name = db.Column(db.String(160), default='')
    outlet_id = db.Column(db.String(180), default='')
    account_identifier = db.Column(db.String(180), default='')
    portal_url = db.Column(db.Text, default='')
    developer_url = db.Column(db.Text, default='')
    api_base_url = db.Column(db.Text, default='')
    api_token_env = db.Column(db.String(120), default='')
    api_key_env = db.Column(db.String(120), default='')
    webhook_enabled = db.Column(db.Boolean, default=True)
    api_enabled = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    last_sync_at = db.Column(db.DateTime, nullable=True)
    last_sync_status = db.Column(db.Text, default='')
    last_sync_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


OFFICIAL_FOOD_PORTALS = {
    'Swiggy': {
        'portal_url': 'https://partner.swiggy.com/login',
        'developer_url': 'https://developers.swiggy.com/login',
    },
    'Zomato': {
        'portal_url': 'https://www.zomato.com/partners/onlineordering/orders/',
        'developer_url': 'https://www.zomato.com/business/merchant-app',
    },
    'Toing': {
        'portal_url': 'https://www.toingit.com/',
        'developer_url': '',
    },
}

STALE_FOOD_PORTAL_URLS = {
    'https://partner.swiggy.com/v2/': OFFICIAL_FOOD_PORTALS['Swiggy']['portal_url'],
    'https://partner.swiggy.com/v2': OFFICIAL_FOOD_PORTALS['Swiggy']['portal_url'],
    'https://www.zomato.com/partners': OFFICIAL_FOOD_PORTALS['Zomato']['portal_url'],
    'https://www.zomato.com/partners/': OFFICIAL_FOOD_PORTALS['Zomato']['portal_url'],
}


def ensure_default_food_integrations():
    # Seed the three official starting portals only for a brand-new database.
    # Once the user has configured/removed integrations, respect that choice.
    if FoodIntegration.query.count():
        # Upgrade only obsolete built-in URLs; never overwrite a custom portal.
        changed=False
        for row in FoodIntegration.query.all():
            replacement=STALE_FOOD_PORTAL_URLS.get((row.portal_url or '').strip())
            if replacement:
                row.portal_url=replacement;changed=True
        if changed: db.session.commit()
        return
    for platform,urls in OFFICIAL_FOOD_PORTALS.items():
        db.session.add(FoodIntegration(
            platform=platform,
            display_name=f'{platform} Restaurant Partner',
            portal_url=urls.get('portal_url',''),
            developer_url=urls.get('developer_url',''),
            webhook_enabled=True,
            active=True,
        ))
    db.session.commit()


def _food_float(value):
    try:
        if isinstance(value,str): value=value.replace(',','').replace('₹','').strip()
        return float(value or 0)
    except Exception:
        return 0.0


def _food_get(row, *keys, default=''):
    if not isinstance(row,dict): return default
    for key in keys:
        cur=row
        ok=True
        for part in str(key).split('.'):
            if isinstance(cur,dict) and part in cur:
                cur=cur.get(part)
            else:
                ok=False;break
        if ok and cur not in (None,''):
            return cur
    return default


def _food_records(payload):
    if isinstance(payload,list): return [x for x in payload if isinstance(x,dict)]
    if not isinstance(payload,dict): return []
    for key in ('orders','records','results','items','data'):
        val=payload.get(key)
        if isinstance(val,list): return [x for x in val if isinstance(x,dict)]
        if isinstance(val,dict):
            for nested in ('orders','records','results','items','data'):
                n=val.get(nested)
                if isinstance(n,list): return [x for x in n if isinstance(x,dict)]
    return [payload]


def _upsert_food_order(platform, row, default_outlet=''):
    platform=(platform or 'Direct').strip()[:50]
    order_id=str(_food_get(row,'order_id','orderId','orderID','id','order.id','order.uuid',default=''))[:120]
    outlet=str(_food_get(row,'outlet','outlet_name','restaurant_name','restaurant.name','store.name',default=default_outlet))[:180]
    customer=str(_food_get(row,'customer','customer_name','customer.name','user.name',default=''))[:180]
    order_time=str(_food_get(row,'order_time','ordered_at','created_at','createdAt','order.created_at',default=''))[:60]
    status=str(_food_get(row,'status','order_status','order.status',default='New'))[:50]
    payment_mode=str(_food_get(row,'payment_mode','paymentMode','payment.method','payment_type',default=''))[:50]
    gross=_food_float(_food_get(row,'gross','amount','order_total','orderTotal','total','bill.total','order.amount',default=0))
    commission=_food_float(_food_get(row,'commission','commission_amount','charges.commission',default=0))
    fees=_food_float(_food_get(row,'fees','fee','platform_fee','charges.fees',default=0))
    taxes=_food_float(_food_get(row,'taxes','tax','gst','charges.taxes',default=0))
    net=_food_float(_food_get(row,'net','net_amount','netAmount','settlement_amount','payout_amount',default=0))
    if not net: net=gross-commission-fees-taxes
    settlement=str(_food_get(row,'settlement_status','settlementStatus','payout_status',default='Pending'))[:50]
    obj=None
    if order_id:
        obj=FoodOrder.query.filter(func.lower(FoodOrder.platform)==platform.lower(),FoodOrder.order_id==order_id).first()
    if not obj:
        obj=FoodOrder(platform=platform,order_id=order_id)
        db.session.add(obj)
    obj.outlet=outlet;obj.customer=customer;obj.order_time=order_time;obj.status=status;obj.payment_mode=payment_mode
    obj.gross=gross;obj.commission=commission;obj.fees=fees;obj.taxes=taxes;obj.net=net;obj.settlement_status=settlement
    return obj


def _ingest_food_payload(platform,payload,default_outlet=''):
    rows=_food_records(payload);count=0
    for row in rows:
        _upsert_food_order(platform,row,default_outlet=default_outlet);count+=1
    if count: db.session.commit()
    return count


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

class WebAuthnCredential(db.Model):
    __tablename__ = 'web_authn_credential'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    credential_id = db.Column(db.LargeBinary, unique=True, nullable=False)
    public_key = db.Column(db.LargeBinary, nullable=False)
    sign_count = db.Column(db.BigInteger, default=0, nullable=False)
    transports = db.Column(db.Text, default='[]')
    device_name = db.Column(db.String(180), default='Windows Hello / fingerprint')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)

class WhatsAppMessage(db.Model):
    __tablename__ = 'whatsapp_message'
    id = db.Column(db.Integer, primary_key=True)
    direction = db.Column(db.String(12), nullable=False, default='outbound')
    contact_name = db.Column(db.String(180), default='')
    wa_id = db.Column(db.String(40), nullable=False, default='', index=True)
    message_id = db.Column(db.String(220), unique=True, nullable=True)
    message_type = db.Column(db.String(40), default='text')
    body = db.Column(db.Text, default='')
    status = db.Column(db.String(40), default='sent')
    raw_json = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

class DriveFile(db.Model):
    __tablename__ = 'drive_file'
    id = db.Column(db.Integer, primary_key=True)
    provider_file_id = db.Column(db.String(220), unique=True, nullable=False)
    name = db.Column(db.String(300), nullable=False)
    mime_type = db.Column(db.String(180), default='application/octet-stream')
    file_size = db.Column(db.BigInteger, default=0)
    web_view_link = db.Column(db.Text, default='')
    source = db.Column(db.String(80), default='manual')
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
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


GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
]

def _integration_cipher():
    """Encrypt provider refresh tokens at rest; biometrics are never stored here."""
    from cryptography.fernet import Fernet
    configured=os.getenv('INTEGRATION_ENCRYPTION_KEY','').strip()
    if configured:
        try: return Fernet(configured.encode('ascii'))
        except Exception:
            derived=base64.urlsafe_b64encode(hashlib.sha256(configured.encode()).digest())
            return Fernet(derived)
    derived=base64.urlsafe_b64encode(hashlib.sha256(str(app.config['SECRET_KEY']).encode()).digest())
    return Fernet(derived)

def _encrypted_setting_get(key):
    raw=setting(key,'')
    if not raw: return ''
    try: return _integration_cipher().decrypt(raw.encode('ascii')).decode('utf-8')
    except Exception: return ''

def _encrypted_setting_set(key, value):
    set_setting(key,_integration_cipher().encrypt(value.encode('utf-8')).decode('ascii') if value else '')

def google_oauth_configured():
    return bool(os.getenv('GOOGLE_CLIENT_ID','').strip() and os.getenv('GOOGLE_CLIENT_SECRET','').strip())

def google_connected():
    return bool(_encrypted_setting_get('google_oauth_token'))

def _google_token_data(refresh=True):
    raw=_encrypted_setting_get('google_oauth_token')
    if not raw: return {}
    try: data=json.loads(raw)
    except Exception: return {}
    expires=float(data.get('expires_at') or 0)
    if refresh and (not data.get('access_token') or expires < datetime.datetime.utcnow().timestamp()+90):
        refresh_token=data.get('refresh_token')
        if not (refresh_token and google_oauth_configured()): return {}
        try:
            r=requests.post('https://oauth2.googleapis.com/token',data={
                'client_id':os.getenv('GOOGLE_CLIENT_ID','').strip(),
                'client_secret':os.getenv('GOOGLE_CLIENT_SECRET','').strip(),
                'refresh_token':refresh_token,'grant_type':'refresh_token'
            },timeout=25)
            if not r.ok: return {}
            fresh=r.json(); data.update(fresh); data['refresh_token']=refresh_token
            data['expires_at']=datetime.datetime.utcnow().timestamp()+int(fresh.get('expires_in') or 3600)
            _encrypted_setting_set('google_oauth_token',json.dumps(data))
        except Exception: return {}
    return data

def _google_headers():
    token=_google_token_data().get('access_token','')
    return {'Authorization':f'Bearer {token}'} if token else {}

def ensure_google_drive_folder():
    existing=(setting('google_drive_folder_id','') or os.getenv('GOOGLE_DRIVE_FOLDER_ID','')).strip()
    if existing: return existing
    headers=_google_headers()
    if not headers: return ''
    try:
        r=requests.post('https://www.googleapis.com/drive/v3/files',headers=dict(headers,**{'Content-Type':'application/json'}),params={'fields':'id'},json={'name':'Livenza Back Office','mimeType':'application/vnd.google-apps.folder'},timeout=25)
        if r.ok and r.json().get('id'):
            set_setting('google_drive_folder_id',r.json()['id']); return r.json()['id']
    except Exception: pass
    return ''

def google_drive_upload_bytes(data, filename, mime_type='application/octet-stream', source='manual', uploaded_by=None):
    """Upload through Drive's resumable API and keep non-secret metadata locally."""
    headers=_google_headers()
    if not headers: return None, 'Connect Google in Admin first.'
    folder=ensure_google_drive_folder()
    metadata={'name':filename}
    if folder: metadata['parents']=[folder]
    init_headers=dict(headers,**{'Content-Type':'application/json; charset=UTF-8','X-Upload-Content-Type':mime_type,'X-Upload-Content-Length':str(len(data))})
    try:
        start=requests.post('https://www.googleapis.com/upload/drive/v3/files',params={'uploadType':'resumable','fields':'id,name,mimeType,size,webViewLink'},headers=init_headers,json=metadata,timeout=25)
        if not start.ok or not start.headers.get('Location'):
            return None, f'Drive upload could not start ({start.status_code}): {start.text[:300]}'
        put=requests.put(start.headers['Location'],headers={'Content-Type':mime_type,'Content-Length':str(len(data))},data=data,timeout=180)
        if not put.ok: return None, f'Drive upload failed ({put.status_code}): {put.text[:300]}'
        info=put.json()
        row=DriveFile.query.filter_by(provider_file_id=info.get('id','')).first()
        if not row:
            row=DriveFile(provider_file_id=info.get('id',''),name=info.get('name') or filename)
            db.session.add(row)
        row.name=info.get('name') or filename; row.mime_type=info.get('mimeType') or mime_type
        row.file_size=int(info.get('size') or len(data)); row.web_view_link=info.get('webViewLink') or ''
        row.source=source; row.uploaded_by_user_id=(uploaded_by.id if uploaded_by else None)
        db.session.commit()
        return row, ''
    except Exception as exc:
        db.session.rollback(); return None, f'Drive upload failed: {exc}'

def _pattern_value(value):
    nodes=[]
    for part in str(value or '').split('-'):
        if part.isdigit() and 0 <= int(part) <= 8 and part not in nodes: nodes.append(part)
    return '-'.join(nodes) if len(nodes)>=4 else ''

def _b64url_decode(value):
    value=str(value or '')
    return base64.urlsafe_b64decode(value+'='*((4-len(value)%4)%4))

def _webauthn_context():
    rp_id=os.getenv('WEBAUTHN_RP_ID','').strip() or request.host.split(':')[0]
    origin=os.getenv('WEBAUTHN_ORIGIN','').strip() or request.host_url.rstrip('/')
    return rp_id,origin

MARKET_QUOTE_CACHE = {}
WEATHER_CACHE = {}

COMPANION_LOCATIONS = {
    'Gurugram': (28.4595, 77.0266),
    'Jaipur': (26.9124, 75.7873),
    'Delhi': (28.6139, 77.2090),
    'Mumbai': (19.0760, 72.8777),
    'Bengaluru': (12.9716, 77.5946),
}

COMPANION_QUOTES = [
    'Small improvements become remarkable systems.',
    'Hospitality is care made visible.',
    'A calm workspace creates confident decisions.',
    'Consistency turns everyday service into a trusted brand.',
    'Make the next useful move, then make it beautifully.',
    'Great operations feel effortless because the details are intentional.',
    'Today is a good day to make someone feel at home.',
    'Progress grows wherever attention and action meet.',
]

def _weather_description(code):
    code=int(code or 0)
    if code==0: return 'Clear sky'
    if code in (1,2): return 'Partly cloudy'
    if code==3: return 'Overcast'
    if code in (45,48): return 'Foggy'
    if code in (51,53,55,56,57): return 'Light drizzle'
    if code in (61,63,65,66,67): return 'Rain'
    if code in (71,73,75,77,85,86): return 'Snow'
    if code in (80,81,82): return 'Rain showers'
    if code in (95,96,99): return 'Thunderstorm'
    return 'Changing weather'

def _weather_effect(code, is_day=True):
    code=int(code or 0)
    if code in (95,96,99): return 'storm'
    if code in (51,53,55,56,57,61,63,65,66,67,80,81,82): return 'rain'
    if code in (71,73,75,77,85,86): return 'snow'
    if code in (45,48): return 'fog'
    if code in (1,2,3): return 'clouds'
    return 'sun' if is_day else 'night'

def _companion_weather(city):
    city=next((name for name in COMPANION_LOCATIONS if name.lower()==str(city or '').strip().lower()),None) or 'Gurugram'
    latitude,longitude=COMPANION_LOCATIONS[city]
    if city==setting('companion_default_city','Gurugram'):
        try:
            latitude=float(os.getenv('WEATHER_LATITUDE',latitude));longitude=float(os.getenv('WEATHER_LONGITUDE',longitude))
        except (TypeError,ValueError): pass
    now=datetime.datetime.utcnow().timestamp();cached=WEATHER_CACHE.get(city)
    if cached and now-cached['at']<600: return cached['value']
    params={
        'latitude':latitude,'longitude':longitude,
        'current':'temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,weather_code,wind_speed_10m',
        'daily':'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max',
        'timezone':'Asia/Kolkata','forecast_days':4,
    }
    try:
        response=requests.get('https://api.open-meteo.com/v1/forecast',params=params,headers={'User-Agent':'LivenzaLife-OperationsCloud/1.5.5'},timeout=10)
        response.raise_for_status();payload=response.json();current=payload.get('current') or {};daily=payload.get('daily') or {}
        code=int(current.get('weather_code') or 0);is_day=bool(int(current.get('is_day',1) or 0))
        dates=daily.get('time') or [];codes=daily.get('weather_code') or [];highs=daily.get('temperature_2m_max') or [];lows=daily.get('temperature_2m_min') or [];rain_chance=daily.get('precipitation_probability_max') or []
        forecast=[]
        for index,date in enumerate(dates[:4]):
            day_code=int(codes[index] if index<len(codes) else 0)
            forecast.append({
                'date':date,'condition':_weather_description(day_code),'effect':_weather_effect(day_code,True),
                'high':round(float(highs[index])) if index<len(highs) and highs[index] is not None else None,
                'low':round(float(lows[index])) if index<len(lows) and lows[index] is not None else None,
                'rain_chance':round(float(rain_chance[index])) if index<len(rain_chance) and rain_chance[index] is not None else 0,
            })
        value={
            'available':True,'city':city,'temperature':round(float(current.get('temperature_2m') or 0)),
            'feels_like':round(float(current.get('apparent_temperature') or current.get('temperature_2m') or 0)),
            'humidity':round(float(current.get('relative_humidity_2m') or 0)),
            'wind':round(float(current.get('wind_speed_10m') or 0)),
            'precipitation':round(float(current.get('precipitation') or 0),1),
            'condition':_weather_description(code),'effect':_weather_effect(code,is_day),'is_day':is_day,
            'forecast':forecast,'source':'Open-Meteo','updated_at':current.get('time') or datetime.datetime.now(ZoneInfo('Asia/Kolkata')).isoformat(),
        }
        WEATHER_CACHE[city]={'at':now,'value':value};return value
    except Exception:
        return {'available':False,'city':city,'temperature':None,'condition':'Weather temporarily unavailable','effect':'none','forecast':[],'source':'Open-Meteo'}

def _companion_operations():
    try:
        active=Tenant.query.filter(~Tenant.status.in_(['Vacated','Cancelled','Terminated'])).count()
        beds=0
        for room in Room.query.all():
            if room_status(room)=='Vacant':
                try: beds+=max(1,int(float(room.capacity or 1)))
                except Exception: beds+=1
        earned=float(db.session.query(func.coalesce(func.sum(FoodOrder.net),0)).scalar() or 0)
        hot=QueryLead.query.filter_by(heat='Hot').count()
        return [
            {'label':'Current tenants','value':str(active),'tone':'green','icon':'◉'},
            {'label':'Vacant beds','value':str(beds),'tone':'gold','icon':'▦'},
            {'label':'Amount earned','value':'₹'+format(earned,',.0f'),'tone':'blue','icon':'₹'},
            {'label':'Hot queries','value':str(hot),'tone':'pink','icon':'◎'},
        ]
    except Exception:
        db.session.rollback();return []

def _moneycontrol_quote(label, url):
    """Small, cached, fail-soft reader for a user-selected official Moneycontrol quote page."""
    parsed=urllib.parse.urlparse(url)
    host=(parsed.hostname or '').lower()
    if parsed.scheme!='https' or not (host=='moneycontrol.com' or host.endswith('.moneycontrol.com')):
        return None
    cached=MARKET_QUOTE_CACHE.get(url); now=datetime.datetime.utcnow().timestamp()
    if cached and now-cached['at']<120: return cached['value']
    try:
        r=requests.get(url,headers={'User-Agent':'Mozilla/5.0 (compatible; LivenzaBackOffice/1.5; +https://www.moneycontrol.com/)'},timeout=12)
        if not r.ok: return None
        raw=r.text
        price=''
        for pattern in (
            r'id=["\'](?:nsecp|bsecp)["\'][^>]*>\s*([0-9][0-9,.]*)',
            r'class=["\'][^"\']*(?:inprice1|lastprice)[^"\']*["\'][^>]*>\s*([0-9][0-9,.]*)',
            r'["\'](?:lastPrice|last_price|price)["\']\s*:\s*["\']?([0-9][0-9,.]*)',
        ):
            m=re.search(pattern,raw,re.I)
            if m: price=m.group(1); break
        if not price: return None
        change=''
        for pattern in (r'id=["\'](?:nsechange|bsechange)["\'][^>]*>\s*([^<]{1,40})',r'["\'](?:percentChange|pChange)["\']\s*:\s*["\']?([-+0-9.]+)'):
            m=re.search(pattern,raw,re.I)
            if m: change=re.sub(r'<[^>]+>','',m.group(1)).strip(); break
        value={'label':label[:40],'value':price+((f' ({change}%)' if change and '%' not in change else f' ({change})') if change else ''),'url':url,'source':'Moneycontrol'}
        MARKET_QUOTE_CACHE[url]={'at':now,'value':value}; return value
    except Exception: return None

def live_marquee_items(user=None):
    user=user or current_user(); items=[]
    if setting('marquee_show_username','1')=='1' and user:
        items.append({'label':'Signed in','value':user.full_name or user.username,'tone':'blue'})
    if setting('marquee_show_tenants','1')=='1':
        active=Tenant.query.filter(~Tenant.status.in_(['Vacated','Cancelled','Terminated'])).count()
        items.append({'label':'Current tenants','value':str(active),'tone':'green'})
    rooms=Room.query.all()
    if setting('marquee_show_vacant_beds','1')=='1':
        vacant=[r for r in rooms if room_status(r)=='Vacant']; beds=0
        for r in vacant:
            try: beds+=max(1,int(float(r.capacity or 1)))
            except Exception: beds+=1
        items.append({'label':'Vacant beds','value':str(beds),'tone':'gold'})
    if setting('marquee_show_earnings','1')=='1':
        earned=float(db.session.query(func.coalesce(func.sum(FoodOrder.net),0)).scalar() or 0)
        manual=setting('marquee_manual_earnings','').strip()
        items.append({'label':'Amount earned','value':manual or ('₹'+format(earned,',.0f')),'tone':'green'})
    if setting('marquee_show_favorites','0')=='1' and setting('marquee_favorites','').strip():
        items.append({'label':'Favourites','value':setting('marquee_favorites','').strip()[:180],'tone':'pink'})
    if setting('marquee_custom_text','').strip():
        items.append({'label':'Live update','value':setting('marquee_custom_text','').strip()[:240],'tone':'blue'})
    if setting('marquee_show_stocks','0')=='1':
        configured=setting('marquee_stock_pages','').splitlines()
        if not configured:
            configured=['NIFTY 50|https://www.moneycontrol.com/indian-indices/nifty-50-9.html','SENSEX|https://www.moneycontrol.com/indian-indices/sensex-4.html']
        for line in configured[:5]:
            label,sep,url=line.partition('|')
            quote=_moneycontrol_quote(label.strip() or 'Market',url.strip()) if sep else None
            if quote: quote['tone']='market'; items.append(quote)
    return items



MODULES = {
    'agreements': 'Agreement Studio',
    'rooms': 'Room Status & Tenants',
    'reviews': 'Google Review Generator',
    'food': 'Food Delivery Hub',
    'rentok': 'Livenza Billing Suite',
    'queries': 'Live Queries Manager',
    'video_wall': 'Video Wall Studio',
    'whatsapp': 'WhatsApp Workspace',
    'email': 'Email Workspace',
    'drive': 'Google Drive Files',
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
    if not r.ok: return False,r.text[:800]
    try: return True,str((r.json().get('messages') or [{}])[0].get('id') or 'Sent')
    except Exception: return True,'Sent'

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
        drive_warning=''
        if setting('google_drive_auto_backup','0')=='1' and google_connected():
            _,drive_warning=google_drive_upload_bytes(data,file_storage.filename or os.path.basename(path),mime,source='video-wall',uploaded_by=current_user())
        return {'path':path,'url':public,'size':size,'mime':mime,'type':('image' if mime.startswith('image/') else 'video'),'drive_backup_error':drive_warning}, ''
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
        current_user=current_user(), app_version=APP_VERSION,
        can_access=can_access, module_labels=MODULES,
        is_admin=bool(current_user() and (current_user().role or '').lower()=='admin'), masked_aadhaar=masked_aadhaar,
        kiosk_mode_enabled=setting('kiosk_mode_enabled','0')=='1', marquee_enabled=setting('marquee_enabled','1')=='1',
        companion_enabled=setting('companion_enabled','1')=='1', companion_default_city=setting('companion_default_city','Gurugram'),
        companion_weather_effects=setting('companion_weather_effects','1')=='1'
    )

@app.before_request
def enforce_kiosk_pin_gate():
    """Server-side gate for every authenticated page while application lock is enabled."""
    if not session.get('uid') or setting('kiosk_mode_enabled','0')!='1' or session.get('kiosk_unlocked'):
        return None
    allowed={'kiosk_lock','kiosk_unlock','logout','health','version','static'}
    if request.endpoint not in allowed:
        return redirect(url_for('kiosk_lock',next=request.full_path.rstrip('?')))

@app.route('/kiosk')
@login_required
def kiosk_lock():
    if setting('kiosk_mode_enabled','0')!='1' or session.get('kiosk_unlocked'):
        return redirect(url_for('dashboard'))
    return render_template('kiosk_lock.html')

@app.route('/kiosk/unlock',methods=['POST'])
@login_required
def kiosk_unlock():
    u=current_user(); secret=request.form.get('secret','')
    now=datetime.datetime.utcnow().timestamp(); attempts=int(session.get('kiosk_failed_attempts') or 0); last=float(session.get('kiosk_failed_at') or 0)
    if attempts>=5 and now-last<60:
        flash('Too many unlock attempts. Wait one minute and try again.','danger'); return redirect(url_for('kiosk_lock'))
    if now-last>=60: attempts=0
    pin_hash=setting('kiosk_pin_hash','')
    valid=bool((pin_hash and check_password_hash(pin_hash,secret)) or check_password_hash(u.password_hash,secret))
    if not valid:
        session['kiosk_failed_attempts']=attempts+1; session['kiosk_failed_at']=now
        flash('Incorrect kiosk PIN or account password.','danger'); return redirect(url_for('kiosk_lock'))
    session.pop('kiosk_failed_attempts',None); session.pop('kiosk_failed_at',None)
    session['kiosk_unlocked']=True
    target=request.form.get('next','')
    return redirect(target if target.startswith('/') and not target.startswith('//') else url_for('dashboard'))

@app.route('/kiosk/lock',methods=['POST'])
@login_required
def kiosk_relock():
    if setting('kiosk_mode_enabled','0')=='1':
        session['kiosk_unlocked']=False
        return redirect(url_for('kiosk_lock'))
    return redirect(url_for('dashboard'))

@app.route('/health')
def health(): return jsonify(status='ok', service='livenza-back-office-web', version=APP_VERSION)

@app.after_request
def livenza_no_cache(response):
    # Back Office is an operational web app. During active deployment cycles we
    # deliberately prevent stale HTML/CSS/JS from masking a successful release.
    if request.path.startswith('/static/') or response.mimetype in ('text/html','text/css','application/javascript','text/javascript'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    response.headers['X-Livenza-Build'] = APP_VERSION
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'publickey-credentials-get=(self)'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

@app.teardown_request
def livenza_request_cleanup(exc=None):
    # Flask-SQLAlchemy removes sessions at app-context teardown. Rolling back on
    # failed requests ensures a broken transaction never poisons the next page.
    if exc is not None:
        try:
            db.session.rollback()
        except Exception:
            pass

@app.route('/diagnostics')
def diagnostics():
    route_names = {rule.endpoint for rule in app.url_map.iter_rules()}
    checks = {
        'version': APP_VERSION,
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
def version(): return jsonify(version=APP_VERSION, features=['liquid-glass','live-queries','identity','vacant-room-automation','pwa-icons','aadhaar-agreement-autofill','sticky-footer','optional-agreement-fields','apple-inspired-light-theme','video-wall-studio','multi-screen-player','festive-takeover','fullscreen-control','view-rotation-control','livenza-billing-suite','verified-deploy-marker','no-cache-assets','video-wall-diagnostics','apple-system-typography','enhanced-motion','rotation-popover-fix','database-navigation-resilience','fullscreen-stability','fullscreen-navigation-fix','live-motion-layer','clean-brand-header','white-menu-lock','aligned-top-navigation','unified-view-menu','footer-credit-lock','professional-motion-transitions','reference-style-clean-header','operations-dropdown','operations-cloud-marquee','profile-dropdown','absolute-white-theme-lock','agreement-light-accordions','embedded-help-assistant','persistent-chat-close-control','secure-food-portal-launcher','query-spreadsheet','fullscreen-inplace-navigation','livenza-easter-egg','touch-ripple-microinteractions','windows-kiosk-pin-gate','windows-login-launcher','whatsapp-cloud-workspace','gmail-workspace','google-drive-storage','pattern-login','webauthn-passkeys','configurable-live-status-marquee','moneycontrol-market-watch','hanging-logo-header','applications-mega-menu','animated-tab-art','stable-header-logo','plain-header-logo','ai-light-orbit','transparent-scroll-header','contextual-visual-ribbons','login-welcome-mascot','one-time-login-animation','translucent-workspace-shell','sitewide-glass-material','photographic-depth-background','persistent-live-mascot','live-weather-forecast','transient-weather-scenes','mascot-operational-updates','motivational-quote-companion','floating-star-motion'])

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=User.query.filter_by(username=request.form.get('username','').strip()).first()
        method=request.form.get('auth_method','password')
        valid=False
        if u and u.active and method=='pattern' and u.pattern_hash:
            pattern=_pattern_value(request.form.get('pattern',''))
            valid=bool(pattern and check_password_hash(u.pattern_hash,'pattern:'+pattern))
        elif u and u.active:
            valid=check_password_hash(u.password_hash, request.form.get('password',''))
        if valid:
            session.clear(); session['uid']=u.id
            session['kiosk_unlocked']=setting('kiosk_mode_enabled','0')!='1'
            session['show_login_welcome']=True
            return redirect(url_for('kiosk_lock') if not session['kiosk_unlocked'] else (request.args.get('next') or url_for('dashboard')))
        flash('Invalid login ID, password/pattern or inactive account.', 'danger')
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
    show_login_welcome=bool(session.pop('show_login_welcome',False))
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
    return render_template('dashboard.html', stats=stats, cities=city_rows, permissions=user_permissions(), show_login_welcome=show_login_welcome)

@app.route('/api/marquee')
@login_required
def marquee_status():
    try: refresh=max(30,min(600,int(setting('marquee_refresh_seconds','60') or 60)))
    except Exception: refresh=60
    return jsonify(ok=True,items=live_marquee_items(),refresh_seconds=refresh,updated_at=datetime.datetime.now(ZoneInfo('Asia/Kolkata')).isoformat())

@app.route('/api/companion/pulse')
@login_required
def companion_pulse():
    enabled=setting('companion_enabled','1')=='1'
    requested_city=request.args.get('city',setting('companion_default_city','Gurugram'))
    city=next((name for name in COMPANION_LOCATIONS if name.lower()==str(requested_city or '').strip().lower()),None) or setting('companion_default_city','Gurugram')
    if city not in COMPANION_LOCATIONS: city='Gurugram'
    weather=_companion_weather(city) if setting('companion_weather_enabled','1')=='1' else {'available':False,'city':city,'effect':'none','forecast':[]}
    try: effect_seconds=max(7,min(20,int(setting('companion_effect_seconds','11') or 11)))
    except Exception: effect_seconds=11
    return jsonify(
        ok=True,enabled=enabled,weather=weather,
        weather_effects=setting('companion_weather_effects','1')=='1',effect_seconds=effect_seconds,
        operations=_companion_operations() if setting('companion_operations_enabled','1')=='1' else [],
        quotes=COMPANION_QUOTES if setting('companion_quotes_enabled','1')=='1' else [],
        locations=list(COMPANION_LOCATIONS.keys()),refresh_seconds=600,
        updated_at=datetime.datetime.now(ZoneInfo('Asia/Kolkata')).isoformat(),
    )

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
    ensure_default_food_integrations()
    if request.method=='POST':
        f=request.form
        gross=_food_float(f.get('gross')); commission=_food_float(f.get('commission')); fees=_food_float(f.get('fees')); taxes=_food_float(f.get('taxes'))
        net=_food_float(f.get('net')) or (gross-commission-fees-taxes)
        db.session.add(FoodOrder(platform=f.get('platform','Direct'),order_id=f.get('order_id',''),outlet=f.get('outlet',''),customer=f.get('customer',''),order_time=f.get('order_time',''),status=f.get('status','New'),payment_mode=f.get('payment_mode',''),gross=gross,commission=commission,fees=fees,taxes=taxes,net=net,settlement_status=f.get('settlement_status','Pending')))
        db.session.commit(); flash('Order saved.','success'); return redirect(url_for('food'))
    items=FoodOrder.query.order_by(FoodOrder.created_at.desc()).all(); sums=db.session.query(func.sum(FoodOrder.gross),func.sum(FoodOrder.net)).first()
    integrations=FoodIntegration.query.filter_by(active=True).order_by(FoodIntegration.platform,FoodIntegration.display_name).all()
    return render_template('food.html',items=items,total_gross=sums[0] or 0,total_net=sums[1] or 0,integrations=integrations)

@app.route('/food/integrations')
@permission_required('food')
def food_integrations():
    ensure_default_food_integrations()
    rows=FoodIntegration.query.order_by(FoodIntegration.platform,FoodIntegration.display_name,FoodIntegration.id).all()
    return render_template('food_integrations.html',integrations=rows,webhook_token_configured=bool(setting('food_webhook_token','')),official=OFFICIAL_FOOD_PORTALS)

@app.route('/food/integrations/save',methods=['POST'])
@permission_required('food')
def food_integration_save():
    iid=request.form.get('id','').strip(); row=db.session.get(FoodIntegration,int(iid)) if iid.isdigit() else FoodIntegration()
    if not iid: db.session.add(row)
    row.platform=(request.form.get('platform') or 'Other').strip()[:60]
    row.display_name=(request.form.get('display_name') or f'{row.platform} Integration').strip()[:160]
    row.outlet_id=(request.form.get('outlet_id') or '').strip()[:180]
    row.account_identifier=(request.form.get('account_identifier') or '').strip()[:180]
    row.portal_url=(request.form.get('portal_url') or '').strip()
    row.developer_url=(request.form.get('developer_url') or '').strip()
    row.api_base_url=(request.form.get('api_base_url') or '').strip()
    row.api_token_env=(request.form.get('api_token_env') or '').strip()[:120]
    row.api_key_env=(request.form.get('api_key_env') or '').strip()[:120]
    row.webhook_enabled=request.form.get('webhook_enabled')=='1'; row.api_enabled=request.form.get('api_enabled')=='1'; row.active=request.form.get('active')=='1'
    for attr in ('portal_url','developer_url','api_base_url'):
        val=getattr(row,attr) or ''
        if val and not re.match(r'^https?://',val,re.I):
            flash(f'{attr.replace("_"," ").title()} must start with https:// or http://','danger');return redirect(url_for('food_integrations'))
    db.session.commit();flash('Food partner integration saved.','success');return redirect(url_for('food_integrations'))

@app.route('/food/integrations/<int:iid>/delete',methods=['POST'])
@permission_required('food')
def food_integration_delete(iid):
    row=db.session.get(FoodIntegration,iid) or abort(404);db.session.delete(row);db.session.commit();flash('Integration removed.','success');return redirect(url_for('food_integrations'))

@app.route('/food/integrations/<int:iid>/sync',methods=['POST'])
@permission_required('food')
def food_integration_sync(iid):
    row=db.session.get(FoodIntegration,iid) or abort(404)
    if not row.active or not row.api_enabled or not (row.api_base_url or '').strip():
        flash('Enable API Sync and add the official/API endpoint supplied by the platform first.','warning');return redirect(url_for('food_integrations'))
    headers={'Accept':'application/json','User-Agent':'LivenzaLife-OperationsCloud/1.5.5'}
    bearer=os.getenv((row.api_token_env or '').strip(),'').strip() if row.api_token_env else ''
    api_key=os.getenv((row.api_key_env or '').strip(),'').strip() if row.api_key_env else ''
    if bearer: headers['Authorization']=f'Bearer {bearer}'
    if api_key: headers['X-API-Key']=api_key
    try:
        resp=requests.get(row.api_base_url,headers=headers,timeout=35);resp.raise_for_status();payload=resp.json();count=_ingest_food_payload(row.platform,payload,default_outlet=row.display_name or row.outlet_id)
        row.last_sync_at=datetime.datetime.utcnow();row.last_sync_count=count;row.last_sync_status=f'OK • {count} record(s) received';db.session.commit();flash(f'{row.platform} sync completed: {count} order record(s).','success')
    except Exception as e:
        db.session.rollback();row=db.session.get(FoodIntegration,iid);row.last_sync_at=datetime.datetime.utcnow();row.last_sync_count=0;row.last_sync_status=f'ERROR • {str(e)[:300]}';db.session.commit();flash(f'{row.platform} API sync failed. Check the endpoint, partner access and Render environment credentials.','danger')
    return redirect(url_for('food_integrations'))

@app.route('/food/portals')
@permission_required('food')
def food_portals():
    ensure_default_food_integrations(); rows=FoodIntegration.query.filter_by(active=True).order_by(FoodIntegration.platform,FoodIntegration.display_name).all()
    selected_id=request.args.get('id','');selected=None
    if selected_id.isdigit(): selected=db.session.get(FoodIntegration,int(selected_id))
    if not selected and rows: selected=rows[0]
    return render_template('food_portals.html',integrations=rows,selected=selected)

@app.route('/food/import', methods=['POST'])
@permission_required('food')
def food_import():
    file=request.files.get('file')
    if not file: flash('Choose a CSV file.','danger'); return redirect(url_for('food'))
    text=io.TextIOWrapper(file.stream,encoding='utf-8-sig'); reader=csv.DictReader(text); n=0
    for row in reader:
        _upsert_food_order(row.get('platform','Direct'),row,default_outlet=row.get('outlet','')); n+=1
    db.session.commit(); flash(f'Imported {n} orders.','success'); return redirect(url_for('food'))

@app.route('/webhooks/food/<platform>', methods=['POST'])
def food_webhook(platform):
    token=request.headers.get('X-Livenza-Webhook-Token','')
    configured=setting('food_webhook_token','')
    if not configured or not secrets.compare_digest(token,configured): abort(401)
    payload=request.get_json(silent=True)
    if payload is None: return jsonify(ok=False,error='JSON payload required'),400
    integration=FoodIntegration.query.filter(func.lower(FoodIntegration.platform)==platform.lower(),FoodIntegration.active.is_(True)).first()
    if integration and not integration.webhook_enabled: abort(403)
    display=(integration.platform if integration else platform.replace('-',' ').title())
    count=_ingest_food_payload(display,payload,default_outlet=(integration.display_name if integration else ''))
    if integration:
        integration.last_sync_at=datetime.datetime.utcnow();integration.last_sync_count=count;integration.last_sync_status=f'WEBHOOK • {count} record(s)';db.session.commit()
    return jsonify(ok=True,platform=display,records=count)

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


@app.route('/queries/sheet')
@permission_required('queries')
def query_sheet():
    term=request.args.get('q','').strip()
    qry=QueryLead.query
    if term:
        qry=qry.filter(or_(
            QueryLead.customer_name.ilike(f'%{term}%'),
            QueryLead.mobile.ilike(f'%{term}%'),
            QueryLead.whatsapp.ilike(f'%{term}%'),
            QueryLead.city.ilike(f'%{term}%'),
            QueryLead.property_name.ilike(f'%{term}%'),
            QueryLead.query_text.ilike(f'%{term}%')
        ))
    items=qry.order_by(QueryLead.updated_at.desc()).limit(750).all()
    return render_template('query_sheet.html',items=items,cities=City.query.filter_by(active=True).order_by(City.name).all())


def _query_sheet_apply(q, payload):
    allowed=('source','city','property_name','customer_name','mobile','whatsapp','email','query_text','budget','move_in_date','stay_type','status','heat','next_follow_up','notes')
    for k in allowed:
        if k in payload:
            setattr(q,k,str(payload.get(k) or '').strip())
    if 'score' in payload:
        try:q.score=max(0,min(100,int(payload.get('score') or 0)))
        except Exception:pass
    q.updated_at=datetime.datetime.utcnow()
    return q

@app.route('/api/queries',methods=['POST'])
@permission_required('queries')
def query_sheet_create():
    payload=request.get_json(silent=True) or {}
    q=QueryLead(source='Manual',status='Live',heat='Warm',score=50)
    _query_sheet_apply(q,payload)
    if not q.whatsapp:q.whatsapp=q.mobile
    db.session.add(q);db.session.flush();query_log(q,'Created','Created from spreadsheet view',current_user());db.session.commit()
    return jsonify(ok=True,id=q.id,updated_at=q.updated_at.isoformat() if q.updated_at else '')

@app.route('/api/queries/<int:qid>',methods=['PATCH'])
@permission_required('queries')
def query_sheet_patch(qid):
    q=db.session.get(QueryLead,qid) or abort(404)
    payload=request.get_json(silent=True) or {}
    _query_sheet_apply(q,payload)
    query_log(q,'Spreadsheet update','Updated from spreadsheet view',current_user());db.session.commit()
    return jsonify(ok=True,id=q.id,updated_at=q.updated_at.isoformat() if q.updated_at else '')

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
    db.session.add(asset); db.session.commit(); flash('Media uploaded and ready for screens.','success')
    if info.get('drive_backup_error'): flash('Google Drive mirror warning: '+info['drive_backup_error'],'warning')
    return redirect(url_for('video_wall'))

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


HELP_FEATURES = {
    'agreement': 'Open Operations → Agreements. Create a new agreement, choose a preset, optionally upload Aadhaar to auto-fill tenant details, complete any fields you need, then save and preview in English or Hindi. All agreement fields are optional.',
    'room': 'Open Operations → Rooms to maintain room inventory, occupancy and vacant-room reporting. Vacancy reports can also be scheduled to pre-fed WhatsApp recipients when the WhatsApp Cloud configuration is available.',
    'tenant': 'Open Operations → Tenants to maintain resident records, room allocation, contact information, tariff, security deposit, joining/leaving dates and agreement references.',
    'review': 'Open Reviews. Paste the direct Google Business review link, enter the genuine customer experience, generate review drafts, then copy the review and open the Google review page or scan/download its QR code.',
    'query': 'Open Queries for the live lead manager. Use card view for follow-up workflow or Spreadsheet View for direct Excel-style editing. Queries can come from manual entry, Google/Meta webhooks and OTA integrations.',
    'spreadsheet': 'In Queries, click Spreadsheet View. Edit cells directly like a sheet. Existing rows auto-save when a cell changes; use + New Row to create a fresh enquiry line.',
    'video': 'Open Video Wall. Add media, create TV/screen endpoints, assign a different playlist to each TV, set rotation/fit/loop options, or start a Festive Takeover to run one commercial across all enabled screens.',
    'billing': 'Open Billing for the Livenza Billing Suite. It embeds the configured billing manager when the external service allows embedding and otherwise provides a direct-open fallback.',
    'food': 'Open Food for orders and settlements. Use Integrations to configure Swiggy, Zomato, Toing or another partner using webhook/API details, and Live Partner Websites to open their official restaurant portals inside Operations Cloud when embedding is allowed.',
    'whatsapp': 'Open WhatsApp to send Cloud API messages and view the incoming message feed. Admin must configure the Meta token, phone-number ID and webhook verification secrets.',
    'email': 'Open Email to view the latest Gmail inbox metadata and compose messages without leaving Livenza. An admin must connect Google once from the Admin panel.',
    'drive': 'Open Drive to upload, list, open and download Livenza files in the configured Google Drive folder. Admin can also mirror Video Wall uploads automatically.',
    'security': 'Admins can configure pattern login and allow fingerprint/passkey enrollment per user. The kiosk PIN gate and Windows startup downloads are in Admin → Kiosk & Main Screen.',
    'fullscreen': 'Open View → Full Screen. While fullscreen is active, top navigation uses in-place page switching so moving between modules does not exit fullscreen.',
    'rotate': 'Open View and choose Auto, Portrait, Landscape, 90°, 180° or 270°. Portrait/Landscape can use device orientation on supported fullscreen mobile/tablet browsers; desktop custom angles rotate the application viewport.',
    'user': 'Admins can open the profile menu → Admin to create user IDs, passwords, profile photos and module-by-module access permissions.',
    'city': 'Admins can manage operating cities from the Admin panel. City data is then available across the dashboard, rooms, tenants, agreements and queries.'
}

def _local_help_answer(question):
    q=(question or '').strip().lower()
    if not q:return 'Ask me about any Livenza Operations Cloud feature or workflow.'
    aliases=[
        (('agreement','rent agreement','lease','stamp'), 'agreement'),
        (('vacant','vacancy','room','occupancy'), 'room'),
        (('tenant','resident'), 'tenant'),
        (('review','google review','qr'), 'review'),
        (('spreadsheet','excel','sheet','grid'), 'spreadsheet'),
        (('query','lead','enquiry','inquiry','meta','facebook','airbnb','ota'), 'query'),
        (('video wall','tv','screen','festive','playlist'), 'video'),
        (('food','swiggy','zomato','toing','restaurant partner','delivery order'), 'food'),
        (('billing','rentok','rent ok'), 'billing'),
        (('whatsapp','message','chat'), 'whatsapp'),
        (('email','gmail','mail','inbox'), 'email'),
        (('drive','google drive','cloud file','upload'), 'drive'),
        (('fingerprint','passkey','windows hello','pattern','kiosk','pin','lock'), 'security'),
        (('fullscreen','full screen','f11'), 'fullscreen'),
        (('rotate','portrait','landscape','orientation'), 'rotate'),
        (('user','permission','login','password','access'), 'user'),
        (('city','location'), 'city'),
    ]
    for words,key in aliases:
        if any(w in q for w in words):return HELP_FEATURES[key]
    return 'I can guide you through Agreements, Rooms, Tenants, Reviews, Queries and Spreadsheet View, Video Wall, Billing, Fullscreen/Rotate, users/permissions and city setup. Ask a specific question about the feature you want to use.'

@app.route('/api/help',methods=['POST'])
@login_required
def help_assistant():
    payload=request.get_json(silent=True) or {}
    question=str(payload.get('message') or '')[:1200].strip()
    if not question:return jsonify(ok=False,error='Type a question first.'),400
    fallback=_local_help_answer(question)
    key=os.getenv('OPENAI_API_KEY','').strip()
    if not key:return jsonify(ok=True,answer=fallback,mode='local')
    try:
        from openai import OpenAI
        client=OpenAI(api_key=key)
        feature_text='\n'.join(f'- {k}: {v}' for k,v in HELP_FEATURES.items())
        prompt=(
            'You are the embedded help assistant for Livenza Life Operations Cloud. '
            'Answer only questions about how to use this web application. Be concise, practical and never invent a capability. '
            'If the question is outside the application, say you can only help with Operations Cloud features. '
            'Available feature guide:\n'+feature_text+'\n\nUser question: '+question
        )
        resp=client.responses.create(model=os.getenv('OPENAI_HELP_MODEL',os.getenv('OPENAI_REVIEW_MODEL','gpt-5.6-luna')),input=prompt)
        answer=(getattr(resp,'output_text','') or '').strip() or fallback
        return jsonify(ok=True,answer=answer[:4000],mode='ai')
    except Exception:
        return jsonify(ok=True,answer=fallback,mode='local')

@app.route('/api/webauthn/register/options',methods=['POST'])
@login_required
def webauthn_register_options():
    u=current_user()
    if not u.webauthn_enabled: return jsonify(ok=False,error='Fingerprint/passkey enrollment is not enabled for this user.'),403
    try:
        from webauthn import generate_registration_options, options_to_json
        from webauthn.helpers.structs import AuthenticatorSelectionCriteria, PublicKeyCredentialDescriptor, ResidentKeyRequirement, UserVerificationRequirement
        rp_id,_=_webauthn_context()
        existing=WebAuthnCredential.query.filter_by(user_id=u.id).all()
        options=generate_registration_options(
            rp_id=rp_id,rp_name='Livenza Back Office',user_id=str(u.id).encode(),user_name=u.username,
            user_display_name=u.full_name or u.username,
            exclude_credentials=[PublicKeyCredentialDescriptor(id=c.credential_id) for c in existing],
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.REQUIRED,
            ),
        )
        session['webauthn_register_challenge']=base64.urlsafe_b64encode(options.challenge).decode('ascii')
        return app.response_class(options_to_json(options),mimetype='application/json')
    except Exception as exc:
        return jsonify(ok=False,error=f'Passkey service is unavailable: {exc}'),503

@app.route('/api/webauthn/register/verify',methods=['POST'])
@login_required
def webauthn_register_verify():
    u=current_user(); challenge=session.pop('webauthn_register_challenge','')
    if not (u.webauthn_enabled and challenge): return jsonify(ok=False,error='Enrollment request expired.'),400
    try:
        from webauthn import verify_registration_response
        rp_id,origin=_webauthn_context(); payload=request.get_json(force=True)
        verified=verify_registration_response(
            credential=payload,expected_challenge=base64.urlsafe_b64decode(challenge.encode('ascii')),
            expected_rp_id=rp_id,expected_origin=origin,require_user_verification=True,
        )
        row=WebAuthnCredential.query.filter_by(credential_id=verified.credential_id).first()
        if not row:
            row=WebAuthnCredential(user_id=u.id,credential_id=verified.credential_id,public_key=verified.credential_public_key)
            db.session.add(row)
        row.sign_count=verified.sign_count; row.device_name=str(payload.get('device_name') or 'Windows Hello / fingerprint')[:180]
        row.transports=json.dumps(((payload.get('response') or {}).get('transports') or []))
        u.webauthn_enrolled_at=datetime.datetime.utcnow(); db.session.commit()
        return jsonify(ok=True,message='Fingerprint/passkey enrolled on this device.')
    except Exception as exc:
        db.session.rollback(); return jsonify(ok=False,error=f'Enrollment could not be verified: {exc}'),400

@app.route('/api/webauthn/auth/options',methods=['POST'])
def webauthn_auth_options():
    payload=request.get_json(silent=True) or {}; username=str(payload.get('username') or '').strip()
    u=User.query.filter_by(username=username,active=True).first()
    credentials=WebAuthnCredential.query.filter_by(user_id=u.id).all() if u and u.webauthn_enabled else []
    if not credentials: return jsonify(ok=False,error='No fingerprint/passkey is enrolled for this login ID.'),404
    try:
        from webauthn import generate_authentication_options, options_to_json
        from webauthn.helpers.structs import PublicKeyCredentialDescriptor, UserVerificationRequirement
        rp_id,_=_webauthn_context()
        options=generate_authentication_options(
            rp_id=rp_id,allow_credentials=[PublicKeyCredentialDescriptor(id=c.credential_id) for c in credentials],
            user_verification=UserVerificationRequirement.REQUIRED,
        )
        session['webauthn_auth_challenge']=base64.urlsafe_b64encode(options.challenge).decode('ascii'); session['webauthn_auth_user']=u.id
        return app.response_class(options_to_json(options),mimetype='application/json')
    except Exception as exc:
        return jsonify(ok=False,error=f'Passkey service is unavailable: {exc}'),503

@app.route('/api/webauthn/auth/verify',methods=['POST'])
def webauthn_auth_verify():
    challenge=session.pop('webauthn_auth_challenge',''); uid=session.pop('webauthn_auth_user',None)
    u=db.session.get(User,uid) if uid else None; payload=request.get_json(force=True)
    if not (u and u.active and u.webauthn_enabled and challenge): return jsonify(ok=False,error='Authentication request expired.'),400
    try:
        from webauthn import verify_authentication_response
        credential_id=_b64url_decode(payload.get('id',''))
        row=WebAuthnCredential.query.filter_by(user_id=u.id,credential_id=credential_id).first()
        if not row: return jsonify(ok=False,error='This passkey is not registered.'),404
        rp_id,origin=_webauthn_context()
        verified=verify_authentication_response(
            credential=payload,expected_challenge=base64.urlsafe_b64decode(challenge.encode('ascii')),
            expected_rp_id=rp_id,expected_origin=origin,credential_public_key=row.public_key,
            credential_current_sign_count=row.sign_count,require_user_verification=True,
        )
        row.sign_count=verified.new_sign_count; row.last_used_at=datetime.datetime.utcnow(); db.session.commit()
        session.clear(); session['uid']=u.id; session['kiosk_unlocked']=setting('kiosk_mode_enabled','0')!='1'; session['show_login_welcome']=True
        return jsonify(ok=True,redirect=(url_for('kiosk_lock') if not session['kiosk_unlocked'] else url_for('dashboard')))
    except Exception as exc:
        db.session.rollback(); return jsonify(ok=False,error=f'Fingerprint/passkey verification failed: {exc}'),400

@app.route('/admin/webauthn/<int:credential_id>/delete',methods=['POST'])
@admin_required
def webauthn_credential_delete(credential_id):
    row=db.session.get(WebAuthnCredential,credential_id) or abort(404); uid=row.user_id
    db.session.delete(row); db.session.commit()
    if WebAuthnCredential.query.filter_by(user_id=uid).count()==0:
        u=db.session.get(User,uid); u.webauthn_enrolled_at=None; db.session.commit()
    flash('Registered fingerprint/passkey removed.','success'); return redirect(url_for('admin_panel')+'#user-'+str(uid))

@app.route('/whatsapp',methods=['GET','POST'])
@permission_required('whatsapp')
def whatsapp_workspace():
    if request.method=='POST':
        to=wa_number(request.form.get('to','')); body=request.form.get('body','').strip()
        if not (to and body):
            flash('Enter a valid WhatsApp number and message.','danger'); return redirect(url_for('whatsapp_workspace'))
        ok,result=whatsapp_cloud_text(to,body)
        if ok:
            mid=result if result.startswith('wamid.') else None
            db.session.add(WhatsAppMessage(direction='outbound',wa_id=to,message_id=mid,body=body,status='sent',raw_json=json.dumps({'api_result':result})))
            db.session.commit(); flash('WhatsApp message sent.','success')
        else: flash('WhatsApp send failed: '+result,'danger')
        return redirect(url_for('whatsapp_workspace'))
    rows=WhatsAppMessage.query.order_by(WhatsAppMessage.created_at.desc()).limit(250).all()
    return render_template('whatsapp.html',messages=rows,configured=whatsapp_cloud_configured(),webhook_url=url_for('whatsapp_messages_webhook',_external=True))

@app.route('/webhooks/whatsapp/messages',methods=['GET','POST'])
def whatsapp_messages_webhook():
    if request.method=='GET':
        verify=os.getenv('WHATSAPP_VERIFY_TOKEN',os.getenv('META_VERIFY_TOKEN','')).strip()
        if request.args.get('hub.mode')=='subscribe' and verify and hmac.compare_digest(request.args.get('hub.verify_token',''),verify):
            return request.args.get('hub.challenge','')
        return 'Verification failed',403
    app_secret=os.getenv('META_APP_SECRET','').strip(); raw=request.get_data(cache=True)
    signature=request.headers.get('X-Hub-Signature-256','')
    if app_secret:
        expected='sha256='+hmac.new(app_secret.encode(),raw,hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature,expected): return jsonify(ok=False),403
    payload=request.get_json(silent=True) or {}; changed=0
    for entry in payload.get('entry',[]) or []:
        for change in entry.get('changes',[]) or []:
            value=change.get('value') or {}; contacts={x.get('wa_id'):((x.get('profile') or {}).get('name') or '') for x in value.get('contacts',[]) or []}
            for msg in value.get('messages',[]) or []:
                mid=str(msg.get('id') or '') or None
                row=WhatsAppMessage.query.filter_by(message_id=mid).first() if mid else None
                if not row:
                    mtype=str(msg.get('type') or 'unknown'); content=msg.get('text',{}).get('body','') if mtype=='text' else json.dumps(msg.get(mtype) or {})
                    row=WhatsAppMessage(direction='inbound',contact_name=contacts.get(msg.get('from'),'')[:180],wa_id=str(msg.get('from') or '')[:40],message_id=mid,message_type=mtype,body=content,status='received',raw_json=json.dumps(msg))
                    db.session.add(row); changed+=1
            for status in value.get('statuses',[]) or []:
                row=WhatsAppMessage.query.filter_by(message_id=str(status.get('id') or '')).first()
                if row: row.status=str(status.get('status') or row.status)[:40]; row.raw_json=json.dumps(status); changed+=1
    if changed: db.session.commit()
    return jsonify(ok=True)

@app.route('/integrations/google/connect')
@admin_required
def google_connect():
    if not google_oauth_configured():
        flash('Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET first.','danger'); return redirect(url_for('admin_panel')+'#cloud-integrations')
    state=secrets.token_urlsafe(30); session['google_oauth_state']=state
    redirect_uri=url_for('google_callback',_external=True,_scheme='https' if os.getenv('FORCE_HTTPS','1')=='1' else request.scheme)
    params={'client_id':os.getenv('GOOGLE_CLIENT_ID'),'redirect_uri':redirect_uri,'response_type':'code','scope':' '.join(GOOGLE_SCOPES),'access_type':'offline','include_granted_scopes':'true','prompt':'consent','state':state}
    return redirect('https://accounts.google.com/o/oauth2/v2/auth?'+urllib.parse.urlencode(params))

@app.route('/integrations/google/callback')
@admin_required
def google_callback():
    if not hmac.compare_digest(str(session.pop('google_oauth_state','')),str(request.args.get('state',''))):
        flash('Google connection state did not match. Please try again.','danger'); return redirect(url_for('admin_panel')+'#cloud-integrations')
    redirect_uri=url_for('google_callback',_external=True,_scheme='https' if os.getenv('FORCE_HTTPS','1')=='1' else request.scheme)
    try:
        r=requests.post('https://oauth2.googleapis.com/token',data={'code':request.args.get('code',''),'client_id':os.getenv('GOOGLE_CLIENT_ID'),'client_secret':os.getenv('GOOGLE_CLIENT_SECRET'),'redirect_uri':redirect_uri,'grant_type':'authorization_code'},timeout=25)
        if not r.ok: raise RuntimeError(r.text[:500])
        data=r.json(); data['expires_at']=datetime.datetime.utcnow().timestamp()+int(data.get('expires_in') or 3600)
        _encrypted_setting_set('google_oauth_token',json.dumps(data)); ensure_google_drive_folder(); flash('Google Drive and Gmail connected.','success')
    except Exception as exc: flash(f'Google connection failed: {exc}','danger')
    return redirect(url_for('admin_panel')+'#cloud-integrations')

@app.route('/integrations/google/disconnect',methods=['POST'])
@admin_required
def google_disconnect():
    data=_google_token_data(refresh=False); token=data.get('refresh_token') or data.get('access_token')
    if token:
        try: requests.post('https://oauth2.googleapis.com/revoke',params={'token':token},timeout=15)
        except Exception: pass
    _encrypted_setting_set('google_oauth_token',''); flash('Google connection removed.','success')
    return redirect(url_for('admin_panel')+'#cloud-integrations')

@app.route('/admin/google/settings',methods=['POST'])
@admin_required
def google_settings():
    set_setting('google_drive_folder_id',request.form.get('google_drive_folder_id','').strip())
    set_setting('google_drive_auto_backup','1' if request.form.get('google_drive_auto_backup')=='1' else '0')
    flash('Google Drive settings saved.','success'); return redirect(url_for('admin_panel')+'#cloud-integrations')

@app.route('/drive',methods=['GET','POST'])
@permission_required('drive')
def drive_workspace():
    if request.method=='POST':
        f=request.files.get('file')
        if not f or not f.filename:
            flash('Choose a file to upload.','danger'); return redirect(url_for('drive_workspace'))
        data=f.read(); row,err=google_drive_upload_bytes(data,f.filename,f.mimetype or 'application/octet-stream','manual',current_user())
        flash(('Uploaded to Google Drive.' if row else err),('success' if row else 'danger')); return redirect(url_for('drive_workspace'))
    live=[]; error=''
    headers=_google_headers()
    if headers:
        try:
            folder=ensure_google_drive_folder()
            params={'pageSize':100,'orderBy':'modifiedTime desc','fields':'files(id,name,mimeType,size,modifiedTime,webViewLink)','q':f"'{folder}' in parents and trashed=false" if folder else 'trashed=false'}
            r=requests.get('https://www.googleapis.com/drive/v3/files',headers=headers,params=params,timeout=25)
            if r.ok: live=r.json().get('files',[])
            else: error=r.text[:400]
        except Exception as exc: error=str(exc)
    return render_template('drive.html',files=live,connected=bool(headers),error=error,folder_id=setting('google_drive_folder_id',''))

@app.route('/drive/files/<file_id>/download')
@permission_required('drive')
def drive_file_download(file_id):
    if not re.fullmatch(r'[A-Za-z0-9_-]{10,220}',file_id): abort(400)
    headers=_google_headers()
    if not headers: abort(503)
    meta=requests.get(f'https://www.googleapis.com/drive/v3/files/{file_id}',headers=headers,params={'fields':'name,mimeType'},timeout=25)
    mime=meta.json().get('mimeType','') if meta.ok else ''
    exports={
        'application/vnd.google-apps.document':('application/pdf','.pdf'),
        'application/vnd.google-apps.spreadsheet':('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','.xlsx'),
        'application/vnd.google-apps.presentation':('application/vnd.openxmlformats-officedocument.presentationml.presentation','.pptx'),
        'application/vnd.google-apps.drawing':('application/pdf','.pdf'),
    }
    if mime in exports:
        export_mime,extension=exports[mime]
        content=requests.get(f'https://www.googleapis.com/drive/v3/files/{file_id}/export',headers=headers,params={'mimeType':export_mime},timeout=90)
    else:
        export_mime,extension=mime,''
        content=requests.get(f'https://www.googleapis.com/drive/v3/files/{file_id}',headers=headers,params={'alt':'media'},timeout=90)
    if not (meta.ok and content.ok): abort(502)
    info=meta.json(); name=info.get('name') or 'drive-file'
    if extension and not name.lower().endswith(extension): name+=extension
    return send_file(io.BytesIO(content.content),download_name=name,mimetype=export_mime or 'application/octet-stream',as_attachment=True)

def _gmail_plain_text(part):
    if not isinstance(part,dict): return ''
    mime=part.get('mimeType',''); data=(part.get('body') or {}).get('data','')
    if mime=='text/plain' and data:
        try: return _b64url_decode(data).decode('utf-8','replace')
        except Exception: return ''
    for child in part.get('parts',[]) or []:
        text=_gmail_plain_text(child)
        if text: return text
    return ''

@app.route('/email',methods=['GET','POST'])
@permission_required('email')
def email_workspace():
    headers=_google_headers(); messages=[]; error=''
    if request.method=='POST':
        if not headers:
            flash('Connect Google in Admin first.','danger'); return redirect(url_for('email_workspace'))
        to=request.form.get('to','').strip(); subject=request.form.get('subject','').strip(); body=request.form.get('body','').strip()
        if not (to and body):
            flash('Recipient and message are required.','danger'); return redirect(url_for('email_workspace'))
        mail=EmailMessage(); mail['To']=to; mail['Subject']=subject; mail.set_content(body)
        raw=base64.urlsafe_b64encode(mail.as_bytes()).decode('ascii').rstrip('=')
        r=requests.post('https://gmail.googleapis.com/gmail/v1/users/me/messages/send',headers=dict(headers,**{'Content-Type':'application/json'}),json={'raw':raw},timeout=30)
        flash(('Email sent.' if r.ok else 'Email send failed: '+r.text[:300]),('success' if r.ok else 'danger')); return redirect(url_for('email_workspace'))
    if headers:
        try:
            listing=requests.get('https://gmail.googleapis.com/gmail/v1/users/me/messages',headers=headers,params={'maxResults':15},timeout=25)
            for item in (listing.json().get('messages',[]) if listing.ok else []):
                r=requests.get(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{item['id']}",headers=headers,params={'format':'metadata','metadataHeaders':['From','Subject','Date']},timeout=20)
                if not r.ok: continue
                data=r.json(); hs={x.get('name','').lower():x.get('value','') for x in (data.get('payload',{}).get('headers',[]) or [])}
                messages.append({'id':item['id'],'from':hs.get('from',''),'subject':hs.get('subject','(no subject)'),'date':hs.get('date',''),'snippet':data.get('snippet','')})
            if not listing.ok: error=listing.text[:400]
        except Exception as exc: error=str(exc)
    return render_template('email.html',messages=messages,connected=bool(headers),error=error)

@app.route('/email/messages/<message_id>')
@permission_required('email')
def email_message(message_id):
    if not re.fullmatch(r'[A-Za-z0-9_-]{8,220}',message_id): abort(400)
    headers=_google_headers()
    if not headers: abort(503)
    r=requests.get(f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}',headers=headers,params={'format':'full'},timeout=30)
    if not r.ok: abort(502)
    data=r.json(); hs={x.get('name','').lower():x.get('value','') for x in (data.get('payload',{}).get('headers',[]) or [])}
    message={'from':hs.get('from',''),'to':hs.get('to',''),'subject':hs.get('subject','(no subject)'),'date':hs.get('date',''),'body':_gmail_plain_text(data.get('payload') or {}) or data.get('snippet','')}
    return render_template('email_message.html',message=message)

@app.route('/settings', methods=['GET','POST'])
@admin_required
def settings_page():
    keys=('food_webhook_token','whatsapp_recipient','empty_report_time','default_google_review_url','vacant_report_enabled','vacant_report_time','vacant_report_recipients','query_webhook_token',
          'marquee_enabled','marquee_show_username','marquee_show_tenants','marquee_show_vacant_beds','marquee_show_earnings','marquee_show_favorites','marquee_show_stocks','marquee_favorites','marquee_custom_text','marquee_manual_earnings','marquee_stock_pages','marquee_refresh_seconds',
          'companion_enabled','companion_weather_enabled','companion_weather_effects','companion_quotes_enabled','companion_operations_enabled','companion_default_city','companion_effect_seconds')
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
    defaults={'marquee_enabled':'1','marquee_show_username':'1','marquee_show_tenants':'1','marquee_show_vacant_beds':'1','marquee_show_earnings':'1','marquee_refresh_seconds':'60',
              'companion_enabled':'1','companion_weather_enabled':'1','companion_weather_effects':'1','companion_quotes_enabled':'1','companion_operations_enabled':'1','companion_default_city':'Gurugram','companion_effect_seconds':'11'}
    return render_template('settings.html',settings={k:setting(k,defaults.get(k,'')) for k in keys})

@app.route('/admin')
@admin_required
def admin_panel():
    users=User.query.order_by(User.username).all()
    credentials={u.id:WebAuthnCredential.query.filter_by(user_id=u.id).order_by(WebAuthnCredential.id).all() for u in users}
    return render_template('admin.html', users=users, cities=City.query.order_by(City.name).all(), modules=MODULES,
        query_templates=QueryTemplate.query.order_by(QueryTemplate.id.desc()).all(), aadhaar_provider_configured=bool(os.getenv('AADHAAR_AUTH_URL','').strip()),
        credentials=credentials, google_oauth_ready=google_oauth_configured(), google_is_connected=google_connected(),
        drive_folder_id=setting('google_drive_folder_id',''), drive_auto_backup=setting('google_drive_auto_backup','0')=='1',
        kiosk_enabled=setting('kiosk_mode_enabled','0')=='1')

@app.route('/admin/kiosk/settings',methods=['POST'])
@admin_required
def kiosk_settings():
    u=current_user(); password=request.form.get('admin_password','')
    if not check_password_hash(u.password_hash,password):
        flash('Administrator password is required to change Windows/kiosk lock settings.','danger'); return redirect(url_for('admin_panel')+'#kiosk-security')
    enabled=request.form.get('kiosk_mode_enabled')=='1'; new_pin=request.form.get('kiosk_pin','').strip()
    if enabled and not (setting('kiosk_pin_hash','') or len(new_pin)>=6):
        flash('Set a kiosk PIN with at least 6 characters before enabling lock mode.','danger'); return redirect(url_for('admin_panel')+'#kiosk-security')
    if new_pin:
        if len(new_pin)<6:
            flash('Kiosk PIN must contain at least 6 characters.','danger'); return redirect(url_for('admin_panel')+'#kiosk-security')
        set_setting('kiosk_pin_hash',generate_password_hash(new_pin))
    set_setting('kiosk_mode_enabled','1' if enabled else '0')
    session['kiosk_unlocked']=not enabled
    flash(('Kiosk lock enabled. Unlock with the kiosk PIN or user password.' if enabled else 'Kiosk lock disabled.'),'success')
    return redirect(url_for('kiosk_lock') if enabled else url_for('admin_panel')+'#kiosk-security')

@app.route('/admin/kiosk/windows/<kind>')
@admin_required
def kiosk_windows_download(kind):
    names={'enable':'Enable-LivenzaKiosk.ps1','disable':'Disable-LivenzaKiosk.ps1','guide':'README_WINDOWS_KIOSK.md'}
    name=names.get(kind) or abort(404)
    return send_file(os.path.join(BASE_DIR,'windows-kiosk',name),as_attachment=True,download_name=name)

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
    u.webauthn_enabled=request.form.get('webauthn_enabled')=='1'
    pattern=_pattern_value(request.form.get('pattern',''))
    if request.form.get('clear_pattern')=='1': u.pattern_hash=''
    elif pattern: u.pattern_hash=generate_password_hash('pattern:'+pattern)
    elif request.form.get('pattern'):
        flash('Pattern was not changed: connect at least 4 different dots.','warning')
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


def ensure_v150_user_columns():
    """Small compatibility bridge; production schema is also provided as a migration."""
    existing={c['name'] for c in inspect(db.engine).get_columns('user')}
    statements=[]
    if 'pattern_hash' not in existing: statements.append('ALTER TABLE "user" ADD COLUMN pattern_hash TEXT DEFAULT \'\'')
    if 'webauthn_enabled' not in existing: statements.append('ALTER TABLE "user" ADD COLUMN webauthn_enabled BOOLEAN NOT NULL DEFAULT FALSE')
    if 'webauthn_enrolled_at' not in existing: statements.append('ALTER TABLE "user" ADD COLUMN webauthn_enrolled_at TIMESTAMP NULL')
    for sql in statements: db.session.execute(db.text(sql))
    if statements: db.session.commit()

def bootstrap():
    os.makedirs(os.path.join(BASE_DIR,'instance'),exist_ok=True)
    db.create_all()
    ensure_v150_user_columns()
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
