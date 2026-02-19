// Reading history: show "Read" / "Listened" on article links
function applyReadBadges() {
  try {
    const readRaw = localStorage.getItem('hfn_read_slugs');
    const listenedRaw = localStorage.getItem('hfn_listened_slugs');
    const readSlugs = readRaw ? JSON.parse(readRaw) : [];
    const listenedSlugs = listenedRaw ? JSON.parse(listenedRaw) : [];
    const readSet = new Set(readSlugs);
    const listenedSet = new Set(listenedSlugs);
    document.querySelectorAll('a[href^="/articles/"]').forEach((a) => {
      const m = (a.getAttribute('href') || '').match(/\/articles\/([^/?#]+)/);
      if (!m) return;
      if (listenedSet.has(m[1])) a.classList.add('article-link-listened');
      if (readSet.has(m[1])) a.classList.add('article-link-read');
    });
  } catch (e) {}
}

// Mobile nav toggle + scroll-based back bar
document.addEventListener('DOMContentLoaded', () => {
  applyReadBadges();
  const toggle = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => links.classList.toggle('open'));
    links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => links.classList.remove('open')));
  }

  // Back-to-section bar: show when scrolled past article header
  const backBar = document.getElementById('backBar');
  const articleHeader = document.querySelector('.article-header');
  if (backBar && articleHeader) {
    let ticking = false;
    const onScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          const rect = articleHeader.getBoundingClientRect();
          const pastHeader = rect.bottom < 0;
          backBar.classList.toggle('visible', pastHeader);
          ticking = false;
        });
        ticking = true;
      }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // Focus mode: hide nav when scrolling down on article pages; show "Menu" button to reveal
  const articleBody = document.querySelector('article .article-body');
  if (articleBody) {
    let lastY = window.scrollY;
    let menuBtn = null;
    const threshold = 400;
    let tickingFocus = false;
    const onScrollFocus = () => {
      if (!tickingFocus) {
        window.requestAnimationFrame(() => {
          const y = window.scrollY;
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
              menuBtn.onclick = () => {
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
  }
});
