# Apex Plumbing

A complete 28-page static plumbing website using **HTML5, CSS3 and native JavaScript**. No framework, database, app compilation or runtime CDN is required. The optional GitHub Pages workflow only packages static files and deployment metadata. Fonts and imagery are hosted locally.

## Deploy on GitHub Pages

**বাংলা step-by-step guide: [GITHUB-DEPLOY.md](GITHUB-DEPLOY.md).** Upload the extracted project contents to the repository root, including `.github/workflows/deploy-pages.yml`. In Settings → Pages, choose **GitHub Actions**, then run/re-run **Deploy Apex Plumbing to GitHub Pages** on the default branch. Subsequent default-branch pushes deploy automatically. Do not upload just the ZIP or an extra enclosing project folder.

The workflow derives the real Pages/custom-domain URL, stages only runtime files into ignored `dist/`, validates local references/canonicals/sitemap, and generates a root `404.html` with base-path-safe assets and recovery links. Source content remains untouched. Project subpaths (`/repository/`), account sites and configured HTTPS custom domains are supported. No personal token or backend secret is required. Actual GitHub deployment still requires enabling Pages/Actions and a successful run in your own repository.

## Business details

- **Brand:** Apex Plumbing
- **WhatsApp:** [+880 1718-658326](https://wa.me/8801718658326)
- **Email:** alimasrafi@zohomail.com
- **Contact location:** Dhaka, Bangladesh
- **Service areas:** Austin, Round Rock, Cedar Park and Pflugerville, Texas, United States
- **Contact hours:** 9:00 AM–6:00 PM; confirm the applicable time zone when arranging an appointment
- **Urgent work and meetings:** by prior discussion and confirmed availability

These details and the Texas coverage were supplied/confirmed by the project owner. No physical Texas branch address, customer endorsement, numeric review score, license, insurance, award or operating history has been invented.

## Preview and hosting

Unzip the archive and open `index.html`, or serve the project with a standard static host. For development: `python -m http.server 3000 --bind 0.0.0.0`. This server is a development convenience, not a website backend. HTTP/HTTPS hosting gives predictable relative navigation and same-origin theme storage; file:// storage behavior varies by browser.

The isolated file viewer cannot resolve a complete multi-file site. Use the live preview or a browser/static host for the working website.

## Included pages

- Homepage and About
- Service overview and eight individual plumbing services
- Service-area overview and four Texas location pages
- **Approach** page, explaining service principles rather than displaying unsupplied customer reviews
- Blog listing and three separate article pages; **Blog → Blog Details** opens the first standalone article
- Contact and enquiry form
- Privacy, Terms, Cookie Policy and Accessibility
- Enquiry next steps and 404

**Content width:** only the inner `.container` layout is capped at **1200px** and centered. Header, footer, section backgrounds and gradients remain full-width, matching the original design. On mobile/tablet, containers stay fluid with the original responsive grids, menu behavior and gutters. The whole website/body is not boxed.

The original routes and all existing IDs remain intact. Body copy uses Inter at 20px, supporting UI is at least 16px, and headings use locally hosted Syne. Desktop/mobile navigation, restrained native motion, keyboard disclosure controls, reduced motion, light/dark mode and responsive layouts are retained.

## Desktop dropdown navigation

At desktop widths (1200px+), mouse hover over Services, Service Areas or Blog opens its dropdown. Moving into submenu links keeps it open. Arrow click/tap, keyboard activation, Escape and focus behavior remain available; mobile stays tap-based. No layout or content-width change is involved. See `docs/dropdown-hover-report.md`.

## Enquiries: how the form works

The contact form validates locally and prepares a **WhatsApp draft**. It does not send anything automatically. The visitor explicitly opens the prepared link, reviews the message in WhatsApp and chooses **Send**. Scope, price and appointments are agreed in conversation; the next-steps page does not imply delivery or booking.

Form entries are not saved in cookies, localStorage or sessionStorage. Opening WhatsApp or an email app involves the chosen external provider under its own policies. Privacy and consent copy describe this behavior. Only a manually selected light/dark theme is saved under `apex-theme`.

A separate backend is needed only if automatic email/server-side form processing is desired. None is included or implied. Do not change the interface to claim a request was received without an actual delivery-confirmation process.

## Editing

The delivered HTML/CSS/JS are the source of truth. Edit them directly; no build is required. Shared components live under `assets/css/components/`, shared theme rules under `assets/css/global/theme.css`, and each page has its existing page stylesheet. Functional controls and the theme/handoff controller use `assets/js/main.js`; native motion uses `assets/js/animations.js`.

`assets/data/` contains reference inventories, not a database or runtime data source. Keep them aligned with public content when editing. `scripts/build_site.py` is now a harmless compatibility check and **does not regenerate or overwrite pages**.

## Domain-specific SEO

Titles, descriptions, service/city copy, internal links, H1 structure and Organization JSON-LD have been updated. The organization uses the actual supplied Dhaka contact location and approved Texas service areas, not an invented US office or rating.

For **GitHub Actions deployment**, no manual domain replacement is required. The workflow uses the actual URL from `actions/configure-pages` and generates canonical/og:url tags, sitemap.xml and a robots sitemap entry in the deployment artifact, leaving source pages unchanged. Account and custom-domain sites use their root; project sites preserve `/repository/`. No fabricated production URL is committed.

For a different static host, you can still run the optional `scripts/configure_seo.py --base-url https://YOUR-ACTUAL-DOMAIN` with the approved URL (install `requirements-deploy.txt` first). `--root` can target a staging directory instead of the source. Do not use a synthetic QA URL for publication.

GitHub-specific root 404 handling is included in the Actions artifact. On other hosts configure real HTTP 404 handling yourself. Project-level `/repository/robots.txt` cannot set the shared host's root robots policy. See the deployment guide for custom-domain/DNS, HTTPS and final live-check instructions. Block indexing on any public staging copy if needed.

## Images, fonts and policies

Plumbing visuals are illustrative and may be AI-generated; they are not presented as actual staff or completed jobs. Replace them with approved business photography if desired. Keep accurate alternative text and retain the local font license notices.

Policy text reflects this website's implemented behavior, but the operator should review it for the actual business, hosting, service arrangements and applicable law before publication. Operating days/time zone, permits, professional requirements, prices and warranties must be confirmed for the work; no unsupported business credentials are asserted.

## Executed quality assurance

See **`docs/responsive-report.md`**, **`docs/client-content-report.md`** and the current JSON/log evidence. The seven website suites below passed for the unchanged runtime site. Additional GitHub Pages artifact tests and their explicit local-simulation limits are documented in `docs/github-pages-report.md`. The remote Actions workflow has not been executed in your GitHub repository.

- Content-only width suite: 28 pages × 23 widths (320–3840px) × 2 themes = 1,288 cases and 6,442 assertions; full-width design and centered content verified
- 28 pages × 17 widths; 2,244 local references; 29 interactions
- 56 light and 56 dark settled-state axe scans with no reported violations
- 406 theme checks (392 page/theme/viewport cases)
- 200 motion checks, with no compared header/font/main-width geometry differences
- 504 readability/landscape cases plus menu checks
- 129 client-copy and explicit WhatsApp-handoff checks
- All 28 documents passed HTML5 validation; source syntax checks passed

QA used Chromium and intercepted a synthetic WhatsApp handoff—no message was sent to the recipient. Real-device, Safari/Firefox, screen-reader, final-host and actual contact-channel checks remain recommended. These results are not legal advice, accessibility certification, search-ranking or message-delivery guarantees.

The scripts are development-only and use optional Python/Playwright/BeautifulSoup tooling; they are not needed for hosting. For strict CSP, allow the current inline startup and JSON-LD hashes recorded in `docs/client-modified-files.json`.
