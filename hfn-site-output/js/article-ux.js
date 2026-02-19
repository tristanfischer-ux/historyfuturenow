/**
 * Article-only UX: table of contents, scroll-to-top, keyboard nav, etc.
 * Only loaded on article pages.
 */
(function () {
  function slugify(text) {
    return text.trim().toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '') || 'section';
  }

  function initToc() {
    const toc = document.getElementById('articleToc');
    const tocToggle = document.getElementById('articleTocToggle');
    const body = document.querySelector('.article-body');
    if (!toc || !body) return;

    const headings = body.querySelectorAll('h2, h3');
    if (headings.length === 0) {
      toc.remove();
      if (tocToggle) tocToggle.remove();
      return;
    }

    const seen = {};
    const items = [];
    headings.forEach((h) => {
      let id = h.id || slugify(h.textContent);
      if (seen[id]) {
        seen[id]++;
        id = id + '-' + seen[id];
      } else {
        seen[id] = 1;
      }
      h.id = id;
      items.push({ id, tag: h.tagName, text: h.textContent.trim() });
    });

    const nav = document.createElement('div');
    nav.className = 'article-toc-inner';
    const title = document.createElement('div');
    title.className = 'article-toc-title';
    title.textContent = 'Contents';
    nav.appendChild(title);
    const list = document.createElement('ul');
    list.className = 'article-toc-list';
    items.forEach(function (it) {
      const li = document.createElement('li');
      li.className = 'article-toc-item article-toc-' + it.tag.toLowerCase();
      const a = document.createElement('a');
      a.href = '#' + it.id;
      a.textContent = it.text;
      a.addEventListener('click', function (e) {
        e.preventDefault();
        document.getElementById(it.id).scrollIntoView({ behavior: 'smooth' });
        if (window.innerWidth < 900) {
          toc.classList.remove('open');
          if (tocToggle) tocToggle.setAttribute('aria-expanded', 'false');
        }
      });
      li.appendChild(a);
      list.appendChild(li);
    });
    nav.appendChild(list);
    toc.appendChild(nav);

    // Scroll spy
    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          const id = entry.target.id;
          toc.querySelectorAll('.article-toc-item a').forEach(function (a) {
            a.classList.toggle('active', a.getAttribute('href') === '#' + id);
          });
        });
      },
      { rootMargin: '-80px 0px -70% 0px', threshold: 0 }
    );
    headings.forEach(function (h) {
      observer.observe(h);
    });

    // Mobile toggle
    if (tocToggle) {
      tocToggle.style.display = '';
      tocToggle.addEventListener('click', function () {
        const open = toc.classList.toggle('open');
        tocToggle.setAttribute('aria-expanded', open);
      });
    }
  }

  function initFootnotePopovers() {
    const refs = document.querySelector('.article-references');
    if (!refs) return;
    const body = document.querySelector('.article-body');
    if (!body) return;
    const links = body.querySelectorAll('a[href^="#"]');
    let popover = null;
    let hideTimer = null;
    function showPopover(targetId, refLink) {
      const target = document.getElementById(targetId);
      if (!target || !refs.contains(target)) return;
      hidePopover();
      popover = document.createElement('div');
      popover.className = 'footnote-popover';
      popover.setAttribute('role', 'tooltip');
      popover.innerHTML = target.innerHTML;
      if (refLink) {
        const back = document.createElement('p');
        back.className = 'footnote-popover-back';
        const a = document.createElement('a');
        a.href = '#';
        a.textContent = '← Back to text';
        a.onclick = function (e) {
          e.preventDefault();
          hidePopover();
          refLink.scrollIntoView({ behavior: 'smooth', block: 'center' });
        };
        back.appendChild(a);
        popover.appendChild(back);
      }
      document.body.appendChild(popover);
      const link = refLink || document.querySelector('.article-body a[href="#' + targetId + '"]');
      if (link) {
        const rect = link.getBoundingClientRect();
        requestAnimationFrame(function () {
          popover.style.left = Math.max(8, Math.min(rect.left, window.innerWidth - popover.offsetWidth - 8)) + 'px';
          popover.style.top = (rect.top - popover.offsetHeight - 6) + 'px';
        });
      }
    }
    function hidePopover() {
      if (hideTimer) clearTimeout(hideTimer);
      hideTimer = null;
      if (popover) {
        popover.remove();
        popover = null;
      }
    }
    links.forEach(function (a) {
      const id = (a.getAttribute('href') || '').slice(1);
      if (!id) return;
      const target = document.getElementById(id);
      if (!target || !refs.contains(target)) return;
      a.addEventListener('mouseenter', function () {
        if (hideTimer) clearTimeout(hideTimer);
        showPopover(id, a);
      });
      a.addEventListener('mouseleave', function () {
        hideTimer = setTimeout(hidePopover, 150);
      });
      a.addEventListener('focus', function () {
        if (hideTimer) clearTimeout(hideTimer);
        showPopover(id, a);
      });
      a.addEventListener('blur', function () {
        hideTimer = setTimeout(hidePopover, 150);
      });
      a.addEventListener('click', function (e) {
        e.preventDefault();
        if (popover) hidePopover();
        else showPopover(id, a);
      });
    });
  }

  function initWhereYouLeftOff() {
    const path = window.location.pathname;
    const match = path.match(/\/articles\/([^/]+)/);
    if (!match) return;
    const slug = match[1];
    const key = 'hfn_scroll_' + slug;
    const STORAGE_MIN = 400;

    function saveScroll() {
      if (window.scrollY < STORAGE_MIN) return;
      try {
        localStorage.setItem(key, String(window.scrollY));
      } catch (e) {}
    }

    let saveTicking = false;
    document.addEventListener('scroll', function () {
      if (saveTicking) return;
      saveTicking = true;
      requestAnimationFrame(function () {
        saveScroll();
        saveTicking = false;
      });
    }, { passive: true });

    var stored = null;
    try {
      stored = localStorage.getItem(key);
    } catch (e) {}
    if (!stored) return;
    var pos = parseInt(stored, 10);
    if (isNaN(pos) || pos < STORAGE_MIN) return;
    if (window.location.hash) return;

    var toast = document.createElement('div');
    toast.className = 'where-left-off-toast';
    toast.innerHTML = '<span class="where-left-off-msg">Pick up where you left off?</span> <button type="button" class="where-left-off-btn">Go</button>';
    document.body.appendChild(toast);
    requestAnimationFrame(function () {
      toast.classList.add('visible');
    });
    toast.querySelector('button').addEventListener('click', function () {
      window.scrollTo({ top: pos, behavior: 'smooth' });
      try {
        localStorage.removeItem(key);
      } catch (e) {}
      toast.classList.remove('visible');
      setTimeout(function () {
        toast.remove();
      }, 300);
    });
    toast.addEventListener('click', function (e) {
      if (e.target.tagName !== 'BUTTON') return;
    });
    setTimeout(function () {
      if (toast.parentNode) {
        toast.classList.remove('visible');
        setTimeout(function () {
          if (toast.parentNode) toast.remove();
        }, 300);
      }
    }, 6000);
  }

  function initHeroParallax() {
    const wrap = document.querySelector('.article-hero-wrap');
    if (!wrap) return;
    const img = wrap.querySelector('.article-hero-img');
    if (!img) return;
    var ticking = false;
    function update() {
      if (window.innerWidth < 768) {
        img.style.transform = '';
        return;
      }
      var scrolled = window.scrollY;
      var rate = 0.15;
      img.style.transform = 'translate3d(0,' + (scrolled * rate * 0.5) + 'px,0)';
    }
    window.addEventListener('scroll', function () {
      if (!ticking) {
        requestAnimationFrame(function () {
          update();
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });
    update();
  }

  function initScrollToTop() {
    var btn = document.getElementById('scrollToTopBtn');
    if (!btn) return;
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    var ticking = false;
    window.addEventListener('scroll', function () {
      if (!ticking) {
        requestAnimationFrame(function () {
          var show = window.scrollY > window.innerHeight * 0.8;
          btn.style.display = show ? 'flex' : 'none';
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });
  }

  function initKeyboardNav() {
    var article = document.querySelector('.page-container[data-prev-href][data-next-href]');
    if (!article) return;
    var prev = article.getAttribute('data-prev-href');
    var next = article.getAttribute('data-next-href');
    var tooltipShown = false;
    function showHint() {
      if (tooltipShown) return;
      try {
        if (localStorage.getItem('hfn_arrow_hint_seen')) return;
      } catch (e) {}
      tooltipShown = true;
      var tip = document.createElement('div');
      tip.className = 'keyboard-nav-hint';
      tip.textContent = 'Use ← → to move between articles';
      document.body.appendChild(tip);
      requestAnimationFrame(function () {
        tip.classList.add('visible');
      });
      setTimeout(function () {
        tip.classList.remove('visible');
        setTimeout(function () {
          tip.remove();
        }, 300);
      }, 3500);
      try {
        localStorage.setItem('hfn_arrow_hint_seen', '1');
      } catch (e) {}
    }
    document.addEventListener('keydown', function (e) {
      if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable)) return;
      if (e.key === 'ArrowLeft' && prev) {
        showHint();
        location.href = prev;
      } else if (e.key === 'ArrowRight' && next) {
        showHint();
        location.href = next;
      }
    });
  }

  function initPullQuoteCopy() {
    var url = document.querySelector('link[rel="canonical"]') ? document.querySelector('link[rel="canonical"]').href : window.location.href;
    document.querySelectorAll('.article-body .pull-quote').forEach(function (aside) {
      if (aside.querySelector('.pull-quote-copy-btn')) return;
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'pull-quote-copy-btn';
      btn.setAttribute('aria-label', 'Copy quote and link');
      btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
      aside.appendChild(btn);
      btn.addEventListener('click', function () {
        var text = aside.querySelector('p') ? aside.querySelector('p').textContent.trim() : aside.textContent.trim();
        var full = text + ' ' + url;
        navigator.clipboard.writeText(full).then(function () {
          if (window.showToast) window.showToast('Quote copied');
          var orig = btn.innerHTML;
          btn.innerHTML = '<span class="pull-quote-copied">Copied</span>';
          btn.classList.add('copied');
          setTimeout(function () { btn.innerHTML = orig; btn.classList.remove('copied'); }, 1500);
        });
      });
    });
  }

  function initEntranceAnimations() {
    const body = document.querySelector('.article-body');
    if (!body) return;
    const blocks = body.querySelectorAll('p, .chart-figure, .pull-quote, .article-body h2, .article-body h3');
    if (blocks.length === 0) return;
    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('article-enter-visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: '0px 0px -40px 0px', threshold: 0 }
    );
    blocks.forEach(function (el) {
      el.classList.add('article-enter');
      observer.observe(el);
    });
  }

  function initSelectionShare() {
    const body = document.querySelector('.article-body');
    if (!body) return;
    const url = document.querySelector('link[rel="canonical"]') ? document.querySelector('link[rel="canonical"]').href : window.location.href;

    let tooltip = null;
    function hideTooltip() {
      if (tooltip) {
        tooltip.remove();
        tooltip = null;
      }
    }

    function showTooltip(quote) {
      hideTooltip();
      tooltip = document.createElement('div');
      tooltip.className = 'selection-share-tooltip';
      tooltip.innerHTML = '<span class="selection-share-label">Share this quote</span>' +
        '<button type="button" class="selection-share-btn selection-share-x" aria-label="Share on X">X</button>' +
        '<button type="button" class="selection-share-btn selection-share-copy" aria-label="Copy quote and link">Copy</button>';
      const text = quote + ' ' + url;
      tooltip.querySelector('.selection-share-copy').addEventListener('click', function () {
        navigator.clipboard.writeText(text).then(function () {
          if (window.showToast) window.showToast('Link copied');
          else tooltip.querySelector('.selection-share-copy').textContent = 'Copied';
          hideTooltip();
          window.getSelection().removeAllRanges();
        });
      });
      tooltip.querySelector('.selection-share-x').addEventListener('click', function () {
        window.open('https://twitter.com/intent/tweet?text=' + encodeURIComponent(text), '_blank', 'noopener,noreferrer');
        hideTooltip();
        window.getSelection().removeAllRanges();
      });
      document.body.appendChild(tooltip);
      const sel = window.getSelection();
      const range = sel.rangeCount ? sel.getRangeAt(0) : null;
      if (range) {
        const rect = range.getBoundingClientRect();
        requestAnimationFrame(function () {
          const w = tooltip.offsetWidth;
          const h = tooltip.offsetHeight;
          let left = rect.left + rect.width / 2 - w / 2;
          left = Math.max(8, Math.min(left, window.innerWidth - w - 8));
          const top = rect.top - h - 8;
          tooltip.style.left = left + 'px';
          tooltip.style.top = (top < 8 ? rect.bottom + 8 : top) + 'px';
        });
      }
    }

    document.addEventListener('mouseup', function () {
      const sel = window.getSelection();
      const text = (sel && sel.toString()) ? sel.toString().trim() : '';
      if (!text || text.length < 10) {
        hideTooltip();
        return;
      }
      if (!body.contains(sel.anchorNode)) {
        hideTooltip();
        return;
      }
      showTooltip(text);
    });
    document.addEventListener('mousedown', function (e) {
      if (tooltip && !tooltip.contains(e.target)) hideTooltip();
    });
  }

  function markArticleRead() {
    var match = window.location.pathname.match(/\/articles\/([^/]+)/);
    if (!match) return;
    var slug = match[1];
    try {
      var raw = localStorage.getItem('hfn_read_slugs');
      var slugs = raw ? JSON.parse(raw) : [];
      if (slugs.indexOf(slug) === -1) {
        slugs.push(slug);
        if (slugs.length > 500) slugs = slugs.slice(-400);
        localStorage.setItem('hfn_read_slugs', JSON.stringify(slugs));
      }
    } catch (e) {}
  }

  function runAll() {
    markArticleRead();
    initToc();
    initFootnotePopovers();
    initWhereYouLeftOff();
    initScrollToTop();
    initKeyboardNav();
    initPullQuoteCopy();
    initHeroParallax();
    initEntranceAnimations();
    initSelectionShare();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runAll);
  } else {
    runAll();
  }
})();
