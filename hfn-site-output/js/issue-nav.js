/**
 * Issue page: keyboard nav (← →), scroll-triggered floating bar, one-time hint.
 */
(function () {
  const body = document.body;
  const prevUrl = body.getAttribute('data-prev-url');
  const nextUrl = body.getAttribute('data-next-url');
  const floating = document.getElementById('issueNavFloating');
  const hero = document.getElementById('issueHero');
  const cards = document.getElementById('issueNavCards');

  // ── Keyboard navigation ──
  function isInputTarget(el) {
    if (!el) return false;
    const tag = el.tagName && el.tagName.toUpperCase();
    return tag === 'INPUT' || tag === 'TEXTAREA' || el.isContentEditable;
  }

  document.addEventListener('keydown', function (e) {
    if (isInputTarget(e.target)) return;
    if (e.key === 'ArrowLeft' && prevUrl) {
      e.preventDefault();
      window.location.href = prevUrl;
    } else if (e.key === 'ArrowRight' && nextUrl) {
      e.preventDefault();
      window.location.href = nextUrl;
    }
  });

  // ── One-time keyboard hint ──
  const HINT_KEY = 'hfn-issue-nav-hint-seen';
  if ((prevUrl || nextUrl) && !localStorage.getItem(HINT_KEY)) {
    const hint = document.createElement('div');
    hint.className = 'issue-nav-hint';
    hint.setAttribute('aria-live', 'polite');
    hint.textContent = 'Use arrow keys to browse issues';
    body.appendChild(hint);
    requestAnimationFrame(function () {
      hint.classList.add('issue-nav-hint-visible');
    });
    setTimeout(function () {
      hint.classList.remove('issue-nav-hint-visible');
      setTimeout(function () {
        if (hint.parentNode) hint.parentNode.removeChild(hint);
      }, 350);
      localStorage.setItem(HINT_KEY, '1');
    }, 4000);
  }

  // ── Floating bar: show when past hero, hide when cards in view ──
  if (!floating || (!hero && !cards)) return;

  let heroVisible = true;
  let cardsVisible = false;

  function updateFloating() {
    const show = !heroVisible && !cardsVisible;
    floating.classList.toggle('issue-nav-floating-visible', show);
  }

  if (hero) {
    const heroObs = new IntersectionObserver(
      function (entries) {
        heroVisible = entries[0].isIntersecting;
        updateFloating();
      },
      { threshold: 0, rootMargin: '0px' }
    );
    heroObs.observe(hero);
  } else {
    heroVisible = false;
  }

  if (cards) {
    const cardsObs = new IntersectionObserver(
      function (entries) {
        cardsVisible = entries[0].isIntersecting;
        updateFloating();
      },
      { threshold: 0, rootMargin: '-10% 0px 0px 0px' }
    );
    cardsObs.observe(cards);
  }

  updateFloating();
})();
