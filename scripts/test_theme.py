"""Development-only Playwright QA for native light/dark preferences."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:3000/'
paths = ['index.html', *[str(p.relative_to(ROOT)) for p in sorted((ROOT / 'pages').rglob('*.html'))]]
widths = [320, 390, 768, 1199, 1200, 1440, 1920]
report = {'checks': [], 'page_errors': [], 'axe_violations': [], 'viewport_checks': 0, 'dark_axe_scans': 0}

def check(name, value):
    report['checks'].append({'name': name, 'passed': bool(value)})
    if not value:
        print('FAILED:', name, flush=True)

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for theme in ['light', 'dark']:
        context = browser.new_context(color_scheme=theme, reduced_motion='reduce')
        page = context.new_page()
        page.on('pageerror', lambda e: report['page_errors'].append(str(e)))
        for width in widths:
            page.set_viewport_size({'width': width, 'height': 1000})
            for path in paths:
                page.goto(BASE + path, wait_until='domcontentloaded')
                page.evaluate('document.fonts.ready')
                result = page.evaluate('''() => {
                  const b = document.querySelector('.theme-toggle'), r = b.getBoundingClientRect();
                  return {theme: document.documentElement.dataset.theme, pressed: b.getAttribute('aria-pressed'),
                    visible: r.width >= 44 && r.height >= 44 && r.left >= 0 && r.right <= innerWidth,
                    overflow: document.documentElement.scrollWidth > innerWidth,
                    untouched: localStorage.length === 0, size: getComputedStyle(document.body).fontSize};
                }''')
                check(f'{path} {theme} @{width}: palette, control, storage and reflow',
                      result['theme'] == theme and result['pressed'] == str(theme == 'dark').lower()
                      and result['visible'] and not result['overflow'] and result['untouched'] and result['size'] == '20px')
                report['viewport_checks'] += 1
                if theme == 'dark' and width in [390, 1440]:
                    page.add_script_tag(path=str(ROOT / 'scripts/axe.min.js'))
                    audit = page.evaluate('''async () => (await axe.run(document, {
                      runOnly: {type:'tag', values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}
                    })).violations.map(v => ({id:v.id, impact:v.impact, nodes:v.nodes.map(n=>({target:n.target, failureSummary:n.failureSummary}))}))''')
                    report['dark_axe_scans'] += 1
                    if audit:
                        report['axe_violations'].append({'page': path, 'width': width, 'violations': audit})
        context.close()

    context = browser.new_context(color_scheme='light', reduced_motion='reduce')
    page = context.new_page()
    page.goto(BASE)
    button = page.locator('.theme-toggle')
    button.focus()
    page.keyboard.press('Space')
    check('Keyboard Space toggles to dark and stores only preference', page.evaluate("document.documentElement.dataset.theme==='dark' && localStorage.length===1 && localStorage.getItem('apex-theme')==='dark' && sessionStorage.length===0 && document.cookie===''") and button.get_attribute('aria-pressed') == 'true')
    page.reload()
    check('Preference survives reload', page.evaluate("document.documentElement.dataset.theme==='dark'"))
    page.goto(BASE + 'pages/contact/contact.html')
    check('Preference survives relative-link page navigation', page.evaluate("document.documentElement.dataset.theme==='dark'"))
    page.locator('.theme-toggle').click()
    check('Toggle returns to original light palette', page.evaluate("document.documentElement.dataset.theme==='light' && getComputedStyle(document.body).backgroundColor==='rgb(255, 255, 255)'"))
    second = context.new_page()
    second.goto(BASE)
    page.locator('.theme-toggle').click()
    second.wait_for_function("document.documentElement.dataset.theme==='dark'")
    check('Open tabs synchronize saved theme', True)
    page.evaluate("localStorage.removeItem('apex-theme')")
    second.wait_for_function("document.documentElement.dataset.theme==='light'")
    check('Clearing preference restores device default in other tabs', True)
    context.close()

    auto = browser.new_context(color_scheme='light', reduced_motion='reduce')
    page = auto.new_page()
    page.goto(BASE)
    page.emulate_media(color_scheme='dark')
    page.wait_for_function("document.documentElement.dataset.theme==='dark'")
    check('Device changes followed before manual choice', page.evaluate('localStorage.length===0'))
    page.locator('.theme-toggle').click()
    page.emulate_media(color_scheme='light')
    page.emulate_media(color_scheme='dark')
    check('Explicit choice overrides later device changes', page.evaluate("document.documentElement.dataset.theme==='light'"))
    auto.close()

    blocked = browser.new_context(color_scheme='light', reduced_motion='reduce')
    blocked.add_init_script("Object.defineProperty(window, 'localStorage', {get(){throw new DOMException('Blocked','SecurityError')}})")
    page = blocked.new_page()
    page.on('pageerror', lambda e: report['page_errors'].append(str(e)))
    page.goto(BASE)
    page.locator('.theme-toggle').click()
    check('Blocked storage still permits in-memory theme toggle', page.evaluate("document.documentElement.dataset.theme==='dark'"))
    blocked.close()

    nojs = browser.new_context(java_script_enabled=False, color_scheme='dark', viewport={'width':390,'height':844})
    page = nojs.new_page()
    page.goto(BASE)
    check('No-JS follows device palette and hides inactive toggle', page.evaluate("getComputedStyle(document.body).backgroundColor==='rgb(13, 23, 38)'") and not page.locator('.theme-toggle').is_visible() and page.locator('.main-nav').is_visible())
    nojs.close()

    captures = browser.new_context(color_scheme='dark', reduced_motion='reduce', viewport={'width':1440,'height':1000})
    page = captures.new_page()
    page.goto(BASE, wait_until='networkidle')
    page.screenshot(path=str(ROOT / 'docs/theme-dark-home.png'))
    page.locator('.theme-toggle').click()
    page.screenshot(path=str(ROOT / 'docs/theme-light-home.png'))
    page.locator('.theme-toggle').click()
    page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path=str(ROOT / 'docs/theme-dark-mobile.png'))
    page.goto(BASE + 'pages/contact/contact.html', wait_until='networkidle')
    page.locator('#name').focus()
    page.locator('button[type=submit]').click()
    check('Dark form validation remains honest and readable', page.locator('[aria-invalid=true]').count() == 7)
    page.screenshot(path=str(ROOT / 'docs/theme-dark-contact.png'), full_page=True)
    page.emulate_media(media='print')
    check('Print remains light on a dark preference', page.evaluate("getComputedStyle(document.body).backgroundColor==='rgb(255, 255, 255)'"))
    captures.close()
    browser.close()

check('No captured theme browser errors', not report['page_errors'])
check('Dark accessibility scans report no violations', not report['axe_violations'])
report['passed'] = all(c['passed'] for c in report['checks'])
(ROOT / 'docs/theme-qa.json').write_text(json.dumps(report, indent=2))
print(json.dumps({'passed': report['passed'], 'checks': len(report['checks']), 'viewports':report['viewport_checks'], 'dark_axe_scans':report['dark_axe_scans'], 'page_errors':report['page_errors'], 'axe_failures':len(report['axe_violations'])}, indent=2))
raise SystemExit(0 if report['passed'] else 1)
