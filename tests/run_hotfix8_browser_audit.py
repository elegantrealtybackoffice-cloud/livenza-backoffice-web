from __future__ import annotations

import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "hotfix8_visual_fixture.html"
OUT = ROOT / "tests" / "audit_artifacts" / "hotfix8"
OUT.mkdir(parents=True, exist_ok=True)
FIXTURE_HTML = re.sub(r"<link[^>]+rel=[\"\']stylesheet[\"\'][^>]*>", "", FIXTURE.read_text(encoding="utf-8"), flags=re.I)
LEGACY_CSS = (ROOT / "static" / "legacy_modules.css").read_text(encoding="utf-8")
SYSTEM_CSS = (ROOT / "static" / "macos27_system.css").read_text(encoding="utf-8")

VIEWPORTS = [(1920,1080),(1440,900),(1366,768),(1152,720)]
SUITES = ["agreements","banking","creative","settings","overlap"]


def audit_one(page, width: int, height: int, suite: str, reduced: bool = False):
    page.set_viewport_size({"width": width, "height": height})
    page.emulate_media(reduced_motion="reduce" if reduced else "no-preference")
    page.set_content(FIXTURE_HTML, wait_until="load")
    page.add_style_tag(content=LEGACY_CSS)
    page.add_style_tag(content=SYSTEM_CSS)
    page.evaluate("""(suite) => {
      const ws=[...document.querySelectorAll('.demo-window')];
      ws.forEach(w=>w.hidden=true);
      if(suite==='overlap'){
        const a=ws.find(w=>w.dataset.demo==='agreements'); const b=ws.find(w=>w.dataset.demo==='banking');
        if(a)a.hidden=false; if(b){b.hidden=false;b.style.left='480px';b.style.top='210px';b.style.width='720px';b.style.height='500px';}
      }else{const w=ws.find(w=>w.dataset.demo===suite)||ws[0];if(w)w.hidden=false;}
    }""", suite)
    page.evaluate("""() => {
      const safe={left:10,top:42,right:innerWidth-10,bottom:innerHeight-80};
      document.querySelectorAll('.demo-window:not([hidden])').forEach((w)=>{
        const r=w.getBoundingClientRect();
        const minWidth=Math.min(560,Math.max(360,safe.right-safe.left));
        const minHeight=Math.min(360,Math.max(260,safe.bottom-safe.top));
        const width=Math.max(minWidth,Math.min(r.width,safe.right-safe.left));
        const height=Math.max(minHeight,Math.min(r.height,safe.bottom-safe.top));
        const left=Math.max(safe.left,Math.min(r.left,safe.right-width));
        const top=Math.max(safe.top,Math.min(r.top,safe.bottom-height));
        Object.assign(w.style,{left:`${left}px`,top:`${top}px`,width:`${width}px`,height:`${height}px`});
      });
    }""")
    page.wait_for_timeout(80)
    data = page.evaluate("""() => {
      const rect=o=>{const r=o?.getBoundingClientRect();return r?{x:r.x,y:r.y,w:r.width,h:r.height,right:r.right,bottom:r.bottom}:null};
      const body=document.documentElement;
      const dock=document.querySelector('.mac-dock');
      const widgets=document.querySelector('.home-widget-stack');
      const wins=[...document.querySelectorAll('.demo-window:not([hidden])')].map(w=>({app:w.dataset.windowApp,rect:rect(w)}));
      const icons=[...document.querySelectorAll('.mac-dock-icon')].map(icon=>{
        const svg=icon.querySelector('svg'); let bbox=null; try{const b=svg?.getBBox();bbox=b?{w:b.width,h:b.height}:null}catch(e){}
        const cs=svg?getComputedStyle(svg):null;
        return {bbox,stroke:cs?.stroke||'',fill:cs?.fill||'',bg:getComputedStyle(icon).backgroundImage};
      });
      const clipSelectors=['.mac-window-title','h1','h2','.stats b','.home-widget-heading strong','.home-agenda-row b','.home-agenda-row small','.home-weather-copy strong'];
      const clipped=[];
      clipSelectors.forEach(sel=>document.querySelectorAll(sel).forEach(el=>{
        if(el.closest('[hidden]'))return;
        const cs=getComputedStyle(el); const horizontal=el.scrollWidth>el.clientWidth+1; const vertical=el.scrollHeight>el.clientHeight+1;
        if(horizontal||vertical)clipped.push({selector:sel,text:(el.textContent||'').trim().slice(0,80),sw:el.scrollWidth,cw:el.clientWidth,sh:el.scrollHeight,ch:el.clientHeight,overflow:cs.overflow});
      }));
      const firstSurface=document.querySelector('.demo-window:not([hidden]) .mac-suite-surface>.shell,.demo-window:not([hidden]) .mac-suite-surface>section,.demo-window:not([hidden]) .mac-suite-surface>div');
      const motion=firstSurface?getComputedStyle(firstSurface):null;
      return {
        viewport:{w:innerWidth,h:innerHeight},
        body:{sw:body.scrollWidth,sh:body.scrollHeight,cw:body.clientWidth,ch:body.clientHeight},
        dock:rect(dock),widgets:rect(widgets),wins,icons,clipped,
        motion:firstSurface?{animationDuration:motion.animationDuration,transitionDuration:motion.transitionDuration}:null
      };
    }""")
    failures=[]
    if data["body"]["sw"] > width + 1 or data["body"]["sh"] > height + 1:
        failures.append(f"desktop overflow {data['body']}")
    dock=data["dock"]
    if not dock or abs(dock["h"]-58)>1:
        failures.append(f"Dock height {dock}")
    elif dock["bottom"] > height+1 or dock["x"] < -1 or dock["right"] > width+1:
        failures.append(f"Dock out of viewport {dock}")
    widgets=data["widgets"]
    if widgets and width >= 1366 and abs(widgets["w"]-344)>1.5:
        failures.append(f"Widget width {widgets['w']}")
    if widgets and dock:
        overlap = not (widgets["right"] <= dock["x"] or widgets["x"] >= dock["right"] or widgets["bottom"] <= dock["y"] or widgets["y"] >= dock["bottom"])
        if overlap: failures.append("widgets overlap Dock")
    safe={"left":10,"top":42,"right":width-10,"bottom":height-80}
    for win in data["wins"]:
        r=win["rect"]
        if r["x"] < safe["left"]-1 or r["y"] < safe["top"]-1 or r["right"] > safe["right"]+1 or r["bottom"] > safe["bottom"]+1:
            failures.append(f"window {win['app']} outside safe bounds {r}")
    if len(data["icons"]) < 12:
        failures.append(f"too few functional Dock icons: {len(data['icons'])}")
    for idx, icon in enumerate(data["icons"]):
        b=icon.get("bbox") or {}
        if b.get("w",0)<5 or b.get("h",0)<5:
            failures.append(f"blank Dock icon {idx}: {icon}")
        if icon.get("stroke") in ("none","rgba(0, 0, 0, 0)",""):
            failures.append(f"missing icon stroke {idx}: {icon.get('stroke')}")
        if icon.get("bg") in ("none",""):
            failures.append(f"missing icon background {idx}")
    if data["clipped"]:
        failures.append(f"clipped key text: {data['clipped'][:4]}")
    if reduced and data.get("motion") and data["motion"]["animationDuration"] not in ("0s","0ms"):
        failures.append(f"reduced motion animation still active: {data['motion']}")
    return {"viewport":f"{width}x{height}","suite":suite,"reduced_motion":reduced,"failures":failures,"data":data}


