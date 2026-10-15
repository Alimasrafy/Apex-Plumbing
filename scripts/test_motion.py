"""Animation-specific QA. Native browser automation; no runtime dependency."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:3000/'
paths=['index.html',*map(lambda p:str(p.relative_to(ROOT)),sorted((ROOT/'pages').rglob('*.html')))]
report={'page_count':28,'checks':[],'page_errors':[],'initial_cls':{},'geometry_differences':[],'passed':False}
def check(name,condition):
 report['checks'].append({'name':name,'passed':bool(condition)})
 if not condition:print('FAILED',name)
settled='document.getAnimations().every(a=>a.playState!=="running"&&a.playState!=="pending")'
init=r'''window.__motionCount=new WeakMap();window.__motionOptions=new WeakMap();window.__cls=0;
const originalAnimate=Element.prototype.animate;
Element.prototype.animate=function(frames,options){
 window.__motionCount.set(this,(window.__motionCount.get(this)||0)+1);
 const history=window.__motionOptions.get(this)||[];history.push(options);window.__motionOptions.set(this,history);
 return originalAnimate.call(this,frames,options);
};
try{new PerformanceObserver(list=>{for(const entry of list.getEntries()){if(!entry.hadRecentInput)window.__cls+=entry.value}}).observe({type:'layout-shift',buffered:true})}catch(_){}
'''
with sync_playwright() as pw:
 b=pw.chromium.launch()
 normal=b.new_context(viewport={'width':1440,'height':1000});normal.add_init_script(init)
 page=normal.new_page();page.on('pageerror',lambda e:report['page_errors'].append(str(e)))
 for path in paths:
  page.goto(BASE+path,wait_until='domcontentloaded')
  check(path+': singleton motion API',page.evaluate('!!window.ApexMotion'))
  check(path+': immediately readable H1',page.locator('h1').is_visible() and float(page.locator('h1').evaluate('(e)=>getComputedStyle(e).opacity'))>=.8)
  page.wait_for_function(settled,timeout=5000)
  check(path+': no ongoing or looping entrance',page.evaluate('document.getAnimations().length===0'))
  report['initial_cls'][path]=page.evaluate('window.__cls')
 # Confirm once-only reveals rather than repeat on every scroll.
 page.goto(BASE);page.wait_for_function(settled)
 first=page.locator('.service-card').first;first.scroll_into_view_if_needed();page.wait_for_function('document.querySelector(".service-card").classList.contains("is-revealed")');page.wait_for_function(settled)
 count1=first.evaluate('(e)=>window.__motionCount.get(e)||0')
 page.evaluate('scrollTo({top:0,behavior:"instant"})');page.wait_for_timeout(60)
 first.scroll_into_view_if_needed();page.wait_for_function(settled)
 count2=first.evaluate('(e)=>window.__motionCount.get(e)||0')
 check('Scroll reveal runs once per card',count1==1 and count2==1)
 page.goto(BASE,wait_until='domcontentloaded')
 delays=page.evaluate('[...document.querySelectorAll(".hero-copy>.eyebrow,.hero-copy>h1,.hero-description,.hero-copy>.actions,.hero-reassurance")].map(e=>window.__motionOptions.get(e)?.[0]?.delay)')
 check('Home hero sequence uses short ordered delays',delays==[0,85,170,255,340])
 # Sample throughout entrance, not just after all animations settle.
 for width in [320,768,1440]:
  page.set_viewport_size({'width':width,'height':900});page.goto(BASE,wait_until='domcontentloaded')
  for delay in [40,120,240,500]:
   page.wait_for_timeout(delay)
   check(f'No overflow during home entrance at {width}px / sample {delay}ms',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
 # Keyboard and rapid toggles on the original controls.
 page.set_viewport_size({'width':390,'height':844});page.goto(BASE);button=page.locator('.menu-toggle')
 button.focus();page.keyboard.press('Enter')
 check('Keyboard-open mobile menu moves focus to first link',page.evaluate('document.activeElement===document.querySelector(".main-nav .nav-link")'))
 page.keyboard.press('Escape');page.locator('.main-nav').wait_for(state='hidden')
 check('Escape restores toggle focus',page.evaluate('document.activeElement===document.querySelector(".menu-toggle")'))
 for _ in range(7):button.dispatch_event('click',{'detail':1})
 page.wait_for_function(settled)
 check('Rapid odd toggles leave menu open and interactive',button.get_attribute('aria-expanded')=='true' and page.locator('.main-nav').is_visible() and not page.locator('.main-nav').evaluate('(e)=>e.inert'))
 button.dispatch_event('click',{'detail':1});page.emulate_media(reduced_motion='reduce');page.locator('.main-nav').wait_for(state='hidden')
 check('Enabling reduced motion settles an in-progress close',not page.locator('.main-nav').evaluate('(e)=>e.inert'))
 check('Reduced motion cancels all active motion',page.evaluate('document.getAnimations().length===0'))
 page.emulate_media(reduced_motion='no-preference');page.set_viewport_size({'width':1440,'height':1000});page.goto(BASE)
 drop=page.locator('[aria-label="Show services"]');drop.focus();page.keyboard.press('Enter')
 check('Keyboard dropdown moves focus to its first link',page.evaluate('document.activeElement===document.querySelector("#nav-services a")'))
 page.keyboard.press('Escape');page.locator('#nav-services').wait_for(state='hidden')
 check('Dropdown Escape restores trigger focus',drop.evaluate('(e)=>document.activeElement===e'))
 header_height=page.locator('.site-header').evaluate('(e)=>e.offsetHeight')
 page.evaluate('scrollTo({top:900,behavior:"instant"})');page.wait_for_timeout(60)
 check('Sticky header dimensions stay stable',header_height==page.locator('.site-header').evaluate('(e)=>e.offsetHeight'))
 # Core motion module guard must prevent duplicate initialization.
 before=page.locator('.menu-toggle path').count();page.add_script_tag(url=BASE+'assets/js/animations.js')
 check('Re-loading module does not duplicate menu strokes',before==3 and page.locator('.menu-toggle path').count()==3)
 page.goto(BASE+'pages/blog/article-1.html');page.evaluate('document.getElementById("guide-3").scrollIntoView({behavior:"instant",block:"start"})')
 page.wait_for_function("document.querySelector('.article-toc a[aria-current=location]')?.hash === '#guide-3'",timeout=5000)
 check('Article contents highlights the current section',page.locator('.article-toc a[aria-current="location"]').count()==1)
 # No verified ratings, numeric business counters, or business claims are introduced.
 page.goto(BASE+'pages/reviews/reviews.html');page.wait_for_function(settled)
 check('No invented review rating is displayed',page.locator('.illustrative-rating').inner_text().strip()=='Clear plans.' and page.locator('.rating-stars').count()==0)
 # All pages: reduced motion and disabled JavaScript, including native FAQ fallback.
 reduced=b.new_context(reduced_motion='reduce',viewport={'width':390,'height':844});rp=reduced.new_page()
 nojs=b.new_context(java_script_enabled=False,viewport={'width':390,'height':844});np=nojs.new_page()
 for path in paths:
  rp.goto(BASE+path,wait_until='networkidle')
  check(path+': reduced motion visible with no active animations',rp.locator('h1').is_visible() and rp.evaluate('document.getAnimations().length===0'))
  check(path+': reduced motion uses native non-smooth scroll',rp.evaluate('getComputedStyle(document.documentElement).scrollBehavior')=='auto')
  np.goto(BASE+path,wait_until='networkidle')
  check(path+': no-JS content and mobile navigation visible',np.locator('h1').is_visible() and np.locator('.main-nav').is_visible())
 np.goto(BASE);np.locator('.faq-list summary').first.click();check('Native FAQ works with JavaScript disabled',np.locator('.faq-list details').first.get_attribute('open') is not None)
 np.goto(BASE+'pages/contact/contact.html');check('No-JS form remains safely disabled',np.locator('#name').is_disabled())
 # Expected no-motion fallbacks: unsupported IO or Web Animations.
 fallback=b.new_context(viewport={'width':390,'height':844});fallback.add_init_script('window.IntersectionObserver=undefined;Element.prototype.animate=undefined;');fp=fallback.new_page();fp.goto(BASE)
 check('Unsupported motion APIs leave the headline visible',fp.locator('h1').is_visible())
 fp.locator('.menu-toggle').click();check('Unsupported motion APIs keep menu opening functional',fp.locator('.main-nav').is_visible())
 fp.keyboard.press('Escape');check('Unsupported motion APIs keep menu closing functional',not fp.locator('.main-nav').is_visible())
 # Compare immutable layout dimensions and typography with the pre-client-content snapshot.
 baseline=json.loads((ROOT/'docs/layout-baseline.json').read_text())
 for key,before in baseline.items():
  path,width=key.rsplit(':',1);rp.set_viewport_size({'width':int(width),'height':900});rp.goto(BASE+path,wait_until='networkidle')
  after=rp.evaluate('({header:document.querySelector(".site-header").offsetHeight,h1Size:getComputedStyle(document.querySelector("h1")).fontSize,bodySize:getComputedStyle(document.body).fontSize,mainWidth:document.querySelector("main").offsetWidth})')
  for metric,value in after.items():
   if before[metric]!=value:report['geometry_differences'].append({'page':key,'metric':metric,'before':before[metric],'after':value})
 check('Header, primary heading/body sizing, and main width preserved',not report['geometry_differences'])
 check('No animation-script page errors',not report['page_errors'])
 b.close()
report['max_initial_cls']=max(report['initial_cls'].values(),default=0)
report['passed']=all(c['passed'] for c in report['checks']) and not report['page_errors']
(ROOT/'docs/motion-qa.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'passed':report['passed'],'checks':len(report['checks']),'failures':[c for c in report['checks'] if not c['passed']],'page_errors':report['page_errors'],'max_initial_cls':report['max_initial_cls'],'geometry_differences':report['geometry_differences']},indent=2))
