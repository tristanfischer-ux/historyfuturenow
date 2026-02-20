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
    document.body.classList.add('search-open');
    input.value = '';
    results.innerHTML = HINT_HTML;
    activeIdx = -1;
    setTimeout(function () { input.focus(); }, 60);
    if (!index) loadIndex();
  }

  function close() {
    overlay.classList.remove('open');
    overlay.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('search-open');
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

  var BM_KEY = 'hfn_bookmarks';

  function isBookmarked(slug) {
    try {
      var bm = JSON.parse(localStorage.getItem(BM_KEY) || '[]');
      for (var i = 0; i < bm.length; i++) { if (bm[i].slug === slug) return true; }
    } catch (e) {}
    return false;
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
      var sectionLabel = escHtml(a.label + ' \u00b7 ' + a.section);
      var controls = '';
      if (a.hasAudio) {
        controls += '<button class="card-play-btn" data-queue-slug="' + escHtml(a.slug) + '" data-queue-title="' + escHtml(a.title) + '" data-queue-section="' + sectionLabel + '" data-queue-color="' + a.color + '" data-queue-url="/audio/' + escHtml(a.slug) + '.mp3" aria-label="Play">' +
          '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></button>';
      }
      var bmClass = isBookmarked(a.slug) ? ' bookmarked' : '';
      controls += '<button class="card-bookmark-btn' + bmClass + '" data-bookmark-slug="' + escHtml(a.slug) + '" data-bookmark-title="' + escHtml(a.title) + '" data-bookmark-url="/articles/' + escHtml(a.slug) + '" data-bookmark-section="' + sectionLabel + '" data-bookmark-color="' + a.color + '" aria-label="Bookmark">' +
        '<svg class="bk-outline" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>' +
        '<svg class="bk-filled" viewBox="0 0 24 24" fill="currentColor"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>' +
        '</button>';
      html += '<div class="search-result" data-idx="' + i + '">' +
        '<a href="/articles/' + a.slug + '" class="search-result-link">' +
        '<span class="search-result-kicker" style="color:' + a.color + '">' + a.label + ' &middot; ' + escHtml(a.section) + badges + '</span>' +
        '<span class="search-result-title">' + escHtml(a.title) + '</span>' +
        '<span class="search-result-meta">' + a.readingTime + ' min read</span>' +
        '</a>' +
        '<div class="card-controls">' + controls + '</div>' +
        '</div>';
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
      var link = els[activeIdx].querySelector('.search-result-link');
      if (link) link.click();
    }
  }

  // Delegated handlers for play + bookmark buttons inside search results
  results.addEventListener('click', function (e) {
    var playBtn = e.target.closest('.card-play-btn');
    if (playBtn && window.HFNQueue && HFNQueue.openPopover) {
      e.preventDefault();
      e.stopPropagation();
      HFNQueue.openPopover(playBtn);
      return;
    }
    var bmBtn = e.target.closest('.card-bookmark-btn');
    if (bmBtn && window.HFNQueue) {
      e.preventDefault();
      e.stopPropagation();
      HFNQueue.bookmark(
        bmBtn.dataset.bookmarkSlug,
        bmBtn.dataset.bookmarkTitle,
        bmBtn.dataset.bookmarkUrl,
        bmBtn.dataset.bookmarkSection,
        bmBtn.dataset.bookmarkColor
      );
      bmBtn.classList.toggle('bookmarked');
      return;
    }
  });

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
