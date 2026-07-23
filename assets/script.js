// Versus shared site behaviors — keep this file small and dependency-free.

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

  // Scroll progress hairline under the nav (skipped for reduced motion — the
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

  // Analytics — App Store click attribution (PostHog). Fires on every link to
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

  // Waitlist form — POSTs to Supabase Edge Function which adds to Resend Audience.
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
