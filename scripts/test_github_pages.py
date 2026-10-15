"""Local staged-artifact simulation; never publishes or contacts GitHub/WhatsApp.
Playwright URLs match project Pages, account Pages and custom-domain deployments;
all browser traffic is intercepted and fulfilled directly from staged local files.
"""
import json
import subprocess
import sys
import mimetypes
from pathlib import Path
from urllib.parse import urlsplit, unquote, parse_qs
from playwright.sync_api import sync_playwright, expect
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'
r={'checks':[],'deployment_shapes':[],'page_viewport_cases':0,'page_errors':[],'resource_errors':[],'external_requests':[]}
def check(name,ok):
    r['checks'].append({'name':name,'passed':bool(ok)})
    if not ok:print('FAILED',name,flush=True)
def make_route(base):
    origin=urlsplit(base)
    def handle(route):
        url=urlsplit(route.request.url)
        if url.hostname==origin.hostname:
            relative=unquote(url.path[len(origin.path):]) if url.path.startswith(origin.path) else '__outside_repository__'
            target=(OUT/(relative or 'index.html')).resolve()
            status=200
            if not target.is_relative_to(OUT.resolve()) or not target.is_file():
                target=OUT/'404.html';status=404
            if status>=400 and route.request.resource_type!='document':r['resource_errors'].append(route.request.url)
            route.fulfill(status=status,body=target.read_bytes(),content_type=mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
        elif url.hostname=='wa.me':
            route.fulfill(status=200,content_type='text/html',body='<title>Intercepted WhatsApp draft</title>')
        else:
            r['external_requests'].append(route.request.url);route.abort()
    return handle
bases=['https://qa-owner.github.io/apex-plumbing/','https://qa-owner.github.io/','https://plumbing-release.site/']
source_snapshots={p:p.read_bytes() for p in [ROOT/'index.html',*list((ROOT/'pages').rglob('*.html')),ROOT/'robots.txt',ROOT/'assets/data/site.json']}
with sync_playwright() as pw:
 browser=pw.chromium.launch()
 for base in bases:
  subprocess.run([sys.executable,str(ROOT/'scripts/prepare_pages.py'),'--base-url',base],check=True)
  ctx=browser.new_context(reduced_motion='reduce',color_scheme='light')
  ctx.route('**/*',make_route(base))
  p=ctx.new_page();p.on('pageerror',lambda e:r['page_errors'].append(str(e)))
  for rel in ['index.html',*[str(x.relative_to(OUT)) for x in sorted((OUT/'pages').rglob('*.html'))],'404.html']:
   for width in [390,1440]:
    p.set_viewport_size({'width':width,'height':1000});response=p.goto(base+rel,wait_until='networkidle')
    p.evaluate('[...document.images].forEach(i=>i.loading="eager")');p.wait_for_function('[...document.images].every(i=>i.complete)')
    check(f'{base}{rel} @{width}: loads without overflow/broken imagery',response.status==200 and p.locator('h1').count()==1 and p.evaluate('document.documentElement.scrollWidth<=innerWidth && [...document.images].every(i=>i.complete&&i.naturalWidth>0)'))
    check(f'{base}{rel} @{width}: body full-width, content <=1200',p.evaluate('Math.abs(document.body.getBoundingClientRect().width-document.documentElement.clientWidth)<1 && [...document.querySelectorAll(".container")].every(e=>e.getBoundingClientRect().width<=1200.5)'))
    r['page_viewport_cases']+=1
  # Hover all three menus after domain/base-path staging.
  p.goto(base);p.set_viewport_size({'width':1440,'height':1000})
  for id in ['nav-services','nav-service-areas','nav-blog']:
   p.locator('[aria-controls="'+id+'"]').locator('xpath=..').locator('.nav-link').hover();expect(p.locator('#'+id)).to_be_visible()
   p.locator('#'+id+' a').last.hover();check(base+id+' submenu remains hoverable',p.locator('#'+id).is_visible())
   p.locator('.site-header .brand').hover();expect(p.locator('#'+id)).to_be_hidden()
  p.locator('.theme-toggle').click();p.reload();check(base+' theme persists across reload',p.evaluate('document.documentElement.dataset.theme==="dark" && localStorage.getItem("apex-theme")==="dark"'))
  p.set_viewport_size({'width':390,'height':844});p.locator('.menu-toggle').click();expect(p.locator('.main-nav')).to_be_visible();p.keyboard.press('Escape');expect(p.locator('.main-nav')).to_be_hidden();check(base+' mobile navigation + Escape',True)
  # Existing business controls under the deployment prefix.
  p.goto(base+'pages/blog/blog.html');p.locator('#blog-search').fill('zz-no-guide-zz');check(base+' blog search',p.locator('#blog-empty').is_visible());p.locator('#blog-search').fill('')
  p.goto(base+'pages/service-areas/service-areas.html');p.locator('[data-location="3"]').click();check(base+' service-area selector','Pflugerville' in p.locator('#map-detail h3').inner_text())
  p.goto(base+'pages/reviews/reviews.html');p.locator('[data-review-filter="Drain Cleaning"]').click();check(base+' approach filter',p.locator('#reviews-grid .review-card:visible').count()==1)
  p.goto(base+'pages/contact/contact.html');p.locator('button[type=submit]').click();check(base+' required-field validation',p.locator('[aria-invalid=true]').count()==7)
  for key,value in {'name':'GitHub QA <A&B>','phone':'+8801718658326','email':'qa@example.com','location':'Austin, TX','message':'Local staging test; nothing should be sent.'}.items():p.locator('#'+key).fill(value)
  p.locator('#service').select_option(label='Leak Detection');p.locator('#consent').check()
  requests=[];listener=lambda req:requests.append(req.url);p.on('request',listener)
  p.locator('button[type=submit]').click();link=p.locator('#form-status a[href^="https://wa.me/"]');url=link.get_attribute('href')
  check(base+' form prepares without network/storage',not requests and p.evaluate('sessionStorage.length===0 && localStorage.length===1'))
  check(base+' correctly encoded draft',urlsplit(url).path=='/8801718658326' and 'GitHub QA <A&B>' in parse_qs(urlsplit(url).query)['text'][0])
  with p.expect_popup() as pop:link.click()
  popup=pop.value;popup.wait_for_load_state();check(base+' explicit handoff intercepted',popup.url==url);popup.close();p.remove_listener('request',listener)
  for unknown in ['missing-page','nested/deep/missing-page']:
   response=p.goto(base+unknown,wait_until='networkidle')
   check(base+unknown+' actual 404 status + styled page',response.status==404 and p.locator('h1').count()==1 and p.evaluate('[...document.styleSheets].length>=15 && [...document.images].every(i=>i.complete&&i.naturalWidth>0)'))
   check(base+unknown+' recovery link keeps repository prefix',p.locator('.site-header .brand').get_attribute('href')==base+'index.html')
   p.locator('.site-header .brand').click();check(base+unknown+' recovery navigates home',p.url==base+'index.html')
  if 'apex-plumbing/' in base:
   p.set_viewport_size({'width':1440,'height':1000});p.goto(base);p.locator('.theme-toggle').click();p.screenshot(path=str(ROOT/'docs/github-pages-preview.png'))
  r['deployment_shapes'].append({'base':base,'simulated_locally':True,'html_documents':29,'sitemap_urls':26})
  p.goto('about:blank');ctx.unroute_all(behavior='wait');ctx.close()
 browser.close()

check('Deployment preparation leaves source HTML/robots/data untouched',all(p.read_bytes()==value for p,value in source_snapshots.items()))
check('No browser JS errors',not r['page_errors']);check('No missing deployed resources',not r['resource_errors']);check('No unexpected external traffic',not r['external_requests'])
r['passed']=all(x['passed'] for x in r['checks'])
(ROOT/'docs/github-pages-qa.json').write_text(json.dumps(r,indent=2))
print(json.dumps({'passed':r['passed'],'checks':len(r['checks']),'page_viewport_cases':r['page_viewport_cases'],'failures':[x for x in r['checks'] if not x['passed']],'page_errors':r['page_errors'],'resource_errors':r['resource_errors'],'external_requests':r['external_requests']},indent=2))
raise SystemExit(0 if r['passed'] else 1)
