# APEX Plumbing

### From an AI-assisted frontend design to an editable Elementor website kit

APEX Plumbing is a plumbing-service website project developed step by step with the assistance of an AI Agent, followed by iterative design review, refinement and testing.

The project has two distinct parts:

- **Static frontend:** the HTML, CSS and JavaScript website in this repository, with a live GitHub Pages preview.
- **WordPress / Elementor kit:** an installable companion plugin distributed through GitHub Releases. It imports native Elementor layouts, local design assets and website-specific functionality into WordPress.

**[View Static Live Preview](https://alimasrafy.github.io/Apex-Plumbing/)** · **[Download Elementor Kit v1.2.1](https://github.com/Alimasrafy/Apex-Plumbing/releases/download/elementor-v4.3.5/Apex-Plumbing-Elementor-Kit-v1.2.1.zip)** · **[Browse Releases](https://github.com/Alimasrafy/Apex-Plumbing/releases)**

> **Choose the right download:** WordPress users should download `Apex-Plumbing-Elementor-Kit-v1.2.1.zip` from the release assets. GitHub’s automatic **Source code (zip)** and **Source code (tar.gz)** archives contain the tagged repository—not the installable plugin package. Older kit ZIPs may also be listed; choose v1.2.1 for the latest fixes described here.

## Project overview

The goal is to move beyond a visual showcase and provide an editable website starting point for plumbing-service businesses.

The Elementor companion plugin is more than a single-feature add-on: it bundles the website’s page layouts, local media and fonts, styling, animations and core interactions. After installing the required dependencies, an administrator can import the website through **one approved setup action**, rather than rebuilding each page manually.

The live preview demonstrates the **static frontend**. It does not run WordPress, expose the Elementor editor, or demonstrate every later WordPress-specific fix.

## Features

- Responsive layouts for desktop, tablet and mobile.
- Light and dark modes with a saved theme preference.
- Service overview and eight individual service pages.
- Service-area overview and four location pages.
- Blog listing and three individual guides.
- Blog search, category filters and pagination.
- Desktop dropdown navigation and mobile navigation controls.
- FAQ interactions and restrained animations with reduced-motion support.
- Local fonts and illustrative imagery.
- A WhatsApp enquiry flow that prepares a visitor-reviewed message draft.

The Elementor kit additionally provides:

- **24 WordPress pages, 3 WordPress posts and a 404 template.**
- Shared native **Header, Footer and Global Single Post** templates.
- Editable Elementor Containers and widgets—not entire pages embedded in HTML widgets.
- Global colors and typography controls.
- Custom Elementor widgets for theme switching, guide search, service-area selection and WhatsApp enquiry drafts.

These specific custom functions are bundled into the companion plugin, reducing the need for a separate add-on for each one. **Elementor and Elementor Pro are still required.**

## WordPress / Elementor installation

### Requirements

- WordPress and WordPress-capable hosting.
- Hello Elementor theme.
- Elementor.
- **Your own official licensed Elementor Pro.**

The plugin declares WordPress **6.8+** and PHP **8.0+** as minimums; every minimum-version combination has not been tested. Check the release documentation and verify your actual setup on staging.

**Elementor Pro, paid licenses and WordPress core are not included.** This download is a companion plugin—not a WordPress theme, full-site backup, or official Envato/Elementor Import Kit archive.

### Install and import

1. Start with a fresh WordPress installation or a **fully backed-up staging site**.
2. Install and activate **Hello Elementor**, **Elementor** and your own licensed **Elementor Pro**.
3. Download **[Apex-Plumbing-Elementor-Kit-v1.2.1.zip](https://github.com/Alimasrafy/Apex-Plumbing/releases/download/elementor-v4.3.5/Apex-Plumbing-Elementor-Kit-v1.2.1.zip)**.
4. In WordPress, open **Plugins → Add New → Upload Plugin**.
5. Upload the ZIP, select **Install Now**, then **Activate**.
6. Open **Apex Website Kit** in the WordPress dashboard.
7. Read the global setup notice, approve the intended changes, and select **Import / complete Apex website**.
8. Wait for the import to finish, then review the imported site.

> **Important:** The approved import applies the kit’s homepage, global styles and shared templates. Do not run it on an existing live website without a backup and staging review. Keep the companion plugin active after import.

### Customize with Elementor

- **Pages / Posts → Edit with Elementor:** edit the page or article body.
- **Templates → Theme Builder:** edit the shared Header, Footer and Global Single Post layout.
- **Elementor Site Settings:** adjust global colors and typography.
- **WordPress post fields:** update blog titles, excerpts and featured images.
- **Apex custom widgets:** change their available labels, options and contact settings.

Keep blog posts on the **Default** page layout. Before publishing your own website, replace the bundled Apex business details, contact information, service areas, imagery and policies with your approved content.

### Updating an existing installation

| Installed version | Update route |
| --- | --- |
| **v1.2.0** | Back up, upload the v1.2.1 plugin ZIP, choose **Replace current with uploaded**, keep the plugin active and clear caches. No re-import or repeat icon refresh is needed for this hover fix. |
| **v1.1** | Replace the plugin with the current ZIP, then follow the included guide for the explicitly approved icon refresh if it has not already been applied. |
| **v1.0** | Replace the plugin with the current ZIP, complete the global blog layout upgrade first, then apply the approved icon refresh. Follow the included migration warnings. |

**Do not use a full-site re-import as the update method.** If styling remains stale, regenerate Elementor CSS/data and clear host/CDN/browser caches.

Detailed installation, customization, migration and QA documents are included **inside the plugin ZIP’s `docs/` folder**. That folder is part of the release package, not the current repository root.

## What changed in v1.2.1?

- Fixed native Posts thumbnails shifting out of their image frames on hover.
- Preserved Elementor’s native thumbnail centering in touch and reduced-motion modes.
- Kept the subtle whole-card hover lift.
- Versioned the design stylesheet with the plugin release to help invalidate stale caches.

Only `apex-elementor.php` and `assets/wp/design.css` changed at runtime from v1.2.0. This patch does not introduce a saved-document migration.

### Package integrity

For `Apex-Plumbing-Elementor-Kit-v1.2.1.zip`, the SHA-256 is:

```text
871fd954f7349f93b66fb781d5ae06de3b313eca0ddcd690f7b4ce2ea37df8ab
```

## Static frontend: run locally

The repository’s static website uses **HTML5, CSS3 and native JavaScript**. It does not require WordPress, Elementor, Node.js or a database to run.

```bash
git clone https://github.com/Alimasrafy/Apex-Plumbing.git
cd Apex-Plumbing
python -m http.server 3000
```

Open **http://localhost:3000** in your browser. Python is only a convenient local static server, not a website runtime dependency. You can also use another static server.

### Current repository structure

```text
Apex-Plumbing/
├── .github/
│   └── workflows/
│       └── static.yml
├── assets/
├── pages/
├── scripts/
├── LICENSE
├── README.md
├── index.html
└── robots.txt
```

The current main branch contains the static frontend. The installable Elementor package is attached separately to **[GitHub Releases](https://github.com/Alimasrafy/Apex-Plumbing/releases)**; it is not a plugin folder in the repository root.

### GitHub Pages

The existing workflow is **`.github/workflows/static.yml`**, named **Deploy static content to Pages**. It deploys the repository as static content on pushes to `main`, or can be run manually from **Actions**.

For a fork or a new deployment:

1. Open **Settings → Pages**.
2. Set **Build and deployment → Source** to **GitHub Actions**.
3. Open **Actions → Deploy static content to Pages → Run workflow**, or push to `main`.
4. Check the workflow result and the deployment URL.

GitHub Pages hosts the static preview only. **It cannot execute the PHP/WordPress plugin.** The current workflow uploads the repository as its Pages artifact; do not commit secrets, databases, private test environments or paid plugin files.

Before publishing on a different domain, review your actual URLs, metadata, sitemap/robots configuration and host-specific 404 handling. The current simple Pages workflow should not be assumed to generate those automatically.

## Enquiries: what the form actually does

The form validates input locally and prepares a **WhatsApp message draft**. The visitor opens WhatsApp, reviews the message and manually presses **Send**.

It does **not** automatically send an email, store enquiries in a database, confirm receipt, book an appointment or guarantee message delivery. A separate backend/integration would be needed for those capabilities.

## Testing and limitations

The v1.2.1 patch was checked on an isolated WordPress installation with:

- **156 focused checks**, including **96 thumbnail-hover cases**: 3 posts × 8 widths × 2 themes × 2 motion preferences.
- Search, category filters, pagination, keyboard navigation and emulated mobile touch.
- **520 frontend regression checks** across **448 route/width/theme cases**.
- Final ZIP installation through the WordPress dashboard, installed-file hash matching and preservation of native documents/setup state.

Test stack: WordPress **7.1.3**, Elementor **4.3.5**, Hello Elementor **3.5.1**, PHP **8.4.26** and Chromium. A user-supplied modified Pro **4.3.1** copy was used only in the isolated test environment. It is not included, certified official or certified safe. Use trusted official licensed Pro in production and test your actual version combination on staging.

These are local test results—not a production-host, physical-device, every-browser, accessibility or security certification. Full scope and limitations are documented in `docs/QA-REPORT.md` **inside the plugin ZIP**.

## Content, attribution and license

- Built with the assistance of an AI Agent, with iterative review and testing.
- Plumbing visuals are illustrative and may be AI-generated; they are not evidence of actual staff or completed projects.
- Verify business claims, service availability, contact details and policies before publishing a site based on this project.
- The repository contains the **GNU General Public License v3** text: see **[LICENSE](LICENSE)**.
- Third-party fonts retain their own license notices. Preserve applicable notices and review the release package’s licensing/attribution when redistributing it.

## Feedback

Found an issue or have a suggestion? **[Open a GitHub issue](https://github.com/Alimasrafy/Apex-Plumbing/issues)** and include the affected page, browser, viewport width, steps to reproduce and, for WordPress issues, your relevant plugin/theme versions. Never post credentials or private customer information.
