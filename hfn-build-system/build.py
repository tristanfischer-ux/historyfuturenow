#!/usr/bin/env python3
"""
History Future Now — Static Site Builder v2
Enhanced: reading time, related articles, pull quotes, OG tags, section theming, favicon
"""

import os, re, yaml, markdown, json, math, random
import html as html_mod
from pathlib import Path
from chart_defs import get_all_charts, COLORS as CHART_COLORS

ESSAYS_DIR = Path(__file__).parent / "essays"
OUTPUT_DIR = Path(__file__).parent.parent / "hfn-site-output"
ARTICLES_DIR = OUTPUT_DIR / "articles"
MANIFEST_PATH = Path(__file__).parent / "original_articles.txt"

MAX_NEW_ARTICLES = 10

PARTS = {
    "Natural Resources": {"order": 1, "slug": "natural-resources", "color": "#0d9a5a", "color_soft": "#effaf4", "label": "Part 1", "icon": "🌍", "desc": "Energy, food, water, land — the physical foundations that every civilisation depends on."},
    "Global Balance of Power": {"order": 2, "slug": "balance-of-power", "color": "#2563eb", "color_soft": "#eff4ff", "label": "Part 2", "icon": "⚖️", "desc": "How nations rise, compete, and decline — from colonial empires to modern China."},
    "Jobs & Economy": {"order": 3, "slug": "jobs-economy", "color": "#b8751a", "color_soft": "#fef8ee", "label": "Part 3", "icon": "⚙️", "desc": "Automation, trade, debt, and the future of work in an age of intelligent machines."},
    "Society": {"order": 4, "slug": "society", "color": "#7c3aed", "color_soft": "#f5f0ff", "label": "Part 4", "icon": "🏛️", "desc": "Democracy, religion, migration, identity — the human systems that bind us together."},
}

PART_ALIASES = {
    "Natural Resources": "Natural Resources",
    "Global Balance of Power": "Global Balance of Power",
    "Balance of Power": "Global Balance of Power",
    "Jobs & Economy": "Jobs & Economy",
    "Jobs &amp; Economy": "Jobs & Economy",
    "Jobs and the Economy": "Jobs & Economy",
    "Society": "Society",
}

SITE_URL = "https://www.historyfuturenow.com"

def load_original_slugs():
    """Load the set of original article slugs from the manifest file."""
    if not MANIFEST_PATH.exists():
        return set()
    slugs = set()
    for line in MANIFEST_PATH.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            slugs.add(line)
    return slugs

