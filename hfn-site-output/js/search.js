/**
 * History Future Now — Full-text article search (Pagefind)
 * Uses Pagefind for full-text matching; enriches results with search-index.json
 * metadata for badges, audio controls, and section colours.
 */
(function () {
  'use strict';

  var overlay = document.getElementById('searchOverlay');
  var input = document.getElementById('searchInput');
  var results = document.getElementById('searchResults');
  var openBtn = document.getElementById('searchOpen');
  var closeBtn = document.getElementById('searchClose');

  if (!overlay || !input || !results || !openBtn) return;

  var pagefind = null;
  var meta = null;       // slug -> { title, section, label, color, readingTime, chartCount, hasAudio, slug }
  var activeIdx = -1;
  var debounceTimer = null;
  var HINT_HTML = '<div class="search-hint">Type to search across all articles</div>';

  function loadPagefind() {
    if (pagefind) return Promise.resolve();
    return import('/pagefind/pagefind.js').then(function (pf) {
      pagefind = pf;
      return pagefind.init();
    }).catch(function () {
      pagefind = null;
    });
  }

  function loadMeta() {
    if (meta) return Promise.resolve();
    return fetch('/search-index.json')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        meta = {};
        for (var i = 0; i < data.length; i++) {
          meta[data[i].slug] = data[i];
        }
      })
      .catch(function () { meta = {}; });
  }

  function open() {
    overlay.classList.add('open');
    overlay.setAttribute('aria-hidden', 'false');
    document.body.classList.add('search-open');
    input.value = '';
    results.innerHTML = HINT_HTML;
    activeIdx = -1;
    setTimeout(function () { input.focus(); }, 60);
    loadPagefind();
    loadMeta();
  }

  function close() {
    overlay.classList.remove('open');
    overlay.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('search-open');
    activeIdx = -1;
  }

  var BM_KEY = 'hfn_bookmarks';

  function isBookmarked(slug) {
    try {
      var bm = JSON.parse(localStorage.getItem(BM_KEY) || '[]');
      for (var i = 0; i < bm.length; i++) { if (bm[i].slug === slug) return true; }
    } catch (e) {}
    return false;
  }

  function escHtml(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function slugFromUrl(url) {
    var m = url.match(/\/articles\/([^\/]+?)(?:\.html)?$/);
    return m ? m[1] : null;
  }

  function renderResults(items) {
    if (items.length === 0) {
      results.innerHTML = '<div class="search-empty">No articles found</div>';
      return;
    }
    var html = '';
    for (var i = 0; i < items.length; i++) {
      var item = items[i];
      var a = item.meta;
      var excerpt = item.excerpt || '';
      var badges = '';
      if (a && a.chartCount > 0) {
        badges += '<span class="search-badge search-badge-chart">' + a.chartCount + ' charts</span>';
      }
      if (a && a.hasAudio) {
        badges += '<span class="search-badge search-badge-audio">Audio</span>';
      }
      var color = (a && a.color) || '#666';
      var label = (a && a.label) || '';
      var section = (a && a.section) || (item.filterSection || '');
      var sectionLabel = escHtml(label + (label && section ? ' \u00b7 ' : '') + section);
      var slug = item.slug || '';
      var title = item.title || '';
      var readingTime = (a && a.readingTime) || '';

      var controls = '';
      if (a && a.hasAudio) {
        controls += '<button class="card-play-btn" data-queue-slug="' + escHtml(slug) + '" data-queue-title="' + escHtml(title) + '" data-queue-section="' + sectionLabel + '" data-queue-color="' + color + '" data-queue-url="/audio/' + escHtml(slug) + '.mp3" aria-label="Play">' +
          '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></button>';
      }
      var bmClass = isBookmarked(slug) ? ' bookmarked' : '';
      controls += '<button class="card-bookmark-btn' + bmClass + '" data-bookmark-slug="' + escHtml(slug) + '" data-bookmark-title="' + escHtml(title) + '" data-bookmark-url="/articles/' + escHtml(slug) + '" data-bookmark-section="' + sectionLabel + '" data-bookmark-color="' + color + '" aria-label="Bookmark">' +
        '<svg class="bk-outline" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>' +
        '<svg class="bk-filled" viewBox="0 0 24 24" fill="currentColor"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>' +
        '</button>';

      html += '<div class="search-result" data-idx="' + i + '">' +
        '<a href="/articles/' + escHtml(slug) + '" class="search-result-link">' +
        '<span class="search-result-kicker" style="color:' + color + '">' + escHtml(label) + (label && section ? ' &middot; ' : '') + escHtml(section) + badges + '</span>' +
        '<span class="search-result-title">' + escHtml(title) + '</span>' +
        (excerpt ? '<span class="search-result-excerpt">' + excerpt + '</span>' : '') +
        (readingTime ? '<span class="search-result-meta">' + readingTime + ' min read</span>' : '') +
        '</a>' +
        '<div class="card-controls">' + controls + '</div>' +
        '</div>';
    }
    results.innerHTML = html;
  }

  function onInput() {
    clearTimeout(debounceTimer);
    var q = input.value.trim();
    if (q.length === 0) {
      results.innerHTML = HINT_HTML;
      activeIdx = -1;
      return;
    }
    debounceTimer = setTimeout(function () { doSearch(q); }, 120);
  }

  function doSearch(q) {
    if (!pagefind) {
      loadPagefind().then(function () { if (pagefind) doSearch(q); });
      return;
    }

    pagefind.search(q).then(function (search) {
      var toLoad = search.results.slice(0, 20);
      return Promise.all(toLoad.map(function (r) { return r.data(); }));
    }).then(function (loaded) {
      var items = [];
      for (var i = 0; i < loaded.length; i++) {
        var d = loaded[i];
        var slug = slugFromUrl(d.url);
        var m = (meta && slug) ? meta[slug] : null;
        items.push({
          slug: slug || '',
          title: (d.meta && d.meta.title) || '',
          excerpt: d.excerpt || '',
          filterSection: (d.filters && d.filters.section && d.filters.section[0]) || '',
          meta: m
        });
      }
      activeIdx = -1;
      renderResults(items);
    }).catch(function () {
      results.innerHTML = '<div class="search-empty">Search unavailable</div>';
    });
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
    if (e.target.closest('.search-result-link')) close();
  });

  input.addEventListener('input', onInput);
  input.addEventListener('keydown', onKeydown);

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
