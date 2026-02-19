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
});