def fix_encoding(text):
    replacements = {
        'â€™': "'", 'â€˜': "'", 'â€œ': '"', 'â€\x9d': '"', 'â€"': '—', 'â€"': '–',
        'â€¦': '…', 'Â ': ' ', 'Â£': '£', 'Â': '', '\xa0': ' ', 'â‚¬': '€',
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    text = re.sub(r'  +', ' ', text)
    return text

def estimate_reading_time(text):
    words = len(re.findall(r'\w+', text))
    return max(1, math.ceil(words / 250))

def extract_pull_quote(body_html):
    text = re.sub(r'<[^>]+>', '', body_html)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    candidates = []
    for s in sentences:
        s = s.strip()
        if 80 < len(s) < 220:
            score = 0
            for word in ['revolution', 'fundamental', 'critical', 'dominant', 'transform',
                         'collapse', 'unprecedented', 'crucial', 'inevitable', 'radical',
                         'dangerous', 'remarkable', 'extraordinary', 'impossible', 'monopoly',
                         'crisis', 'threat', 'power', 'wealth', 'war', 'future', 'history',
                         'centuries', 'billion', 'million', 'devastating', 'profound']:
                if word.lower() in s.lower():
                    score += 1
            if score > 0:
                candidates.append((score, s))
    candidates.sort(key=lambda x: -x[0])
    return candidates[0][1] if candidates else None

def parse_essay(filepath):
    content = filepath.read_text(encoding='utf-8', errors='replace')
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try: meta = yaml.safe_load(parts[1])
            except: meta = {}
            body = parts[2]
        else: meta, body = {}, content
    else: meta, body = {}, content

    body = fix_encoding(body)
    if meta:
        for key in ['title', 'excerpt']:
            if key in meta and isinstance(meta[key], str):
                meta[key] = fix_encoding(meta[key])

    title = meta.get('title', filepath.stem.replace('-', ' ').title())
    title = re.sub(r'</?strong>', '', title).replace('&nbsp;', '').replace('\xa0', '').strip()

    slug = meta.get('slug', filepath.stem)
    slug = slug.replace('strong', '').replace('nbsp', '').strip('-')
    slug = re.sub(r'-+', '-', slug)

    raw_part = meta.get('part', 'Society')
    part = PART_ALIASES.get(raw_part, raw_part)
    if part not in PARTS: part = "Society"

    excerpt = meta.get('excerpt', '')
    if not excerpt:
        clean = re.sub(r'#.*?\n', '', body).strip()
        paras = [p.strip() for p in clean.split('\n\n') if p.strip() and not p.strip().startswith('#')]
        if paras: excerpt = paras[0][:300]

    reading_time = estimate_reading_time(body)

    body = re.sub(r'^\s*#\s+[^\n]+\n', '', body, count=1)
    body = re.sub(r'\n---\s*\n\s*##\s*THEN:.*$', '', body, flags=re.DOTALL)
    lines = body.rstrip().split('\n')
    while lines and (lines[-1].strip() == '' or lines[-1].strip().startswith('## ')):
        if lines[-1].strip().startswith('## ') and len(lines[-1].strip()) > 3: lines.pop()
        elif lines[-1].strip() == '': lines.pop()
        else: break
    body = '\n'.join(lines)

    body_html = markdown.markdown(body, extensions=['extra', 'smarty', 'nl2br'])
    body_html = re.sub(r'<p>\s*</p>', '', body_html)

    pull_quote = extract_pull_quote(body_html)

    return {
        'title': title, 'slug': slug, 'part': part, 'excerpt': excerpt,
        'body_html': body_html, 'reading_time': reading_time,
        'pull_quote': pull_quote, 'filepath': filepath,
    }

def get_related(essay, all_essays, n=3):
    same = [e for e in all_essays if e['part'] == essay['part'] and e['slug'] != essay['slug']]
    random.seed(hash(essay['slug']))
    return random.sample(same, min(n, len(same)))

def make_head(title, desc="", og_url="", part_color=None, json_ld=None):
    te = html_mod.escape(title)
    de = html_mod.escape(desc[:300]) if desc else ""
    tc = part_color or "#c43425"
    canonical = f'<link rel="canonical" href="{SITE_URL}{og_url}">' if og_url else ""
    og = f'<meta property="og:url" content="{SITE_URL}{og_url}">' if og_url else ""
    ld = f'<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False)}</script>' if json_ld else ""
    return f'''<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{te}</title>
<meta name="description" content="{de}">
{canonical}
<meta property="og:title" content="{te}">
<meta property="og:description" content="{de}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="History Future Now">
<meta property="og:locale" content="en_GB">
<meta property="article:author" content="Tristan Fischer">
{og}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{te}">
<meta name="twitter:description" content="{de}">
<meta name="theme-color" content="{tc}">
<meta name="robots" content="index, follow">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Source+Sans+3:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
{ld}'''

def make_nav(active=None):
    secs = [("Home","/",None),("Resources","/natural-resources","Natural Resources"),
            ("Power","/balance-of-power","Global Balance of Power"),
            ("Economy","/jobs-economy","Jobs & Economy"),("Society","/society","Society")]
    li = ""
    for label, href, part in secs:
        ac = ' class="active"' if part and part == active else ''
        li += f'      <li><a href="{href}"{ac}>{label}</a></li>\n'
    return f'''<nav class="site-nav">
  <div class="nav-inner">
    <a class="nav-logo" href="/">History Future <span>Now</span></a>
    <button class="nav-toggle" aria-label="Menu">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
    </button>
    <ul class="nav-links">
{li}    </ul>
  </div>
</nav>'''

def make_footer():
    return '''<footer class="site-footer">
  <div class="footer-inner">
    <p class="footer-tagline">History doesn&rsquo;t repeat itself, but it does rhyme.</p>
    <ul class="footer-links">
      <li><a href="/">Home</a></li>
      <li><a href="/natural-resources">Resources</a></li>
      <li><a href="/balance-of-power">Power</a></li>
      <li><a href="/jobs-economy">Economy</a></li>
      <li><a href="/society">Society</a></li>
    </ul>
    <p>&copy; 2012&ndash;2026 History Future Now &middot; Tristan Fischer</p>
  </div>
</footer>
<script src="/js/nav.js"></script>'''

def inject_pull_quote(body_html, pq):
    if not pq: return body_html
    pq_html = f'<aside class="pull-quote"><p>{html_mod.escape(pq)}</p></aside>'
    count, pos = 0, 0
    while count < 4:
        idx = body_html.find('</p>', pos)
        if idx == -1: break
        pos = idx + 4
        count += 1
    if count >= 3:
        return body_html[:pos] + '\n\n' + pq_html + '\n\n' + body_html[pos:]
    return body_html

def make_audio_player_script():
    """Inline JavaScript for the article audio player."""
    return '''<script>
(function(){
  var audio=document.getElementById('audioElement');
  if(!audio)return;
  var btn=document.getElementById('audioPlayBtn');
  var bar=document.getElementById('audioProgressBar');
  var wrap=document.getElementById('audioProgressWrap');
  var timeEl=document.getElementById('audioTime');
  var speedEl=document.getElementById('audioSpeed');
  var iconPlay=btn.querySelector('.audio-icon-play');
  var iconPause=btn.querySelector('.audio-icon-pause');
  var speeds=[1,1.25,1.5,1.75,2];
  var si=0;

  function fmt(s){
    if(isNaN(s))return'0:00';
    var m=Math.floor(s/60);
    var sec=Math.floor(s%60);
    return m+':'+(sec<10?'0':'')+sec;
  }

  btn.onclick=function(){
    if(audio.paused){audio.play();iconPlay.style.display='none';iconPause.style.display='block';}
    else{audio.pause();iconPlay.style.display='block';iconPause.style.display='none';}
  };

  audio.ontimeupdate=function(){
    if(audio.duration){
      bar.style.width=(audio.currentTime/audio.duration*100)+'%';
      timeEl.textContent=fmt(audio.currentTime)+' / '+fmt(audio.duration);
    }
  };

  audio.onended=function(){
    iconPlay.style.display='block';iconPause.style.display='none';
    bar.style.width='0%';
  };

  wrap.onclick=function(e){
    if(audio.duration){
      var rect=wrap.getBoundingClientRect();
      var pct=(e.clientX-rect.left)/rect.width;
      audio.currentTime=pct*audio.duration;
    }
  };

  speedEl.onclick=function(){
    si=(si+1)%speeds.length;
    audio.playbackRate=speeds[si];
    speedEl.textContent=speeds[si]+'\\u00d7';
  };
})();
</script>'''

ALL_CHARTS = get_all_charts()

def make_chart_html(chart):
    import re
    js = chart.get('js', '')
    is_horizontal = "indexAxis:'y'" in js or 'indexAxis:"y"' in js
    
    # Count labels for horizontal bars
    n_labels = 0
    label_matches = re.findall(r"labels:\[([^\]]+)\]", js)
    if label_matches:
        n_labels = label_matches[0].count("'") // 2
    # Also check var c=[...] pattern
    var_matches = re.findall(r"var [a-z]=\[([^\]]+)\]", js)
    for m in var_matches:
        cnt = m.count("'") // 2
        if cnt > n_labels:
            n_labels = cnt
    
    # Count datasets for multi-line charts  
    n_datasets = js.count("ds(") + len(re.findall(r"label:'[^']+',data:", js))
    
    # Auto-size: horizontal bars get explicit height based on label count
    size_class = ''
    inline_style = ''
    if chart.get('tall'):
        size_class = ' tall'
    elif is_horizontal and n_labels > 0:
        bar_height = 20
        total_height = n_labels * bar_height + 60
        total_height = max(250, min(480, total_height))
        inline_style = f' style="aspect-ratio:auto;height:{total_height}px"'
    elif n_datasets >= 5 and is_horizontal:
        size_class = ' tall'
    
    return f'''
    <div class="chart-figure">
      <div class="chart-figure-label">Figure {chart['figure_num']}</div>
      <h4>{html_mod.escape(chart['title'])}</h4>
      <p class="chart-desc">{html_mod.escape(chart['desc'])}</p>
      <div class="chart-area{size_class}"{inline_style}><canvas id="{chart['id']}"></canvas></div>
      <p class="chart-source">Source: {html_mod.escape(chart['source'])}</p>
    </div>
'''

def inject_charts_into_body(body_html, charts):
    """Insert chart figures at appropriate positions in the article body."""
    if not charts:
        return body_html, ""

    # Group charts by position
    positioned = {}
    end_charts = []
    for ch in charts:
        pos = ch.get('position', 'before_end')
        if pos == 'before_end':
            end_charts.append(ch)
        else:
            positioned.setdefault(pos, []).append(ch)

    # Insert charts after specific headings or paragraphs
    for pos_key, pos_charts in positioned.items():
        chart_block = '\n'.join(make_chart_html(ch) for ch in pos_charts)

        if pos_key.startswith('after_heading:'):
            heading_text = pos_key.split(':', 1)[1].strip().lower()
            # Find heading containing this text (h2 or h3)
            pattern = re.compile(
                r'(</h[23]>)',
                re.IGNORECASE
            )
            matches = list(pattern.finditer(body_html))
            inserted = False
            for m in matches:
                # Get the heading text before this closing tag
                start = body_html.rfind('<h', 0, m.start())
                if start >= 0:
                    heading_content = re.sub(r'<[^>]+>', '', body_html[start:m.end()]).strip().lower()
                    if heading_text in heading_content:
                        insert_pos = m.end()
                        body_html = body_html[:insert_pos] + '\n' + chart_block + body_html[insert_pos:]
                        inserted = True
                        break
            if not inserted:
                # Fallback: insert after first few paragraphs
                count, pos = 0, 0
                while count < 3:
                    idx = body_html.find('</p>', pos)
                    if idx == -1: break
                    pos = idx + 4
                    count += 1
                if count >= 2:
                    body_html = body_html[:pos] + '\n' + chart_block + body_html[pos:]
                else:
                    end_charts.extend(pos_charts)

        elif pos_key.startswith('after_para_'):
            try:
                para_num = int(pos_key.split('_')[-1])
            except:
                para_num = 3
            count, pos = 0, 0
            while count < para_num:
                idx = body_html.find('</p>', pos)
                if idx == -1: break
                pos = idx + 4
                count += 1
            body_html = body_html[:pos] + '\n' + chart_block + body_html[pos:]

    # Append remaining charts at end
    if end_charts:
        end_block = '\n'.join(make_chart_html(ch) for ch in end_charts)
        body_html += '\n' + end_block

    # Build the combined JS for all charts
    all_js = '\n'.join(ch['js'] for ch in charts)
    script_block = f'''
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
<script>
{CHART_COLORS}
{all_js}
</script>'''

    return body_html, script_block

def build_article(essay, all_essays):
    pi = PARTS[essay['part']]
    te = html_mod.escape(essay['title'])
    body = inject_pull_quote(essay['body_html'], essay['pull_quote'])
    related = get_related(essay, all_essays)

    # Inject charts if available for this article
    article_charts = ALL_CHARTS.get(essay['slug'], [])
    body, chart_script = inject_charts_into_body(body, article_charts)
    chart_count = len(article_charts)

    rel_html = ""
    if related:
        cards = ""
        for r in related:
            rp = PARTS[r['part']]
            cards += f'''      <a href="/articles/{html_mod.escape(r['slug'])}" class="related-card">
        <span class="related-kicker" style="color:{rp['color']}">{rp['label']}</span>
        <span class="related-title">{html_mod.escape(r['title'])}</span>
        <span class="related-time">{r['reading_time']} min read</span>
      </a>\n'''
        rel_html = f'''
  <section class="related-articles">
    <h3>Continue reading in {html_mod.escape(essay['part'])}</h3>
    <div class="related-grid">
{cards}    </div>
  </section>'''

    chart_badge = f'\n    <div class="article-chart-badge">{chart_count} interactive charts</div>' if chart_count > 0 else ''

    # Audio player (if audio file exists)
    audio_file = OUTPUT_DIR / "audio" / f"{essay['slug']}.mp3"
    has_audio = audio_file.exists()
    est_listen = max(1, round(essay['reading_time'] * 250 / 189))  # reading_time is at 250wpm, voice is ~189wpm
    audio_player = ''
    if has_audio:
        audio_player = f'''
  <div class="audio-player" id="audioPlayer">
    <div class="audio-player-inner">
      <button class="audio-play-btn" id="audioPlayBtn" aria-label="Play article narration">
        <svg class="audio-icon-play" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        <svg class="audio-icon-pause" viewBox="0 0 24 24" fill="currentColor" style="display:none"><path d="M6 4h4v16H6zm8 0h4v16h-4z"/></svg>
      </button>
      <div class="audio-info">
        <div class="audio-label">Listen to this article</div>
        <div class="audio-meta">{est_listen} min &middot; British narrator</div>
      </div>
      <div class="audio-progress-wrap" id="audioProgressWrap">
        <div class="audio-progress-bar" id="audioProgressBar"></div>
      </div>
      <div class="audio-time" id="audioTime">0:00</div>
      <div class="audio-speed" id="audioSpeed" title="Playback speed">1&times;</div>
    </div>
    <audio id="audioElement" preload="none" src="/audio/{html_mod.escape(essay['slug'])}.mp3"></audio>
  </div>'''

    # JSON-LD structured data for article
    json_ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": essay['title'],
        "description": essay['excerpt'][:300],
        "author": {"@type": "Person", "name": "Tristan Fischer"},
        "publisher": {"@type": "Organization", "name": "History Future Now", "url": SITE_URL},
        "url": f"{SITE_URL}/articles/{essay['slug']}",
        "mainEntityOfPage": f"{SITE_URL}/articles/{essay['slug']}",
        "articleSection": essay['part'],
        "inLanguage": "en-GB",
    }

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{make_head(f"{essay['title']} — History Future Now", essay['excerpt'], f"/articles/{essay['slug']}", pi['color'], json_ld)}
</head>
<body>

