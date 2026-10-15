"""Desktop mouse hover plus native tap/keyboard disclosure regression checks."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:3000/'
paths=['index.html',*[str(p.relative_to(ROOT)) for p in sorted((ROOT/'pages').rglob('*.html'))]]
ids=['nav-services','nav-service-areas','nav-blog']
r={'page_count':len(paths),'page_theme_cases':0,'checks':[],'page_errors':[]}
def check(name,ok):
 r['checks'].append({'name':name,'passed':bool(ok)})
 if not ok:print('FAILED:',name,flush=True)
with sync_playwright() as pw:
 b=pw.chromium.launch()
 for theme in ['light','dark']:
  ctx=b.new_context(color_scheme=theme,reduced_motion='reduce',viewport={'width':1440,'height':1000})
  p=ctx.new_page();p.on('pageerror',lambda e:r['page_errors'].append(str(e)))
  for path in paths:
   p.goto(BASE+path,wait_until='domcontentloaded')
   for id in ids:
    button=p.locator(f'[aria-controls="{id}"]');panel=p.locator('#'+id)
    row=button.locator('xpath=..');row.locator('.nav-link').hover()
    expect(button).to_have_attribute('aria-expanded','true');expect(panel).to_be_visible()
    check(f'{path} {theme} {id}: label hover opens with ARIA',button.get_attribute('aria-expanded')=='true' and panel.is_visible())
    panel.locator('a').last.hover()
    check(f'{path} {theme} {id}: submenu remains hoverable',panel.is_visible() and button.get_attribute('aria-expanded')=='true')
    check(f'{path} {theme} {id}: hover does not steal focus',not panel.evaluate('(e)=>e.contains(document.activeElement)'))
    p.locator('.site-header .brand').hover();expect(panel).to_be_hidden()
    check(f'{path} {theme} {id}: pointer leaving closes',button.get_attribute('aria-expanded')=='false')
   r['page_theme_cases']+=1
  p.goto(BASE);p.locator('[aria-controls="nav-services"]').locator('xpath=..').locator('.nav-link').hover();p.screenshot(path=str(ROOT/f'docs/dropdown-hover-{theme}.png'))
  ctx.close()
 # Exercise actual motion and desktop/tablet breakpoint boundaries.
 ctx=b.new_context(viewport={'width':1200,'height':1000});p=ctx.new_page()
 for width in [1200,1920]:
  p.set_viewport_size({'width':width,'height':1000});p.goto(BASE)
  p.locator('[aria-controls="nav-services"]').locator('xpath=..').locator('.nav-link').hover()
  expect(p.locator('#nav-services')).to_be_visible()
  p.locator('[aria-controls="nav-blog"]').locator('xpath=..').locator('.nav-link').hover()
  expect(p.locator('#nav-services')).to_be_hidden();expect(p.locator('#nav-blog')).to_be_visible()
  check(f'{width}: switching hovered menus closes sibling',p.locator('.dropdown-toggle[aria-expanded="true"]').count()==1)
  p.locator('#nav-blog a').last.hover();p.keyboard.press('Escape');expect(p.locator('#nav-blog')).to_be_hidden()
  check(f'{width}: Escape dismisses under pointer and restores toggle focus',p.evaluate('document.activeElement===document.querySelector("[aria-controls=nav-blog]")'))
  p.keyboard.press('Enter');expect(p.locator('#nav-blog')).to_be_visible()
  check(f'{width}: Enter opens and focuses first submenu link',p.evaluate('document.activeElement===document.querySelector("#nav-blog a")'))
  p.locator('.site-header .brand').hover()
  check(f'{width}: pointer leaving preserves keyboard-focused submenu',p.locator('[aria-controls="nav-blog"]').get_attribute('aria-expanded')=='true')
  p.locator('.theme-toggle').focus();expect(p.locator('#nav-blog')).to_be_hidden()
  p.locator('[aria-controls="nav-services"]').locator('xpath=..').locator('.nav-link').hover()
  p.locator('h1').click();expect(p.locator('#nav-services')).to_be_hidden()
  check(f'{width}: outside click dismisses hovered menu',p.locator('[aria-controls="nav-services"]').get_attribute('aria-expanded')=='false')
  p.locator('[aria-controls="nav-services"]').locator('xpath=..').locator('.nav-link').hover()
  p.set_viewport_size({'width':1199,'height':900});expect(p.locator('#nav-services')).to_be_hidden()
  check(f'{width}: resize closes dropdown and resets mobile navigation',p.locator('.menu-toggle').get_attribute('aria-expanded')=='false')
 ctx.close()
 # Mobile mouse hover must not open a disclosure, but tap/click still works.
 ctx=b.new_context(viewport={'width':390,'height':844},reduced_motion='reduce');p=ctx.new_page();p.goto(BASE)
 p.locator('.menu-toggle').click();button=p.locator('[aria-controls="nav-services"]');button.locator('xpath=..').locator('.nav-link').hover()
 check('Mobile hover alone does not open dropdown',button.get_attribute('aria-expanded')=='false')
 button.click();expect(p.locator('#nav-services')).to_be_visible();check('Mobile click still opens dropdown',True)
 button.click();expect(p.locator('#nav-services')).to_be_hidden();check('Mobile second click closes dropdown',True);ctx.close()
 # A touch pointer on a large screen is never treated as mouse hover.
 ctx=b.new_context(viewport={'width':1440,'height':1000},has_touch=True,reduced_motion='reduce');p=ctx.new_page();p.goto(BASE)
 button=p.locator('[aria-controls="nav-blog"]');button.tap();expect(p.locator('#nav-blog')).to_be_visible();check('Large-screen touch opens by tap',button.get_attribute('aria-expanded')=='true')
 button.tap();expect(p.locator('#nav-blog')).to_be_hidden();check('Large-screen second tap closes',button.get_attribute('aria-expanded')=='false');ctx.close()
 b.close()
r['passed']=all(c['passed'] for c in r['checks']) and not r['page_errors']
(ROOT/'docs/dropdown-hover-qa.json').write_text(json.dumps(r,indent=2))
print(json.dumps({'passed':r['passed'],'page_theme_cases':r['page_theme_cases'],'checks':len(r['checks']),'failures':[c for c in r['checks'] if not c['passed']],'page_errors':r['page_errors']},indent=2))
raise SystemExit(0 if r['passed'] else 1)
