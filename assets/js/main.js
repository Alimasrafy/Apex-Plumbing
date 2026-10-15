/* Apex Plumbing — framework-free enhancements. No network requests. Only the selected color theme is stored locally. */
'use strict';
document.documentElement.classList.replace('no-js', 'js');
(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const header = $('.site-header');
  const topLink = $('.back-top');
  const menuButton = $('.menu-toggle');
  const navigation = $('.main-nav');
  const mobile = window.matchMedia('(max-width: 1199px)');
  const hoverPointer = window.matchMedia('(any-hover: hover) and (any-pointer: fine)');
  const motion = () => window.ApexMotion;

  // The head primer applies the initial palette before paint; storage is optional.
  const themeButton = $('.theme-toggle');
  const colorPreference = window.matchMedia('(prefers-color-scheme: dark)');
  let selectedTheme = null;
  try {
    const savedTheme = localStorage.getItem('apex-theme');
    if (savedTheme === 'dark' || savedTheme === 'light') selectedTheme = savedTheme;
  } catch (_) { /* Private/restricted storage: this page still works. */ }
  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    themeButton?.setAttribute('aria-pressed', String(theme === 'dark'));
    if (themeButton) themeButton.title = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
    $('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#0d1726' : '#ffffff');
  }
  applyTheme(selectedTheme || (colorPreference.matches ? 'dark' : 'light'));
  if (themeButton) {
    themeButton.addEventListener('click', () => {
      selectedTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      applyTheme(selectedTheme);
      try { localStorage.setItem('apex-theme', selectedTheme); } catch (_) {}
    });
    themeButton.hidden = false;
  }
  colorPreference.addEventListener('change', () => {
    if (!selectedTheme) applyTheme(colorPreference.matches ? 'dark' : 'light');
  });
  window.addEventListener('storage', event => {
    if (event.key !== 'apex-theme' && event.key !== null) return;
    selectedTheme = event.newValue === 'dark' || event.newValue === 'light' ? event.newValue : null;
    applyTheme(selectedTheme || (colorPreference.matches ? 'dark' : 'light'));
  });


  function setPanel(panel, open) {
    if (!panel) return;
    if (motion()) motion().disclose(panel, open, {
      duration: motion().durations.dropdown
    });
    else panel.hidden = !open;
  }

  function closeDropdowns(except = null) {
    $$('.dropdown-toggle').forEach(button => {
      if (button === except) return;
      button.setAttribute('aria-expanded', 'false');
      setPanel(document.getElementById(button.getAttribute('aria-controls')), false);
    });
  }

  function setMenu(open) {
    if (open) document.body.classList.add('navigation-open');
    menuButton?.setAttribute('aria-expanded', String(open));
    menuButton?.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    if (motion() && navigation) {
      motion().disclose(navigation, open, {
        activeClass: 'is-open',
        duration: motion().durations.menu,
        instant: !mobile.matches,
        onComplete: () => {
          if (menuButton?.getAttribute('aria-expanded') !== 'true') document.body.classList.remove('navigation-open');
        },
        items: ':scope > ul > li > .nav-link, :scope > ul > li > .nav-row > .nav-link, .mobile-nav-cta'
      });
    } else {
      navigation?.classList.toggle('is-open', open);
      document.body.classList.toggle('navigation-open', open);
    }
    if (!open) closeDropdowns();
  }
  menuButton?.addEventListener('click', event => {
    const open = menuButton.getAttribute('aria-expanded') !== 'true';
    setMenu(open);
    if (open && event.detail === 0) navigation?.querySelector('.nav-link')?.focus();
  });
  $$('.dropdown-toggle').forEach(button => {
    const panel = document.getElementById(button.getAttribute('aria-controls'));
    const item = button.closest('li');
    // Desktop mouse hover shares the existing disclosure state and motion.
    // The containing li includes its panel, so moving into submenu links keeps it open.
    // Touch remains tap-only; Escape is not overridden by a CSS :hover rule.
    item.addEventListener('pointerenter', event => {
      if (mobile.matches || !hoverPointer.matches || event.pointerType !== 'mouse') return;
      closeDropdowns(button);
      button.setAttribute('aria-expanded', 'true');
      setPanel(panel, true);
    });
    item.addEventListener('pointerleave', event => {
      if (mobile.matches || event.pointerType !== 'mouse' || item.contains(document.activeElement)) return;
      button.setAttribute('aria-expanded', 'false');
      setPanel(panel, false);
    });
    button.addEventListener('click', event => {
      const open = button.getAttribute('aria-expanded') !== 'true';
      closeDropdowns(button);
      button.setAttribute('aria-expanded', String(open));
      setPanel(panel, open);
      if (open && event.detail === 0) panel?.querySelector('a')?.focus();
    });
    button.closest('li').addEventListener('focusout', event => {
      if (!event.currentTarget.contains(event.relatedTarget)) {
        button.setAttribute('aria-expanded', 'false');
        setPanel(panel, false);
      }
    });
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.main-nav')) closeDropdowns();
    if (mobile.matches && !event.target.closest('.site-header')) setMenu(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    const expanded = $('.dropdown-toggle[aria-expanded="true"]');
    if (expanded) {
      closeDropdowns();
      expanded.focus();
    } else if (menuButton?.getAttribute('aria-expanded') === 'true') {
      setMenu(false);
      menuButton.focus();
    }
  });
  mobile.addEventListener('change', () => setMenu(false));
  navigation?.addEventListener('click', event => {
    if (event.target.closest('a') && mobile.matches) setMenu(false);
  });

  function onScroll() {
    header?.classList.toggle('is-scrolled', window.scrollY > 20);
    if (topLink) {
      const visible = window.scrollY >= 500;
      if (motion()) motion().disclose(topLink, visible, {
        duration: motion().durations.micro
      });
      else topLink.hidden = !visible;
    }
  }
  let scrollFrame = 0;

  function queueScroll() {
    if (scrollFrame) return;
    scrollFrame = requestAnimationFrame(() => {
      scrollFrame = 0;
      onScroll();
    });
  }
  window.addEventListener('scroll', queueScroll, {
    passive: true
  });
  onScroll();

  // Native <details> supports keyboard activation without JavaScript.
  $$('.faq-list').forEach(list => $$('summary', list).forEach(summary => {
    summary.addEventListener('click', () => {
      const selected = summary.parentElement;
      if (!selected.open) $$('details', list).forEach(item => {
        if (item !== selected) item.open = false;
      });
    });
  }));

  // Manual-only testimonial carousel: no auto-rotation or unexpected focus changes.
  $$('.review-slider').forEach(slider => {
    const cards = $$('.review-card', slider);
    const smallScreen = window.matchMedia('(max-width: 767px)');
    let index = 0;

    function render(options = {}) {
      slider.classList.toggle('is-mobile', smallScreen.matches);
      cards.forEach((card, i) => {
        card.hidden = smallScreen.matches && i !== index;
      });
      $('.slide-status', slider).textContent = `${index + 1} of ${cards.length}`;
      motion()?.swapVisible(slider, cards.filter(card => !card.hidden), {
        slide: true,
        ...options
      });
    }
    $$('[data-slide]', slider).forEach(button => button.addEventListener('click', () => {
      index = (index + (button.dataset.slide === 'next' ? 1 : -1) + cards.length) % cards.length;
      render({
        direction: button.dataset.slide === 'next' ? 1 : -1
      });
    }));
    smallScreen.addEventListener('change', () => render({
      instant: true
    }));
    render({
      instant: true
    });
  });

  // Client-side search, category filtering, and honest pagination over the 3 supplied guides.
  const blogGrid = $('#blog-grid');
  if (blogGrid) {
    const cards = $$('.blog-card', blogGrid);
    const input = $('#blog-search');
    const categoryButtons = $$('[data-blog-category]');
    let category = 'All';
    let page = 1;
    const pageSize = 2;

    function render() {
      const term = input.value.trim().toLowerCase();
      const matches = cards.filter(card => (category === 'All' || card.dataset.category === category) && card.dataset.search.includes(term));
      const pageCount = Math.max(1, Math.ceil(matches.length / pageSize));
      page = Math.min(page, pageCount);
      cards.forEach(card => {
        card.hidden = true;
      });
      matches.slice((page - 1) * pageSize, page * pageSize).forEach(card => {
        card.hidden = false;
      });
      $('#blog-empty').hidden = matches.length !== 0;
      $('#blog-count').textContent = `${matches.length} helpful guide${matches.length === 1 ? '' : 's'} · page ${page} of ${pageCount}`;
      $('#blog-page').textContent = String(page);
      $('#blog-page').setAttribute('aria-label', `Page ${page} of ${pageCount}`);
      $('#blog-prev').disabled = page <= 1;
      $('#blog-next').disabled = page >= pageCount;
      motion()?.swapVisible(blogGrid, cards.filter(card => !card.hidden));
    }
    input.addEventListener('input', () => {
      page = 1;
      render();
    });
    categoryButtons.forEach(button => button.addEventListener('click', () => {
      category = button.dataset.blogCategory;
      page = 1;
      categoryButtons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
      render();
    }));
    $('#blog-prev').addEventListener('click', () => {
      page--;
      render();
    });
    $('#blog-next').addEventListener('click', () => {
      page++;
      render();
    });
    render();
  }
  const reviewGrid = $('#reviews-grid');
  if (reviewGrid) {
    const buttons = $$('[data-review-filter]');
    motion()?.swapVisible(reviewGrid, $$('.review-card', reviewGrid));
    buttons.forEach(button => button.addEventListener('click', () => {
      const category = button.dataset.reviewFilter;
      let count = 0;
      $$('.review-card', reviewGrid).forEach(card => {
        card.hidden = category !== 'All' && card.dataset.category !== category;
        if (!card.hidden) count++;
      });
      buttons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
      $('#review-count').textContent = `${count} service topic${count === 1 ? '' : 's'}`;
      motion()?.swapVisible(reviewGrid, $$('.review-card', reviewGrid).filter(card => !card.hidden));
    }));
  }

  const mapNames = ['Austin', 'Round Rock', 'Cedar Park', 'Pflugerville'];
  $$('[data-location]').forEach(button => button.addEventListener('click', () => {
    const number = Number(button.dataset.location);
    $$('[data-location]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    $('#map-detail h3').textContent = `${mapNames[number]}, Texas`;
    $('#map-detail p.mt-24').textContent = `Discuss plumbing services in ${mapNames[number]}, Texas. Share your property address, service needs, and preferred timing so we can agree on the next step.`;
    const link = $('#map-location-link');
    link.href = `location-${number + 1}.html`;
    // Preserve the decorative inline arrow without inserting untrusted HTML.
    link.firstChild.textContent = `Explore ${mapNames[number]} `;
    motion()?.enter($('#map-detail'), {
      type: 'fade-in',
      duration: 200
    });
  }));

  // Validate locally, then offer an explicit, user-reviewed WhatsApp handoff. Never store entries or claim delivery.
  const form = $('#quote-form');
  if (form) {
    const date = $('#date');
    const now = new Date();
    const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    date.min = today;
    const fields = $$('input, select, textarea', form);

    function errorFor(field) {
      if (field.type === 'checkbox') return field.checked ? '' : 'Please confirm that you agree to share these details through WhatsApp.';
      const value = field.value.trim();
      if (field.required && !value) return 'Please complete this field.';
      if (!value) return '';
      if (field.type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Enter an email address such as name@example.com.';
      if (field.type === 'tel' && (value.replace(/\D/g, '').length < 7 || !/^[+()\d\s.\-]+$/.test(value))) return 'Enter a phone number with at least 7 digits.';
      if (field.id === 'message' && value.length < 10) return 'Please add at least 10 characters about the issue.';
      if (field.type === 'date' && value < today) return 'Choose today or a future date.';
      return '';
    }

    function validate(field) {
      const message = errorFor(field);
      field.setAttribute('aria-invalid', String(Boolean(message)));
      document.getElementById(`${field.id}-error`).textContent = message;
      return !message;
    }
    form.addEventListener('submit', event => {
      event.preventDefault();
      const results = fields.map(validate);
      const firstInvalid = fields[results.indexOf(false)];
      const status = $('#form-status');
      status.hidden = false;
      if (firstInvalid) {
        status.textContent = 'Please review the highlighted fields. Nothing has been sent.';
        firstInvalid.focus();
        return;
      }
      status.replaceChildren();
      const message = document.createElement('p');
      message.textContent = 'Your request is ready. Open WhatsApp, review the message, and press Send to contact Apex Plumbing. Availability and appointments are confirmed in conversation.';
      const next = document.createElement('a');
      const draft = [
        'Plumbing enquiry for Apex Plumbing',
        `Name: ${$('#name').value.trim()}`,
        `Phone: ${$('#phone').value.trim()}`,
        `Email: ${$('#email').value.trim()}`,
        `Service: ${$('#service').value}`,
        `Property location: ${$('#location').value.trim()}`,
        `Preferred date: ${$('#date').value || 'To discuss'}`,
        `Details: ${$('#message').value.trim()}`,
        'Please contact me to discuss the scope, timing, and availability.'
      ].join('\n');
      next.href = 'https://wa.me/8801718658326?text=' + encodeURIComponent(draft);
      next.target = '_blank';
      next.rel = 'noopener noreferrer';
      next.className = 'text-link mt-24';
      next.textContent = 'Continue in WhatsApp →';
      const steps = document.createElement('a');
      steps.href = '../thank-you.html';
      steps.className = 'text-link mt-24';
      steps.textContent = 'Read the enquiry next steps →';
      status.append(message, next, document.createElement('br'), steps);
      status.setAttribute('tabindex', '-1');
      status.focus();
    });
    fields.forEach(field => {
      field.addEventListener('blur', () => validate(field));
      field.addEventListener('input', () => {
        if (field.getAttribute('aria-invalid') === 'true') validate(field);
        $('#form-status').hidden = true;
      });
    });
    // Enabled only after the prevention/validation handler is registered.
    const fieldset = $('fieldset', form);
    if (fieldset) fieldset.disabled = false;
  }

  // Start decorative entrances only after functional controls and fallback states are ready.
  motion()?.initialize();
})();
