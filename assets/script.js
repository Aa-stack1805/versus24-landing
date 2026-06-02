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

  // Reveal-on-scroll
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('shown');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
    document.querySelectorAll('.reveal').forEach(el => io.observe(el));
  } else {
    document.querySelectorAll('.reveal').forEach(el => el.classList.add('shown'));
  }

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
        const msg = json.duplicate
          ? "You're already on the list. We'll email you at launch."
          : "You're on the list. We'll email you the moment Versus is live.";
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
