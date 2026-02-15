// Mobile nav toggle + scroll-based back bar
document.addEventListener('DOMContentLoaded', () => {
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
