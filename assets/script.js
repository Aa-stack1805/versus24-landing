// Versus shared site behaviors. Keep this file small and dependency-free.

(() => {
  const nav = document.querySelector('.nav');
  const toggle = document.querySelector('.nav-toggle');

  // Mobile nav
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open);
    });
    // Close on link click (mobile)
    nav.querySelectorAll('.nav-link, .nav-cta').forEach(el => {
      el.addEventListener('click', () => nav.classList.remove('open'));
    });
  }

  // Nav border on scroll
  if (nav) {
    const updateNav = () => nav.classList.toggle('scrolled', window.scrollY > 8);
    updateNav();
    window.addEventListener('scroll', updateNav, { passive: true });
  }

  // Reveal-on-scroll, staggered per container: siblings that reveal together
  // cascade in at 70ms intervals instead of landing as one block.
  const reveals = document.querySelectorAll('.reveal');
  reveals.forEach(el => {
    const siblings = el.parentElement
      ? [...el.parentElement.children].filter(c => c.classList.contains('reveal'))
      : [el];
    const i = siblings.indexOf(el);
    if (i > 0) el.style.setProperty('--reveal-delay', Math.min(i * 70, 420) + 'ms');
  });
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('shown');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach(el => io.observe(el));
  } else {
    reveals.forEach(el => el.classList.add('shown'));
  }

  // Scroll progress hairline under the nav (skipped for reduced motion, since the
  // bar is display:none there anyway, so don't pay for the scroll listener).
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const bar = document.createElement('div');
    bar.className = 'scroll-progress';
    bar.setAttribute('aria-hidden', 'true');
    document.body.appendChild(bar);
    let ticking = false;
    const updateBar = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.transform = 'scaleX(' + (max > 0 ? Math.min(window.scrollY / max, 1) : 0) + ')';
      ticking = false;
    };
    window.addEventListener('scroll', () => {
      if (!ticking) { ticking = true; requestAnimationFrame(updateBar); }
    }, { passive: true });
    updateBar();
  }

  // Analytics: App Store click attribution (PostHog). Fires on every link to
  // the App Store: nav Download, hero badge, pricing CTAs, final-CTA badge, footer.
  document.querySelectorAll('a[href*="apps.apple.com"]').forEach(a => {
    a.addEventListener('click', () => {
      if (!window.posthog || typeof window.posthog.capture !== 'function') return;
      let location = 'other';
      if (a.closest('.nav')) location = 'nav';
      else if (a.closest('.hero, .hero-ctas')) location = 'hero';
      else if (a.closest('.pricing-grid, .plan')) location = 'pricing';
      else if (a.closest('.final-cta')) location = 'final_cta';
      else if (a.closest('.footer')) location = 'footer';
      try {
        window.posthog.capture('app_store_click', {
          location,
          page: window.location.pathname,
          link_text: (a.textContent || '').trim().slice(0, 40) || 'app_store_badge',
        });
      } catch (e) {}
    });
  });

  // Regional pricing. Billing runs through the App Store, which charges
  // per-storefront prices; the cards should show the visitor's storefront.
  // USD is baked into the HTML as the default; detection is local-only
  // (timezone/locale, no network) and a manual toggle always wins.
  const PRICING = {
    US: { label: '$ USD', symbol: '$',
          core:  { mo: 9.99,  yr: 79.99  },
          elite: { mo: 14.99, yr: 119.99 } },
    IN: { label: '₹ INR', symbol: '₹',
          core:  { mo: 250, yr: 2000 },
          elite: { mo: 500, yr: 4000 } },
  };

  const fmtPrice = n => n.toLocaleString('en-US', {
    minimumFractionDigits: Number.isInteger(n) ? 0 : 2,
    maximumFractionDigits: 2,
  });

  function detectRegion() {
    let stored = null;
    try { stored = localStorage.getItem('versus_region'); } catch (e) {}
    if (stored && PRICING[stored]) return { region: stored, source: 'manual' };
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      if (tz === 'Asia/Kolkata' || tz === 'Asia/Calcutta') return { region: 'IN', source: 'detected' };
    } catch (e) {}
    const langs = navigator.languages || [navigator.language || ''];
    if ([...langs].some(l => /-in$/i.test(l))) return { region: 'IN', source: 'detected' };
    return { region: 'US', source: 'default' };
  }

  function applyRegion(region) {
    const p = PRICING[region];
    document.querySelectorAll('[data-price]').forEach(el => {
      const tier = p[el.getAttribute('data-price')];
      if (!tier) return;
      const [int, dec] = fmtPrice(tier.mo).split('.');
      el.innerHTML = '<sup>' + p.symbol + '</sup>' + int + '<small>' + (dec ? '.' + dec : '') + '/mo</small>';
    });
    document.querySelectorAll('[data-period]').forEach(el => {
      const tier = p[el.getAttribute('data-period')];
      if (!tier) return;
      const save = Math.round((1 - tier.yr / (tier.mo * 12)) * 100);
      el.textContent = 'or ' + p.symbol + fmtPrice(tier.yr) + '/yr (save ' + save + '%)';
    });
    document.querySelectorAll('.currency-toggle button').forEach(btn => {
      btn.setAttribute('aria-pressed', String(btn.dataset.region === region));
    });
  }

  function captureEvent(name, props) {
    if (!window.posthog || typeof window.posthog.capture !== 'function') return;
    try { window.posthog.capture(name, props); } catch (e) {}
  }

  if (document.querySelector('[data-price]')) {
    const { region, source } = detectRegion();
    const grid = document.querySelector('.pricing-grid');
    // The toggle is an escape hatch for misdetection, not a feature for
    // everyone: a default-US visitor can't choose to pay INR (Apple charges
    // their storefront regardless), so they get no toggle at all. It renders
    // only for detected-IN visitors and anyone who has manually switched;
    // both need the way back.
    if (grid && (region !== 'US' || source === 'manual')) {
      const toggle = document.createElement('div');
      toggle.className = 'currency-toggle';
      toggle.setAttribute('role', 'group');
      toggle.setAttribute('aria-label', 'Currency');
      Object.keys(PRICING).forEach(code => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.dataset.region = code;
        btn.textContent = PRICING[code].label;
        btn.setAttribute('aria-pressed', 'false');
        btn.addEventListener('click', () => {
          try { localStorage.setItem('versus_region', code); } catch (e) {}
          applyRegion(code);
          captureEvent('pricing_currency_toggled', { region: code, page: window.location.pathname });
        });
        toggle.appendChild(btn);
      });
      grid.parentElement.insertBefore(toggle, grid);
    }
    applyRegion(region);
    captureEvent('pricing_region_shown', { region, source, page: window.location.pathname });
  }

  // Units. The app and most of the world are metric, so metric is what ships
  // in the HTML; visitors whose locale is imperial get the copy converted.
  // Screenshot alt text is deliberately left alone: it describes what is
  // actually on the screen, which is always metric.
  const UNITS = {
    cm: { to: 'in', factor: 1 / 2.54 },
    kg: { to: 'lb', factor: 2.2046226 },
  };

  function usesImperial() {
    const langs = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language || ''];
    for (const tag of langs) {
      let region = '';
      try {
        region = (new Intl.Locale(tag)).region || '';
      } catch (e) {
        const m = /[-_]([A-Za-z]{2})\b/.exec(tag);
        region = m ? m[1] : '';
      }
      // Only these three still use imperial for body measurements.
      if (region) return ['US', 'LR', 'MM'].indexOf(region.toUpperCase()) !== -1;
    }
    return false;
  }

  if (usesImperial()) {
    document.querySelectorAll('[data-measure]').forEach(el => {
      const unit = UNITS[el.getAttribute('data-unit')];
      const value = parseFloat(el.getAttribute('data-measure'));
      if (!unit || isNaN(value)) return;
      el.textContent = Math.round(value * unit.factor) + ' ' + unit.to;
    });
  }

  // Waitlist form. POSTs to Supabase Edge Function which adds to Resend Audience.
  const WAITLIST_ENDPOINT = 'https://fuoylucdxtrnbolxkqjz.supabase.co/functions/v1/waitlist-signup';

  document.querySelectorAll('form[data-waitlist]').forEach(form => {
    // Inject honeypot once
    if (!form.querySelector('input[name="website"]')) {
      const hp = document.createElement('input');
      hp.type = 'text';
      hp.name = 'website';
      hp.tabIndex = -1;
      hp.autocomplete = 'off';
      hp.setAttribute('aria-hidden', 'true');
      hp.style.cssText = 'position:absolute;left:-9999px;width:1px;height:1px;opacity:0;pointer-events:none;';
      form.insertBefore(hp, form.firstChild);
    }

    form.addEventListener('submit', async e => {
      e.preventDefault();
      const data = new FormData(form);
      const email = (data.get('email') || '').toString().trim();
      const website = (data.get('website') || '').toString();
      const list = form.getAttribute('data-list') || '';

      if (!email || !email.includes('@')) {
        showFormMessage(form, 'Please enter a valid email.', false);
        return;
      }

      const submitBtn = form.querySelector('button[type="submit"]');
      const originalText = submitBtn ? submitBtn.textContent : '';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Adding…';
      }

      try {
        const params = new URLSearchParams(window.location.search);
        const res = await fetch(WAITLIST_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email,
            website,
            list,
            source_page: window.location.pathname,
            utm_source: params.get('utm_source') || '',
            utm_medium: params.get('utm_medium') || '',
            utm_campaign: params.get('utm_campaign') || '',
          }),
        });
        const json = await res.json().catch(() => ({}));
        if (!res.ok) {
          showFormMessage(form, json.error || "Couldn't add you to the list. Try again in a moment.", false);
          return;
        }
        const android = list === 'android';
        const msg = json.duplicate
          ? (android ? "You're already on the Android list. We'll email you at launch."
                     : "You're already on the list. We'll email you at launch.")
          : (android ? "You're on the list. We'll email you the moment Versus lands on Android."
                     : "You're on the list. We'll email you the moment Versus is live.");
        showFormMessage(form, msg, true);
        form.reset();
      } catch {
        showFormMessage(form, 'Network error. Try again in a moment.', false);
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = originalText;
        }
      }
    });
  });

  function showFormMessage(form, text, ok) {
    let el = form.querySelector('.form-message');
    if (!el) {
      el = document.createElement('p');
      el.className = 'form-message waitlist-microcopy';
      form.appendChild(el);
    }
    el.textContent = text;
    el.style.color = ok ? 'var(--success)' : 'var(--error)';
  }
})();