{make_nav(essay['part'])}

<article class="page-container">
  <header class="article-header">
    <div class="article-kicker" style="color:{pi['color']}">{pi['label']} &middot; {html_mod.escape(essay['part'])}</div>
    <h1>{te}</h1>
    <div class="article-meta">
      <span class="article-byline">By <strong>Tristan Fischer</strong></span>
      <span class="meta-sep">&middot;</span>
      <span class="article-reading-time">{essay['reading_time']} min read</span>
    </div>{chart_badge}
  </header>
{audio_player}
  <div class="article-body">
    {body}
  </div>

  <div class="article-footer">
    <a href="/{pi['slug']}" class="back-to-section" style="color:{pi['color']}">&larr; All {html_mod.escape(essay['part'])} articles</a>
  </div>
{rel_html}
</article>

{make_footer()}
{chart_script}
{make_audio_player_script() if has_audio else ''}
</body>
</html>'''

def build_section(part_name, essays, new_slugs=None):
    if new_slugs is None:
        new_slugs = set()
    pi = PARTS[part_name]
    se = [e for e in essays if e['part'] == part_name]
    cards = ""
    for e in se:
        chart_count = len(ALL_CHARTS.get(e['slug'], []))
        chart_tag = f' <span class="card-charts">&middot; {chart_count} chart{"s" if chart_count != 1 else ""}</span>' if chart_count > 0 else ''
        new_badge = '<span class="card-new-badge">New</span> ' if e['slug'] in new_slugs else ''
        cards += f'''    <a href="/articles/{html_mod.escape(e['slug'])}" class="card" data-section="{pi['slug']}">
      <div class="card-kicker" style="color:{pi['color']}">{new_badge}{pi['label']}</div>
      <h3>{html_mod.escape(e['title'])}</h3>
      <p>{html_mod.escape(e['excerpt'][:200])}</p>
      <div class="card-meta">
        <span class="card-link" style="color:{pi['color']}">Read article &rarr;</span>
        <span class="card-time">{e['reading_time']} min{chart_tag}</span>
      </div>
    </a>\n'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{make_head(f"{pi['label']}: {part_name} — History Future Now", pi['desc'], f"/{pi['slug']}", pi['color'])}
