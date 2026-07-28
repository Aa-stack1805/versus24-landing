/* The invite page.
 *
 * Three URL shapes reach this script, and all three have to keep working:
 *
 *   /r/{code}     what shipped app builds hand out. GitHub Pages has no
 *                 wildcard routing, so this is served by 404.html with a 404
 *                 status. It renders fine, but a 404 means most messaging
 *                 apps refuse to build a link preview for it.
 *   /r/?c={code}  a real 200 page, so previews work.
 *   /r/#{code}    also 200, and the code never reaches the server at all.
 *                 This is the shape new app builds should generate.
 *
 * The same script also renders the plain 404 state, so there is one copy of
 * this UI rather than one per entry point.
 */
(function () {
  var APP_ID = '6760545665';
  var SITE = 'https://versus24.net';

  // ct is the App Analytics campaign token, so an install that came from an
  // invite is not counted as one that came from a dead link. It only records
  // once a Provider ID (pt) from App Store Connect is added alongside it;
  // until then Apple drops both, which costs nothing but attributes nothing.
  function storeUrl(campaign) {
    return 'https://apps.apple.com/app/id' + APP_ID + '?ct=' + campaign + '&mt=8';
  }

  var slot = document.getElementById('rr-slot');
  if (!slot) return;

  var onInvitePath = /^\/r(\/|$)/.test(location.pathname);

  function readCode() {
    var params = location.search ? new URLSearchParams(location.search) : null;
    var raw = (params && params.get('c')) ||
              location.hash.replace(/^#/, '') ||
              (location.pathname.match(/^\/r\/([^\/?#]+)/) || [])[1] || '';
    try { raw = decodeURIComponent(raw); } catch (e) { /* leave as-is */ }
    // Codes are uppercase alphanumeric with hyphens. Anything else is damage
    // from a mis-pasted link, and stripping it can legitimately leave nothing.
    return raw.toUpperCase().replace(/[^A-Z0-9\-]/g, '').slice(0, 32);
  }

  function track(event, props) {
    if (window.posthog && window.posthog.capture) {
      try { window.posthog.capture(event, props || {}); } catch (e) {}
    }
  }

  function storeBadge(campaign, code) {
    var a = document.createElement('a');
    a.className = 'appstore-badge';
    a.href = storeUrl(campaign);
    a.setAttribute('aria-label', 'Download Versus Training on the App Store');
    a.innerHTML = '<img src="/assets/appstore-badge.svg" alt="Download on the App Store"/>';
    a.addEventListener('click', function () {
      track(campaign + '_appstore_click', { code: code || null });
    });
    return a;
  }

  function render(html) {
    slot.innerHTML = html;
    return slot;
  }

  if (onInvitePath) {
    var code = readCode();

    if (code) {
      // Tapping the Smart App Banner should carry the code into the app, and
      // the path shape is the one every shipped build already parses.
      var banner = document.querySelector('meta[name="apple-itunes-app"]');
      if (banner) {
        banner.setAttribute('content',
          'app-id=' + APP_ID + ', app-argument=' + SITE + '/r/' + encodeURIComponent(code));
      }
      document.title = 'Your invite · Versus Training';

      render(
        '<p class="eyebrow">You have been invited</p>' +
        '<h1 class="rr-title">Get <span class="accent-gold">7 free days of Core</span>.</h1>' +
        '<p class="rr-lead">You and the friend who invited you both get 7 free days of Versus Core.</p>' +
        '<button class="rr-code" type="button" id="rr-code" title="Tap to copy"></button>' +
        '<p class="rr-copy-state" id="rr-copy-state">Tap the code to copy it</p>' +
        '<p class="rr-steps">Download Versus, then enter this code when you sign up.</p>' +
        '<p class="rr-what">Versus is a training log for people who do more than one thing: ' +
        'combat sports, lifting, endurance and sport in one app, on iPhone and Apple Watch. ' +
        '<a href="/features/" class="text-gold">See what is in it</a></p>');

      var codeEl = document.getElementById('rr-code');
      var state = document.getElementById('rr-copy-state');
      codeEl.textContent = code;
      slot.insertBefore(storeBadge('referral', code), state.nextSibling);

      var revert;
      codeEl.addEventListener('click', function () {
        var done = function (ok) {
          state.textContent = ok ? 'Copied' : 'Select the code above to copy it';
          state.classList.toggle('is-done', ok);
          clearTimeout(revert);
          revert = setTimeout(function () {
            state.textContent = 'Tap the code to copy it';
            state.classList.remove('is-done');
          }, 2400);
          track('referral_code_copied', { code: code, ok: ok });
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(code).then(function () { done(true); },
                                                   function () { done(false); });
        } else {
          done(false);
        }
      });

      track('referral_link_opened', {
        code: code,
        // Which shape they arrived on, so the 404 shape can be retired once
        // app builds stop generating it.
        shape: location.search ? 'query' : (location.hash ? 'hash' : 'path')
      });

    } else {
      // An invite path with no usable code: the link was truncated or mangled
      // in whatever app it was pasted through. Say so, and still offer the app.
      document.title = 'Invite link · Versus Training';
      render(
        '<p class="eyebrow">Invite link</p>' +
        '<h1 class="rr-title">This invite is missing its code.</h1>' +
        '<p class="rr-lead">The link came through incomplete. Ask your friend to send it again, ' +
        'or download Versus and enter their code when you sign up.</p>');
      slot.appendChild(storeBadge('referral'));
      track('referral_incomplete', { path: location.pathname + location.search });
    }

  } else {
    render(
      '<p class="eyebrow">404</p>' +
      '<h1 class="rr-title">Page not found.</h1>' +
      '<p class="rr-lead">That page does not exist. Head back home, or grab the app.</p>' +
      '<div class="rr-actions"><a class="btn btn-ghost btn-lg" href="/">Go home</a></div>');
    slot.appendChild(storeBadge('notfound'));
    track('page_404', { path: location.pathname });
  }
})();
