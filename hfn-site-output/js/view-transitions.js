/**
 * Smooth page transitions using View Transitions API (when supported).
 * Intercepts same-origin link clicks, fetches the new page, and fades between views.
 */
(function () {
  if (!document.startViewTransition) return;

  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest('a');
    if (!a || a.target === '_blank' || a.hasAttribute('download') || a.getAttribute('rel') === 'external') return;
    var href = a.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) return;
    try {
      var url = new URL(href, location.origin);
      if (url.origin !== location.origin) return;
    } catch (err) {
      return;
    }

    e.preventDefault();
    fetch(url.pathname + url.search, { headers: { 'Accept': 'text/html' } })
      .then(function (res) {
        if (!res.ok) throw new Error(res.status);
        return res.text();
      })
      .then(function (html) {
        var parser = new DOMParser();
        var doc = parser.parseFromString(html, 'text/html');
        var newBody = doc.body;
        var runScripts = function () {
          document.body.querySelectorAll('script').forEach(function (oldScript) {
            var s = document.createElement('script');
            if (oldScript.src) {
              s.src = oldScript.src;
              s.async = false;
            } else {
              s.textContent = oldScript.textContent;
            }
            oldScript.parentNode.replaceChild(s, oldScript);
          });
        };
        document.startViewTransition(function () {
          document.title = doc.title;
          document.body.innerHTML = newBody.innerHTML;
          runScripts();
        }).finished.catch(function () {}).then(function () {
          history.pushState({}, '', url.href);
        });
      })
      .catch(function () {
        location.href = href;
      });
  });
})();