</head>
<body>

{make_nav(part_name)}

<section class="section-hero" style="--section-color:{pi['color']};--section-soft:{pi['color_soft']}">
  <div class="section-hero-inner">
    <span class="section-icon">{pi['icon']}</span>
    <h1>{pi['label']}: {html_mod.escape(part_name)}</h1>
    <p class="section-hero-desc">{html_mod.escape(pi['desc'])}</p>
    <div class="section-hero-count">{len(se)} articles</div>
  </div>
</section>

<div class="section-grid">
  <div class="cards">
{cards}  </div>
</div>

{make_footer()}
</body>
</html>'''

def build_homepage(essays, new_essays=None):
    if new_essays is None:
        new_essays = []
    from chart_defs import get_all_charts, COLORS
    all_charts = get_all_charts()

    total_articles = len(essays)
    total_charts = sum(len(v) for v in all_charts.values())
    total_reading = sum(e.get('reading_time', 5) for e in essays)
    total_hours = round(total_reading / 60)

    # Sort essays by file modification time (newest first) for "latest" ordering
    import os
    for e in essays:
        if 'mtime' not in e:
            for f in ESSAYS_DIR.glob("*.md"):
                if e['slug'] in str(f):
                    e['mtime'] = os.path.getmtime(f)
                    break
            else:
                e['mtime'] = 0
    sorted_essays = sorted(essays, key=lambda x: x.get('mtime', 0), reverse=True)

    # ── Latest Articles: top 3 newest as hero cards ──
    # If new articles exist, the newest new article gets the hero slot
    if new_essays:
        hero_essay = new_essays[0]
        remaining = [e for e in sorted_essays if e['slug'] != hero_essay['slug']]
        latest = [hero_essay] + remaining[:2]
    else:
        latest = sorted_essays[:3]

    latest_html = ""
    for i, e in enumerate(latest):
        pi = PARTS[e['part']]
        n_charts = len(all_charts.get(e['slug'], []))
        badge = f'<span class="latest-badge">{n_charts} charts</span>' if n_charts else ''
        size_class = "latest-hero" if i == 0 else "latest-secondary"
        new_tag = '<span class="latest-new">New</span> ' if e.get('is_new') else ''
        latest_html += f"""      <a href="/articles/{html_mod.escape(e['slug'])}" class="latest-card {size_class}" style="--accent:{pi['color']}">
        <div class="latest-kicker">{new_tag}{pi['label']} &middot; {html_mod.escape(e['part'])} {badge}</div>
        <h3>{html_mod.escape(e['title'])}</h3>
        <p>{html_mod.escape(e['excerpt'][:200])}</p>
        <span class="latest-meta">{e['reading_time']} min read &rarr;</span>
      </a>\n"""

    # ── New Articles section (grouped by category) ──
    new_section_html = ""
    if new_essays:
        new_cards_by_part = {}
        for e in new_essays:
            new_cards_by_part.setdefault(e['part'], []).append(e)

        new_cards_html = ""
        for pn in sorted(PARTS.keys(), key=lambda p: PARTS[p]['order']):
            if pn not in new_cards_by_part:
                continue
            pi = PARTS[pn]
            for e in new_cards_by_part[pn]:
                n_charts = len(all_charts.get(e['slug'], []))
                chart_badge = f' <span class="card-charts">&middot; {n_charts} chart{"s" if n_charts != 1 else ""}</span>' if n_charts > 0 else ''
                new_cards_html += f"""    <a href="/articles/{html_mod.escape(e['slug'])}" class="card" data-section="{pi['slug']}">
      <div class="card-kicker" style="color:{pi['color']}"><span class="card-new-badge">New</span> {pi['label']}</div>
      <h3>{html_mod.escape(e['title'])}</h3>
      <p>{html_mod.escape(e['excerpt'][:160])}</p>
      <div class="card-meta">
        <span class="card-link" style="color:{pi['color']}">Read article &rarr;</span>
        <span class="card-time">{e['reading_time']} min{chart_badge}</span>
      </div>
    </a>\n"""

        new_section_html = f"""
<div class="new-articles-wrap">
  <div class="new-articles-inner">
    <div class="new-articles-header">
      <h2 class="new-articles-title">New Articles</h2>
      <p class="new-articles-intro">Recently published analysis across all sections.</p>
    </div>
    <div class="cards">
{new_cards_html}    </div>
  </div>
</div>
"""

    # ── Data Stories: expanded carousel with 12 stories ──
    data_stories = [
        {'slug':'the-unintended-consequences-of-war-how-the-loss-of-young-men-transformed-womens-roles-in-society-and-ushered-in-the-welfare-state',
         'chart_id':'heroWar','headline':'Nearly half of Soviet men aged 18-30 were killed in WW2','sub':'The Unintended Consequences of War','color':'#c43425',
         'js':"""(()=>{const ctx=document.getElementById('heroWar');new Chart(ctx,{type:'bar',data:{labels:['Soviet\\nUnion','Germany','Germany\\n(WW1)','Confederate\\nStates','Russia\\n(WW1)','France\\n(WW1)'],datasets:[{data:[49,45,28,19,18.7,17],backgroundColor:['#c43425','#c43425cc','#7c3aed','#2563eb','#7c3aedcc','#b8751a'],borderRadius:3,borderSkipped:false}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{backgroundColor:'#1a1815ee',callbacks:{label:i=>i.raw+'% of males 18-30 killed'}}},scales:{x:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',callback:v=>v+'%',font:{size:9}}},y:{grid:{display:false},ticks:{color:'#8a8479',font:{size:9}}}}}});})();"""},
        {'slug':'the-renewables-and-battery-revolution',
         'chart_id':'heroSolar','headline':'Solar costs fell 99% in 40 years','sub':'The Renewables & Battery Revolution','color':'#0d9a5a',
         'js':"""(()=>{const ctx=document.getElementById('heroSolar');new Chart(ctx,{type:'line',data:{datasets:[{data:_xy([1976,1985,1995,2000,2005,2010,2015,2020,2024],[100,25,8,5,4,2,0.6,0.25,0.2]),borderColor:'#0d9a5a',backgroundColor:'#0d9a5a18',fill:true,tension:.35,pointRadius:2,pointBackgroundColor:'#0d9a5a',borderWidth:2.5}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{backgroundColor:'#1a1815ee',callbacks:{label:i=>'$'+i.parsed.y+'/watt'}}},scales:{x:{type:'linear',min:1976,max:2024,grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9}}},y:{type:'logarithmic',grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>'$'+v}}}}});})();"""},
        {'slug':'debt-jubilees-and-hyperinflation-why-history-shows-that-this-might-be-the-way-forward-for-us-all',
         'chart_id':'heroDebt','headline':'A loaf of bread cost 3 billion Marks by 1923','sub':'Debt Jubilees & Hyperinflation','color':'#b8751a',
         'js':"""(()=>{const ctx=document.getElementById('heroDebt');new Chart(ctx,{type:'line',data:{datasets:[{data:_xy([1921.0,1921.5,1922.0,1922.5,1923.0,1923.25,1923.5,1923.67,1923.83],[1,2,3,10,250,500,100000,2000000,3000000000]),borderColor:'#b8751a',backgroundColor:'#b8751a18',fill:true,tension:.3,pointRadius:2,pointBackgroundColor:'#b8751a',borderWidth:2.5}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{backgroundColor:'#1a1815ee',callbacks:{label:i=>{const v=i.parsed.y;return v>=1e9?(v/1e9)+'B Marks':v>=1e6?(v/1e6)+'M':v>=1e3?(v/1e3)+'K':v+' Marks'}}}},scales:{x:{type:'linear',min:1921,max:1924,grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>{const yr=Math.floor(v);const f=v-yr;if(f<0.01)return'Jan '+yr;if(Math.abs(f-0.5)<0.01)return'Jul '+yr;return''}}},y:{type:'logarithmic',grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>{if(v>=1e9)return v/1e9+'B';if(v>=1e6)return v/1e6+'M';if(v>=1e3)return v/1e3+'K';return v}}}}}});})();"""},
        {'slug':'lets-talk-about-sex-does-the-separation-of-pleasure-and-procreation-mean-the-end-of-people',
         'chart_id':'heroFertility','headline':'South Korea: 0.72 children per woman','sub':'The Separation of Sex & Procreation','color':'#7c3aed',
         'js':"""(()=>{const ctx=document.getElementById('heroFertility');new Chart(ctx,{type:'bar',data:{labels:['S.Korea','China','Italy','Japan','Germany','UK','France','US','India','Nigeria'],datasets:[{data:[0.72,1.09,1.24,1.20,1.35,1.49,1.79,1.62,2.03,5.14],backgroundColor:['#c43425','#c43425','#c43425','#c43425','#c43425','#b8751a','#b8751a','#b8751a','#0d9a5a','#0d9a5a'],borderRadius:3,borderSkipped:false}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{backgroundColor:'#1a1815ee',callbacks:{label:i=>i.raw+' children per woman'}},annotation:{annotations:{line1:{type:'line',yMin:2.1,yMax:2.1,borderColor:'#8a8479',borderDash:[4,3],borderWidth:1}}}},scales:{x:{grid:{display:false},ticks:{color:'#8a8479',font:{size:8},maxRotation:45}},y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9}},min:0,max:5.5}}}});})();"""},
        {'slug':'what-does-it-take-to-get-europeans-to-have-a-revolution',
         'chart_id':'heroRev','headline':'60+ revolutions in 350 years','sub':'What Does It Take To Start A Revolution?','color':'#2563eb',
         'js':"""(()=>{const ctx=document.getElementById('heroRev');const ch=[{y:1642,i:3,c:'#2563eb'},{y:1688,i:2,c:'#2563eb'},{y:1775,i:5,c:'#c43425'},{y:1789,i:9,c:'#c43425'},{y:1821,i:3,c:'#7c3aed'},{y:1830,i:4,c:'#b8751a'},{y:1848,i:10,c:'#c43425'},{y:1917,i:8,c:'#c43425'},{y:1989,i:9,c:'#0d9a5a'}];new Chart(ctx,{type:'bubble',data:{datasets:[{data:ch.map(c=>({x:c.y,y:c.i,r:c.i*1.8})),backgroundColor:ch.map(c=>c.c+'55'),borderColor:ch.map(c=>c.c),borderWidth:1.5}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{backgroundColor:'#1a1815ee'}},scales:{x:{type:'linear',min:1620,max:2000,grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9}}},y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9}},min:0,max:12}}}});})();"""},
        {'slug':'the-great-emptying-how-collapsing-birth-rates-will-reshape-power-politics-and-people',
         'chart_id':'heroEmpty','headline':'No country has recovered from sub-1.5 fertility','sub':'The Great Emptying','color':'#c43425',
         'js':"""(()=>{const ctx=document.getElementById('heroEmpty');const yrs=[1960,1970,1980,1990,2000,2010,2020,2024];new Chart(ctx,{type:'line',data:{datasets:[{label:'S. Korea',data:_xy(yrs,[6.0,4.53,2.83,1.59,1.48,1.23,0.84,0.72]),borderColor:'#c43425',fill:false,tension:.3,pointRadius:2,borderWidth:2},{label:'China',data:_xy(yrs,[5.76,5.81,2.63,2.51,1.60,1.54,1.28,1.02]),borderColor:'#7c3aed',fill:false,tension:.3,pointRadius:2,borderWidth:2,borderDash:[5,3]},{label:'US',data:_xy(yrs,[3.65,2.48,1.84,2.08,2.06,1.93,1.64,1.62]),borderColor:'#2563eb',fill:false,tension:.3,pointRadius:2,borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'bottom',labels:{padding:8,usePointStyle:true,pointStyle:'circle',font:{size:9}}},tooltip:{backgroundColor:'#1a1815ee'}},scales:{x:{type:'linear',min:1960,max:2024,grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9}}},y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9}},min:0}}}});})();"""},
        {'slug':'europe-rearms-why-the-continent-that-invented-total-war-is-spending-800-billion-on-defence',
         'chart_id':'heroRearm','headline':'€800 billion: Europe rearming at unprecedented speed','sub':'Europe Rearms','color':'#2563eb',
         'js':"""(()=>{const ctx=document.getElementById('heroRearm');new Chart(ctx,{type:'bar',data:{labels:['Poland','Estonia','Lithuania','Latvia','Finland','UK','France','Germany','Italy','Spain'],datasets:[{data:[4.2,3.4,3.5,3.2,2.5,2.3,2.1,2.1,1.6,1.3],backgroundColor:function(c){return c.raw>3?'#c43425':c.raw>2?'#2563eb':'#8a847966'},borderRadius:3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{backgroundColor:'#1a1815ee',callbacks:{label:i=>i.raw+'% of GDP'}},annotation:{annotations:{nato:{type:'line',yMin:2,yMax:2,borderColor:'#8a8479',borderDash:[4,3],borderWidth:1}}}},scales:{x:{grid:{display:false},ticks:{color:'#8a8479',font:{size:8}}},y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>v+'%'},min:0}}}});})();"""},
        {'slug':'the-death-of-the-fourth-estate-what-the-collapse-of-newspapers-means-for-democracy-power-and-truth',
         'chart_id':'heroPress','headline':'US newspaper jobs down 80% since 1990','sub':'The Death of the Fourth Estate','color':'#7c3aed',
         'js':"""(()=>{const ctx=document.getElementById('heroPress');new Chart(ctx,{type:'line',data:{labels:['1990','1995','2000','2005','2010','2015','2020','2025'],datasets:[{data:[458,400,412,310,260,183,140,87],borderColor:'#7c3aed',backgroundColor:'#7c3aed18',fill:true,tension:.3,pointRadius:2,borderWidth:2.5}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{backgroundColor:'#1a1815ee',callbacks:{label:i=>i.raw+'k jobs'}}},scales:{x:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9}}},y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>v+'k'},min:0}}}});})();"""},
        {'slug':'the-rise-of-the-west-was-based-on-luck-that-has-run-out',
         'chart_id':'heroWest','headline':'Western dominance was a 200-year anomaly','sub':'The Rise of the West Was Based on Luck','color':'#b8751a',
         'js':"""(()=>{const ctx=document.getElementById('heroWest');const yrs=[1,1500,1700,1870,1950,2000,2025];new Chart(ctx,{type:'line',data:{datasets:[{label:'West',data:_xy(yrs,[12,18,24,42,52,42,30]),borderColor:'#2563eb',fill:false,tension:.35,pointRadius:2,borderWidth:2},{label:'China',data:_xy(yrs,[26,25,22,17,5,12,20]),borderColor:'#c43425',fill:false,tension:.35,pointRadius:2,borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'bottom',labels:{padding:8,usePointStyle:true,pointStyle:'circle',font:{size:9}}},tooltip:{backgroundColor:'#1a1815ee'}},scales:{x:{type:'linear',min:1,max:2025,grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9}}},y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>v+'%'},max:55}}}});})();"""},
        {'slug':'robotics-and-slavery',
         'chart_id':'heroRobot','headline':'Robot costs falling below human labour','sub':'Robotics and Slavery','color':'#b8751a',
         'js':"""(()=>{const ctx=document.getElementById('heroRobot');const yrs=[2010,2015,2018,2020,2022,2024,2027,2030];new Chart(ctx,{type:'line',data:{datasets:[{label:'Robot cost/hr',data:_xy(yrs,[15,10,7,5,3.5,2.5,1.5,1]),borderColor:'#b8751a',fill:false,tension:.3,pointRadius:2,borderWidth:2},{label:'Human min wage',data:_xy(yrs,[7.25,7.25,7.25,7.25,7.25,7.25,7.25,7.25]),borderColor:'#c43425',fill:false,tension:0,pointRadius:0,borderWidth:1.5,borderDash:[5,3]}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'bottom',labels:{padding:8,usePointStyle:true,pointStyle:'circle',font:{size:9}}},tooltip:{backgroundColor:'#1a1815ee'}},scales:{x:{type:'linear',min:2010,max:2030,grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9}}},y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>'$'+v},min:0}}}});})();"""},
        {'slug':'the-long-term-impact-of-covid-19',
         'chart_id':'heroCovid','headline':'COVID accelerated deglobalisation by a decade','sub':'The Long-Term Impact of COVID-19','color':'#c43425',
         'js':"""(()=>{const ctx=document.getElementById('heroCovid');new Chart(ctx,{type:'bar',data:{labels:['Trade','Remote Work','Digital Health','Automation','Debt/GDP','Inequality'],datasets:[{label:'Change (%)',data:[-15,300,180,40,25,18],backgroundColor:function(c){return c.raw<0?'#c43425':'#0d9a5a'},borderRadius:3}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{backgroundColor:'#1a1815ee',callbacks:{label:i=>(i.raw>0?'+':'')+i.raw+'%'}}},scales:{x:{grid:{display:false},ticks:{color:'#8a8479',font:{size:8}}},y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>(v>0?'+':'')+v+'%'}}}}});})();"""},
        {'slug':'history-is-written-by-the-winners-and-europeans-are-losing',
         'chart_id':'heroWinners','headline':'By 2100, Africa will have 4 billion people','sub':'History Is Written By The Winners','color':'#0d9a5a',
         'js':"""(()=>{const ctx=document.getElementById('heroWinners');new Chart(ctx,{type:'bar',data:{labels:['Europe','N. America','China','India','SE Asia','Africa'],datasets:[{label:'2025',data:[450,375,1410,1440,700,1500],backgroundColor:'#2563eb88',borderRadius:2},{label:'2100',data:[350,400,750,1500,850,4000],backgroundColor:'#0d9a5a88',borderRadius:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'bottom',labels:{padding:8,usePointStyle:true,pointStyle:'circle',font:{size:9}}},tooltip:{backgroundColor:'#1a1815ee',callbacks:{label:i=>i.dataset.label+': '+i.raw+'M'}}},scales:{x:{grid:{display:false},ticks:{color:'#8a8479',font:{size:8}}},y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>v>=1000?(v/1000)+'B':v+'M'}}}}});})();"""},
    ]

    # Build data stories HTML
    stories_html = ""
    stories_js = ""
    for ds in data_stories:
        stories_html += f"""      <a href="/articles/{ds['slug']}" class="ds-card">
        <div class="ds-chart"><canvas id="{ds['chart_id']}"></canvas></div>
        <div class="ds-text">
          <p class="ds-headline">{ds['headline']}</p>
          <p class="ds-sub">{ds['sub']} &rarr;</p>
        </div>
      </a>\n"""
        stories_js += ds['js'] + "\n"

    # ── Hero chart: West vs East GDP ──
    hero_chart_js = """
const _xy=(xs,ys)=>xs.map((x,i)=>({x:+x,y:ys[i]}));
(()=>{const ctx=document.getElementById('heroChart');
const yrs=[1,1000,1500,1600,1700,1820,1870,1913,1950,1973,2000,2025];
new Chart(ctx,{type:'line',data:{
datasets:[
{label:'West (Europe + US)',data:_xy(yrs,[12,12,18,22,24,30,42,50,52,48,42,30]),borderColor:'#2563eb',backgroundColor:'#2563eb18',fill:true,tension:.35,pointRadius:3,pointBackgroundColor:'#2563eb',borderWidth:2.5},
{label:'China',data:_xy(yrs,[26,22,25,29,22,33,17,9,5,5,12,20]),borderColor:'#c43425',backgroundColor:'#c4342518',fill:true,tension:.35,pointRadius:3,pointBackgroundColor:'#c43425',borderWidth:2.5},
{label:'India',data:_xy(yrs,[32,28,24,22,24,16,12,8,4,3,5,8]),borderColor:'#b8751a',backgroundColor:'#b8751a18',fill:true,tension:.35,pointRadius:3,pointBackgroundColor:'#b8751a',borderWidth:2.5}
]},options:{responsive:true,maintainAspectRatio:false,plugins:{
legend:{display:true,position:'bottom',labels:{padding:14,usePointStyle:true,pointStyle:'circle',font:{size:11}}},
tooltip:{backgroundColor:'#1a1815ee',titleFont:{size:12},bodyFont:{size:11},padding:8,cornerRadius:5,callbacks:{label:i=>i.dataset.label+': '+i.parsed.y+'% of world GDP'}}},
scales:{x:{type:'linear',min:1,max:2025,grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:10}}},
y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:10},callback:v=>v+'%'},title:{display:true,text:'Share of world GDP (%)',color:'#8a8479',font:{size:11}},max:55}}}});
})();"""

    # ── Section teasers ──
    section_chart_picks = {
        'Natural Resources': {'slug':'the-renewables-and-battery-revolution','chart_id':'secChart1',
         'js':"""(()=>{const ctx=document.getElementById('secChart1');new Chart(ctx,{type:'line',data:{labels:['2010','2012','2014','2016','2018','2020','2022','2024'],datasets:[{data:[1100,700,500,350,200,140,110,90],borderColor:'#0d9a5a',backgroundColor:'#0d9a5a18',fill:true,tension:.35,pointRadius:0,borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{enabled:false}},scales:{x:{display:false},y:{display:false}}}});})();"""},
        'Global Balance of Power': {'slug':'the-long-term-impact-of-covid-19','chart_id':'secChart2',
         'js':"""(()=>{const ctx=document.getElementById('secChart2');const yrs=[1870,1913,1950,1973,2000,2025];new Chart(ctx,{type:'line',data:{datasets:[{data:_xy(yrs,[55,58,52,48,42,30]),borderColor:'#2563eb',backgroundColor:'#2563eb18',fill:true,tension:.35,pointRadius:0,borderWidth:2},{data:_xy(yrs,[18,12,5,5,12,35]),borderColor:'#c43425',backgroundColor:'#c4342518',fill:true,tension:.35,pointRadius:0,borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{enabled:false}},scales:{x:{type:'linear',display:false},y:{display:false}}}});})();"""},
        'Jobs & Economy': {'slug':'robotics-and-slavery','chart_id':'secChart3',
         'js':"""(()=>{const ctx=document.getElementById('secChart3');const yrs=[2020,2022,2024,2026,2028,2030,2032,2035];new Chart(ctx,{type:'line',data:{datasets:[{data:_xy(yrs,[15,13,11,8,6,4,3,2]),borderColor:'#b8751a',backgroundColor:'#b8751a18',fill:true,tension:.35,pointRadius:0,borderWidth:2},{data:_xy(yrs,[50,30,18,12,8,5,3,2]),borderColor:'#7c3aed',backgroundColor:'#7c3aed18',fill:true,tension:.35,pointRadius:0,borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{enabled:false}},scales:{x:{type:'linear',display:false},y:{display:false}}}});})();"""},
        'Society': {'slug':'what-does-it-take-to-get-europeans-to-have-a-revolution','chart_id':'secChart4',
         'js':"""(()=>{const ctx=document.getElementById('secChart4');new Chart(ctx,{type:'bar',data:{labels:['1640s','1680s','1770s','1780s','1820s','1840s','1910s','1980s'],datasets:[{data:[1,1,1,2,3,8,4,6],backgroundColor:['#2563eb88','#2563eb88','#c4342588','#c4342588','#7c3aed88','#c4342588','#c4342588','#0d9a5a88'],borderRadius:2,borderSkipped:false}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{enabled:false}},scales:{x:{display:false},y:{display:false}}}});})();"""},
    }

    sec_chart_js = ""
    secs = ""
    for pn in sorted(PARTS.keys(), key=lambda p: PARTS[p]['order']):
        pi = PARTS[pn]
        se = [e for e in sorted_essays if e['part'] == pn]
        if not se: continue

        cards = ""
        for e in se[:3]:
            n_charts = len(all_charts.get(e['slug'], []))
            chart_badge = f'<span class="card-charts">{n_charts} charts</span>' if n_charts > 0 else ''
            cards += f"""      <a href="/articles/{html_mod.escape(e['slug'])}" class="card" data-section="{pi['slug']}">
        <div class="card-kicker" style="color:{pi['color']}">{pi['label']} {chart_badge}</div>
        <h3>{html_mod.escape(e['title'])}</h3>
        <p>{html_mod.escape(e['excerpt'][:160])}</p>
        <div class="card-meta">
          <span class="card-link" style="color:{pi['color']}">Read &rarr;</span>
          <span class="card-time">{e['reading_time']} min</span>
        </div>
      </a>\n"""

        sc = section_chart_picks.get(pn)
        chart_preview = ""
        if sc:
            sec_chart_js += sc['js'] + "\n"
            chart_preview = f'<div class="sec-chart-preview"><canvas id="{sc["chart_id"]}"></canvas></div>'

        secs += f"""  <div class="home-section">
    <div class="home-section-header">
      <div class="home-section-title-row">
        {chart_preview}
        <div>
          <h2><span class="home-section-icon">{pi['icon']}</span> <a href="/{pi['slug']}">{pi['label']}: {html_mod.escape(pn)}</a></h2>
          <p class="section-desc">{html_mod.escape(pi['desc'])}</p>
        </div>
      </div>
      <a href="/{pi['slug']}" class="home-section-all" style="color:{pi['color']}">All {len(se)} &rarr;</a>
    </div>
    <div class="cards">
{cards}    </div>
  </div>\n\n"""

    # JSON-LD for homepage
    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "History Future Now",
        "url": SITE_URL,
        "description": f"Data-driven analysis of the forces shaping our future. {total_articles} articles with {total_charts} interactive charts covering demographics, energy, geopolitics, and economics.",
        "author": {"@type": "Person", "name": "Tristan Fischer"},
        "publisher": {"@type": "Organization", "name": "History Future Now"},
        "inLanguage": "en-GB",
    }

    home_desc = f"Data-driven analysis of the forces shaping our future — demographics, technology, energy, geopolitics. {total_articles} articles with {total_charts} interactive charts."

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{make_head("History Future Now", home_desc, "/", json_ld=json_ld)}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
</head>
<body>

{make_nav()}

<section class="hero">
  <h1>History Future <em>Now</em></h1>
  <p class="hero-sub">Data-driven analysis of the structural forces &mdash; demographic, technological, economic &mdash;<br>that will shape the next century.</p>
  <hr class="hero-rule">
</section>

<div class="latest-wrap">
  <div class="latest-inner">
    <div class="latest-header">
      <h2 class="latest-title">Latest</h2>
      <span class="latest-pulse"></span>
    </div>
    <div class="latest-grid">
{latest_html}    </div>
  </div>
</div>
{new_section_html}
<div class="hero-chart-wrap">
  <div class="hero-chart-inner">
    <div class="hero-chart-label">The Big Picture</div>
    <h2 class="hero-chart-title">Who Runs the World Economy?</h2>
    <p class="hero-chart-desc">Western dominance was a 200-year anomaly. The world is reverting to the historical mean.</p>
    <div class="hero-chart-box"><canvas id="heroChart"></canvas></div>
    <p class="hero-chart-source">Source: Maddison Project, IMF &middot; <a href="/articles/the-rise-of-the-west-was-based-on-luck-that-has-run-out">Read the full analysis &rarr;</a></p>
  </div>
</div>

<div class="stats-bar">
  <div class="stats-inner">
    <div class="stat"><span class="stat-num">{total_articles}</span><span class="stat-label">Articles</span></div>
    <div class="stat"><span class="stat-num">{total_charts}</span><span class="stat-label">Interactive Charts</span></div>
    <div class="stat"><span class="stat-num">{total_hours}+</span><span class="stat-label">Hours of Analysis</span></div>
    <div class="stat"><span class="stat-num">500</span><span class="stat-label">Years of History</span></div>
  </div>
</div>

<div class="data-stories-wrap">
  <div class="data-stories-inner">
    <h2 class="ds-title">Data Stories</h2>
    <p class="ds-intro">Every article backed by interactive data visualisations. Explore the numbers behind history.</p>
    <div class="ds-scroll">
{stories_html}    </div>
  </div>
</div>

<div class="section-grid">

  <div class="featured-banner">
    <a href="/articles/the-great-emptying-how-collapsing-birth-rates-will-reshape-power-politics-and-people" class="featured-card">
      <div class="featured-badge">Featured &middot; 10 interactive charts</div>
      <h2>The Great Emptying: How Collapsing Birth Rates Will Reshape Power, Politics And People</h2>
      <p>No country in human history has recovered from a sustained fertility rate below 1.5. The forces that drive the decline &mdash; urbanisation, education, contraception &mdash; are things we call progress. The clock is already at zero.</p>
      <span class="featured-cta">Read the full analysis &rarr;</span>
    </a>
  </div>

{secs}
</div>

{make_footer()}
<script>
{hero_chart_js}
{stories_js}
{sec_chart_js}
</script>
</body>
</html>"""

def main():
    essays = []
    for md in sorted(ESSAYS_DIR.glob("*.md")):
        try:
            e = parse_essay(md)
            essays.append(e)
            print(f"  ✓ [{e['part']}] {e['title'][:60]}")
        except Exception as ex:
            print(f"  ✗ {md.name}: {ex}")

    print(f"\nParsed {len(essays)} essays")
    for pn in sorted(PARTS.keys(), key=lambda p: PARTS[p]['order']):
        c = sum(1 for e in essays if e['part'] == pn)
        print(f"  {PARTS[pn]['label']}: {pn} — {c} articles")

    # ── Classify articles as original vs new ──
    original_slugs = load_original_slugs()
    for e in essays:
        e['is_new'] = e['slug'] not in original_slugs

    # Resolve file mtime for new articles (needed for FIFO ordering)
    for e in essays:
        if e['is_new']:
            e['mtime'] = os.path.getmtime(e['filepath'])

    new_essays = sorted(
        [e for e in essays if e['is_new']],
        key=lambda x: x['mtime'],
        reverse=True
    )[:MAX_NEW_ARTICLES]
    new_slugs = {e['slug'] for e in new_essays}

    if new_essays:
        print(f"\n  🆕 {len(new_essays)} new articles:")
        for e in new_essays:
            print(f"     [{e['part']}] {e['title'][:60]}")
    else:
        print("\n  No new articles found.")

    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

    print("\nBuilding article pages...")
    for e in essays:
        (ARTICLES_DIR / f"{e['slug']}.html").write_text(build_article(e, essays), encoding='utf-8')
    print(f"  Built {len(essays)} article pages")

    print("Building section pages...")
    for pn, pi in PARTS.items():
        (OUTPUT_DIR / f"{pi['slug']}.html").write_text(build_section(pn, essays, new_slugs), encoding='utf-8')
    print(f"  Built {len(PARTS)} section pages")

    print("Building homepage...")
    (OUTPUT_DIR / "index.html").write_text(build_homepage(essays, new_essays), encoding='utf-8')
    print("  Built homepage")

    # ── SEO files ──
    print("Building SEO files...")
    all_charts = get_all_charts()

    # sitemap.xml
    urls = [f'  <url><loc>{SITE_URL}/</loc><priority>1.0</priority><changefreq>weekly</changefreq></url>']
    for pi in PARTS.values():
        urls.append(f'  <url><loc>{SITE_URL}/{pi["slug"]}</loc><priority>0.8</priority><changefreq>weekly</changefreq></url>')
    for e in essays:
        urls.append(f'  <url><loc>{SITE_URL}/articles/{e["slug"]}</loc><priority>0.7</priority><changefreq>monthly</changefreq></url>')
    sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>'''
    (OUTPUT_DIR / "sitemap.xml").write_text(sitemap, encoding='utf-8')

    # robots.txt
    robots = f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}/sitemap.xml

