"""Authoring QA only. Requires beautifulsoup4 and playwright; not used by the website."""
import json, re
from pathlib import Path
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:3000/'
pages=[ROOT/'index.html',*sorted((ROOT/'pages').rglob('*.html'))]
report={'page_count':len(pages),'static_errors':[],'browser_errors':[],'overflow':[],'image_errors':[],'axe_violations':[],'interactions':[],'widths':[320,360,390,414,480,600,767,768,820,1023,1024,1100,1199,1200,1280,1440,1920]}
soups={p:BeautifulSoup(p.read_text(),'html.parser') for p in pages}
titles=[];descriptions=[]; references=0
for p,s in soups.items():
 rel=str(p.relative_to(ROOT));titles.append(s.title.text);descriptions.append(s.select_one('meta[name=description]')['content'])
 def err(msg):report['static_errors'].append(rel+': '+msg)
 if len(s.select('h1'))!=1:err('Expected one h1')
 ids=[e['id'] for e in s.select('[id]')]
 if len(ids)!=len(set(ids)):err('Duplicate IDs')
 for image in s.select('img'):
  if not image.has_attr('alt') or not image.get('width') or not image.get('height'):err('Missing alt or image dimensions')
 for tag,attr in [('a','href'),('link','href'),('script','src'),('img','src')]:
  for e in s.select(f'{tag}[{attr}]'):
   url=urlsplit(e[attr])
   if url.scheme or url.netloc:continue
   references+=1
   target=(p.parent/unquote(url.path)).resolve() if url.path else p
   if not target.exists():err('Broken '+attr+': '+e[attr]);continue
   if url.fragment and target.suffix=='.html':
    target_soup=soups.get(target) or BeautifulSoup(target.read_text(),'html.parser')
    if not target_soup.find(id=unquote(url.fragment)):err('Broken anchor: '+e[attr])
 for e in s.select('[aria-controls], [aria-describedby]'):
  for attr in ['aria-controls','aria-describedby']:
   for id in e.get(attr,'').split():
    if not s.find(id=id):err('Missing ARIA target '+id)
 for e in s.select('input:not([type=hidden]),select,textarea'):
  if not s.find('label',attrs={'for':e.get('id')}):err('Missing form label')
 if not s.select_one('link[href$="pages/'+('home' if p.name=='index.html' else 'not used')+'.css"]'):
  css=[x['href'] for x in s.select('link[rel=stylesheet]') if '/pages/' in x['href']]
  if len(css)!=1:err('Expected one dedicated page CSS file')
 for link in s.select('a[href]'):
  if not link.get_text(strip=True) and not link.get('aria-label'):err('Unnamed link')
if len(set(titles))!=len(pages):report['static_errors'].append('Non-unique page titles')
if len(set(descriptions))!=len(pages):report['static_errors'].append('Non-unique descriptions')
for css in (ROOT/'assets/css').rglob('*.css'):
 for raw in re.findall(r'(?:url\()([^)]+)',css.read_text()):
  path=raw.strip('"\' ')
  if not urlsplit(path).scheme and not (css.parent/path).exists():report['static_errors'].append('Broken CSS asset '+str(css)+': '+path)
report['checked_local_references']=references

def check(condition,name):
 report['interactions'].append({'name':name,'passed':bool(condition)})
 if not condition: print('FAILED:',name)

