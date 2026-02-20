/**
 * History Future Now — Soft Navigation
 *
 * Intercepts same-origin link clicks and swaps page content without a full
 * reload, preserving the audio element and queue player state so playback
 * continues uninterrupted across page navigations.
 */
(function () {
  'use strict';

  var SKIP_SCRIPTS = ['queue.js', 'soft-nav.js'];
  var navigating = false;

  function shouldIntercept(a) {
    if (!a || a.target === '_blank' || a.hasAttribute('download')) return false;
    if (a.getAttribute('rel') === 'external') return false;
    var href = a.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('mailto:') ||
        href.startsWith('tel:') || href.startsWith('javascript:')) return false;
    try {
      var url = new URL(href, location.origin);
      if (url.origin !== location.origin) return false;
      return url;
    } catch (e) { return false; }
  }

  function isSkippedScript(src) {
    if (!src) return false;
    for (var i = 0; i < SKIP_SCRIPTS.length; i++) {
      if (src.indexOf(SKIP_SCRIPTS[i]) !== -1) return true;
    }
    return false;
  }

  function isAlreadyLoaded(src) {
    if (!src) return false;
    var path = src.replace(/\?.*$/, '');
    if (path.indexOf('chart.umd') !== -1 && window.Chart) return true;
    if (path.indexOf('chartjs-plugin-annotation') !== -1 && window.Chart) return true;
    if (path.indexOf('chartjs-chart-geo') !== -1 && window.ChartGeo) return true;
    return false;
  }

  function executeScripts(container, callback) {
    var scripts = [];
    container.querySelectorAll('script').forEach(function (s) {
      if (s.src && isSkippedScript(s.src)) return;
      scripts.push(s);
    });

    var i = 0;
    function next() {
      if (i >= scripts.length) { callback(); return; }
      var old = scripts[i++];
      var s = document.createElement('script');

      if (old.src) {
        if (isAlreadyLoaded(old.src)) { next(); return; }
        s.src = old.src;
        s.async = false;
        s.onload = next;
        s.onerror = next;
        old.parentNode.replaceChild(s, old);
      } else {
        s.textContent = old.textContent;
        old.parentNode.replaceChild(s, old);
        next();
      }
    }
    next();
  }

  function navigateTo(path, isPopstate) {
    if (navigating) return;
    navigating = true;

    fetch(path, { headers: { 'Accept': 'text/html' } })
      .then(function (res) {
        if (!res.ok) throw new Error(res.status);
        return res.text();
      })
      .then(function (html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');

        // Detach persistent elements from current DOM
        var audioEl = document.querySelector('body > audio');
        var toast = document.getElementById('hfnToast');
        var queueBarEl = document.getElementById('queueBar');
        var queuePanelEl = document.getElementById('queuePanel');
        if (audioEl) audioEl.remove();
        if (toast) toast.remove();
        if (queueBarEl) queueBarEl.remove();
        if (queuePanelEl) queuePanelEl.remove();

        // Strip queue bar, queue panel, and persistent scripts from new page
        var newBody = doc.body;
        var stripIds = ['queueBar', 'queuePanel'];
        stripIds.forEach(function (id) {
          var el = newBody.querySelector('#' + id);
          if (el) el.remove();
        });
        newBody.querySelectorAll('script').forEach(function (s) {
          if (s.src && isSkippedScript(s.src)) s.remove();
        });

        // Clear current body and insert new content
        document.body.innerHTML = '';
        document.body.style.overflow = '';
        document.body.classList.remove('nav-focus-hidden');
        while (newBody.firstChild) {
          document.body.appendChild(newBody.firstChild);
        }

        // Re-attach persistent elements
        if (audioEl) document.body.appendChild(audioEl);
        if (toast) document.body.appendChild(toast);
        if (queueBarEl) document.body.appendChild(queueBarEl);
        if (queuePanelEl) document.body.appendChild(queuePanelEl);

        // Update document title and meta
        document.title = doc.title;
        var metaNames = ['description'];
        var metaProps = ['og:title', 'og:description', 'og:image', 'og:url',
                         'twitter:title', 'twitter:description', 'twitter:image'];
        metaNames.forEach(function (name) {
          var nw = doc.head.querySelector('meta[name="' + name + '"]');
          var cur = document.head.querySelector('meta[name="' + name + '"]');
          if (nw && cur) cur.setAttribute('content', nw.getAttribute('content'));
        });
        metaProps.forEach(function (prop) {
          var nw = doc.head.querySelector('meta[property="' + prop + '"]');
          var cur = document.head.querySelector('meta[property="' + prop + '"]');
          if (nw && cur) cur.setAttribute('content', nw.getAttribute('content'));
        });

        // Execute new page scripts sequentially, then rebind queue
        executeScripts(document.body, function () {
          if (window.HFNQueue && window.HFNQueue.rebind) {
            window.HFNQueue.rebind();
          }
          navigating = false;
        });

        if (!isPopstate) {
          history.pushState({ softNav: true }, '', path);
        }
        window.scrollTo(0, 0);
      })
      .catch(function () {
        navigating = false;
        location.href = path;
      });
  }

  // Intercept link clicks
  document.addEventListener('click', function (e) {
    if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    var a = e.target && e.target.closest('a');
    var url = shouldIntercept(a);
    if (!url) return;

    // Same-page hash link — let browser handle
    if (url.pathname === location.pathname && url.hash) return;

    e.preventDefault();
    navigateTo(url.pathname + url.search + url.hash);
  });

  // Handle back/forward navigation
  window.addEventListener('popstate', function () {
    navigateTo(location.pathname + location.search + location.hash, true);
  });
})();
