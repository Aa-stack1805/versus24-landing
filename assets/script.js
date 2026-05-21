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

  // Waitlist form — captures locally for now. TODO wire to Beehiiv/Resend.
  document.querySelectorAll('form[data-waitlist]').forEach(form => {
    form.addEventListener('submit', e => {
      e.preventDefault();
      const email = (new FormData(form).get('email') || '').toString().trim();
      if (!email || !email.includes('@')) {
        showFormMessage(form, 'Please enter a valid email.', false);
        return;
      }
      try {
        const stored = JSON.parse(localStorage.getItem('versus_waitlist') || '[]');
        if (!stored.includes(email)) stored.push(email);
        localStorage.setItem('versus_waitlist', JSON.stringify(stored));
      } catch {}
      showFormMessage(form, "You're on the list. We'll email you the moment Versus is live.", true);
      form.reset();
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
