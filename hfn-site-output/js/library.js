(function(){
  /* ── View toggle ── */
  var viewBtns = document.querySelectorAll('.lib-view-btn');
  var views = document.querySelectorAll('.lib-view');

  viewBtns.forEach(function(btn){
    btn.addEventListener('click', function(){
      var target = btn.dataset.view;
      viewBtns.forEach(function(b){ b.classList.remove('active'); });
      btn.classList.add('active');
      views.forEach(function(v){
        v.style.display = v.id === 'lib-' + target ? '' : 'none';
      });
      history.replaceState(null, '', '/library' + (target === 'themes' ? '' : '#timeline'));
    });
  });

  /* ── Expand/collapse theme book lists ── */
  document.querySelectorAll('.lib-theme-toggle').forEach(function(btn){
    btn.addEventListener('click', function(){
      var card = btn.closest('.lib-theme-card');
      var list = card.querySelector('.lib-book-list');
      var isOpen = list.style.display !== 'none';
      list.style.display = isOpen ? 'none' : '';
      btn.textContent = isOpen ? 'Show books ▸' : 'Hide books ▾';
      btn.setAttribute('aria-expanded', !isOpen);
    });
  });

  /* ── Timeline year expand/collapse ── */
  document.querySelectorAll('.lib-year-toggle').forEach(function(btn){
    btn.addEventListener('click', function(){
      var section = btn.closest('.lib-year-section');
      var list = section.querySelector('.lib-year-books');
      var isOpen = list.style.display !== 'none';
      list.style.display = isOpen ? 'none' : '';
      var arrow = btn.querySelector('.lib-year-arrow');
      if(arrow) arrow.textContent = isOpen ? '▸' : '▾';
      btn.setAttribute('aria-expanded', !isOpen);
    });
  });

  /* ── Restore view from hash ── */
  if(location.hash === '#timeline'){
    var tlBtn = document.querySelector('.lib-view-btn[data-view="timeline"]');
    if(tlBtn) tlBtn.click();
  }
})();