User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Claude-Web
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Applebot-Extended
Allow: /
"""
    (OUTPUT_DIR / "robots.txt").write_text(robots, encoding='utf-8')

    # llms.txt - structured content for AI crawlers
    llms_lines = [
        "# History Future Now",
        f"## {SITE_URL}",
        "",
        "Data-driven analysis of the structural forces — demographic, technological, economic — that will shape the next century.",
        f"Author: Tristan Fischer",
        f"Total articles: {len(essays)}",
        "",
        "## Sections",
    ]
    for pn in sorted(PARTS.keys(), key=lambda p: PARTS[p]['order']):
        pi = PARTS[pn]
        se = [e for e in essays if e['part'] == pn]
        llms_lines.append(f"### {pn} ({len(se)} articles)")
        llms_lines.append(f"- URL: {SITE_URL}/{pi['slug']}")
        llms_lines.append(f"- {pi['desc']}")
        llms_lines.append("")

    llms_lines.append("## Articles")
    llms_lines.append("")
    for e in essays:
        n_charts = len(all_charts.get(e['slug'], []))
        chart_note = f" [{n_charts} charts]" if n_charts else ""
        llms_lines.append(f"### {e['title']}{chart_note}")
        llms_lines.append(f"- URL: {SITE_URL}/articles/{e['slug']}")
        llms_lines.append(f"- Section: {e['part']}")
        llms_lines.append(f"- Reading time: {e['reading_time']} min")
        llms_lines.append(f"- {e['excerpt'][:200]}")
        llms_lines.append("")

    (OUTPUT_DIR / "llms.txt").write_text("\n".join(llms_lines), encoding='utf-8')
    print("  Built sitemap.xml, robots.txt, llms.txt")

    total = len(essays) + len(PARTS) + 1
    print(f"\n✅ Site built: {total} HTML pages")
    print(f"   Output: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
