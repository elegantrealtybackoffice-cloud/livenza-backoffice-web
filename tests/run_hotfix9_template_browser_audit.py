from __future__ import annotations
import json, re
from pathlib import Path
from types import SimpleNamespace
from jinja2 import Environment, FileSystemLoader, ChainableUndefined
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tests'/'audit_artifacts'/'hotfix9_templates'; OUT.mkdir(parents=True,exist_ok=True)
LEGACY=(ROOT/'static/legacy_modules.css').read_text(encoding='utf-8')
SYSTEM=(ROOT/'static/macos27_system.css').read_text(encoding='utf-8')
INTEGRATIONS=(ROOT/'static/integrations.css').read_text(encoding='utf-8')
LETTERHEAD=(ROOT/'static/letterhead.css').read_text(encoding='utf-8')
SHELL=(ROOT/'static/macos27_shell.js').read_text(encoding='utf-8')

env=Environment(loader=FileSystemLoader(str(ROOT/'templates')),undefined=ChainableUndefined,autoescape=False)
APP_META={
    'agreements':{'family':'productivity','accent':'#248CFF','accent2':'#6757E8','icon':'agreement','tone':'blue','title':'Agreement Studio'},
    'rooms':{'family':'occupancy','accent':'#24C7F4','accent2':'#197BFF','icon':'room','tone':'cyan','title':'Rooms'},
    'queries':{'family':'pipeline','accent':'#FF9B42','accent2':'#FF5D3A','icon':'queries','tone':'orange','title':'Queries'},
    'reviews':{'family':'reputation','accent':'#FFD447','accent2':'#FF4E8B','icon':'review','tone':'yellow','title':'Reviews'},
    'food':{'family':'hospitality','accent':'#49CD72','accent2':'#FF9A3D','icon':'food','tone':'green','title':'Food'},
    'billing':{'family':'finance','accent':'#2ED5B5','accent2':'#1A9DE0','icon':'billing','tone':'mint','title':'Billing'},
    'banking_suite':{'family':'finance','accent':'#5575D9','accent2':'#283A8C','icon':'banking','tone':'navy','title':'Banking'},
    'electricity_studio':{'family':'utilities','accent':'#FFD24A','accent2':'#FF8A2D','icon':'electricity','tone':'amber','title':'Electricity'},
    'whatsapp_workspace':{'family':'communication','accent':'#48D06A','accent2':'#13A857','icon':'whatsapp','tone':'green','title':'WhatsApp'},
    'email_workspace':{'family':'communication','accent':'#59B1FF','accent2':'#4D62E8','icon':'email','tone':'blue','title':'Email'},
    'drive_workspace':{'family':'communication','accent':'#37D1E8','accent2':'#3478F6','icon':'drive','tone':'cyan','title':'Drive'},
    'letterhead_studio':{'family':'documents','accent':'#FF5B6C','accent2':'#8B57FF','icon':'letterhead','tone':'red','title':'Letterhead Studio'},
    'system_settings_pane':{'family':'system','accent':'#7C86F8','accent2':'#67707E','icon':'settings','tone':'settings','title':'System Settings'},
}
def ui_meta(ep):
    return dict(APP_META.get(ep,{'family':'productivity','accent':'#248CFF','accent2':'#6757E8','icon':'home','tone':'blue','title':ep.replace('_',' ').title()}))

