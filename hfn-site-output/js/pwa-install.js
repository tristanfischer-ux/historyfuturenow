/**
 * PWA Install Prompt
 *
 * Shows a subtle, non-intrusive banner inviting readers to add HFN
 * to their home screen. Triggers after engagement (scroll or dwell),
 * respects prior dismissals and already-installed state.
 */
(function () {
  'use strict';

  var DISMISS_KEY = 'hfn_pwa_dismissed';
  var DISMISS_DAYS = 30;
  var ENGAGE_SCROLL_PCT = 0.25;
  var ENGAGE_DWELL_MS = 30000;

  var deferredPrompt = null;
  var banner = null;
  var engaged = false;
  var shown = false;

  function isInstalled() {
    if (window.matchMedia('(display-mode: standalone)').matches) return true;
    if (window.navigator.standalone === true) return true;
    return false;
  }

  function wasDismissed() {
    try {
      var ts = localStorage.getItem(DISMISS_KEY);
      if (!ts) return false;
      var diff = Date.now() - parseInt(ts, 10);
      return diff < DISMISS_DAYS * 86400000;
    } catch (e) { return false; }
  }

  function saveDismiss() {
    try { localStorage.setItem(DISMISS_KEY, String(Date.now())); } catch (e) {}
  }

  function isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
  }

  function showBanner() {
    if (shown || isInstalled() || wasDismissed()) return;
    if (!deferredPrompt && !isIOS()) return;
    shown = true;

    banner = document.createElement('div');
    banner.className = 'pwa-install-banner';
    banner.setAttribute('role', 'complementary');
    banner.setAttribute('aria-label', 'Install app');

    var icon = '<svg viewBox="0 0 32 32" width="28" height="28" style="flex-shrink:0;border-radius:5px">' +
      '<rect width="32" height="32" rx="6" fill="#1a1815"/>' +
      '<text x="4" y="23" font-family="Georgia,serif" font-size="20" font-weight="700" fill="#fff">H</text>' +
      '<text x="17" y="23" font-family="Georgia,serif" font-size="20" font-style="italic" font-weight="400" fill="#c43425">N</text></svg>';

    if (isIOS()) {
      banner.innerHTML = icon +
        '<span class="pwa-install-text">Read offline &mdash; tap <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-2px;margin:0 1px"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg> then <strong>Add to Home Screen</strong></span>' +
        '<button type="button" class="pwa-install-close" aria-label="Dismiss">&times;</button>';
    } else {
      banner.innerHTML = icon +
        '<span class="pwa-install-text">Read offline &mdash; add History Future Now to your home screen</span>' +
        '<button type="button" class="pwa-install-btn">Add</button>' +
        '<button type="button" class="pwa-install-close" aria-label="Dismiss">&times;</button>';
    }

    document.body.appendChild(banner);
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        banner.classList.add('visible');
      });
    });

    var addBtn = banner.querySelector('.pwa-install-btn');
    if (addBtn) {
      addBtn.addEventListener('click', function () {
        if (!deferredPrompt) return;
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then(function (result) {
          if (result.outcome === 'accepted') {
            if (window.gtag) gtag('event', 'pwa_install', { event_category: 'engagement' });
          }
          deferredPrompt = null;
          hideBanner(true);
        });
      });
    }

    banner.querySelector('.pwa-install-close').addEventListener('click', function () {
      hideBanner(true);
    });

    // Auto-dismiss after 12 seconds
    setTimeout(function () { hideBanner(false); }, 12000);
  }

  function hideBanner(persist) {
    if (!banner) return;
    if (persist) saveDismiss();
    banner.classList.remove('visible');
    setTimeout(function () {
      if (banner && banner.parentNode) banner.parentNode.removeChild(banner);
      banner = null;
    }, 400);
  }

  // Capture the install prompt event (Chrome, Edge, Samsung)
  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferredPrompt = e;
    if (engaged) showBanner();
  });

  // Track engagement: scroll past 25% of article
  var scrollDone = false;
  function checkScroll() {
    if (scrollDone) return;
    var scrollable = document.documentElement.scrollHeight - window.innerHeight;
    if (scrollable > 0 && window.scrollY / scrollable >= ENGAGE_SCROLL_PCT) {
      scrollDone = true;
      engaged = true;
      showBanner();
    }
  }
  document.addEventListener('scroll', checkScroll, { passive: true });

  // Track engagement: dwell for 30s
  setTimeout(function () {
    engaged = true;
    showBanner();
  }, ENGAGE_DWELL_MS);

  // Already installed: listen for the event
  window.addEventListener('appinstalled', function () {
    hideBanner(true);
    deferredPrompt = null;
  });
})();