with sync_playwright() as pw:
 b=pw.chromium.launch()
 ctx=b.new_context(viewport={'width':1440,'height':1000})
 page=ctx.new_page()
 page.on('pageerror',lambda e:report['browser_errors'].append(str(e)))
 page.on('console',lambda m:report['browser_errors'].append(m.text) if m.type=='error' else None)
 for p in pages:
  rel=str(p.relative_to(ROOT));page.goto(BASE+rel,wait_until='networkidle')
  for width in report['widths']:
   page.set_viewport_size({'width':width,'height':900})
   page.wait_for_timeout(30)
   over=page.evaluate('document.documentElement.scrollWidth > window.innerWidth')
   if over:
    offenders=page.evaluate('[...document.querySelectorAll("body *")].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.right>innerWidth+1||r.left < -1)}).slice(0,8).map(e=>e.tagName+"."+e.className)')
    report['overflow'].append({'page':rel,'width':width,'elements':offenders})
  # Scroll through the page once to trigger loading of all lazy imagery.
  page.evaluate('document.querySelectorAll("img").forEach(e=>e.loading="eager")');page.wait_for_timeout(80)
  bad=page.locator('img').evaluate_all('(els)=>els.filter(e=>!e.complete||e.naturalWidth===0).map(e=>e.src)')
  if bad:report['image_errors'].append({'page':rel,'images':bad})
  page.set_viewport_size({'width':1440,'height':1000})
  page.wait_for_function('document.getAnimations().every(a=>a.playState!=="running"&&a.playState!=="pending")',timeout=5000)
  page.add_script_tag(path=str(ROOT/'scripts/axe.min.js'))
  result=page.evaluate('async()=>await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa","wcag22aa"]}})')
  for v in result['violations']:
   report['axe_violations'].append({'page':rel,'width':1440,'rule':v['id'],'impact':v['impact'],'nodes':[{'target':n['target'],'summary':n.get('failureSummary','')} for n in v['nodes']]})
  page.set_viewport_size({'width':390,'height':844})
  page.wait_for_function('document.getAnimations().every(a=>a.playState!=="running"&&a.playState!=="pending")',timeout=5000)
  result=page.evaluate('async()=>await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa","wcag22aa"]}})')
  for v in result['violations']:
   report['axe_violations'].append({'page':rel,'width':390,'rule':v['id'],'impact':v['impact'],'nodes':[{'target':n['target'],'summary':n.get('failureSummary','')} for n in v['nodes']]})
  print(rel,'tested')
 # Navigation / keyboard / sticky UI.
 page.set_viewport_size({'width':1440,'height':1000})
 page.goto(BASE);page.locator('.nav-row').filter(has=page.locator('[aria-label="Show services"]')).locator('.nav-link').hover();check(page.locator('#nav-services').is_visible(),'Desktop service dropdown opens on label hover')
 page.keyboard.press('Escape');page.locator('#nav-services').wait_for(state='hidden');check(not page.locator('#nav-services').is_visible(),'Escape closes dropdown')
 page.set_viewport_size({'width':390,'height':844});page.locator('.menu-toggle').click();check(page.locator('.main-nav').is_visible(),'Mobile menu opens')
 page.locator('[aria-label="Show service areas"]').click();check(page.locator('#nav-service-areas').is_visible(),'Mobile location dropdown opens')
 page.keyboard.press('Escape');page.keyboard.press('Escape');page.locator('.main-nav').wait_for(state='hidden');check(not page.locator('.main-nav').is_visible(),'Escape closes mobile navigation')
 page.locator('.faq-list summary').first.click();check(page.locator('.faq-list details').first.get_attribute('open') is not None,'FAQ opens')
 page.locator('.faq-list summary').nth(1).click();check(page.locator('.faq-list details').first.get_attribute('open') is None,'FAQ closes previous answer')
 page.locator('[data-slide=next]').click();check('2 of 3' in page.locator('.slide-status').inner_text(),'Service-principle slider next')
 page.locator('[data-slide=prev]').click();check('1 of 3' in page.locator('.slide-status').inner_text(),'Service-principle slider previous')
 page.evaluate('window.scrollTo(0,900)');page.wait_for_timeout(80);check(page.locator('.back-top').is_visible(),'Back-to-top appears on scroll')
 page.locator('.back-top').click();page.wait_for_function('scrollY < 1 && !document.querySelector(".site-header").classList.contains("is-scrolled")',timeout=5000);check(page.evaluate('scrollY')<10,'Back-to-top returns to top')
 check('is-scrolled' not in (page.locator('.site-header').get_attribute('class') or ''),'Sticky header state resets')
 # Blog filters and actual page changes.
 page.goto(BASE+'pages/blog/blog.html');check(page.locator('#blog-grid .blog-card:visible').count()==2,'Blog page size is two')
 page.locator('#blog-next').click();check(page.locator('#blog-grid .blog-card:visible').count()==1,'Blog next page reveals third guide')
 page.locator('#blog-prev').click();page.locator('#blog-search').fill('drain');check(page.locator('#blog-grid .blog-card:visible').count()==1,'Blog search')
 page.locator('#blog-search').fill('xyz-no-match');check(page.locator('#blog-empty').is_visible(),'Blog empty state')
 page.locator('#blog-search').fill('');page.locator('[data-blog-category="Maintenance"]').click();check(page.locator('#blog-grid .blog-card:visible').count()==1,'Blog category filter')
 page.goto(BASE+'pages/reviews/reviews.html');page.locator('[data-review-filter="Drain Cleaning"]').click();check(page.locator('#reviews-grid .review-card:visible').count()==1,'Service-topic filter')
 page.goto(BASE+'pages/service-areas/service-areas.html');page.locator('[data-location="2"]').click();check(page.locator('#map-detail h3').inner_text()=='Cedar Park, Texas','Map marker changes details');check(page.locator('#map-location-link').get_attribute('href')=='location-3.html','Map changes location link')
 # No form request may leave the document.
 page.goto(BASE+'pages/contact/contact.html');requests=[]
 page.on('request',lambda r: requests.append({'method':r.method,'url':r.url}))
 page.locator('button[type=submit]').click();check(page.locator('[aria-invalid=true]').count()==7,'Required form field errors');check(page.evaluate('document.activeElement.id')=='name','Form focuses first error')
 for field,value in [('name','QA Enquiry'),('phone','+8801718658326'),('email','qa@example.com'),('location','Austin'),('message','A safe local-only validation test.')]:page.locator('#'+field).fill(value)
 page.locator('#service').select_option(label='Drain Cleaning');page.locator('#consent').check();page.locator('button[type=submit]').click()
 check('Your request is ready.' in page.locator('#form-status').inner_text() and page.locator('#form-status a[href^="https://wa.me/8801718658326?text="]').count()==1,'User-reviewed WhatsApp draft is ready, not sent');check(not requests,'Form sends zero network requests');check(page.url.endswith('/pages/contact/contact.html'),'Form does not pretend to book or redirect')
 check(page.evaluate('localStorage.length===0 && sessionStorage.length===0 && document.cookie===""'),'No enquiry data or cookies stored without a theme choice')
 page.screenshot(path=str(ROOT/'docs/contact-mobile.png'),full_page=True)
 page.set_viewport_size({'width':1440,'height':1000});page.goto(BASE);page.wait_for_function('document.getAnimations().length===0',timeout=5000);page.screenshot(path=str(ROOT/'docs/home-desktop.png'),full_page=True);page.screenshot(path=str(ROOT/'docs/home-top.png'))
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(ROOT/'docs/home-mobile.png'),full_page=True)
 # Reduced-motion and no-JS safety.
 page.emulate_media(reduced_motion='reduce');check(page.evaluate('getComputedStyle(document.documentElement).scrollBehavior')=='auto','Reduced motion disables smooth scrolling')
 nojs=b.new_context(java_script_enabled=False,viewport={'width':390,'height':844});np=nojs.new_page();np.goto(BASE+'pages/contact/contact.html');check(np.locator('#name').is_disabled() and np.locator('button[type=submit]').is_disabled(),'No-JS form cannot leak data');check(np.locator('.main-nav').is_visible(),'No-JS mobile navigation remains visible');nojs.close()
 b.close()
report['passed']=not any(report[k] for k in ['static_errors','browser_errors','overflow','image_errors','axe_violations']) and all(x['passed'] for x in report['interactions'])
(ROOT/'docs/qa-results.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['interactions','axe_violations']},indent=2))
print('Axe violations:',len(report['axe_violations']),'Interactions:',len(report['interactions']))
