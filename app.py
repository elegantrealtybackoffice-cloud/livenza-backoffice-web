import os, io, csv, json, hashlib, datetime, urllib.parse, html
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy import func
from dateutil.relativedelta import relativedelta
import requests
import qrcode

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
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
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
    'rentok': 'RentOK Manager',
}

BASE_REQUIRED_AGREEMENT_FIELDS = [
    'agreement_template','agreement_type','agreement_reference','agreement_date','place_of_execution',
    'start_date','end_date','term_months','stamp_value','jurisdiction',
    'landlord_name','landlord_address','landlord_id_type','landlord_id_no','landlord_mobile',
    'tenant_name','tenant_address','tenant_id_type','tenant_id_no','tenant_mobile','tenant_whatsapp',
    'city','property_name','premises','room_unit_no','room_type','purpose','monthly_rent','security_deposit',
    'due_day','lockin_months','notice_days','electricity_rate','genset_rate','deposit_refund_days',
    'payment_mode','subletting_policy','relocation_policy','operating_model','language_precedence',
    'witness1','witness2'
]

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
    req=set(BASE_REQUIRED_AGREEMENT_FIELDS)
    if preset_name in ('Corporate / Serviced Stay','OTA Commercial Hosting Rights','Foreign Corporate Guest - Gurugram'):
        req.update({'corporate_name','corporate_address','corporate_representative','corporate_mobile','corporate_email'})
    foreign=(data.get('foreign_status') or '')
    if preset_name=='Foreign Corporate Guest - Gurugram' or foreign in ('Foreign national','OCI Cardholder','Mixed / group booking including foreign nationals or OCI Cardholders'):
        req.update({'foreign_nationality','passport_no','passport_expiry','visa_oci_no','visa_type','visa_expiry','purpose_of_visit','arrival_date_time'})
    return req


def field_label_map():
    m={x[0]:x[1] for x in FIELDS}
    m['city']='City'
    return m


def missing_agreement_fields(preset_name, data):
    labels=field_label_map()
    missing=[]
    for key in agreement_required_fields(preset_name,data):
        if not str(data.get(key,'') or '').strip():
            missing.append((key,labels.get(key,key.replace('_',' ').title())))
    return sorted(missing,key=lambda x:x[1])


def normalize_whatsapp_number(value):
    raw=''.join(ch for ch in (value or '') if ch.isdigit())
    if len(raw)==10:
        raw='91'+raw
    return raw if 8 <= len(raw) <= 15 else ''


def share_serializer():
    return URLSafeTimedSerializer(app.config['SECRET_KEY'], salt='livenza-agreement-share-v1')

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
        current_user=current_user(), app_version='Web 1.2.1',
        can_access=can_access, module_labels=MODULES,
        is_admin=bool(current_user() and (current_user().role or '').lower()=='admin')
    )

@app.route('/health')
def health(): return jsonify(status='ok', service='livenza-back-office-web', version='1.2')

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
        db.session.commit(); flash('Account updated.','success'); return redirect(url_for('account'))
    return render_template('account.html', user=u)

@app.route('/')
@login_required
def dashboard():
    rooms=Room.query.all(); statuses=[room_status(r) for r in rooms]
    stats={
        'agreements':Agreement.query.count(), 'tenants':Tenant.query.count(), 'rooms':len(rooms),
        'vacant':sum(1 for x in statuses if x=='Vacant'), 'orders':FoodOrder.query.count(), 'reviews':Review.query.count()
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
        missing=missing_agreement_fields(preset,d)
        if missing:
            flash('Please complete all mandatory agreement fields: ' + ', '.join(label for _,label in missing), 'danger')
            return render_template('agreement_edit.html', **agreement_editor_context(ag,d)), 400
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
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=36,rightMargin=36,topMargin=42,bottomMargin=42)
    styles=getSampleStyleSheet(); story=[Paragraph('LIVENZA LIFE - EMPTY ROOMS REPORT',styles['Title']),Paragraph(datetime.datetime.now().strftime('%d %b %Y, %I:%M %p'),styles['Normal']),Spacer(1,12)]
    rows=[['City','Property','Room','Type','Tariff','Status']]
    for r in Room.query.order_by(Room.city,Room.property_name,Room.room_no):
        st=room_status(r)
        if st=='Vacant': rows.append([r.city,r.property_name,r.room_no,r.room_type,r.standard_tariff,st])
    if len(rows)==1: rows.append(['-','-','-','-','-','No vacant rooms'])
    t=Table(rows,repeatRows=1,colWidths=[65,110,45,85,70,65]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#5c34d6')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.4,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP')]))
    story.append(t); doc.build(story); buf.seek(0)
    return send_file(buf,mimetype='application/pdf',as_attachment=True,download_name=f"Livenza_Empty_Rooms_{datetime.date.today().isoformat()}.pdf")


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

@app.route('/rentok')
@permission_required('rentok')
def rentok(): return render_template('rentok.html',url='https://manager.rentok.com/')

@app.route('/settings', methods=['GET','POST'])
@admin_required
def settings_page():
    keys=('food_webhook_token','whatsapp_recipient','empty_report_time','default_google_review_url')
    if request.method=='POST':
        for k in keys:
            if k in request.form:
                val=request.form[k].strip()
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
    return render_template('admin.html', users=User.query.order_by(User.username).all(), cities=City.query.order_by(City.name).all(), modules=MODULES)

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
