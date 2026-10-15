"""Build-time GitHub Pages packaging. No website/backend dependency.
Creates dist/ from an allowlist, configures actual-domain SEO and a robust root 404.
Usage: python scripts/prepare_pages.py --base-url https://YOUR-ACTUAL-PAGES-URL
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
from xml.etree import ElementTree
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]

def prepare(base_url):
    base = base_url.rstrip('/') + '/'
    u = urlsplit(base)
    if u.scheme != 'https' or not u.hostname or u.username or u.password or u.query or u.fragment or '..' in unquote(u.path).split('/'):
        raise ValueError('Use the actual HTTPS Pages base URL without credentials, query or fragment.')
    output = ROOT / 'dist'
    if output.is_symlink():
        raise ValueError('Refusing to replace a symlink at dist/.')
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    for name in ['assets', 'pages']:
        shutil.copytree(ROOT / name, output / name)
    for name in ['index.html', 'robots.txt']:
        shutil.copy2(ROOT / name, output / name)
    (output / '.nojekyll').write_text('')
    if (ROOT / 'CNAME').exists():
        if (ROOT / 'CNAME').read_text().strip().lower() != u.hostname.lower():
            raise ValueError('CNAME must match the configured Pages/custom-domain host.')
        shutil.copy2(ROOT / 'CNAME', output / 'CNAME')
    subprocess.run([sys.executable, str(ROOT / 'scripts/configure_seo.py'), '--base-url', base, '--root', str(output)], check=True)

    # GitHub serves root 404.html at arbitrarily nested unknown paths.
    # Absolute deployment URLs avoid resolving CSS/images/links against that unknown path.
    soup = BeautifulSoup((output / 'pages/404.html').read_text(), 'html.parser')
    original_url = urljoin(base, 'pages/404.html')
    for tag in soup.find_all(True):
        for attr in ['href', 'src', 'action']:
            value = tag.get(attr)
            if value and not value.startswith('#') and not urlsplit(value).scheme and not urlsplit(value).netloc:
                tag[attr] = urljoin(original_url, value)
    html = re.sub(r'alimasrafi@\s*<wbr\s*/?>\s*zohomail\.com', 'alimasrafi@<wbr/>zohomail.com', soup.prettify())
    (output / '404.html').write_text(html, encoding='utf-8')
    validate(output, base)
    return output

def validate(output, base):
    pages = sorted(output.rglob('*.html'))
    if len(pages) != 29:
        raise ValueError('Expected 28 original HTML routes plus deployment-only root 404.html.')
    references = 0
    for page in pages:
        soup = BeautifulSoup(page.read_text(), 'html.parser')
        if not page.read_text().lstrip().lower().startswith('<!doctype html>') or len(soup.select('h1')) != 1:
            raise ValueError(f'Invalid document structure: {page}')
        for tag, attr in [('a','href'),('link','href'),('img','src'),('script','src')]:
            for node in soup.select(f'{tag}[{attr}]'):
                raw = node[attr]
                actual = urlsplit(urljoin(urljoin(base, page.relative_to(output).as_posix()), raw))
                parsed_base = urlsplit(base)
                if actual.netloc != parsed_base.netloc or actual.scheme not in ['http','https']:
                    continue
                prefix = parsed_base.path
                if not actual.path.startswith(prefix):
                    raise ValueError(f'Internal URL escapes repository prefix: {page}: {raw}')
                relative = unquote(actual.path[len(prefix):]) or 'index.html'
                target = (output / relative).resolve()
                if not target.is_relative_to(output.resolve()) or not target.is_file():
                    raise ValueError(f'Missing local reference: {page}: {raw}')
                if actual.fragment and target.suffix == '.html':
                    if not BeautifulSoup(target.read_text(), 'html.parser').find(id=unquote(actual.fragment)):
                        raise ValueError(f'Missing anchor: {page}: {raw}')
                references += 1
        if page.name not in ['404.html','thank-you.html']:
            expected = urljoin(base, '' if page.name == 'index.html' else page.relative_to(output).as_posix())
            canonical = soup.select_one('link[rel=canonical]')
            social = soup.select_one('meta[property="og:url"]')
            if not canonical or canonical['href'] != expected or not social or social['content'] != expected:
                raise ValueError(f'Incorrect deployment metadata: {page}')
    for css in (output / 'assets/css').rglob('*.css'):
        for raw in re.findall(r'url\(\s*[\'"]?([^\)\'\"]+)', css.read_text()):
            if not urlsplit(raw).scheme and not (css.parent / unquote(raw)).is_file():
                raise ValueError(f'Missing CSS asset: {css}: {raw}')
    for fontcss in (output / 'assets/fonts').glob('*.css'):
        for raw in re.findall(r'url\(\s*[\'"]?([^\)\'\"]+)', fontcss.read_text()):
            if not (fontcss.parent / raw).is_file():
                raise ValueError(f'Missing font: {raw}')
    sitemap = ElementTree.parse(output / 'sitemap.xml')
    urls = [n.text for n in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    if len(urls) != 26 or not all(url.startswith(base) for url in urls):
        raise ValueError('Incorrect sitemap URL count/base.')
    if any((output / name).exists() for name in ['docs','scripts','uploads','.github','README.md']):
        raise ValueError('Development files must not be deployed.')
    print(json.dumps({'html_documents':len(pages),'content_sitemap_urls':len(urls),'local_references':references,'base_url':base,'artifact':'dist/','passed':True}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prepare and verify the runtime-only GitHub Pages artifact.')
    parser.add_argument('--base-url', required=True, help='Actual Pages URL from actions/configure-pages')
    args = parser.parse_args()
    prepare(args.base_url)
