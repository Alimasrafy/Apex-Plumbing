/* Apex Plumbing motion: native browser APIs only. No tracking, loops, or dependency. */
'use strict';
(() => {
  if (window.ApexMotion) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const narrow = matchMedia('(max-width: 767px)');
  const rootStyle = getComputedStyle(document.documentElement);
  const ease = rootStyle.getPropertyValue('--motion-ease').trim() || 'cubic-bezier(0.22, 1, 0.36, 1)';
  const ms = (name, fallback) => parseFloat(rootStyle.getPropertyValue(name)) || fallback;
  const durations = {
    reveal: ms('--motion-reveal', 620),
    hero: ms('--motion-hero', 760),
    menu: ms('--motion-menu', 300),
    dropdown: ms('--motion-dropdown', 200),
    micro: ms('--motion-fast', 200)
  };
  const active = new Map();
  const disclosureStates = new WeakMap();
  const visibleGroups = new WeakMap();
  const revealed = new WeakSet();
  let revealObserver = null;
  const pendingReveals = new Set();
  const supportsAnimation = typeof Element.prototype.animate === 'function';

  function stop(element, settle = false) {
    const record = active.get(element);
    if (!record) return;
    active.delete(element);
    record.animation.cancel();
    if (settle) record.complete?.();
  }

  function play(element, frames, options = {}, complete = null) {
    if (!element) return;
    stop(element);
    if (reduce.matches || !supportsAnimation || options.instant) {
      complete?.();
      return;
    }
    try {
      const animation = element.animate(frames, {
        duration: options.duration || durations.reveal,
        delay: options.delay || 0,
        easing: ease,
        fill: options.delay ? 'backwards' : 'none'
      });
      const record = {
        animation,
        complete
      };
      active.set(element, record);
      animation.finished.then(() => {
        if (active.get(element) !== record) return;
        active.delete(element);
        complete?.();
      }).catch(() => {
        /* Cancellation is expected on rapid toggles and preference changes. */
      });
    } catch (_) {
      complete?.(); // Unsupported animation options must never hide content or break a control.
    }
  }

  function framesFor(type = 'fade-up', distance = narrow.matches ? 16 : 24) {
    const x = narrow.matches ? 12 : 24;
    const transform = {
      'fade-up': `translateY(${distance}px)`,
      'fade-in': 'none',
      'slide-left': `translateX(-${x}px)`,
      'slide-right': `translateX(${x}px)`,
      'scale-in': 'translateY(12px) scale(0.98)'
    } [type] || `translateY(${distance}px)`;
    return [{
      opacity: 0,
      transform
    }, {
      opacity: 1,
      transform: 'none'
    }];
  }

  function enter(element, options = {}) {
    if (!element || element.hidden || element.matches(':focus-within')) return;
    const distance = options.distance ?? (element.classList.contains('motion-reveal') ? parseFloat(getComputedStyle(element).getPropertyValue('--reveal-distance')) || undefined : undefined);
    play(element, framesFor(options.type, distance), options);
  }

  // Semantic state is updated immediately; only the visual close is deferred.
  // Closing panels are inert and excluded from the accessibility tree until hidden.
  function disclose(element, open, options = {}) {
    if (!element) return;
    if (disclosureStates.get(element) === open) {
      if (options.instant) stop(element, true);
      return;
    }
    disclosureStates.set(element, open);
    stop(element);
    const classMode = Boolean(options.activeClass);
    const finish = () => {
      if (disclosureStates.get(element) !== open) return;
      if (classMode) element.classList.toggle(options.activeClass, open);
      else element.hidden = !open;
      element.inert = false;
      element.removeAttribute('aria-hidden');
      options.onComplete?.();
    };
    if (open) {
      if (classMode) element.classList.add(options.activeClass);
      else element.hidden = false;
      element.inert = false;
      element.removeAttribute('aria-hidden');
      play(element, [{
        opacity: 0,
        transform: 'translateY(8px)'
      }, {
        opacity: 1,
        transform: 'none'
      }], options, finish);
      if (options.items && !reduce.matches && !options.instant) {
        [...element.querySelectorAll(options.items)].filter(item => item.getClientRects().length).forEach((item, i) => {
          play(item, [{
            opacity: 0.65,
            transform: 'translateY(5px)'
          }, {
            opacity: 1,
            transform: 'none'
          }], {
            duration: 230,
            delay: Math.min(i * 28, 140)
          });
        });
      }
    } else {
      const alreadyHidden = element.hidden || getComputedStyle(element).display === 'none';
      element.inert = true;
      element.setAttribute('aria-hidden', 'true');
      play(element, [{
        opacity: 1,
        transform: 'none'
      }, {
        opacity: 0,
        transform: 'translateY(6px)'
      }], {
        ...options,
        instant: options.instant || alreadyHidden
      }, finish);
    }
  }

  // Filters and manual sliders keep their existing hidden states and layout semantics.
  // Only newly visible results receive a short entrance, never auto-rotation.
  function swapVisible(container, items, options = {}) {
    if (!container) return;
    const next = new Set(items);
    const previous = visibleGroups.get(container);
    visibleGroups.set(container, next);
    if (!previous || options.instant || reduce.matches) return;
    items.filter(item => !previous.has(item)).forEach((item, i) => {
      if (!inViewport(item)) return;
      revealed.add(item);
      revealObserver?.unobserve(item);
      const frames = options.slide ? [{
        opacity: 0.45,
        transform: `translateX(${(options.direction || 1) * 12}px)`
      }, {
        opacity: 1,
        transform: 'none'
      }] : framesFor('fade-up', 8);
      play(item, frames, {
        duration: 300,
        delay: Math.min(i * 40, 120)
      });
    });
  }

  function inViewport(element) {
    const r = element.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.top < innerHeight && r.bottom > 0;
  }

  // Public integration hooks are used by existing controls, not additional click listeners.
  window.ApexMotion = {
    enter,
    disclose,
    swapVisible,
    stop,
    durations
  };

  // Add separate strokes to the existing SVG; keep its class, size, and accessible button.
  const menuIcon = document.querySelector('.menu-toggle .icon');
  if (menuIcon && menuIcon.querySelectorAll('path').length === 1) {
    const top = menuIcon.querySelector('path');
    top.setAttribute('d', 'M4 6h16');
    top.setAttribute('class', 'menu-line menu-line-top');
    for (const [name, d] of [
        ['middle', 'M4 12h16'],
        ['bottom', 'M4 18h16']
      ]) {
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      line.setAttribute('d', d);
      line.setAttribute('class', `menu-line menu-line-${name}`);
      menuIcon.append(line);
    }
  }

  function heroEntrance() {
    const copy = document.querySelector('.hero-copy');
    if (copy) {
      const sequence = ['.eyebrow', 'h1', '.hero-description', '.actions', '.hero-reassurance'];
      sequence.forEach((selector, i) => {
        const element = copy.querySelector(selector);
        if (!element) return;
        // The headline is never hidden or delayed from view; this is progressive enhancement.
        play(element, [{
          opacity: selector === 'h1' ? 0.85 : 0.6,
          transform: 'translateY(20px)'
        }, {
          opacity: 1,
          transform: 'none'
        }], {
          duration: durations.hero,
          delay: i * 85
        });
      });
      const image = document.querySelector('.hero-photo');
      play(image, [{
        opacity: 0.75,
        transform: 'scale(1.03)'
      }, {
        opacity: 1,
        transform: 'scale(1)'
      }], {
        duration: 820,
        delay: 360
      });
    } else {
      const pageHero = document.querySelector('.page-hero');
      if (pageHero) {
        ['.breadcrumbs', '.eyebrow', 'h1', '.lead'].forEach((selector, i) => {
          const element = pageHero.querySelector(selector);
          play(element, [{
            opacity: selector === 'h1' ? 0.85 : 0.65,
            transform: 'translateY(12px)'
          }, {
            opacity: 1,
            transform: 'none'
          }], {
            duration: document.body.className.includes('legal-') ? 500 : durations.hero,
            delay: i * 70
          });
        });
      }
      const error = document.querySelector('.error-content');
      if (error)[...error.children].slice(0, 4).forEach((element, i) => {
        play(element, [{
          opacity: element.tagName === 'H1' ? 0.85 : 0.75,
          transform: 'translateY(12px)'
        }, {
          opacity: 1,
          transform: 'none'
        }], {
          duration: 680,
          delay: i * 80
        });
      });
    }
  }

  function setupReveals() {
    if (!('IntersectionObserver' in window) || reduce.matches) return;
    const pending = pendingReveals;
    revealObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting || revealed.has(entry.target)) return;
        const target = entry.target;
        revealed.add(target);
        revealObserver.unobserve(target);
        pending.delete(target);
        target.classList.add('is-revealed');
        enter(target, {
          type: target.dataset.motion,
          delay: Number(target.dataset.motionDelay) || 0
        });
        // Small nested checklist movement is limited to 6px; no separate observer/listener.
        [...target.querySelectorAll('.check-list li')].forEach((li, i) => {
          play(li, [{
            opacity: 0.6,
            transform: 'translateY(6px)'
          }, {
            opacity: 1,
            transform: 'none'
          }], {
            duration: 500,
            delay: Math.min(i * 60, 180)
          });
        });
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -40px 0px'
    });

    function register(selector, type = 'fade-up', stagger = false) {
      document.querySelectorAll(selector).forEach((element, i) => {
        if (element.classList.contains('motion-reveal') || element.closest('.home-hero, .page-hero')) return;
        if (element.parentElement?.closest('.motion-reveal')) return;
        element.classList.add('motion-reveal');
        element.dataset.motion = type;
        element.dataset.motionDelay = String(stagger ? Math.min(i % 4 * 70, 210) : 0);
        pending.add(element);
        revealObserver.observe(element);
      });
    }
    register('main .section-head');
    register('main .about-visual, main .split > img', 'slide-left');
    register('main .split > div:not(.about-visual)', 'slide-right');
    register('main .grid > .card, main .grid > .feature-card', 'fade-up', true);
    register('main .grid > .step', 'scale-in', true);
    register('.trust-grid > div', 'fade-in', true);
    register('.emergency-band .container > div, .final-cta .container > div', 'fade-up');
    register('main .grid > figure', 'fade-in', true);
    register('.confirmation-icon', 'scale-in');
    register('.confirmation-panel > h2, .confirmation-panel > p', 'fade-up');
    register('.footer-grid > div', 'fade-in', true);

  }

  // Keyboard jumps should show focused content immediately, not wait for a reveal.
  document.addEventListener('focusin', event => {
    for (let element = event.target; element && element !== document.body; element = element.parentElement) {
      const isReveal = element.classList?.contains('motion-reveal');
      if (!isReveal && !element.matches('.hero-copy .actions, .nav-dropdown, .main-nav.is-open, .main-nav .nav-link')) continue;
      stop(element, true);
      if (isReveal) {
        revealed.add(element);
        revealObserver?.unobserve(element);
        element.classList.add('is-revealed');
      }
    }
  });

  function setupContents() {
    // Article contents uses a small observer region, never a per-scroll DOM scan.
    const toc = document.querySelector('.article-toc');
    if (toc && 'IntersectionObserver' in window) {
      const links = [...toc.querySelectorAll('a[href^="#"]')];
      const lookup = new Map(links.map(link => [link.hash.slice(1), link]));
      const candidates = new Set();
      let tocObserver;
      let resizeFrame = 0;

      function observeContents() {
        tocObserver?.disconnect();
        candidates.clear();
        const header = document.querySelector('.site-header');
        const top = Math.min((header?.offsetHeight || 88) + 20, innerHeight * 0.25);
        const bottom = Math.round(innerHeight * 0.5);
        tocObserver = new IntersectionObserver(entries => {
          entries.forEach(entry => {
            if (entry.isIntersecting) candidates.add(entry.target);
            else candidates.delete(entry.target);
          });
          const visible = [...candidates].map(section => ({
            section,
            top: section.getBoundingClientRect().top
          })).sort((a, b) => a.top - b.top);
          if (!visible.length) return;
          const headerBottom = (header?.getBoundingClientRect().bottom || 0) + 16;
          const pick = visible.find(item => item.top >= headerBottom) || visible[visible.length - 1];
          const current = lookup.get(pick.section.id);
          links.forEach(link => {
            if (link === current) link.setAttribute('aria-current', 'location');
            else link.removeAttribute('aria-current');
          });
        }, {
          rootMargin: `-${Math.round(top)}px 0px -${bottom}px 0px`,
          threshold: 0
        });
        lookup.forEach((_, id) => {
          const section = document.getElementById(id);
          if (section) tocObserver.observe(section);
        });
      }
      observeContents();
      window.addEventListener('resize', () => {
        if (resizeFrame) return;
        resizeFrame = requestAnimationFrame(() => {
          resizeFrame = 0;
          observeContents();
        });
      }, {
        passive: true
      });
    }

  }

  reduce.addEventListener('change', () => {
    if (!reduce.matches) return;
    [...active.keys()].forEach(element => stop(element, true));
    revealObserver?.disconnect();
    pendingReveals.forEach(element => element.classList.add('is-revealed'));
    pendingReveals.clear();
  });

  // A responsive layout change finishes decorative movement without hiding content.
  narrow.addEventListener('change', () => {
    [...active.entries()].forEach(([element, record]) => {
      if (!record.complete) stop(element);
    });
  });

  let initialized = false;

  function initialize() {
    if (initialized) return;
    initialized = true;
    document.querySelectorAll('.review-slider, #blog-grid, #reviews-grid').forEach(container => {
      swapVisible(container, [...container.querySelectorAll('.review-card, .blog-card')].filter(card => !card.hidden), {
        instant: true
      });
    });
    setupContents();
    if (!reduce.matches) {
      heroEntrance();
      setupReveals();
    }
  }
  window.ApexMotion.initialize = initialize;
  initialize();
})();
