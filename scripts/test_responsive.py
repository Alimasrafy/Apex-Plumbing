"""Development-only checks for the full-width design with centered 1200px content containers."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
paths=['index.html',*[str(p.relative_to(ROOT)) for p in sorted((ROOT/'pages').rglob('*.html'))]]
widths=[320,360,375,390,414,430,479,480,600,767,768,820,1024,1100,1199,1200,1280,1366,1440,1536,1920,2560,3840]
r={'page_count':len(paths),'widths':widths,'themes':['light','dark'],'cases':0,'failures':[],'page_errors':[],'checks':[]}
def check(name,ok,detail=None):
 r['checks'].append({'name':name,'passed':bool(ok)})
 if not ok:r['failures'].append({'name':name,'detail':detail})
with sync_playwright() as pw:
 b=pw.chromium.launch()
 for theme in r['themes']:
  ctx=b.new_context(color_scheme=theme,reduced_motion='reduce')
  page=ctx.new_page();page.on('pageerror',lambda e:r['page_errors'].append(str(e)))
  for path in paths:
   page.goto('http://127.0.0.1:3000/'+path,wait_until='networkidle');page.evaluate('document.fonts.ready')
   for w in widths:
    page.set_viewport_size({'width':w,'height':900})
    d=page.evaluate('''() => {
      const box=e=>{const r=e.getBoundingClientRect();return {x:r.left,right:r.right,width:r.width}};
      const body=box(document.body), main=box(document.querySelector('main'));
      const containers=[...document.querySelectorAll('.container')].map(box);
      const header=box(document.querySelector('.site-header'));
      const footer=box(document.querySelector('.site-footer'));
      const desktop=getComputedStyle(document.querySelector('.menu-toggle')).display==='none';
      const links=[...document.querySelectorAll('.header-inner>.brand,.header-inner>.theme-toggle,.header-inner>.header-cta,.header-inner>.menu-toggle,.main-nav>ul>li')].filter(e=>e.getClientRects().length).map(box);
      return {vw:document.documentElement.clientWidth,body,main,header,footer,containers,desktop,links,
       sections:[...document.querySelectorAll('main>.home-hero,main>.page-hero,main>.section,main>.trust-strip,main>.final-cta,main>.emergency-band')].map(box),
       overflow:document.documentElement.scrollWidth>document.documentElement.clientWidth,
       images:[...document.images].filter(e=>e.getClientRects().length).map(box)};
    }''')
    label=f'{path} {theme} @{w}'
    expected=d['vw']
    check(label+' full-width canvas/header/main/footer',all(abs(d[k]['width']-expected)<1 and abs(d[k]['x'])<1 for k in ['body','main','header','footer']),d)
    check(label+' section backgrounds remain full-width',all(abs(x['width']-expected)<1 and abs(x['x'])<1 for x in d['sections']),d)
    check(label+' only content is capped and centered',bool(d['containers']) and all(x['width']<=1200.5 and abs(x['x']-(d['vw']-x['width'])/2)<1 for x in d['containers']),d)
    check(label+' real reflow without horizontal overflow',not d['overflow'] and all(x['x']>=d['body']['x']-1 and x['right']<=d['body']['right']+1 for x in d['containers']+d['images']+d['links']),d)
    check(label+' correct navigation breakpoint',d['desktop']==(w>=1200),d)
    r['cases']+=1
  if theme=='light':
   page.goto('http://127.0.0.1:3000/');page.set_viewport_size({'width':1920,'height':1080})
   page.screenshot(path=str(ROOT/'docs/responsive-desktop-1920.png'),full_page=True)
   page.keyboard.press('Tab');skip=page.locator('.skip-link').bounding_box();body=page.locator('body').bounding_box()
   check('Keyboard skip link stays accessible inside viewport',skip['x']>=body['x'] and skip['x']+skip['width']<=body['x']+body['width'])
   page.locator('.site-footer').scroll_into_view_if_needed();page.locator('.back-top').wait_for(state='visible');top=page.locator('.back-top').bounding_box()
   check('Desktop back-to-top retains original viewport placement',top['x']>=body['x'] and top['x']+top['width']<=body['x']+body['width'])
   page.set_viewport_size({'width':390,'height':844});page.goto('http://127.0.0.1:3000/');page.screenshot(path=str(ROOT/'docs/responsive-mobile-390.png'),full_page=True)
   page.set_viewport_size({'width':820,'height':1180});page.goto('http://127.0.0.1:3000/pages/contact/contact.html');page.screenshot(path=str(ROOT/'docs/responsive-tablet-820.png'),full_page=True)
  ctx.close()
 b.close()
r['passed']=not r['failures'] and not r['page_errors']
(ROOT/'docs/responsive-qa.json').write_text(json.dumps(r,indent=2))
print(json.dumps({k:v for k,v in r.items() if k!='checks'},indent=2))
raise SystemExit(0 if r['passed'] else 1)