def main():
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path="/usr/bin/chromium",headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
        page=browser.new_page()
        for width,height in VIEWPORTS:
            for suite in SUITES:
                results.append(audit_one(page,width,height,suite,False))
            results.append(audit_one(page,width,height,"agreements",True))
        # Fresh visual evidence from the main desktop-sized audit cases.
        for suite in SUITES:
            page.set_viewport_size({"width":1440,"height":900})
            page.emulate_media(reduced_motion="no-preference")
            page.set_content(FIXTURE_HTML, wait_until="load")
            page.add_style_tag(content=LEGACY_CSS)
            page.add_style_tag(content=SYSTEM_CSS)
            page.evaluate("""(suite) => {const ws=[...document.querySelectorAll('.demo-window')];ws.forEach(w=>w.hidden=true);if(suite==='overlap'){const a=ws.find(w=>w.dataset.demo==='agreements'),b=ws.find(w=>w.dataset.demo==='banking');if(a)a.hidden=false;if(b){b.hidden=false;b.style.left='480px';b.style.top='210px';b.style.width='720px';b.style.height='500px'}}else{const w=ws.find(w=>w.dataset.demo===suite)||ws[0];if(w)w.hidden=false;}const safe={left:10,top:42,right:innerWidth-10,bottom:innerHeight-80};document.querySelectorAll('.demo-window:not([hidden])').forEach(w=>{const r=w.getBoundingClientRect(),width=Math.min(r.width,safe.right-safe.left),height=Math.min(r.height,safe.bottom-safe.top);Object.assign(w.style,{left:`${Math.max(safe.left,Math.min(r.left,safe.right-width))}px`,top:`${Math.max(safe.top,Math.min(r.top,safe.bottom-height))}px`,width:`${width}px`,height:`${height}px`})})}""", suite)
            page.screenshot(path=str(OUT/f"{suite}-1440x900-final.png"),full_page=False)
        browser.close()
    (OUT/"browser_audit_final.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
    failures=[r for r in results if r["failures"]]
    print(f"Browser audit scenarios: {len(results)}; failures: {len(failures)}")
    if failures:
        for r in failures[:12]:
            print(r["viewport"],r["suite"],"reduced" if r["reduced_motion"] else "motion",r["failures"])
        raise SystemExit(1)

if __name__=="__main__":
    main()
