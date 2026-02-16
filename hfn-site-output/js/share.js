/* History Future Now — Share Buttons */
(function() {
  'use strict';

  var SITE = 'https://www.historyfuturenow.com';

  function openShare(platform, url, title, text) {
    var shareUrl;
    var encoded = encodeURIComponent(url);
    var encodedTitle = encodeURIComponent(title);
    var encodedText = encodeURIComponent(text);

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
          navigator.clipboard.writeText(url).then(function() {
            showCopyToast();
          });
        } else {
          var ta = document.createElement('textarea');
          ta.value = url;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
          showCopyToast();
        }
        return;
    }

    if (shareUrl) {
      window.open(shareUrl, '_blank', 'width=600,height=400,noopener');
    }
  }

  function showCopyToast() {
    var toast = document.getElementById('copyToast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'copyToast';
      toast.className = 'copy-toast';
      toast.textContent = 'Link copied';
      document.body.appendChild(toast);
    }
    toast.classList.add('show');
    setTimeout(function() { toast.classList.remove('show'); }, 2000);
  }

  document.addEventListener('click', function(e) {
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
