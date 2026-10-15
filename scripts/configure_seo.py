"""Optional build-time launch tool. Does not run on the website.
Usage: python scripts/configure_seo.py --base-url https://YOUR-REAL-DOMAIN
Run with the approved final HTTPS domain after verifying deployment.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit, urljoin
from xml.sax.saxutils import escape
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description='Create real-domain canonical tags, sitemap, and production robots.txt.')
parser.add_argument('--base-url', required=True, help='Final HTTPS site URL, including a subdirectory if applicable')
parser.add_argument('--root', type=Path, help='Optional staged site directory; source files are left untouched when set')
args = parser.parse_args()
if args.root:
    ROOT = args.root.resolve()
base = args.base_url.rstrip('/') + '/'
u = urlsplit(base)
reserved = {'example.com', 'example.org', 'example.net', 'localhost'}
if u.scheme != 'https' or not u.hostname or u.hostname in reserved or u.hostname.endswith(('.example', '.invalid', '.test')) or u.query or u.fragment or u.username:
    parser.error('Provide the actual final HTTPS domain, not a placeholder, local address, query, or fragment.')

site_file = ROOT / 'assets/data/site.json'
site = json.loads(site_file.read_text())
locations = []
for rel in site['pages']:
    page = ROOT / rel
    soup = BeautifulSoup(page.read_text(), 'html.parser')
    if rel in ['pages/404.html', 'pages/thank-you.html']:
        continue
    final_url = urljoin(base, '' if rel == 'index.html' else rel)
    for existing in soup.select('link[rel=canonical], meta[property="og:url"]'):
        existing.decompose()
    canonical = soup.new_tag('link', rel='canonical', href=final_url)
    social = soup.new_tag('meta', property='og:url', content=final_url)
    soup.head.append(canonical)
    soup.head.append(social)
    html = re.sub(r'alimasrafi@\s*<wbr\s*/?>\s*zohomail\.com', 'alimasrafi@<wbr/>zohomail.com', soup.prettify())
    page.write_text(html, encoding='utf-8')
    locations.append(final_url)

xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
xml += ''.join('  <url><loc>' + escape(url) + '</loc></url>\n' for url in locations)
xml += '</urlset>\n'
(ROOT / 'sitemap.xml').write_text(xml)
(ROOT / 'robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: ' + urljoin(base, 'sitemap.xml') + '\n')
site['domain'] = base
site_file.write_text(json.dumps(site, indent=2))
print(f'Configured {len(locations)} content URLs for {base}. Revalidate links and metadata before deploying.')
