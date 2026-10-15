"""Additional readable text, clipping, landscape, and mobile-navigation QA."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
paths=[Path('index.html'),*sorted((ROOT/'pages').rglob('*.html'))]
paths=[str(p.relative_to(ROOT)) if p.is_absolute() else str(p) for p in paths]
widths=[320,360,390,414,480,600,767,768,820,1023,1024,1100,1199,1200,1280,1440,1920]
report={'pages':28,'widths':widths,'small_text':[],'clipped_text':[],'landscape_overflow':[],'navigation_failures':[],'passed':False}
inspect_js=r'''() => {
 const small=[],clipped=[];
 const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
 while(walker.nextNode()) {
  const node=walker.currentNode,el=node.parentElement,text=node.textContent.trim();
  if(!el||!text||el.closest('script,style,.sr-only,[hidden],[aria-hidden="true"]'))continue;
  const s=getComputedStyle(el);
  if(s.display==='none'||s.visibility==='hidden'||!el.getClientRects().length)continue;
  const range=document.createRange();range.selectNodeContents(node);
  const rects=[...range.getClientRects()].filter(r=>r.width>0&&r.height>0);
  if(!rects.length)continue;
  if(parseFloat(s.fontSize)<15.99)small.push({text:text.slice(0,100),selector:el.tagName+'.'+el.className,size:s.fontSize});
  for(let a=el;a&&a!==document.body;a=a.parentElement) {
   const style=getComputedStyle(a),bound=a.getBoundingClientRect();
   const x=['hidden','clip'].includes(style.overflowX),y=['hidden','clip'].includes(style.overflowY);
   if(!x&&!y)continue;
   if(rects.some(r=>(x&&(r.left<bound.left-2||r.right>bound.right+2))||(y&&(r.top<bound.top-2||r.bottom>bound.bottom+2)))) {
    clipped.push({text:text.slice(0,100),container:a.tagName+'.'+a.className});break;
   }
  }
 }
 return {small,clipped};
}'''
with sync_playwright() as pw:
 b=pw.chromium.launch();page=b.new_page()
 for path in paths:
  page.goto('http://127.0.0.1:3000/'+path,wait_until='networkidle')
  for width in widths:
   page.set_viewport_size({'width':width,'height':900})
   result=page.evaluate(inspect_js)
   if result['small']:report['small_text'].append({'page':path,'width':width,'nodes':result['small']})
   if result['clipped']:report['clipped_text'].append({'page':path,'width':width,'nodes':result['clipped']})
  page.set_viewport_size({'width':844,'height':390})
  if page.evaluate('document.documentElement.scrollWidth>innerWidth'):report['landscape_overflow'].append(path)
 for width,height in [(320,568),(390,844),(600,800),(820,1180),(1024,768),(1100,800),(1199,800),(844,390)]:
  page.set_viewport_size({'width':width,'height':height});page.goto('http://127.0.0.1:3000/')
  page.locator('.menu-toggle').click()
  if not page.locator('.main-nav').is_visible():report['navigation_failures'].append({'width':width,'reason':'Menu not visible'})
  if width<768 and page.locator('.sticky-call').is_visible():report['navigation_failures'].append({'width':width,'reason':'Sticky CTA overlaps open menu'})
  page.locator('[aria-label="Show services"]').click()
  target=page.locator('#nav-services a').last;target.scroll_into_view_if_needed()
  rect=target.bounding_box()
  if not rect or rect['y']<0 or rect['y']+rect['height']>height+2:report['navigation_failures'].append({'width':width,'height':height,'reason':'Last dropdown link inaccessible in viewport'})
  page.keyboard.press('Escape');page.keyboard.press('Escape');page.locator('.main-nav').wait_for(state='hidden')
  if page.locator('.main-nav').is_visible():report['navigation_failures'].append({'width':width,'reason':'Escape did not close menu'})
 page.set_viewport_size({'width':390,'height':844});page.goto('http://127.0.0.1:3000/');page.screenshot(path=str(ROOT/'docs/home-mobile-top.png'))
 page.goto('http://127.0.0.1:3000/pages/service-areas/service-areas.html');page.locator('.coverage-layout').screenshot(path=str(ROOT/'docs/coverage-mobile.png'))
 page.set_viewport_size({'width':1440,'height':1000});page.goto('http://127.0.0.1:3000/pages/blog/blog.html');page.screenshot(path=str(ROOT/'docs/blog-desktop.png'),full_page=True)
 b.close()
report['page_viewport_checks']=28*len(widths)
report['landscape_checks']=28
report['passed']=not any(report[k] for k in ['small_text','clipped_text','landscape_overflow','navigation_failures'])
(ROOT/'docs/readability-qa.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
