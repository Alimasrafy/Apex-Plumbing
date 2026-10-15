"""Compatibility entry point for this build-free static project.
The finalized HTML is the source of truth. This command intentionally does not
regenerate pages or overwrite approved business copy, styles, or functionality.
"""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    pages = [root / 'index.html', *sorted((root / 'pages').rglob('*.html'))]
    if not all(p.exists() for p in pages) or len(pages) != 28:
        raise SystemExit('Expected the complete 28-page static source.')
    print('28 static pages found. No build is required; edit the delivered HTML/CSS/JS directly.')
