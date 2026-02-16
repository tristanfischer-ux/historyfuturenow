/* History Future Now — Share Buttons */
(function() {
  'use strict';

  var SITE = 'https://www.historyfuturenow.com';
  var h2cLoaded = false;

  function loadHtml2Canvas(cb) {
    if (h2cLoaded) { cb(); return; }
    var s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js';
    s.onload = function() { h2cLoaded = true; cb(); };
    document.head.appendChild(s);
  }

  function openShare(platform, url, title, text) {
    var encoded = encodeURIComponent(url);
    var encodedTitle = encodeURIComponent(title);
    var encodedText = encodeURIComponent(text);
    var shareUrl;

    switch (platform) {
      case 'x':
        shareUrl = 'https://x.com/intent/tweet?text=' + encodedText + '&url=' + encoded;
        break;
      case 'linkedin':
        shareUrl = 'https://www.linkedin.com/sharing/share-offsite/?url=' + encoded;
        break;
      case 'whatsapp':
        shareUrl = 'https://wa.me/?text=' + encodeURIComponent(title + ' — ' + text + ' ' + url);
        break;
      case 'email':
        shareUrl = 'mailto:?subject=' + encodedTitle + '&body=' + encodeURIComponent(text + '\n\n' + url);
        break;
      case 'copy':
        if (navigator.clipboard) {
          navigator.clipboard.writeText(url).then(function() { showToast('Link copied'); });
        } else {
          fallbackCopy(url);
          showToast('Link copied');
        }
        return;
    }

    if (shareUrl) {
      window.open(shareUrl, '_blank', 'width=600,height=400,noopener');
    }
  }

  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  }

  function showToast(message) {
    var toast = document.getElementById('copyToast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'copyToast';
      toast.className = 'copy-toast';
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(function() { toast.classList.remove('show'); }, 2000);
  }

  /* ── Chart capture ─────────────────────────────────────────────────────── */

  function captureChart(chartFigure, callback) {
    loadHtml2Canvas(function() {
      chartFigure.classList.add('capturing');

      html2canvas(chartFigure, {
        backgroundColor: '#faf9f6',
        scale: 2,
        useCORS: true,
        logging: false,
        onclone: function(doc) {
          var clone = doc.querySelector('.chart-figure.capturing');
          if (clone) {
            clone.style.margin = '0';
            clone.style.borderRadius = '0';
          }
        }
      }).then(function(canvas) {
        chartFigure.classList.remove('capturing');
        callback(canvas);
      }).catch(function() {
        chartFigure.classList.remove('capturing');
        showToast('Could not capture chart');
      });
    });
  }

  function downloadChart(chartFigure) {
    showToast('Capturing chart...');
    captureChart(chartFigure, function(canvas) {
      var title = chartFigure.getAttribute('data-chart-title') || 'chart';
      var filename = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '') + '.png';
      var link = document.createElement('a');
      link.download = filename;
      link.href = canvas.toDataURL('image/png');
      link.click();
      showToast('Chart downloaded');
    });
  }

  function copyChartImage(chartFigure) {
    showToast('Copying chart...');
    captureChart(chartFigure, function(canvas) {
      canvas.toBlob(function(blob) {
        if (navigator.clipboard && navigator.clipboard.write) {
          navigator.clipboard.write([
            new ClipboardItem({ 'image/png': blob })
          ]).then(function() {
            showToast('Chart image copied');
          }).catch(function() {
            showToast('Copy not supported in this browser');
          });
        } else {
          showToast('Copy not supported in this browser');
        }
      }, 'image/png');
    });
  }

  function shareChartSocial(chartFigure, platform) {
    var title = chartFigure.getAttribute('data-chart-title') || 'Chart';
    var articleTitle = document.title.replace(' — History Future Now', '');
    var url = window.location.href;
    var text = title + ' — from "' + articleTitle + '" on History Future Now';

    openShare(platform, url, articleTitle, text);
  }

  /* ── Event delegation ──────────────────────────────────────────────────── */

  document.addEventListener('click', function(e) {
    // Chart share buttons
    var chartBtn = e.target.closest('[data-chart-share]');
    if (chartBtn) {
      e.preventDefault();
      var action = chartBtn.getAttribute('data-chart-share');
      var chartFigure = chartBtn.closest('.chart-figure');
      if (!chartFigure) return;

      switch (action) {
        case 'download':    downloadChart(chartFigure); break;
        case 'copy-image':  copyChartImage(chartFigure); break;
        case 'x':
        case 'linkedin':
        case 'whatsapp':    shareChartSocial(chartFigure, action); break;
      }
      return;
    }

    // Article share buttons
    var btn = e.target.closest('[data-share]');
    if (!btn) return;
    e.preventDefault();

    var platform = btn.getAttribute('data-share');
    var container = btn.closest('[data-share-url]') || document.querySelector('[data-share-url]');
    var url = container ? container.getAttribute('data-share-url') : window.location.href;
    var title = container ? container.getAttribute('data-share-title') : document.title;
    var text = container ? (container.getAttribute('data-share-text') || '') : '';

    openShare(platform, url, title, text);
  });
})();