env.globals.update(
    url_for=lambda endpoint,**kw:'#'+endpoint,
    get_flashed_messages=lambda **kw:[],
    can_access=lambda *a,**k: True,
    ui_app_available=lambda *a,**k: True,
    ui_app_meta=ui_meta,
    masked_aadhaar=lambda x:x,
)
USER=SimpleNamespace(avatar_data_uri='',photo_data_uri='',full_name='Admin',username='admin',role='admin',id=1)
COMMON=dict(current_user=USER,app_version='27.0.1',os_name='Tesla OS 27',os_version='27.0.1',os_build='27A101',marquee_enabled=False,is_admin=True,companion_enabled=False,kiosk_mode_enabled=False,mascot_preferences=SimpleNamespace(position='right',size='medium',intensity='subtle'),companion_default_city='Gurugram',companion_weather_effects=False,dock_apps=[],module_labels={},cloud_whatsapp=False,google_connected=False,connected=False,configured=False)
settings_item=SimpleNamespace(group='Appearance',key='appearance',label='Appearance',description='Colour and material',icon='settings')
SCENARIOS={
    'agreements':('agreements.html',dict(items=[])),
    'banking':('banking.html',dict(banks=[],templates=[],statements=[],runs=[])),
    'rooms':('rooms.html',dict(rows=[],cities=[])),
    'queries':('queries.html',dict(items=[],cities=[],users=[],templates=[],request=SimpleNamespace(endpoint='queries',args={}))),
    'reviews':('reviews.html',dict(form_data={},review_url='',generated=[],history=[])),
    'food':('food.html',dict(integrations=[],total_gross=0,total_net=0,items=[])),
    'billing':('rentok.html',dict(url='#')),
    'electricity':('electricity.html',dict(providers=[],cities=[],vault_entries=[],connections=[],bills=[],bill_draft=None,payment_by_bill={})),
    'whatsapp':('whatsapp.html',dict(configured=False,templates=[],recent=[])),
    'email':('email.html',dict(connected=False,messages=[])),
    'drive':('drive.html',dict(connected=False,files=[])),
    'letterhead':('letterhead_studio.html',dict(documents=[],templates=[],recent=[],drafts=[])),
    'settings':('system_settings.html',dict(settings_panes=[settings_item],selected_settings_pane='appearance',selected_settings=settings_item)),
}
ENDPOINTS={'banking':'banking_suite','billing':'billing','electricity':'electricity_studio','whatsapp':'whatsapp_workspace','email':'email_workspace','drive':'drive_workspace','letterhead':'letterhead_studio','settings':'system_settings_pane'}


