// Reading history: show "Read" / "Listened" on article links
function applyReadBadges() {
  try {
    var readRaw = localStorage.getItem('hfn_read_slugs');
    var listenedRaw = localStorage.getItem('hfn_listened_slugs');
    var readSlugs = readRaw ? JSON.parse(readRaw) : [];
    var listenedSlugs = listenedRaw ? JSON.parse(listenedRaw) : [];
    var readSet = new Set(readSlugs);
    var listenedSet = new Set(listenedSlugs);
    document.querySelectorAll('a[href^="/articles/"]').forEach(function (a) {
      var m = (a.getAttribute('href') || '').match(/\/articles\/([^/?#]+)/);
      if (!m) return;
      if (listenedSet.has(m[1])) a.classList.add('article-link-listened');
      if (readSet.has(m[1])) a.classList.add('article-link-read');
    });
  } catch (e) {}
}

// Scroll handler cleanup between soft navigations
var _hfnScrollCleanup = window._hfnScrollCleanup || [];

function initNav() {
  applyReadBadges();

  // Clean up scroll handlers from previous page
  _hfnScrollCleanup.forEach(function (fn) { fn(); });
  _hfnScrollCleanup.length = 0;
  window._hfnScrollCleanup = _hfnScrollCleanup;

  document.body.classList.remove('nav-focus-hidden');
  var oldMenuBtn = document.querySelector('.focus-menu-btn');
  if (oldMenuBtn) oldMenuBtn.remove();

  // Close mobile nav on page change
  var links = document.querySelector('.nav-links');
  if (links) links.classList.remove('open');

  // Back-to-section bar: show when scrolled past article header
  var backBar = document.getElementById('backBar');
  var articleHeader = document.querySelector('.article-header');
  if (backBar && articleHeader) {
    var ticking = false;
    var onScroll = function () {
      if (!ticking) {
        window.requestAnimationFrame(function () {
          var rect = articleHeader.getBoundingClientRect();
          backBar.classList.toggle('visible', rect.bottom < 0);
          ticking = false;
        });
        ticking = true;
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    _hfnScrollCleanup.push(function () { window.removeEventListener('scroll', onScroll); });
  }

  // Focus mode: hide nav when scrolling down on article pages
  var articleBody = document.querySelector('article .article-body');
  if (articleBody) {
    var lastY = window.scrollY;
    var menuBtn = null;
    var threshold = 400;
    var tickingFocus = false;
    var onScrollFocus = function () {
      if (!tickingFocus) {
        window.requestAnimationFrame(function () {
          var y = window.scrollY;
          if (y > threshold) {
            if (y > lastY) document.body.classList.add('nav-focus-hidden');
            else document.body.classList.remove('nav-focus-hidden');
          } else {
            document.body.classList.remove('nav-focus-hidden');
          }
          lastY = y;
          if (document.body.classList.contains('nav-focus-hidden')) {
            if (!menuBtn) {
              menuBtn = document.createElement('button');
              menuBtn.type = 'button';
              menuBtn.className = 'focus-menu-btn';
              menuBtn.setAttribute('aria-label', 'Show menu');
              menuBtn.textContent = 'Menu';
              menuBtn.onclick = function () {
                document.body.classList.remove('nav-focus-hidden');
              };
              document.body.appendChild(menuBtn);
            }
            menuBtn.style.display = '';
          } else if (menuBtn) menuBtn.style.display = 'none';
          tickingFocus = false;
        });
        tickingFocus = true;
      }
    };
    window.addEventListener('scroll', onScrollFocus, { passive: true });
    _hfnScrollCleanup.push(function () {
      window.removeEventListener('scroll', onScrollFocus);
      if (menuBtn && menuBtn.parentNode) menuBtn.parentNode.removeChild(menuBtn);
    });
  }
}

// Event delegation for nav clicks — bound once on document, survives DOM replacement
if (!window._hfnNavBound) {
  window._hfnNavBound = true;
  document.addEventListener('click', function (e) {
    var toggle = e.target.closest('.nav-toggle');
    if (toggle) {
      var links = document.querySelector('.nav-links');
      if (links) links.classList.toggle('open');
      return;
    }
    var navLink = e.target.closest('.nav-links a');
    if (navLink) {
      var links = document.querySelector('.nav-links');
      if (links) links.classList.remove('open');
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initNav);
} else {
  initNav();
}
