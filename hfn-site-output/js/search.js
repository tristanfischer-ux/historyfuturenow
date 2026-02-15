/**
 * History Future Now — Client-side article search
 * Lazily loads /search-index.json on first open, filters in real-time.
 */
(function () {
  'use strict';

  var overlay = document.getElementById('searchOverlay');
  var input = document.getElementById('searchInput');
  var results = document.getElementById('searchResults');
  var openBtn = document.getElementById('searchOpen');
  var closeBtn = document.getElementById('searchClose');

  if (!overlay || !input || !results || !openBtn) return;

  var index = null;
  var activeIdx = -1;
  var HINT_HTML = '<div class="search-hint">Type to search across all articles</div>';

  function open() {
    overlay.classList.add('open');
    overlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    input.value = '';
    results.innerHTML = HINT_HTML;
    activeIdx = -1;
    setTimeout(function () { input.focus(); }, 60);
    if (!index) loadIndex();
  }

  function close() {
    overlay.classList.remove('open');
    overlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    activeIdx = -1;
  }

  function loadIndex() {
    fetch('/search-index.json')
      .then(function (r) { return r.json(); })
      .then(function (data) { index = data; })
      .catch(function () { index = []; });
  }

  /** @description Simple scoring: matches in title score higher than excerpt. */
  function score(article, terms) {
    var s = 0;
    var titleLower = article.title.toLowerCase();
    var excerptLower = article.excerpt.toLowerCase();
    var sectionLower = article.section.toLowerCase();
    for (var i = 0; i < terms.length; i++) {
      var t = terms[i];
      if (titleLower.indexOf(t) !== -1) s += 10;
      if (sectionLower.indexOf(t) !== -1) s += 3;
      if (excerptLower.indexOf(t) !== -1) s += 1;
    }
    return s;
  }

  function render(matched) {
    if (matched.length === 0) {
      results.innerHTML = '<div class="search-empty">No articles found</div>';
      return;
    }
    var html = '';
    for (var i = 0; i < matched.length; i++) {
      var a = matched[i];
      var badges = '';
      if (a.chartCount > 0) {
        badges += '<span class="search-badge search-badge-chart">' + a.chartCount + ' charts</span>';
      }
      if (a.hasAudio) {
        badges += '<span class="search-badge search-badge-audio">Audio</span>';
      }
      html += '<a href="/articles/' + a.slug + '" class="search-result" data-idx="' + i + '">' +
        '<span class="search-result-kicker" style="color:' + a.color + '">' + a.label + ' &middot; ' + escHtml(a.section) + badges + '</span>' +
        '<span class="search-result-title">' + escHtml(a.title) + '</span>' +
        '<span class="search-result-meta">' + a.readingTime + ' min read</span>' +
        '</a>';
    }
    results.innerHTML = html;
  }

  function escHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function onInput() {
    if (!index) return;
    var q = input.value.trim().toLowerCase();
    if (q.length === 0) {
      results.innerHTML = HINT_HTML;
      activeIdx = -1;
      return;
    }
    var terms = q.split(/\s+/).filter(function (t) { return t.length > 0; });
    var scored = [];
    for (var i = 0; i < index.length; i++) {
      var s = score(index[i], terms);
      if (s > 0) scored.push({ article: index[i], score: s });
    }
    scored.sort(function (a, b) { return b.score - a.score; });
    var matched = scored.map(function (s) { return s.article; });
    activeIdx = -1;
    render(matched);
  }

  function getResultEls() {
    return results.querySelectorAll('.search-result');
  }

  function highlightResult(idx) {
    var els = getResultEls();
    for (var i = 0; i < els.length; i++) {
      els[i].classList.toggle('search-result-active', i === idx);
    }
    if (els[idx]) {
      els[idx].scrollIntoView({ block: 'nearest' });
    }
  }

  function onKeydown(e) {
    var els = getResultEls();
    if (e.key === 'Escape') {
      close();
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      activeIdx = Math.min(activeIdx + 1, els.length - 1);
      highlightResult(activeIdx);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      activeIdx = Math.max(activeIdx - 1, 0);
      highlightResult(activeIdx);
    } else if (e.key === 'Enter' && activeIdx >= 0 && els[activeIdx]) {
      e.preventDefault();
      els[activeIdx].click();
    }
  }

  openBtn.addEventListener('click', open);
  if (closeBtn) closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) close();
  });

  input.addEventListener('input', onInput);
  input.addEventListener('keydown', onKeydown);

  // Global keyboard shortcut: Cmd/Ctrl+K or /
  document.addEventListener('keydown', function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      open();
    }
    if (e.key === '/' && !overlay.classList.contains('open') &&
        document.activeElement.tagName !== 'INPUT' &&
        document.activeElement.tagName !== 'TEXTAREA') {
      e.preventDefault();
      open();
    }
  });
})();