def render(name,template,extra):
    ctx={**COMMON,**extra}
    ctx.setdefault('request',SimpleNamespace(endpoint=ENDPOINTS.get(name,name),args={}))
    html=env.get_template(template).render(**ctx)
    html=re.sub(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>','',html,flags=re.I)
    html=re.sub(r'<script[^>]*>[\s\S]*?</script>','',html,flags=re.I)
    html=re.sub(r'<script[^>]+src=[^>]+></script>','',html,flags=re.I)
    return html

def rgba(value):
    nums=re.findall(r'[0-9.]+',value or '')
    if len(nums)<3:return 255,255,255,1.0
    r,g,b=(float(nums[0]),float(nums[1]),float(nums[2]))
    a=float(nums[3]) if len(nums)>3 else 1.0
    return r,g,b,a

def luma(value):
    r,g,b,a=rgba(value)
    if a <= 0.02:
        return 255
    return .2126*r+.7152*g+.0722*b

def audit_page(page,name,width,height):
    data=page.evaluate("""()=>{
      const rect=e=>{const r=e?.getBoundingClientRect();return r?{x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom}:null};
      const root=document.documentElement,main=document.querySelector('#appMain'),toolbar=document.querySelector('#macToolbar');
      const visible=e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0};
      const heads=[...main.querySelectorAll('h1,h2,h3')].filter(visible).map(e=>({text:e.textContent.trim(),sw:e.scrollWidth,cw:e.clientWidth,sh:e.scrollHeight,ch:e.clientHeight,wb:getComputedStyle(e).wordBreak,ow:getComputedStyle(e).overflowWrap}));
      const buttons=[...main.querySelectorAll('button,.btn')].filter(visible).map(e=>({text:e.textContent.trim(),r:rect(e)}));
      const tabs=[...main.querySelectorAll('.safe-tab')].filter(visible).map(e=>({text:e.textContent.trim(),r:rect(e),sh:e.scrollHeight,ch:e.clientHeight,ws:getComputedStyle(e).whiteSpace}));
      const dark=[...main.querySelectorAll('section,article,div')].filter(visible).map(e=>{const r=rect(e),s=getComputedStyle(e);return {r,bg:s.backgroundColor,cls:e.className||''}}).filter(x=>x.r.w*x.r.h>innerWidth*innerHeight*.18);
      const mascotEl=document.querySelector('.mascot-companion'),footerEl=document.querySelector('.utility-legal-footer');
      return {root:{sw:root.scrollWidth,cw:root.clientWidth},main:{r:rect(main),bg:getComputedStyle(main).backgroundColor,bgi:getComputedStyle(main).backgroundImage,color:getComputedStyle(main).color},toolbar:toolbar?{r:rect(toolbar),bg:getComputedStyle(toolbar).backgroundColor}:null,heads,buttons,tabs,dark,mascot:mascotEl&&visible(mascotEl)?rect(mascotEl):null,footer:footerEl&&visible(footerEl)?rect(footerEl):null};
    }""")
    failures=[]
    if data['root']['sw']>width+2: failures.append(f"horizontal page overflow {data['root']}")
    if data['toolbar'] and abs(data['toolbar']['r']['h']-52)>1.5: failures.append(f"route toolbar height {data['toolbar']['r']['h']}")
    if luma(data['main']['bg'])<145: failures.append(f"dark main canvas {data['main']['bg']}")
    for h in data['heads']:
        if h['sw']>h['cw']+2 or h['sh']>h['ch']+3: failures.append(f"clipped heading {h['text']}")
        if h['wb']!='normal': failures.append(f"heading word-break {h['text']} {h['wb']}")
    for t in data['tabs']:
        if t['ws']!='nowrap' or t['sh']>t['ch']+2: failures.append(f"tab wraps {t['text']}")
    for b in data['buttons']:
        h=b['r']['h']
        if h>48 and b['text'] and len(b['text'])<40:
            # Appearance choice cards are intentionally preview-sized controls, not toolbar buttons.
            if not any(label in b['text'] for label in ('AutomaticFollow this device','LightBright app surfaces','DarkDark app surfaces')):
                failures.append(f"oversized control {b['text']} {h}")
    for d in data['dark']:
        if luma(d['bg'])<55: failures.append(f"large dark slab {d['cls']} {d['bg']}")
    if data['mascot']: failures.append('mascot overlaps full-page app route')
    if data['footer']: failures.append('legacy footer visible on app route')
    return failures,data

def main():
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page()
        for name,(template,extra) in SCENARIOS.items():
            html=render(name,template,extra)
            for width,height in ((1440,900),(1152,720)):
                page.set_viewport_size({'width':width,'height':height})
                page.set_content(html,wait_until='load')
                page.evaluate("document.documentElement.dataset.appearance='light'")
                page.add_style_tag(content=LEGACY)
                if name=='settings': page.add_style_tag(content=INTEGRATIONS)
                if name=='letterhead': page.add_style_tag(content=LETTERHEAD)
                page.add_style_tag(content=SYSTEM)
                page.add_script_tag(content=SHELL)
                page.wait_for_timeout(80)
                failures,data=audit_page(page,name,width,height)
                results.append({'scenario':name,'viewport':f'{width}x{height}','failures':failures,'data':data})
                if width==1440:
                    page.screenshot(path=str(OUT/f'{name}-1440x900.png'),full_page=False)
        browser.close()
    (OUT/'template_browser_audit.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    bad=[r for r in results if r['failures']]
    print(f'Hotfix 9 real-template Chromium scenarios: {len(results)}; failures: {len(bad)}')
    for r in bad[:30]: print(r['scenario'],r['viewport'],r['failures'][:8])
    if bad: raise SystemExit(1)

if __name__=='__main__':main()
