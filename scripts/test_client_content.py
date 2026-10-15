"""Release QA for approved business content and the explicit WhatsApp handoff."""
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlsplit, parse_qs
from playwright.sync_api import sync_playwright
import json, re
ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:3000/'
paths = [ROOT/'index.html', *sorted((ROOT/'pages').rglob('*.html'))]
checks = []
errors = []
def check(name, ok):
    checks.append({'name': name, 'passed': bool(ok)})
    if not ok: print('FAILED', name, flush=True)

soups = {p:BeautifulSoup(p.read_text(),'html.parser') for p in paths}
for p,s in soups.items():
    public = ' '.join(n.strip() for n in s.find_all(string=True) if n.parent.name not in ['script','style'])
    public += ' ' + ' '.join(str(e[a]) for e in s.find_all(True) for a in ['content','aria-label','title'] if e.has_attr(a))
    check(str(p.relative_to(ROOT))+': no retired preview or fabricated rating copy', not re.search(r'\b(?:demo|demonstration|fictional|template|unconfirmed)\b|24/7|★★★★★|\b5\.0\b|555-0148|apexplumbing\.example',public,re.I))
    check(str(p.relative_to(ROOT))+': real contact links and city-only contact location', bool(s.select('a[href="https://wa.me/8801718658326"]')) and bool(s.select('a[href="mailto:alimasrafi@zohomail.com"]')) and 'Dhaka, Bangladesh' in s.footer.get_text(' ',strip=True))
    check(str(p.relative_to(ROOT))+': no invented reviews or customer names', not s.select('.stars,.rating-stars') and not re.search(r'Jordan M\.|Alex L\.|Taylor S\.|Riley P\.|Casey W\.|Drew K\.',public))
    check(str(p.relative_to(ROOT))+': unique heading and meaningful metadata',p.read_text().lstrip().lower().startswith('<!doctype html>') and len(s.select('h1'))==1 and len(s.title.get_text(strip=True))>15 and 60<=len(s.select_one('meta[name="description"]')['content'])<=180)
check('Unique titles across all 28 pages',len({s.title.get_text(strip=True) for s in soups.values()})==28)
org=json.loads(soups[ROOT/'index.html'].select_one('script[type="application/ld+json"]').string)
check('Structured data uses Dhaka contact address, four Texas service areas and no review score',org['address']['addressCountry']=='BD' and len(org['areaServed'])==4 and 'aggregateRating' not in org and 'foundingDate' not in org)
check('Robots permits crawling without an invented sitemap domain','Allow: /' in (ROOT/'robots.txt').read_text() and 'Disallow: /' not in (ROOT/'robots.txt').read_text())
with sync_playwright() as pw:
    b=pw.chromium.launch()
    c=b.new_context(reduced_motion='reduce',viewport={'width':1440,'height':1000})
    page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'pages/contact/contact.html',wait_until='networkidle')
    page.locator('button[type=submit]').click()
    check('Seven missing required fields are reported',page.locator('[aria-invalid=true]').count()==7)
    check('Invalid submission focuses the first error',page.evaluate('document.activeElement.id')=='name')
    requests=[]
    page.on('request',lambda request:requests.append(request.url))
    values={'name':'QA <A&B>','phone':'+8801718658326','email':'qa@example.com','location':'Austin, TX','message':'A kitchen leak <test> & a slow drain. Please discuss timing.'}
    for field,value in values.items():page.locator('#'+field).fill(value)
    page.locator('#service').select_option(label='Leak Detection');page.locator('#consent').check();page.locator('button[type=submit]').click()
    check('Preparing a valid message makes no network request or redirect',not requests and page.url.endswith('/pages/contact/contact.html'))
    draft_link=page.locator('#form-status a[href^="https://wa.me/"]')
    url=draft_link.get_attribute('href');parsed=urlsplit(url);draft=parse_qs(parsed.query)['text'][0]
    check('WhatsApp URL targets the supplied number with safely encoded original values',parsed.netloc=='wa.me' and parsed.path=='/8801718658326' and all(v in draft for v in values.values()) and '<' not in url and '>' not in url)
    check('Status tells the visitor to review and choose Send, not that delivery occurred','press Send' in page.locator('#form-status').inner_text() and 'received' not in page.locator('#form-status').inner_text().lower())
    check('No enquiry data or cookies written to browser storage',page.evaluate('localStorage.length===0 && sessionStorage.length===0 && document.cookie===""'))
    c.route('https://wa.me/**',lambda route:route.fulfill(status=200,content_type='text/html',body='<title>Intercepted handoff</title><p>QA intercepted this request. Nothing was sent.</p>'))
    with page.expect_popup() as popup_info:draft_link.click()
    popup=popup_info.value;popup.wait_for_load_state();check('Explicit handoff opens the correct draft without contacting the real recipient',popup.url==url);popup.close()
    page.goto(BASE+'pages/thank-you.html');check('Next-steps page does not imply a confirmed booking','confirmed only after' in page.locator('main').inner_text())
    page.goto(BASE+'pages/reviews/reviews.html');page.locator('[data-review-filter="Drain Cleaning"]').click();check('Service-topic filter remains functional without fictional testimonials','1 service topic' in page.locator('#review-count').inner_text() and page.locator('#reviews-grid .review-card:visible').count()==1)
    page.goto(BASE+'pages/service-areas/service-areas.html')
    for i,city in enumerate(['Austin','Round Rock','Cedar Park','Pflugerville']):
        page.locator('[data-location="'+str(i)+'"]').click()
        check('Coverage selector uses client-approved '+city,city in page.locator('#map-detail h3').inner_text() and 'demo' not in page.locator('#map-detail').inner_text().lower())
    # Fresh, unfilled pages for client-facing previews.
    for path,file in [('index.html','client-home-light.png'),('pages/contact/contact.html','client-contact.png'),('pages/reviews/reviews.html','client-approach.png'),('pages/service-areas/location-1.html','client-austin.png')]:
        page.goto(BASE+path,wait_until='networkidle');page.screenshot(path=str(ROOT/'docs'/file))
    page.goto(BASE,wait_until='networkidle');page.locator('.theme-toggle').click();page.screenshot(path=str(ROOT/'docs/client-home-dark.png'))
    page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(ROOT/'docs/client-mobile.png'))
    c.close();b.close()
check('No captured content/handoff page errors',not errors)
r={'passed':all(v['passed'] for v in checks),'checks':checks,'page_errors':errors,'facts_source':'Business details and Texas coverage supplied/confirmed by the user; not independently verified.','handoff':'User prepares a draft, explicitly opens WhatsApp, then must choose Send. No QA message was sent.'}
(ROOT/'docs/client-content-qa.json').write_text(json.dumps(r,indent=2))
print(json.dumps({'passed':r['passed'],'checks':len(checks),'failed':[v['name'] for v in checks if not v['passed']],'page_errors':errors},indent=2))
raise SystemExit(0 if r['passed'] else 1)
