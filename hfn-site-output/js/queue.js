/**
 * History Future Now — Audio Queue & Playlist Player
 *
 * Persistent bottom bar with queue management, drag-to-reorder,
 * continuous playback across articles, and localStorage persistence.
 */
(function () {
  'use strict';

  // ─── State ──────────────────────────────────────────────────────────────────
  var STORAGE_KEY = 'hfn_audio_queue';
  var queue = [];        // [{slug, title, section, color, duration, url}]
  var currentIndex = -1;
  var isPlaying = false;
  var speeds = [1, 1.25, 1.5, 1.75, 2];
  var speedIndex = 1;
  var queueOpen = false;
  var audio = null;
  var dragSrcIndex = null;

  // ─── Persistence ────────────────────────────────────────────────────────────
  function save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        queue: queue,
        currentIndex: currentIndex,
        speedIndex: speedIndex,
        currentTime: audio ? audio.currentTime : 0,
        isPlaying: isPlaying,
      }));
    } catch (e) { /* quota exceeded — fail silently */ }
  }

  function load() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return { currentTime: 0, wasPlaying: false };
      var data = JSON.parse(raw);
      if (data.queue && data.queue.length) {
        queue = data.queue;
        currentIndex = typeof data.currentIndex === 'number' ? data.currentIndex : -1;
        speedIndex = typeof data.speedIndex === 'number' ? data.speedIndex : 1;
        if (currentIndex >= queue.length) currentIndex = queue.length - 1;
      }
      return { currentTime: data.currentTime || 0, wasPlaying: !!data.isPlaying };
    } catch (e) { return { currentTime: 0, wasPlaying: false }; }
  }

  // ─── Formatting ─────────────────────────────────────────────────────────────
  function fmt(s) {
    if (!s || !isFinite(s)) return '0:00';
    var m = Math.floor(s / 60);
    var sec = Math.floor(s % 60);
    return m + ':' + (sec < 10 ? '0' : '') + sec;
  }

  // ─── DOM References ─────────────────────────────────────────────────────────
  var bar, playBtn, iconPlay, iconPause, titleEl, sectionEl;
  var progressWrap, progressBar, progressThumb, timeEl, speedBtn;
  var prevBtn, nextBtn, queueBtn, queuePanel, queueList, queueCount;
  var closeQueueBtn, clearQueueBtn, barCloseBtn;
  var qDragging = false;

  function initDOM() {
    bar = document.getElementById('queueBar');
    playBtn = document.getElementById('queuePlayBtn');
    iconPlay = playBtn.querySelector('.q-icon-play');
    iconPause = playBtn.querySelector('.q-icon-pause');
    titleEl = document.getElementById('queueTitle');
    sectionEl = document.getElementById('queueSection');
    progressWrap = document.getElementById('queueProgressWrap');
    progressBar = document.getElementById('queueProgressBar');
    progressThumb = document.getElementById('queueThumb');
    timeEl = document.getElementById('queueTime');
    speedBtn = document.getElementById('queueSpeed');
    prevBtn = document.getElementById('queuePrev');
    nextBtn = document.getElementById('queueNext');
    queueBtn = document.getElementById('queueToggle');
    queuePanel = document.getElementById('queuePanel');
    queueList = document.getElementById('queueList');
    queueCount = document.getElementById('queueCount');
    closeQueueBtn = document.getElementById('queuePanelClose');
    clearQueueBtn = document.getElementById('queueClear');
    barCloseBtn = document.getElementById('queueBarClose');

    if (!audio) {
      audio = document.createElement('audio');
      audio.preload = 'none';
    }
    if (!audio.parentNode) document.body.appendChild(audio);

    playBtn.onclick = togglePlay;
    prevBtn.onclick = playPrev;
    nextBtn.onclick = playNext;
    queueBtn.onclick = toggleQueue;
    closeQueueBtn.onclick = toggleQueue;
    clearQueueBtn.onclick = clearQueue;
    barCloseBtn.onclick = closeBar;
    speedBtn.onclick = cycleSpeed;

    function qSeekTo(e) {
      if (!audio.duration) return;
      var rect = progressWrap.getBoundingClientRect();
      var pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
      audio.currentTime = pct * audio.duration;
      qUpdateBar(pct);
    }

    function qSeekToTouch(e) {
      if (!audio.duration) return;
      var rect = progressWrap.getBoundingClientRect();
      var touch = e.touches[0];
      var pct = Math.max(0, Math.min(1, (touch.clientX - rect.left) / rect.width));
      audio.currentTime = pct * audio.duration;
      qUpdateBar(pct);
    }

    function qUpdateBar(pct) {
      var p = (pct * 100) + '%';
      progressBar.style.width = p;
      if (progressThumb) progressThumb.style.left = p;
    }

    progressWrap.addEventListener('mousedown', function (e) {
      e.preventDefault();
      qDragging = true;
      progressWrap.classList.add('scrubbing');
      qSeekTo(e);
      function onMove(ev) { qSeekTo(ev); }
      function onUp() {
        qDragging = false;
        progressWrap.classList.remove('scrubbing');
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      }
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });

    progressWrap.addEventListener('touchstart', function (e) {
      e.preventDefault();
      qDragging = true;
      progressWrap.classList.add('scrubbing');
      qSeekToTouch(e);
      function onTouchMove(ev) { ev.preventDefault(); qSeekToTouch(ev); }
      function onTouchEnd() {
        qDragging = false;
        progressWrap.classList.remove('scrubbing');
        document.removeEventListener('touchmove', onTouchMove);
        document.removeEventListener('touchend', onTouchEnd);
      }
      document.addEventListener('touchmove', onTouchMove, { passive: false });
      document.addEventListener('touchend', onTouchEnd);
    });

    audio.ontimeupdate = function () {
      if (qDragging) return;
      if (!audio.duration) return;
      qUpdateBar(audio.currentTime / audio.duration);
      if (window.innerWidth <= 640) {
        timeEl.textContent = '-' + fmt(audio.duration - audio.currentTime);
      } else {
        timeEl.textContent = fmt(audio.currentTime) + ' / ' + fmt(audio.duration);
      }
      save();
    };

    audio.onended = function () {
      if (currentIndex >= 0 && currentIndex < queue.length) {
        try {
          var slug = queue[currentIndex].slug;
          var raw = localStorage.getItem('hfn_listened_slugs');
          var slugs = raw ? JSON.parse(raw) : [];
          if (slugs.indexOf(slug) === -1) {
            slugs.push(slug);
            if (slugs.length > 500) slugs = slugs.slice(-400);
            localStorage.setItem('hfn_listened_slugs', JSON.stringify(slugs));
          }
        } catch (e) {}
      }
      playNext();
    };

    audio.onerror = function () {
      // Skip to next on error
      if (queue.length > 1) playNext();
    };

    window.addEventListener('beforeunload', function () {
      if (queue.length > 0 && audio) save();
    });
  }

  // ─── Playback Controls ──────────────────────────────────────────────────────
  function loadTrack(index, autoplay, seekTo) {
    if (index < 0 || index >= queue.length) return;
    currentIndex = index;
    var track = queue[currentIndex];
    audio.src = track.url;
    audio.playbackRate = speeds[speedIndex];
    titleEl.textContent = track.title;
    sectionEl.textContent = track.section;
    sectionEl.style.color = track.color;
    progressBar.style.width = '0%';
    timeEl.textContent = '0:00';
    updateQueueHighlight();
    updateNavButtons();
    if (!seekTo || seekTo <= 0) {
      save();
    }

    if (seekTo && seekTo > 0) {
      audio.addEventListener('loadedmetadata', function onMeta() {
        audio.removeEventListener('loadedmetadata', onMeta);
        audio.currentTime = seekTo;
        if (autoplay) {
          audio.play().then(function () {
            setPlayingState(true);
          }).catch(function () {
            setPlayingState(false);
          });
        }
      });
      audio.load();
    } else if (autoplay) {
      audio.play().then(function () {
        setPlayingState(true);
      }).catch(function () {
        setPlayingState(false);
      });
    }
  }

  function togglePlay() {
    if (currentIndex < 0 && queue.length > 0) {
      loadTrack(0, true);
      return;
    }
    if (audio.paused) {
      audio.play().then(function () { setPlayingState(true); }).catch(function () {});
    } else {
      audio.pause();
      setPlayingState(false);
    }
  }

  function playNext() {
    if (currentIndex < queue.length - 1) {
      loadTrack(currentIndex + 1, true);
    } else {
      // End of queue
      setPlayingState(false);
      progressBar.style.width = '0%';
    }
  }

  function playPrev() {
    // If more than 3 seconds in, restart current track
    if (audio.currentTime > 3 && currentIndex >= 0) {
      audio.currentTime = 0;
      return;
    }
    if (currentIndex > 0) {
      loadTrack(currentIndex - 1, true);
    }
  }

  function cycleSpeed() {
    speedIndex = (speedIndex + 1) % speeds.length;
    audio.playbackRate = speeds[speedIndex];
    speedBtn.textContent = speeds[speedIndex] + '\u00d7';
    save();
  }

  function setPlayingState(playing) {
    isPlaying = playing;
    iconPlay.style.display = playing ? 'none' : 'block';
    iconPause.style.display = playing ? 'block' : 'none';
  }

  function updateNavButtons() {
    prevBtn.disabled = currentIndex <= 0;
    nextBtn.disabled = currentIndex >= queue.length - 1;
    prevBtn.style.opacity = currentIndex <= 0 ? '0.35' : '1';
    nextBtn.style.opacity = currentIndex >= queue.length - 1 ? '0.35' : '1';
  }

  // ─── Queue Management ───────────────────────────────────────────────────────
  function showBar() {
    bar.classList.add('visible');
    document.body.classList.add('has-queue-bar');
  }

  function closeBar() {
    audio.pause();
    setPlayingState(false);
    bar.classList.remove('visible');
    document.body.classList.remove('has-queue-bar');
    queue = [];
    currentIndex = -1;
    save();
    renderQueueList();
    updateBadges();
  }

  function toggleQueue() {
    queueOpen = !queueOpen;
    queuePanel.classList.toggle('open', queueOpen);
    if (queueOpen) renderQueueList();
  }

  function clearQueue() {
    var wasPlaying = isPlaying;
    audio.pause();
    setPlayingState(false);
    queue = [];
    currentIndex = -1;
    save();
    renderQueueList();
    updateBadges();
    bar.classList.remove('visible');
    document.body.classList.remove('has-queue-bar');
    queueOpen = false;
    queuePanel.classList.remove('open');
  }

  function addToQueue(item) {
    for (var i = 0; i < queue.length; i++) {
      if (queue[i].slug === item.slug) return false;
    }
    queue.push(item);
    save();
    showBar();
    updateBadges();
    renderQueueList();

    if (queue.length === 1) {
      loadTrack(0, false);
    }
    return true;
  }

  function addNextToQueue(item) {
    for (var i = 0; i < queue.length; i++) {
      if (queue[i].slug === item.slug) return false;
    }
    var insertAt = currentIndex >= 0 ? currentIndex + 1 : 0;
    queue.splice(insertAt, 0, item);
    save();
    showBar();
    updateBadges();
    renderQueueList();

    if (queue.length === 1) {
      loadTrack(0, false);
    }
    return true;
  }

  function playNowItem(item) {
    for (var i = 0; i < queue.length; i++) {
      if (queue[i].slug === item.slug) {
        loadTrack(i, true);
        showBar();
        return;
      }
    }
    var insertAt = currentIndex >= 0 ? currentIndex + 1 : 0;
    queue.splice(insertAt, 0, item);
    showBar();
    updateBadges();
    renderQueueList();
    loadTrack(insertAt, true);
  }

  function removeFromQueue(index) {
    if (index < 0 || index >= queue.length) return;
    var wasCurrentOrBefore = index <= currentIndex;
    queue.splice(index, 1);

    if (queue.length === 0) {
      clearQueue();
      return;
    }

    if (index === currentIndex) {
      // Removed the currently playing track
      audio.pause();
      if (currentIndex >= queue.length) currentIndex = queue.length - 1;
      loadTrack(currentIndex, isPlaying);
    } else if (wasCurrentOrBefore) {
      currentIndex = Math.max(0, currentIndex - 1);
    }

    save();
    renderQueueList();
    updateBadges();
  }

  function moveInQueue(fromIndex, toIndex) {
    if (fromIndex === toIndex) return;
    if (toIndex < 0 || toIndex >= queue.length) return;
    var item = queue.splice(fromIndex, 1)[0];
    queue.splice(toIndex, 0, item);

    // Update currentIndex to follow the playing track
    if (fromIndex === currentIndex) {
      currentIndex = toIndex;
    } else if (fromIndex < currentIndex && toIndex >= currentIndex) {
      currentIndex--;
    } else if (fromIndex > currentIndex && toIndex <= currentIndex) {
      currentIndex++;
    }

    save();
    renderQueueList();
  }

  // ─── Queue Panel Rendering ──────────────────────────────────────────────────
  function renderQueueList() {
    if (!queueList) return;
    queueCount.textContent = queue.length;

    if (queue.length === 0) {
      queueList.innerHTML = '<div class="q-empty">Your queue is empty. Add articles from the Listen section or article pages.</div>';
      return;
    }

    var html = '';
    for (var i = 0; i < queue.length; i++) {
      var t = queue[i];
      var isCurrent = i === currentIndex;
      html += '<div class="q-item' + (isCurrent ? ' q-current' : '') + '" draggable="true" data-index="' + i + '">';
      html += '<div class="q-item-grip" title="Drag to reorder">&#x2630;</div>';
      html += '<button class="q-item-play" data-index="' + i + '" aria-label="Play">';
      if (isCurrent && isPlaying) {
        html += '<svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M6 4h4v16H6zm8 0h4v16h-4z"/></svg>';
      } else {
        html += '<svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M8 5v14l11-7z"/></svg>';
      }
      html += '</button>';
      html += '<div class="q-item-info">';
      html += '<div class="q-item-title">' + escHtml(t.title) + '</div>';
      html += '<div class="q-item-section" style="color:' + t.color + '">' + escHtml(t.section) + '</div>';
      html += '</div>';
      html += '<div class="q-item-actions">';
      if (i > 0) html += '<button class="q-item-up" data-index="' + i + '" title="Move up" aria-label="Move up">&uarr;</button>';
      if (i < queue.length - 1) html += '<button class="q-item-down" data-index="' + i + '" title="Move down" aria-label="Move down">&darr;</button>';
      html += '<button class="q-item-remove" data-index="' + i + '" title="Remove" aria-label="Remove">&times;</button>';
      html += '</div>';
      html += '</div>';
    }
    queueList.innerHTML = html;

    // Bind events
    var items = queueList.querySelectorAll('.q-item');
    for (var j = 0; j < items.length; j++) {
      (function (el) {
        el.addEventListener('dragstart', onDragStart);
        el.addEventListener('dragover', onDragOver);
        el.addEventListener('drop', onDrop);
        el.addEventListener('dragend', onDragEnd);
      })(items[j]);
    }

    queueList.querySelectorAll('.q-item-play').forEach(function (btn) {
      btn.onclick = function () { loadTrack(parseInt(this.dataset.index), true); };
    });
    queueList.querySelectorAll('.q-item-up').forEach(function (btn) {
      btn.onclick = function () { var i = parseInt(this.dataset.index); moveInQueue(i, i - 1); };
    });
    queueList.querySelectorAll('.q-item-down').forEach(function (btn) {
      btn.onclick = function () { var i = parseInt(this.dataset.index); moveInQueue(i, i + 1); };
    });
    queueList.querySelectorAll('.q-item-remove').forEach(function (btn) {
      btn.onclick = function () { removeFromQueue(parseInt(this.dataset.index)); };
    });
  }

  function updateQueueHighlight() {
    if (!queueList) return;
    var items = queueList.querySelectorAll('.q-item');
    for (var i = 0; i < items.length; i++) {
      items[i].classList.toggle('q-current', i === currentIndex);
    }
  }

  // ─── Drag & Drop ────────────────────────────────────────────────────────────
  function onDragStart(e) {
    dragSrcIndex = parseInt(this.dataset.index);
    this.classList.add('q-dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', dragSrcIndex);
  }

  function onDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    this.classList.add('q-dragover');
  }

  function onDrop(e) {
    e.preventDefault();
    this.classList.remove('q-dragover');
    var toIndex = parseInt(this.dataset.index);
    if (dragSrcIndex !== null && dragSrcIndex !== toIndex) {
      moveInQueue(dragSrcIndex, toIndex);
    }
    dragSrcIndex = null;
  }

  function onDragEnd() {
    this.classList.remove('q-dragging');
    var items = queueList.querySelectorAll('.q-item');
    for (var i = 0; i < items.length; i++) items[i].classList.remove('q-dragover');
  }

  // ─── Badge Updates ──────────────────────────────────────────────────────────
  function updateBadges() {
    // Update all "Add to Queue" buttons on the page
    var btns = document.querySelectorAll('[data-queue-slug]');
    for (var i = 0; i < btns.length; i++) {
      var slug = btns[i].dataset.queueSlug;
      var inQueue = false;
      for (var j = 0; j < queue.length; j++) {
        if (queue[j].slug === slug) { inQueue = true; break; }
      }
      btns[i].classList.toggle('in-queue', inQueue);
      var label = btns[i].querySelector('.q-add-label');
      if (label) label.textContent = inQueue ? 'In Queue' : 'Add to Queue';
    }
  }

  // ─── Utility ────────────────────────────────────────────────────────────────
  function escHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ─── Bookmarks ─────────────────────────────────────────────────────────────
  var BOOKMARK_KEY = 'hfn_bookmarks';
  var bookmarks = [];

  function loadBookmarks() {
    try {
      var raw = localStorage.getItem(BOOKMARK_KEY);
      if (raw) bookmarks = JSON.parse(raw);
    } catch (e) { bookmarks = []; }
  }

  function saveBookmarks() {
    try {
      localStorage.setItem(BOOKMARK_KEY, JSON.stringify(bookmarks));
    } catch (e) { /* quota exceeded */ }
  }

  function toggleBookmark(slug, title, url, section, color) {
    var idx = -1;
    for (var i = 0; i < bookmarks.length; i++) {
      if (bookmarks[i].slug === slug) { idx = i; break; }
    }
    if (idx >= 0) {
      bookmarks.splice(idx, 1);
      saveBookmarks();
      updateBookmarkIcons();
      return false;
    }
    var entry = { slug: slug, title: title, url: url, savedAt: Date.now() };
    if (section) entry.section = section;
    if (color) entry.color = color;
    bookmarks.push(entry);
    saveBookmarks();
    updateBookmarkIcons();
    return true;
  }

  function isBookmarked(slug) {
    for (var i = 0; i < bookmarks.length; i++) {
      if (bookmarks[i].slug === slug) return true;
    }
    return false;
  }

  function updateBookmarkIcons() {
    document.querySelectorAll('.card-bookmark-btn').forEach(function (btn) {
      var slug = btn.dataset.bookmarkSlug;
      var saved = isBookmarked(slug);
      btn.classList.toggle('bookmarked', saved);
      btn.setAttribute('aria-label', saved ? 'Remove bookmark' : 'Bookmark');
    });
  }

  function updateSavedBadge() {
    var link = document.querySelector('.nav-links a[href="/saved"]');
    if (!link) return;
    var dot = link.querySelector('.saved-badge-dot');
    if (bookmarks.length > 0) {
      if (!dot) {
        dot = document.createElement('span');
        dot.className = 'saved-badge-dot';
        link.appendChild(dot);
      }
    } else if (dot) {
      dot.remove();
    }
  }

  // ─── Toast ────────────────────────────────────────────────────────────────
  var toastTimer = null;

  function showToast(msg, useHtml) {
    var el = document.getElementById('hfnToast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'hfnToast';
      el.className = 'hfn-toast';
      document.body.appendChild(el);
    }
    if (useHtml) {
      el.innerHTML = msg;
      el.classList.add('hfn-toast-interactive');
    } else {
      el.textContent = msg;
      el.classList.remove('hfn-toast-interactive');
    }
    el.classList.add('visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.classList.remove('visible'); }, 2800);
  }

  // ─── Popover ──────────────────────────────────────────────────────────────
  var activePopover = null;

  function closePopover() {
    if (activePopover) {
      activePopover.remove();
      activePopover = null;
    }
  }

  function openPopover(btn) {
    closePopover();
    var slug = btn.dataset.queueSlug;
    var title = btn.dataset.queueTitle;
    var section = btn.dataset.queueSection || '';
    var color = btn.dataset.queueColor || '#7c3aed';
    var url = btn.dataset.queueUrl;

    var pop = document.createElement('div');
    pop.className = 'audio-popover';
    pop.innerHTML =
      '<button class="audio-popover-item" data-action="playNow">' +
        '<svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16"><path d="M8 5v14l11-7z"/></svg>' +
        ' Play now</button>' +
      '<button class="audio-popover-item" data-action="addNext">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M17 11H3M21 7l-4 4 4 4M7 5v14"/></svg>' +
        ' Add next</button>' +
      '<button class="audio-popover-item" data-action="addEnd">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M12 5v14M5 12h14"/></svg>' +
        ' Add to end</button>';

    var item = { slug: slug, title: title, section: section, color: color, url: url };

    pop.querySelectorAll('.audio-popover-item').forEach(function (opt) {
      opt.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var action = this.dataset.action;
        if (action === 'playNow') {
          playNowItem(item);
          showToast('Playing now');
        } else if (action === 'addNext') {
          addNextToQueue(item) ? showToast('Playing next') : showToast('Already in queue');
        } else if (action === 'addEnd') {
          addToQueue(item) ? showToast('Added to queue') : showToast('Already in queue');
        }
        closePopover();
      });
    });

    var rect = btn.getBoundingClientRect();
    pop.style.position = 'fixed';
    pop.style.zIndex = '10001';

    document.body.appendChild(pop);

    var popRect = pop.getBoundingClientRect();
    var top = rect.bottom + 4;
    var left = rect.left;
    if (top + popRect.height > window.innerHeight) top = rect.top - popRect.height - 4;
    if (left + popRect.width > window.innerWidth) left = window.innerWidth - popRect.width - 8;
    if (left < 8) left = 8;
    pop.style.top = top + 'px';
    pop.style.left = left + 'px';

    activePopover = pop;
  }

  document.addEventListener('click', function (e) {
    if (activePopover && !activePopover.contains(e.target) && !e.target.closest('.card-play-btn')) {
      closePopover();
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closePopover();
  });

  // ─── Public API ──────────────────────────────────────────────────────────────
  window.HFNQueue = {
    add: function (slug, title, section, color, url) {
      var added = addToQueue({ slug: slug, title: title, section: section, color: color, url: url });
      if (added) {
        updateBadges();
        showToast('Added to queue');
      } else {
        showToast('Already in queue');
      }
    },
    addNext: function (slug, title, section, color, url) {
      var added = addNextToQueue({ slug: slug, title: title, section: section, color: color, url: url });
      if (added) {
        updateBadges();
        showToast('Playing next');
      } else {
        showToast('Already in queue');
      }
    },
    playNow: function (slug, title, section, color, url) {
      playNowItem({ slug: slug, title: title, section: section, color: color, url: url });
      showToast('Playing now');
    },
    addAll: function (items) {
      var count = 0;
      for (var i = 0; i < items.length; i++) {
        if (addToQueue(items[i])) count++;
      }
      updateBadges();
      if (count > 0) showToast(count + ' added to queue');
      return count;
    },
    bookmark: function (slug, title, url, section, color) {
      var added = toggleBookmark(slug, title, url, section, color);
      showToast(
        added ? 'Saved \u2014 <a href="/saved" class="hfn-toast-link">View saved articles</a>' : 'Removed from saved',
        added
      );
      updateSavedBadge();
    },
    isBookmarked: isBookmarked,
    rebind: function () {
      if (!document.getElementById('queueBar')) return;
      initDOM();
      if (queue.length > 0) {
        showBar();
        if (currentIndex >= 0 && currentIndex < queue.length) {
          var track = queue[currentIndex];
          titleEl.textContent = track.title;
          sectionEl.textContent = track.section;
          sectionEl.style.color = track.color;
          speedBtn.textContent = speeds[speedIndex] + '\u00d7';
          setPlayingState(!audio.paused);
          updateNavButtons();
          if (audio.duration) {
            var pct = audio.currentTime / audio.duration;
            progressBar.style.width = (pct * 100) + '%';
            if (progressThumb) progressThumb.style.left = (pct * 100) + '%';
            timeEl.textContent = fmt(audio.currentTime) + ' / ' + fmt(audio.duration);
          }
        }
      }
      bindQueueButtons();
      updateBadges();
      updateBookmarkIcons();
      updateSavedBadge();
      renderQueueList();
    },
  };

  // ─── Bind data-attribute buttons ────────────────────────────────────────────
  function bindQueueButtons() {
    // Legacy "Add to Queue" buttons (q-add-btn with data attributes)
    document.querySelectorAll('.q-add-btn[data-queue-slug]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        HFNQueue.add(
          this.dataset.queueSlug,
          this.dataset.queueTitle,
          this.dataset.queueSection,
          this.dataset.queueColor,
          this.dataset.queueUrl
        );
      });
    });

    // Play buttons — open popover
    document.querySelectorAll('.card-play-btn[data-queue-slug]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        openPopover(this);
      });
    });

    // Bookmark buttons
    document.querySelectorAll('.card-bookmark-btn').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        HFNQueue.bookmark(
          this.dataset.bookmarkSlug,
          this.dataset.bookmarkTitle,
          this.dataset.bookmarkUrl,
          this.dataset.bookmarkSection || '',
          this.dataset.bookmarkColor || ''
        );
      });
    });

    // "Queue All" button
    var queueAllBtn = document.getElementById('queueAllBtn');
    if (queueAllBtn && queueAllBtn.dataset.items) {
      queueAllBtn.addEventListener('click', function () {
        try {
          var items = JSON.parse(this.dataset.items);
          HFNQueue.addAll(items);
        } catch (e) { /* malformed JSON */ }
      });
    }
  }

  // ─── Init ───────────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    if (!document.getElementById('queueBar')) return;

    loadBookmarks();
    initDOM();
    var state = load();

    if (queue.length > 0) {
      showBar();
      if (currentIndex >= 0 && currentIndex < queue.length) {
        loadTrack(currentIndex, state.wasPlaying, state.currentTime);
      }
      speedBtn.textContent = speeds[speedIndex] + '\u00d7';
    }

    bindQueueButtons();
    updateBadges();
    updateBookmarkIcons();
    updateSavedBadge();
    renderQueueList();
  });
})();
