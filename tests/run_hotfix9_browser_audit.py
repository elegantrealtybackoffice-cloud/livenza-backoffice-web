from __future__ import annotations

import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests' / 'hotfix9_visual_fixture.html'
OUT = ROOT / 'tests' / 'audit_artifacts' / 'hotfix9'
OUT.mkdir(parents=True, exist_ok=True)
HTML = re.sub(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', '', FIXTURE.read_text(encoding='utf-8'), flags=re.I)
LEGACY = (ROOT/'static/legacy_modules.css').read_text(encoding='utf-8')
SYSTEM = (ROOT/'static/macos27_system.css').read_text(encoding='utf-8')
VIEWPORTS=[(1920,1080),(1600,900),(1440,900),(1366,768),(1280,720),(1152,720)]
SCENARIOS=['launcher','agreements','banking','creative','settings','overlap']

def rgb_luma(value: str) -> float:
    nums=[int(x) for x in re.findall(r'\d+', value)[:3]]
    if len(nums)<3: return 255
    r,g,b=nums
    return .2126*r+.7152*g+.0722*b

def prepare(page, width, height, scenario, reduced=False):
    page.set_viewport_size({'width':width,'height':height})
    page.emulate_media(reduced_motion='reduce' if reduced else 'no-preference')
    page.set_content(HTML, wait_until='load')
    page.add_style_tag(content=LEGACY)
    page.add_style_tag(content=SYSTEM)
    page.evaluate("""(scenario)=>{
      const launcher=document.querySelector('.suites-launcher');
      const wins=[...document.querySelectorAll('.demo-window')];
      wins.forEach(w=>w.hidden=true);
      if(launcher) launcher.hidden=scenario!=='launcher';
      if(scenario==='overlap'){
        const a=wins.find(w=>w.dataset.demo==='agreements'); const b=wins.find(w=>w.dataset.demo==='banking');
        if(a)a.hidden=false;if(b){b.hidden=false;b.style.left='480px';b.style.top='210px';b.style.width='720px';b.style.height='500px';}
      } else if(scenario!=='launcher') {
        const w=wins.find(w=>w.dataset.demo===scenario)||wins[0]; if(w)w.hidden=false;
      }
      const safe={left:10,top:42,right:innerWidth-10,bottom:innerHeight-80};
      document.querySelectorAll('.demo-window:not([hidden])').forEach(w=>{
        const r=w.getBoundingClientRect();
        const width=Math.min(r.width,safe.right-safe.left),height=Math.min(r.height,safe.bottom-safe.top);
        Object.assign(w.style,{left:`${Math.max(safe.left,Math.min(r.left,safe.right-width))}px`,top:`${Math.max(safe.top,Math.min(r.top,safe.bottom-height))}px`,width:`${width}px`,height:`${height}px`});
      });
      window.scrollTo(0,0);
    }""", scenario)
    page.wait_for_timeout(100)

def audit(page,width,height,scenario,reduced=False):
    prepare(page,width,height,scenario,reduced)
    d=page.evaluate("""()=>{
      const rect=e=>{const r=e?.getBoundingClientRect();return r?{x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom}:null};
      const root=document.documentElement,dock=document.querySelector('.mac-dock'),launcher=document.querySelector('.suites-launcher:not([hidden])');
      const cards=[...document.querySelectorAll('.suite-launch-card')].filter(e=>!e.closest('[hidden]')).map(e=>({rect:rect(e),title:(e.querySelector('.suite-launch-title')?.textContent||'').trim(),titleRect:rect(e.querySelector('.suite-launch-title')),titleStyle:{wordBreak:getComputedStyle(e.querySelector('.suite-launch-title')).wordBreak,overflowWrap:getComputedStyle(e.querySelector('.suite-launch-title')).overflowWrap},color:getComputedStyle(e).color,bg:getComputedStyle(e).backgroundColor}));
      const tabs=[...document.querySelectorAll('.suites-launcher .safe-tab')].map(e=>({text:e.textContent.trim(),rect:rect(e),whiteSpace:getComputedStyle(e).whiteSpace,sh:e.scrollHeight,ch:e.clientHeight}));
      const win=document.querySelector('.demo-window:not([hidden])');const content=win?.querySelector('.mac-window-content');
      const headings=[...document.querySelectorAll('.demo-window:not([hidden]) h1,.demo-window:not([hidden]) h2,.suite-launch-title')].map(e=>({text:e.textContent.trim(),sw:e.scrollWidth,cw:e.clientWidth,sh:e.scrollHeight,ch:e.clientHeight,wordBreak:getComputedStyle(e).wordBreak,overflowWrap:getComputedStyle(e).overflowWrap}));
      const motion=document.querySelector('.suite-launch-card')||document.querySelector('.demo-window:not([hidden]) .mac-suite-surface>.shell');
      return {body:{sw:root.scrollWidth,sh:root.scrollHeight,cw:root.clientWidth,ch:root.clientHeight},dock:rect(dock),launcher:rect(launcher),cards,tabs,win:rect(win),content:content?{bg:getComputedStyle(content).backgroundColor,color:getComputedStyle(content).color}:null,headings,motion:motion?{animation:getComputedStyle(motion).animationDuration,transition:getComputedStyle(motion).transitionDuration}:null};
    }""")
    f=[]
    if d['body']['sw']>width+1 or d['body']['sh']>height+1:f.append(f"desktop overflow {d['body']}")
    if not d['dock'] or abs(d['dock']['h']-58)>1.2:f.append(f"Dock geometry {d['dock']}")
    if scenario=='launcher':
        r=d['launcher']
        if not r:f.append('launcher missing')
        else:
            if r['x']<-1 or r['right']>width+1 or r['y']<0 or r['bottom']>height-65:f.append(f'launcher out of safe bounds {r}')
        if len(d['cards'])<5:f.append(f"too few launcher cards {len(d['cards'])}")
        for c in d['cards']:
            if c['rect']['w']<218 and width>=1152:f.append(f"launcher card too narrow {c['title']} {c['rect']['w']}")
            if c['titleStyle']['wordBreak']!='normal' or c['titleStyle']['overflowWrap'] not in ('normal',''):
                f.append(f"bad title wrapping {c['title']} {c['titleStyle']}")
        for t in d['tabs']:
            if t['whiteSpace']!='nowrap' or t['sh']>t['ch']+1:f.append(f"tab wraps {t}")
    else:
        if d['content'] and rgb_luma(d['content']['bg'])<110:f.append(f"suite canvas is dark {d['content']}")
        if d['content'] and rgb_luma(d['content']['color'])>150:f.append(f"suite primary text too light {d['content']}")
    for h in d['headings']:
        if h['sw']>h['cw']+2 or h['sh']>h['ch']+2:f.append(f"clipped heading {h}")
        if h['wordBreak']!='normal':f.append(f"heading breaks words {h}")
    if reduced and d.get('motion'):
        if d['motion']['animation'] not in ('0s','0ms') or d['motion']['transition'] not in ('0s','0ms'):
            f.append(f"reduced motion active {d['motion']}")
    return {'viewport':f'{width}x{height}','scenario':scenario,'reduced':reduced,'failures':f,'data':d}

def main():
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page()
        for w,h in VIEWPORTS:
            for scenario in SCENARIOS: results.append(audit(page,w,h,scenario,False))
            results.append(audit(page,w,h,'launcher',True))
            results.append(audit(page,w,h,'agreements',True))
        for scenario in SCENARIOS:
            prepare(page,1440,900,scenario,False)
            page.screenshot(path=str(OUT/f'{scenario}-1440x900.png'),full_page=False)
        browser.close()
    (OUT/'browser_audit.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    failures=[r for r in results if r['failures']]
    print(f'Hotfix 9 Chromium scenarios: {len(results)}; failures: {len(failures)}')
    for r in failures[:16]: print(r['viewport'],r['scenario'],r['failures'])
    if failures: raise SystemExit(1)

if __name__=='__main__': main()
