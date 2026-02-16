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

# Feature flag: set to False to disable debate/discussion players across the site.
# Discussion scripts and audio files are preserved on disk — just not rendered.
ENABLE_DISCUSSIONS = False

def truncate_excerpt(text, max_len):
    """Truncate text to max_len characters, adding ellipsis if truncated."""
    if len(text) <= max_len:
        return html_mod.escape(text)
    return html_mod.escape(text[:max_len].rstrip()) + '&hellip;'

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

# Publication dates inferred from content temporal references (most recent year cited,
# current-event references, technology mentions, etc.). Author started writing in 2012.
# Format: slug -> "YYYY-MM-DD" (day is approximate — set to 1st or 15th of estimated month)
ARTICLE_DATES = {
    # 2010–2011
    "green-is-not-red-but-blue-environmentalism-and-the-mystery-of-right-wing-opposition": "2011-03-15",
    "the-north-african-threat-and-mediterranean-reunification": "2012-01-15",
    # 2012
    "keynes-and-hayek-are-both-dead-and-wrong": "2012-03-01",
    "the-immorality-of-climate-change-a-reflection-on-slavery-and-the-civil-war": "2012-04-15",
    "what-does-it-take-to-get-europeans-to-have-a-revolution": "2012-05-01",
    "where-are-all-the-jobs-going-lessons-from-the-first-industrial-revolution-and-150-years-of-pain": "2012-06-01",
    "why-do-we-need-the-military-securing-energy-supplies-and-trade-routes": "2012-07-01",
    "who-are-the-losers-in-the-energy-revolution": "2012-08-01",
    "why-the-nuclear-family-needs-to-die-in-order-for-us-to-live": "2012-09-01",
    "dont-confuse-what-is-legal-with-what-is-morally-right": "2012-10-01",
    "the-rise-of-the-west-was-based-on-luck-that-has-run-out": "2012-11-01",
    "roots-a-historical-understanding-of-climate-change-denial-creationism-and-slavery-1629-1775": "2012-12-01",
    "cassandra-time-to-give-up-on-predicting-climate-change": "2012-06-15",
    "rome-vs-persia-and-the-transfer-of-strategic-technologies-to-china": "2012-10-15",
    # 2013
    "what-the-history-of-immigration-teaches-us-about-europes-future": "2013-02-01",
    "why-is-bisexuality-becoming-mainstream": "2013-03-15",
    "emigration-colonies-of-the-mind-and-space": "2013-04-01",
    "crisis-or-an-explanation-on-the-origins-of-the-decline-of-the-west": "2013-05-01",
    "prisons-we-never-used-to-have-them-will-they-exist-in-the-future": "2013-06-01",
    "jobs-first-get-rid-of-expensive-westerners-second-get-rid-of-people-entirely": "2013-07-01",
    "a-lost-generation-why-the-personal-story-of-the-beautiful-yulia-is-also-our-story": "2013-08-01",
    "a-frozen-society-the-long-term-implications-of-nsas-secrets": "2013-09-01",
    "why-buying-cheap-imported-products-is-more-expensive-for-individuals-and-not-just-society": "2013-10-01",
    "debt-jubilees-and-hyperinflation-why-history-shows-that-this-might-be-the-way-forward-for-us-all": "2013-11-01",
    # 2014
    "are-europeans-fundamentally-racist": "2014-02-01",
    "what-happens-when-china-becomes-the-largest-economy-in-the-world": "2014-04-01",
    "why-land-deals-in-africa-could-make-the-great-irish-famine-a-minor-event": "2014-06-01",
    "is-democracy-the-opium-of-the-masses": "2014-08-01",
    "lets-talk-about-sex-does-the-separation-of-pleasure-and-procreation-mean-the-end-of-people": "2014-10-01",
    "china-has-many-of-the-characteristics-of-an-emerging-colonial-power-how-does-it-compare-historically": "2014-11-01",
    "why-god-needs-the-government-multiculturalism-vs-monotheism": "2014-12-01",
    # 2015
    "who-benefits-from-our-increased-social-fragmentation": "2015-03-01",
    "establishing-a-price-floor-for-energy": "2015-06-01",
    "clash-of-titans-how-the-warrior-ethos-and-judeo-christian-monotheism-shaped-the-soul-of-the-west": "2015-09-01",
    "why-china-could-invade-taiwan-and-get-away-with-it": "2015-11-01",
    # 2016–2017
    "dealing-with-the-consequences-of-climate-chance-inaction-the-impact-of-food": "2016-03-01",
    "hinkley-point-decision-is-really-about-china-and-brexit": "2016-09-01",
    "history-is-written-by-the-winners-and-europeans-are-losing": "2017-04-01",
    # 2018
    "the-renewables-and-battery-revolution": "2018-03-01",
    "big-european-electricity-utilities-are-facing-an-existential-crisis-how-did-this-happen-and-what-should-they-do": "2018-06-01",
    "the-wests-romance-with-free-trade-is-over-why": "2019-01-15",
    # 2020
    "the-long-term-impact-of-covid-19": "2020-04-01",
    "the-unintended-consequences-of-war-how-the-loss-of-young-men-transformed-womens-roles-in-society-and-ushered-in-the-welfare-state": "2020-06-01",
    # 2021–2022
    "the-great-emptying-how-collapsing-birth-rates-will-reshape-power-politics-and-people": "2021-09-01",
    "vertical-farming-the-electrical-convergence-power-transport-and-agriculture": "2022-01-15",
    "forging-peace-from-centuries-of-war-to-ukraines-future": "2022-04-01",
    "the-war-in-ukraine-escalation-miscalculation-and-the-path-to-peace": "2022-10-01",
    # 2023
    "the-perils-of-prediction-lessons-from-history-on-navigating-an-uncertain-future": "2023-06-01",
    # 2024
    "robotics-and-slavery": "2024-04-01",
    "the-150-year-life-how-radical-longevity-will-transform-our-world": "2024-06-01",
    "platform-technologies-how-foundational-technologies-of-the-past-show-us-the-foundational-technologies-of-the-future": "2024-03-01",
    "the-paradox-of-mass-migration-and-robots-in-the-age-of-automation": "2024-05-01",
    "the-empty-cradle-bargain-why-your-decision-not-to-have-children-is-everyones-problem": "2024-09-01",
    "the-gates-of-nations-how-every-civilisation-in-history-controlled-immigration-until-the-west-stopped": "2024-11-01",
    # 2025–2026
    "the-robot-bargain-how-ai-will-save-ageing-nations-from-the-immigration-trap": "2026-02-01",
    "the-silence-of-the-scribes-how-every-civilisation-that-controlled-speech-collapsed": "2026-02-05",
    "the-scramble-for-the-solar-system-why-the-next-colonial-race-has-already-begun": "2026-02-06",
    "who-guards-the-guards-bureaucracy-empire-and-the-eternal-struggle-to-control-the-state": "2026-02-07",
    "the-return-of-the-state-factory-why-nations-that-forgot-how-to-make-things-are-remembering": "2026-02-08",
    "the-death-of-the-fourth-estate-what-the-collapse-of-newspapers-means-for-democracy-power-and-truth": "2026-02-09",
    "europe-rearms-why-the-continent-that-invented-total-war-is-spending-800-billion-on-defence": "2026-02-10",
    "the-new-literacy": "2026-02-16",
    "the-builders-are-dying-how-the-populations-that-made-the-modern-world-are-disappearing": "2026-02-16",
}

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

def format_date_human(iso_date):
    """Convert 'YYYY-MM-DD' to a human-readable British date like '1 March 2012'."""
    if not iso_date:
        return ''
    from datetime import datetime
    dt = datetime.strptime(iso_date, '%Y-%m-%d')
    return dt.strftime('%-d %B %Y')

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

    audio_file = OUTPUT_DIR / "audio" / f"{slug}.mp3"
    has_audio = audio_file.exists()
    discussion_file = OUTPUT_DIR / "audio" / "discussions" / f"{slug}.mp3"
    has_discussion = discussion_file.exists() and ENABLE_DISCUSSIONS

    share_summary = meta.get('share_summary', '')

    # Prefer date from frontmatter, fall back to hardcoded mapping
    pub_date = meta.get('date', '') or ARTICLE_DATES.get(slug, '')

    return {
        'title': title, 'slug': slug, 'part': part, 'excerpt': excerpt,
        'body_html': body_html, 'reading_time': reading_time,
        'pull_quote': pull_quote, 'filepath': filepath,
        'has_audio': has_audio, 'has_discussion': has_discussion,
        'share_summary': share_summary,
        'pub_date': pub_date,
    }

def get_related(essay, all_essays, n=3):
    same = [e for e in all_essays if e['part'] == essay['part'] and e['slug'] != essay['slug']]
    random.seed(hash(essay['slug']))
    return random.sample(same, min(n, len(same)))

IMAGES_DIR = OUTPUT_DIR / "images" / "articles"

def get_hero_image(slug):
    """Check if a hero image exists for this article and return its path."""
    for ext in ['png', 'webp', 'jpg']:
        img_path = IMAGES_DIR / slug / f"hero.{ext}"
        if img_path.exists():
            return f"/images/articles/{slug}/hero.{ext}"
    return None

def make_head(title, desc="", og_url="", part_color=None, json_ld=None, og_image=None, pub_date=None):
    te = html_mod.escape(title)
    de = html_mod.escape(desc[:300]) if desc else ""
    tc = part_color or "#c43425"
    canonical = f'<link rel="canonical" href="{SITE_URL}{og_url}">' if og_url else ""
    og = f'<meta property="og:url" content="{SITE_URL}{og_url}">' if og_url else ""
    og_img = f'<meta property="og:image" content="{SITE_URL}{og_image}">\n<meta name="twitter:image" content="{SITE_URL}{og_image}">' if og_image else ""
    og_date = f'\n<meta property="article:published_time" content="{pub_date}">' if pub_date else ""
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
<meta property="article:author" content="Tristan Fischer">{og_date}
{og}
{og_img}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{te}">
<meta name="twitter:description" content="{de}">
<meta name="theme-color" content="{tc}">
<meta name="robots" content="index, follow">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="alternate" type="application/rss+xml" title="History Future Now" href="/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Source+Sans+3:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-6PS9DYS2PZ"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-6PS9DYS2PZ');</script>
{ld}'''

def make_nav(active=None):
    secs = [("Home","/",None),("Resources","/natural-resources","Natural Resources"),
            ("Power","/balance-of-power","Global Balance of Power"),
            ("Economy","/jobs-economy","Jobs & Economy"),("Society","/society","Society"),
            ("Listen","/listen",None),("Library","/library",None)]
    li = ""
    for label, href, part in secs:
        ac = ' class="active"' if (part and part == active) or (label == active) else ''
        li += f'      <li><a href="{href}"{ac}>{label}</a></li>\n'
    return f'''<nav class="site-nav">
  <div class="nav-inner">
    <div class="nav-top-row">
      <a class="nav-logo" href="/">History Future <span>Now</span></a>
      <div class="nav-right">
        <button class="nav-search-btn" id="searchOpen" aria-label="Search articles">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        </button>
        <button class="nav-toggle" aria-label="Menu">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
        </button>
      </div>
    </div>
    <ul class="nav-links">
{li}    </ul>
  </div>
</nav>'''

def make_search_overlay():
    """Generate the full-screen search overlay HTML."""
    return '''<div class="search-overlay" id="searchOverlay" role="dialog" aria-label="Search articles" aria-hidden="true">
  <div class="search-overlay-inner">
    <div class="search-header">
      <div class="search-input-wrap">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
        <input type="text" class="search-input" id="searchInput" placeholder="Search articles..." autocomplete="off" autofocus>
      </div>
      <button class="search-close" id="searchClose" aria-label="Close search">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
      </button>
    </div>
    <div class="search-results" id="searchResults">
      <div class="search-hint">Type to search across all articles</div>
    </div>
  </div>
</div>'''

def make_breadcrumbs(items):
    """Generate breadcrumb navigation HTML.

    @param items: list of (label, href) tuples. Last item's href should be None (current page).
    @returns: breadcrumb nav HTML string.
    """
    crumbs = []
    for i, (label, href) in enumerate(items):
        if href:
            crumbs.append(f'<a href="{href}">{html_mod.escape(label)}</a>')
        else:
            crumbs.append(f'<span class="breadcrumb-current">{html_mod.escape(label)}</span>')
    sep = ' <span class="breadcrumb-sep">/</span> '
    return f'<nav class="breadcrumbs" aria-label="Breadcrumb">{sep.join(crumbs)}</nav>'

def make_queue_bar():
    """Persistent bottom audio queue bar — appears on every page."""
    return '''
<div class="queue-bar" id="queueBar">
  <div class="queue-bar-inner">
    <button class="q-nav-btn" id="queuePrev" aria-label="Previous" title="Previous">
      <svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>
    </button>
    <button class="q-play-btn" id="queuePlayBtn" aria-label="Play">
      <svg class="q-icon-play" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
      <svg class="q-icon-pause" viewBox="0 0 24 24" fill="currentColor" style="display:none"><path d="M6 4h4v16H6zm8 0h4v16h-4z"/></svg>
    </button>
    <button class="q-nav-btn" id="queueNext" aria-label="Next" title="Next">
      <svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>
    </button>
    <div class="q-track-info">
      <div class="q-track-title" id="queueTitle">No track loaded</div>
      <div class="q-track-section" id="queueSection"></div>
    </div>
    <div class="q-progress-wrap" id="queueProgressWrap">
      <div class="q-progress-track"><div class="q-progress-bar" id="queueProgressBar"></div></div>
      <div class="scrub-thumb" id="queueThumb"></div>
    </div>
    <div class="q-time" id="queueTime">0:00</div>
    <div class="q-speed" id="queueSpeed" title="Playback speed">1&times;</div>
    <button class="q-toggle-btn" id="queueToggle" aria-label="Queue" title="View queue">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>
      <span class="q-badge" id="queueCount">0</span>
    </button>
    <button class="q-bar-close" id="queueBarClose" aria-label="Close queue" title="Close queue">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
    </button>
  </div>
</div>
<div class="queue-panel" id="queuePanel">
  <div class="q-panel-header">
    <span class="q-panel-title">Queue</span>
    <div class="q-panel-actions">
      <button class="q-panel-btn" id="queueClear">Clear all</button>
      <button class="q-panel-close" id="queuePanelClose" aria-label="Close">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
      </button>
    </div>
  </div>
  <div class="q-list" id="queueList"></div>
</div>'''


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
      <li><a href="/listen">Listen</a></li>
      <li><a href="/library">Library</a></li>
    </ul>
    <p>&copy; 2012&ndash;2026 History Future Now &middot; Tristan Fischer</p>
  </div>
</footer>
''' + make_queue_bar() + '''
<script src="/js/nav.js"></script>
<script src="/js/search.js"></script>
<script src="/js/queue.js"></script>'''

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
    """Inline JavaScript for the article audio player (narration + discussion)."""
    return '''<script>
(function(){
  function initPlayer(audioId,btnId,barId,wrapId,timeId,speedId,thumbId){
    var audio=document.getElementById(audioId);
    if(!audio)return;
    var btn=document.getElementById(btnId);
    var bar=document.getElementById(barId);
    var wrap=document.getElementById(wrapId);
    var timeEl=document.getElementById(timeId);
    var speedEl=document.getElementById(speedId);
    var thumb=document.getElementById(thumbId);
    if(!btn)return;
    var iconPlay=btn.querySelector('.audio-icon-play');
    var iconPause=btn.querySelector('.audio-icon-pause');
    var speeds=[1,1.25,1.5,1.75,2];
    var si=0;
    var dragging=false;

    function fmt(s){
      if(isNaN(s))return'0:00';
      var m=Math.floor(s/60);
      var sec=Math.floor(s%60);
      return m+':'+(sec<10?'0':'')+sec;
    }

    function seekTo(e){
      if(!audio.duration)return;
      var rect=wrap.getBoundingClientRect();
      var pct=Math.max(0,Math.min(1,(e.clientX-rect.left)/rect.width));
      audio.currentTime=pct*audio.duration;
      updateBar(pct);
    }

    function seekToTouch(e){
      if(!audio.duration)return;
      var rect=wrap.getBoundingClientRect();
      var touch=e.touches[0];
      var pct=Math.max(0,Math.min(1,(touch.clientX-rect.left)/rect.width));
      audio.currentTime=pct*audio.duration;
      updateBar(pct);
    }

    function updateBar(pct){
      var p=(pct*100)+'%';
      bar.style.width=p;
      if(thumb)thumb.style.left=p;
    }

    btn.onclick=function(){
      if(audio.paused){audio.play();iconPlay.style.display='none';iconPause.style.display='block';}
      else{audio.pause();iconPlay.style.display='block';iconPause.style.display='none';}
    };

    audio.ontimeupdate=function(){
      if(dragging)return;
      if(audio.duration){
        var pct=audio.currentTime/audio.duration;
        updateBar(pct);
        timeEl.textContent=fmt(audio.currentTime)+' / '+fmt(audio.duration);
      }
    };

    audio.onended=function(){
      iconPlay.style.display='block';iconPause.style.display='none';
      updateBar(0);
    };

    wrap.addEventListener('mousedown',function(e){
      e.preventDefault();
      dragging=true;
      wrap.classList.add('scrubbing');
      seekTo(e);
      function onMove(ev){seekTo(ev);}
      function onUp(){
        dragging=false;
        wrap.classList.remove('scrubbing');
        document.removeEventListener('mousemove',onMove);
        document.removeEventListener('mouseup',onUp);
      }
      document.addEventListener('mousemove',onMove);
      document.addEventListener('mouseup',onUp);
    });

    wrap.addEventListener('touchstart',function(e){
      e.preventDefault();
      dragging=true;
      wrap.classList.add('scrubbing');
      seekToTouch(e);
      function onTouchMove(ev){ev.preventDefault();seekToTouch(ev);}
      function onTouchEnd(){
        dragging=false;
        wrap.classList.remove('scrubbing');
        document.removeEventListener('touchmove',onTouchMove);
        document.removeEventListener('touchend',onTouchEnd);
      }
      document.addEventListener('touchmove',onTouchMove,{passive:false});
      document.addEventListener('touchend',onTouchEnd);
    });

    if(speedEl){
      speedEl.onclick=function(){
        si=(si+1)%speeds.length;
        audio.playbackRate=speeds[si];
        speedEl.textContent=speeds[si]+'\\u00d7';
      };
    }
  }

  initPlayer('audioElement','audioPlayBtn','audioProgressBar','audioProgressWrap','audioTime','audioSpeed','audioThumb');
  if(document.getElementById('discussionElement')){initPlayer('discussionElement','discussionPlayBtn','discussionProgressBar','discussionProgressWrap','discussionTime','discussionSpeed','discussionThumb');}
})();
</script>'''

ALL_CHARTS = get_all_charts()

# SVG icons for share buttons (inline, no external deps)
_SHARE_ICONS = {
    'x': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>',
    'linkedin': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>',
    'whatsapp': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>',
    'email': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>',
    'copy': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
}

def make_share_bar(essay, position='top'):
    """Generate share button bar HTML for an article."""
    url = f"{SITE_URL}/articles/{essay['slug']}"
    title = html_mod.escape(essay['title'])
    text = html_mod.escape(essay.get('share_summary', '') or essay['excerpt'][:140])
    pos_class = 'share-bar-top' if position == 'top' else 'share-bar-bottom'

    buttons = ''
    for platform, icon in _SHARE_ICONS.items():
        label = {'x': 'Share on X', 'linkedin': 'Share on LinkedIn', 'whatsapp': 'Share on WhatsApp', 'email': 'Share via email', 'copy': 'Copy link'}[platform]
        buttons += f'<button class="share-btn" data-share="{platform}" aria-label="{label}" title="{label}">{icon}</button>\n'

    return f'''<div class="share-bar {pos_class}" data-share-url="{url}" data-share-title="{title}" data-share-text="{text}">
    <span class="share-label">Share</span>
    {buttons}
  </div>'''

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
    
    download_icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>'
    image_icon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>'
    return f'''
    <div class="chart-figure" data-chart-title="{html_mod.escape(chart['title'])}" data-chart-source="Source: {html_mod.escape(chart['source'])}">
      <div class="chart-share-bar">
        <button class="share-btn chart-share-btn" data-chart-share="download" aria-label="Download chart as image" title="Download image">{download_icon}</button>
        <button class="share-btn chart-share-btn" data-chart-share="copy-image" aria-label="Copy chart as image" title="Copy image">{image_icon}</button>
        <button class="share-btn chart-share-btn" data-chart-share="x" aria-label="Share chart on X" title="Share on X">{_SHARE_ICONS['x']}</button>
        <button class="share-btn chart-share-btn" data-chart-share="linkedin" aria-label="Share chart on LinkedIn" title="Share on LinkedIn">{_SHARE_ICONS['linkedin']}</button>
        <button class="share-btn chart-share-btn" data-chart-share="whatsapp" aria-label="Share chart on WhatsApp" title="Share on WhatsApp">{_SHARE_ICONS['whatsapp']}</button>
      </div>
      <div class="chart-figure-label">Figure {chart['figure_num']}</div>
      <h4>{html_mod.escape(chart['title'])}</h4>
      <p class="chart-desc">{html_mod.escape(chart['desc'])}</p>
      <div class="chart-area{size_class}"{inline_style}><canvas id="{chart['id']}"></canvas></div>
      <p class="chart-source">Source: {html_mod.escape(chart['source'])}</p>
    </div>
'''

def _find_article_paragraphs(html):
    """Find positions of </p> tags that are article content, not inside chart containers.

    Returns a list of end positions (after '</p>') for each article paragraph.
    """
    positions = []
    depth = 0
    i = 0
    while i < len(html):
        if html[i:i+len('<div class="chart-figure')] == '<div class="chart-figure':
            depth += 1
            i += 1
        elif depth > 0 and html[i:i+6] == '</div>':
            depth -= 1
            i += 6
        elif depth == 0 and html[i:i+4] == '</p>':
            positions.append(i + 4)
            i += 4
        else:
            i += 1
    return positions


def inject_charts_into_body(body_html, charts):
    """Insert chart figures at appropriate positions in the article body.

    Uses a two-pass approach: first pass inserts placeholder tokens, second pass
    replaces them with actual chart HTML. This avoids position drift when earlier
    insertions shift paragraph counts for later ones.
    """
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

    # Sort position keys so that heading-based insertions come after paragraph-based
    # ones (headings don't shift paragraph counts, but we process para-based first
    # to place placeholders before any HTML is modified).
    # Use placeholders to avoid position drift between insertions.
    placeholder_map = {}
    placeholder_insertions = []  # (insert_pos, placeholder_token)

    for pos_key, pos_charts in positioned.items():
        token = f'<!--CHART_PLACEHOLDER_{id(pos_charts)}-->'
        placeholder_map[token] = '\n'.join(make_chart_html(ch) for ch in pos_charts)

        if pos_key.startswith('after_heading:'):
            heading_text = pos_key.split(':', 1)[1].strip().lower()
            pattern = re.compile(r'(</h[23]>)', re.IGNORECASE)
            matches = list(pattern.finditer(body_html))
            inserted = False
            for m in matches:
                start = body_html.rfind('<h', 0, m.start())
                if start >= 0:
                    heading_content = re.sub(r'<[^>]+>', '', body_html[start:m.end()]).strip().lower()
                    if heading_text in heading_content:
                        placeholder_insertions.append((m.end(), token))
                        inserted = True
                        break
            if not inserted:
                para_positions = _find_article_paragraphs(body_html)
                if len(para_positions) >= 3:
                    placeholder_insertions.append((para_positions[2], token))
                else:
                    end_charts.extend(pos_charts)
                    del placeholder_map[token]

        elif pos_key.startswith('after_para_'):
            try:
                para_num = int(pos_key.split('_')[-1])
            except:
                para_num = 3
            para_positions = _find_article_paragraphs(body_html)
            if para_num <= len(para_positions):
                placeholder_insertions.append((para_positions[para_num - 1], token))
            else:
                end_charts.extend(pos_charts)
                del placeholder_map[token]

    # Insert placeholders in reverse order so earlier positions aren't shifted
    placeholder_insertions.sort(key=lambda x: x[0], reverse=True)
    for insert_pos, token in placeholder_insertions:
        body_html = body_html[:insert_pos] + '\n' + token + body_html[insert_pos:]

    # Replace placeholders with actual chart HTML
    for token, chart_html in placeholder_map.items():
        body_html = body_html.replace(token, chart_html)

    # Append remaining charts at end
    if end_charts:
        end_block = '\n'.join(make_chart_html(ch) for ch in end_charts)
        body_html += '\n' + end_block

    # Build the combined JS for all charts
    all_js = '\n'.join(ch['js'] for ch in charts)
    script_block = f'''
<script src="/js/chart.umd.min.js"></script>
<script src="/js/chartjs-plugin-annotation.min.js"></script>
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
            audio_tag = ' <span class="related-audio">Audio</span>' if (r.get('has_audio') or r.get('has_discussion')) else ''
            cards += f'''      <a href="/articles/{html_mod.escape(r['slug'])}" class="related-card">
        <span class="related-kicker" style="color:{rp['color']}">{rp['label']}</span>
        <span class="related-title">{html_mod.escape(r['title'])}</span>
        <span class="related-time">{r['reading_time']} min read{audio_tag}</span>
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
        section_label = f"{pi['label']} · {essay['part']}"
        audio_player = f'''
  <div class="audio-player" id="audioPlayer">
    <div class="audio-player-inner">
      <button class="audio-play-btn" id="audioPlayBtn" aria-label="Play article narration">
        <svg class="audio-icon-play" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        <svg class="audio-icon-pause" viewBox="0 0 24 24" fill="currentColor" style="display:none"><path d="M6 4h4v16H6zm8 0h4v16h-4z"/></svg>
      </button>
      <div class="audio-info">
        <div class="audio-label">Listen to this article</div>
        <div class="audio-meta">{est_listen} min</div>
      </div>
      <div class="audio-progress-wrap" id="audioProgressWrap">
        <div class="audio-progress-track"><div class="audio-progress-bar" id="audioProgressBar"></div></div>
        <div class="scrub-thumb" id="audioThumb"></div>
      </div>
      <div class="audio-time" id="audioTime">0:00</div>
      <div class="audio-speed" id="audioSpeed" title="Playback speed">1&times;</div>
      <button class="q-add-btn-light" data-queue-slug="{html_mod.escape(essay['slug'])}" data-queue-title="{html_mod.escape(essay['title'])}" data-queue-section="{html_mod.escape(section_label)}" data-queue-color="{pi['color']}" data-queue-url="/audio/{html_mod.escape(essay['slug'])}.mp3" aria-label="Add to queue">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M12 5v14M5 12h14"/></svg>
        <span class="q-add-label">Add to Queue</span>
      </button>
    </div>
    <audio id="audioElement" preload="none" src="/audio/{html_mod.escape(essay['slug'])}.mp3"></audio>
  </div>'''

    # Discussion player (if discussion audio file exists and feature is enabled)
    discussion_file = OUTPUT_DIR / "audio" / "discussions" / f"{essay['slug']}.mp3"
    has_discussion = discussion_file.exists() and ENABLE_DISCUSSIONS
    discussion_player = ''
    if has_discussion:
        discussion_section_label = f"{pi['label']} · {essay['part']}"
        discussion_player = f'''
  <div class="discussion-player" id="discussionPlayer">
    <div class="discussion-player-inner">
      <button class="discussion-play-btn" id="discussionPlayBtn" aria-label="Play article discussion">
        <svg class="audio-icon-play" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        <svg class="audio-icon-pause" viewBox="0 0 24 24" fill="currentColor" style="display:none"><path d="M6 4h4v16H6zm8 0h4v16h-4z"/></svg>
      </button>
      <div class="discussion-info">
        <div class="discussion-label">Listen to the debate about this</div>
      </div>
      <div class="discussion-progress-wrap" id="discussionProgressWrap">
        <div class="discussion-progress-track"><div class="discussion-progress-bar" id="discussionProgressBar"></div></div>
        <div class="scrub-thumb" id="discussionThumb"></div>
      </div>
      <div class="discussion-time" id="discussionTime">0:00</div>
      <div class="discussion-speed" id="discussionSpeed" title="Playback speed">1&times;</div>
      <button class="q-add-btn-light" data-queue-slug="discussion-{html_mod.escape(essay['slug'])}" data-queue-title="Discussion: {html_mod.escape(essay['title'])}" data-queue-section="{html_mod.escape(discussion_section_label)}" data-queue-color="{pi['color']}" data-queue-url="/audio/discussions/{html_mod.escape(essay['slug'])}.mp3" aria-label="Add discussion to queue">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M12 5v14M5 12h14"/></svg>
        <span class="q-add-label">Add to Queue</span>
      </button>
    </div>
    <audio id="discussionElement" preload="none" src="/audio/discussions/{html_mod.escape(essay['slug'])}.mp3"></audio>
  </div>'''

    # Hero image injection
    hero_img = get_hero_image(essay['slug'])

    # JSON-LD structured data for article
    json_ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": essay['title'],
        "description": essay['excerpt'][:300],
        "author": {"@type": "Person", "name": "Tristan Fischer", "url": SITE_URL},
        "publisher": {"@type": "Organization", "name": "History Future Now", "url": SITE_URL},
        "url": f"{SITE_URL}/articles/{essay['slug']}",
        "mainEntityOfPage": f"{SITE_URL}/articles/{essay['slug']}",
        "articleSection": essay['part'],
        "inLanguage": "en-GB",
    }
    if essay.get('pub_date'):
        json_ld["datePublished"] = essay['pub_date']
        json_ld["dateModified"] = essay['pub_date']
    if hero_img:
        json_ld["image"] = f"{SITE_URL}{hero_img}"

    # Breadcrumbs: Home / Section / Article title (truncated)
    truncated_title = essay['title'] if len(essay['title']) <= 50 else essay['title'][:47] + '...'
    breadcrumbs = make_breadcrumbs([
        ('Home', '/'),
        (essay['part'], f'/{pi["slug"]}'),
        (truncated_title, None),
    ])
    hero_img_html = ''
    if hero_img:
        hero_img_html = f'''
  <div class="article-hero-wrap">
    <img src="{hero_img}" alt="Editorial illustration for {html_mod.escape(essay['title'])}" class="article-hero-img" loading="lazy" width="1200" height="675">
  </div>'''

    # Split body at References heading so we can insert the discussion + share CTA before it
    import re
    refs_pattern = re.compile(r'(<h2[^>]*>\s*References\s*</h2>)', re.IGNORECASE)
    refs_match = refs_pattern.search(body)
    if refs_match:
        body_before_refs = body[:refs_match.start()]
        body_refs = body[refs_match.start():]
    else:
        body_before_refs = body
        body_refs = ''

    # Build end-of-article CTA: discussion player + share prompt
    share_url = f"{SITE_URL}/articles/{essay['slug']}"
    share_title = html_mod.escape(essay['title'])
    share_text = html_mod.escape(essay.get('share_summary', '') or essay['excerpt'][:140])
    share_cta = f'''
  <div class="article-end-cta" data-share-url="{share_url}" data-share-title="{share_title}" data-share-text="{share_text}">
    <p class="cta-prompt">If this changed how you think, share it with someone who should read it.</p>
    <div class="cta-share-buttons">
      <button class="share-btn" data-share="x" aria-label="Share on X" title="Share on X">{_SHARE_ICONS['x']}</button>
      <button class="share-btn" data-share="linkedin" aria-label="Share on LinkedIn" title="Share on LinkedIn">{_SHARE_ICONS['linkedin']}</button>
      <button class="share-btn" data-share="whatsapp" aria-label="Share on WhatsApp" title="Share on WhatsApp">{_SHARE_ICONS['whatsapp']}</button>
      <button class="share-btn" data-share="email" aria-label="Share via email" title="Share via email">{_SHARE_ICONS['email']}</button>
      <button class="share-btn" data-share="copy" aria-label="Copy link" title="Copy link">{_SHARE_ICONS['copy']}</button>
    </div>
  </div>'''

    end_of_article_cta = discussion_player + share_cta

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{make_head(f"{essay['title']} — History Future Now", essay['excerpt'], f"/articles/{essay['slug']}", pi['color'], json_ld, og_image=hero_img, pub_date=essay.get('pub_date'))}
</head>
<body>

{make_nav(essay['part'])}
<div class="back-bar" id="backBar" data-section-href="/{pi['slug']}" data-section-label="{html_mod.escape(essay['part'])}" data-section-color="{pi['color']}">
  <div class="back-bar-inner">
    <a href="/{pi['slug']}" style="color:{pi['color']}">&larr; {html_mod.escape(essay['part'])}</a>
  </div>
</div>

{make_search_overlay()}

<article class="page-container">
  {breadcrumbs}
  <header class="article-header">
    <div class="article-kicker" style="color:{pi['color']}">{pi['label']} &middot; {html_mod.escape(essay['part'])}</div>
    <h1>{te}</h1>
    <div class="article-meta">
      <span class="article-reading-time">{essay['reading_time']} min read</span>
      {f'<span class="meta-sep">&middot;</span><time class="article-date" datetime="{essay["pub_date"]}">{format_date_human(essay["pub_date"])}</time>' if essay.get('pub_date') else ''}
    </div>{chart_badge}
  </header>{hero_img_html}
{audio_player}
  {make_share_bar(essay, 'top')}
  <div class="article-body">
    {body_before_refs}
  </div>
{end_of_article_cta}
  <div class="article-references">
    {body_refs}
  </div>
  {make_share_bar(essay, 'bottom')}

  <div class="article-footer">
    <a href="/{pi['slug']}" class="back-to-section" style="color:{pi['color']}">&larr; All {html_mod.escape(essay['part'])} articles</a>
    <a href="#" class="back-to-top" onclick="window.scrollTo({{top:0,behavior:'smooth'}});return false;">&uarr; Back to top</a>
  </div>
{rel_html}
</article>

{make_footer()}
{chart_script}
{make_audio_player_script() if (has_audio or has_discussion) else ''}
<script src="/js/share.js"></script>
</body>
</html>'''

def _load_section_intros_cache():
    """Load the cached section editorial intros (generated by generate_section_intros.py)."""
    cache_path = Path(__file__).parent / "section_intros_cache.json"
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}

_SECTION_INTROS_CACHE = None

def _get_section_intro(part_name):
    """Get the editorial intro HTML and chart IDs for a section, if available."""
    global _SECTION_INTROS_CACHE
    if _SECTION_INTROS_CACHE is None:
        _SECTION_INTROS_CACHE = _load_section_intros_cache()
    section_data = _SECTION_INTROS_CACHE.get("sections", {}).get(part_name, {})
    return section_data.get("html", ""), section_data.get("chart_ids", [])

def _build_section_editorial(part_name, pi):
    """Build the editorial intro HTML block for a section page, including charts."""
    intro_html, chart_ids = _get_section_intro(part_name)
    if not intro_html:
        return "", ""

    # Build chart figures for the editorial
    chart_figures = ""
    chart_js_parts = []
    for chart_id in chart_ids:
        # Find the chart definition across all articles
        for slug_charts in ALL_CHARTS.values():
            for ch in slug_charts:
                if ch['id'] == chart_id:
                    chart_figures += f'''
    <figure class="section-editorial-chart">
      <h4>{html_mod.escape(ch['title'])}</h4>
      <p class="chart-desc">{html_mod.escape(ch.get('desc', ''))}</p>
      <div class="chart-area"><canvas id="{ch['id']}"></canvas></div>
      <p class="chart-source">Source: {html_mod.escape(ch.get('source', ''))}</p>
    </figure>'''
                    chart_js_parts.append(ch['js'])
                    break

    editorial_block = f'''
<div class="section-editorial" style="--section-color:{pi['color']}">
  <div class="section-editorial-inner">
    <div class="section-editorial-prose">
{intro_html}
    </div>
{chart_figures}
  </div>
</div>'''

    # Build chart script block
    chart_script = ""
    if chart_js_parts:
        all_js = "\n".join(chart_js_parts)
        chart_script = f'''
<script src="/js/chart.umd.min.js"></script>
<script src="/js/chartjs-plugin-annotation.min.js"></script>
<script>
{CHART_COLORS}
const _xy=(xs,ys)=>xs.map((x,i)=>({{x:+x,y:ys[i]}}));
{all_js}
</script>'''

    return editorial_block, chart_script


def build_section(part_name, essays, new_slugs=None):
    if new_slugs is None:
        new_slugs = set()
    pi = PARTS[part_name]
    se = [e for e in essays if e['part'] == part_name]

    # Build editorial intro (from cached LLM-generated content)
    editorial_block, editorial_chart_script = _build_section_editorial(part_name, pi)

    # Build newspaper-style article list with thumbnails
    article_items = ""
    for e in se:
        chart_count = len(ALL_CHARTS.get(e['slug'], []))
        chart_tag = f'<span>{chart_count} chart{"s" if chart_count != 1 else ""}</span>' if chart_count > 0 else ''
        audio_tag = '<span>Audio</span>' if (e.get('has_audio') or e.get('has_discussion')) else ''
        new_badge = '<span class="card-new-badge">New</span> ' if e['slug'] in new_slugs else ''

        hero_img = get_hero_image(e['slug'])
        thumb_html = f'<img src="{hero_img}" alt="" class="section-article-thumb" loading="lazy" width="160" height="110">' if hero_img else ''

        article_items += f'''    <a href="/articles/{html_mod.escape(e['slug'])}" class="section-article-item">
      {thumb_html}
      <div class="section-article-text">
        <h3>{new_badge}{html_mod.escape(e['title'])}</h3>
        <p>{truncate_excerpt(e['excerpt'], 180)}</p>
        <div class="section-article-meta">
          <span>{e['reading_time']} min read</span>
          {chart_tag}
          {audio_tag}
        </div>
      </div>
    </a>\n'''

    breadcrumbs = make_breadcrumbs([
        ('Home', '/'),
        (f'{pi["label"]}: {part_name}', None),
    ])

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{make_head(f"{pi['label']}: {part_name} — History Future Now", pi['desc'], f"/{pi['slug']}", pi['color'])}
</head>
<body>

{make_nav(part_name)}

{make_search_overlay()}

<section class="section-hero" style="--section-color:{pi['color']};--section-soft:{pi['color_soft']}">
  <div class="section-hero-inner">
    {breadcrumbs}
    <span class="section-icon">{pi['icon']}</span>
    <h1>{pi['label']}: {html_mod.escape(part_name)}</h1>
    <p class="section-hero-desc">{html_mod.escape(pi['desc'])}</p>
    <div class="section-hero-count">{len(se)} articles</div>
  </div>
</section>

{editorial_block}

<div class="section-article-list">
{article_items}</div>

{make_footer()}
{editorial_chart_script}
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
        audio_badge = '<span class="latest-badge latest-audio-badge">Audio</span>' if (e.get('has_audio') or e.get('has_discussion')) else ''
        size_class = "latest-hero" if i == 0 else "latest-secondary"
        new_tag = '<span class="latest-new">New</span> ' if e.get('is_new') else ''

        hero_img = get_hero_image(e['slug'])
        img_html = f'<img src="{hero_img}" alt="" class="latest-card-img" loading="lazy">' if hero_img else ''

        latest_html += f"""      <a href="/articles/{html_mod.escape(e['slug'])}" class="latest-card {size_class}" style="--accent:{pi['color']}">
        {img_html}
        <div class="latest-kicker">{new_tag}{pi['label']} &middot; {html_mod.escape(e['part'])} {badge} {audio_badge}</div>
        <h3>{html_mod.escape(e['title'])}</h3>
        <p>{truncate_excerpt(e['excerpt'], 200)}</p>
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
                audio_badge = ' <span class="card-audio">&middot; Audio</span>' if (e.get('has_audio') or e.get('has_discussion')) else ''
                new_cards_html += f"""    <a href="/articles/{html_mod.escape(e['slug'])}" class="card" data-section="{pi['slug']}">
      <div class="card-kicker" style="color:{pi['color']}"><span class="card-new-badge">New</span> {pi['label']}</div>
      <h3>{html_mod.escape(e['title'])}</h3>
      <p>{truncate_excerpt(e['excerpt'], 160)}</p>
      <div class="card-meta">
        <span class="card-link" style="color:{pi['color']}">Read article &rarr;</span>
        <span class="card-time">{e['reading_time']} min{chart_badge}{audio_badge}</span>
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
        {'slug':'why-china-could-invade-taiwan-and-get-away-with-it',
         'chart_id':'heroTaiwan','headline':'Taiwan makes 63% of the world\'s advanced chips','sub':'Why China Could Invade Taiwan','color':'#c43425',
         'js':"""(()=>{const ctx=document.getElementById('heroTaiwan');new Chart(ctx,{type:'bar',data:{labels:['Taiwan','S. Korea','China','US','Europe','Other'],datasets:[{data:[63,18,6,5,3,5],backgroundColor:['#c43425','#2563eb','#b8751a','#7c3aed','#0c8f8f','#8a8479'],borderRadius:3,borderSkipped:false}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{backgroundColor:'#1a1815ee',callbacks:{label:i=>i.raw+'% of global advanced chips'}}},scales:{x:{grid:{display:false},ticks:{color:'#8a8479',font:{size:8}}},y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>v+'%'},min:0}}}});})();"""},
        {'slug':'the-scramble-for-the-solar-system-why-the-next-colonial-race-has-already-begun',
         'chart_id':'heroSpace','headline':'Launch costs fell from $54,500 to $200/kg','sub':'The Scramble for the Solar System','color':'#2563eb',
         'js':"""(()=>{const ctx=document.getElementById('heroSpace');new Chart(ctx,{type:'bar',data:{labels:['Shuttle','Atlas V','Falcon 9','F. Heavy','Starship'],datasets:[{data:[54500,13200,2720,1500,200],backgroundColor:['#8a8479','#b8751a','#2563eb','#2563ebcc','#c43425'],borderRadius:3,borderSkipped:false}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{backgroundColor:'#1a1815ee',callbacks:{label:i=>'$'+i.raw.toLocaleString()+'/kg'}}},scales:{x:{grid:{display:false},ticks:{color:'#8a8479',font:{size:8}}},y:{type:'logarithmic',grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>'$'+v.toLocaleString()}}}}});})();"""},
        {'slug':'the-gates-of-nations-how-every-civilisation-in-history-controlled-immigration-until-the-west-stopped',
         'chart_id':'heroGates','headline':'Foreign-born populations tripled since 1970','sub':'The Gates of Nations','color':'#0d9a5a',
         'js':"""(()=>{const ctx=document.getElementById('heroGates');new Chart(ctx,{type:'line',data:{datasets:[{label:'UK',data:_xy([1960,1970,1980,1990,2000,2010,2020,2025],[4.3,5.8,6.2,6.5,8.3,12.0,14.4,15.8]),borderColor:'#c43425',fill:false,tension:.3,pointRadius:2,borderWidth:2},{label:'Germany',data:_xy([1960,1970,1980,1990,2000,2010,2020,2025],[2.8,6.6,7.5,8.4,12.5,13.0,18.8,20.2]),borderColor:'#0d9a5a',fill:false,tension:.3,pointRadius:2,borderWidth:2},{label:'US',data:_xy([1960,1970,1980,1990,2000,2010,2020,2025],[5.4,4.7,6.2,7.9,11.1,12.9,13.7,14.3]),borderColor:'#2563eb',fill:false,tension:.3,pointRadius:2,borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'bottom',labels:{padding:8,usePointStyle:true,pointStyle:'circle',font:{size:9}}},tooltip:{backgroundColor:'#1a1815ee'}},scales:{x:{type:'linear',min:1960,max:2025,grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9}}},y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>v+'%'},min:0}}}});})();"""},
        {'slug':'the-north-african-threat-and-mediterranean-reunification',
         'chart_id':'heroNAfrica','headline':'North Africa will outnumber Southern Europe by 2030','sub':'The North African Threat','color':'#b8751a',
         'js':"""(()=>{const ctx=document.getElementById('heroNAfrica');new Chart(ctx,{type:'line',data:{datasets:[{label:'N. Africa',data:_xy([1960,1980,2000,2020,2035,2050],[55,95,150,210,260,310]),borderColor:'#c43425',fill:false,tension:.3,pointRadius:2,borderWidth:2},{label:'S. Europe',data:_xy([1960,1980,2000,2020,2035,2050],[95,112,121,122,116,107]),borderColor:'#2563eb',fill:false,tension:.3,pointRadius:2,borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'bottom',labels:{padding:8,usePointStyle:true,pointStyle:'circle',font:{size:9}}},tooltip:{backgroundColor:'#1a1815ee',callbacks:{label:i=>i.dataset.label+': '+i.parsed.y+'M'}}},scales:{x:{type:'linear',min:1960,max:2050,grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9}}},y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>v+'M'},min:0}}}});})();"""},
        {'slug':'the-return-of-the-state-factory-why-nations-that-forgot-how-to-make-things-are-remembering',
         'chart_id':'heroFactory','headline':'Manufacturing fell from 30% to 11% of US GDP','sub':'The Return of the State Factory','color':'#0c8f8f',
         'js':"""(()=>{const ctx=document.getElementById('heroFactory');new Chart(ctx,{type:'line',data:{datasets:[{label:'US',data:_xy([1970,1985,2000,2010,2025],[24,18,15,12,11]),borderColor:'#2563eb',fill:false,tension:.3,pointRadius:2,borderWidth:2},{label:'UK',data:_xy([1970,1985,2000,2010,2025],[28,18,14,10,9]),borderColor:'#0c8f8f',fill:false,tension:.3,pointRadius:2,borderWidth:2},{label:'China',data:_xy([1970,1985,2000,2010,2025],[30,34,32,32,28]),borderColor:'#c43425',fill:false,tension:.3,pointRadius:2,borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'bottom',labels:{padding:8,usePointStyle:true,pointStyle:'circle',font:{size:9}}},tooltip:{backgroundColor:'#1a1815ee'}},scales:{x:{type:'linear',min:1970,max:2025,grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9}}},y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>v+'%'},min:5,max:40}}}});})();"""},
        {'slug':'who-guards-the-guards-bureaucracy-empire-and-the-eternal-struggle-to-control-the-state',
         'chart_id':'heroGuards','headline':'US federal regulations grew 18x since 1950','sub':'Who Guards the Guards?','color':'#7c3aed',
         'js':"""(()=>{const ctx=document.getElementById('heroGuards');new Chart(ctx,{type:'line',data:{datasets:[{data:_xy([1950,1960,1970,1975,1980,1990,2000,2010,2020,2025],[10,19,35,54,71,102,128,157,175,180]),borderColor:'#7c3aed',backgroundColor:'#7c3aed18',fill:true,tension:.3,pointRadius:2,pointBackgroundColor:'#7c3aed',borderWidth:2.5}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{backgroundColor:'#1a1815ee',callbacks:{label:i=>i.parsed.y+'K pages'}}},scales:{x:{type:'linear',min:1950,max:2025,grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9}}},y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>v+'K'},min:0}}}});})();"""},
        {'slug':'the-150-year-life-how-radical-longevity-will-transform-our-world',
         'chart_id':'heroLongevity','headline':'Human life expectancy: from 30 to 150 years','sub':'The 150-Year Life','color':'#0d9a5a',
         'js':"""(()=>{const ctx=document.getElementById('heroLongevity');new Chart(ctx,{type:'bar',data:{labels:['Stone Age','Classical','Medieval','1800','1900','1950','2000','2025','2100?'],datasets:[{data:[30,35,40,40,50,60,70,78,150],backgroundColor:['#8a8479','#8a8479','#8a8479','#8a8479','#b8751a','#b8751a','#2563eb','#2563eb','#0d9a5a'],borderRadius:3,borderSkipped:false}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{backgroundColor:'#1a1815ee',callbacks:{label:i=>i.raw+' years'}}},scales:{x:{grid:{display:false},ticks:{color:'#8a8479',font:{size:7},maxRotation:45}},y:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9}},min:0}}}});})();"""},
        {'slug':'the-silence-of-the-scribes-how-every-civilisation-that-controlled-speech-collapsed',
         'chart_id':'heroScribes','headline':'India made 78,500 content removal requests in 2024','sub':'The Silence of the Scribes','color':'#e11d48',
         'js':"""(()=>{const ctx=document.getElementById('heroScribes');new Chart(ctx,{type:'bar',data:{labels:['India','Turkey','Russia','S. Korea','France','Germany','Brazil','US'],datasets:[{data:[78.5,15.3,14.8,12.1,9.7,8.4,7.2,5.9],backgroundColor:['#c43425','#b8751a','#7c3aed','#2563eb','#0c8f8f','#2563ebcc','#0d9a5a','#0284c7'],borderRadius:3,borderSkipped:false}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{backgroundColor:'#1a1815ee',callbacks:{label:i=>i.raw+'K requests'}}},scales:{x:{grid:{color:'#f2eeea'},ticks:{color:'#8a8479',font:{size:9},callback:v=>v+'K'}},y:{grid:{display:false},ticks:{color:'#8a8479',font:{size:8}}}}}});})();"""},
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
            audio_badge = ' <span class="card-audio">Audio</span>' if (e.get('has_audio') or e.get('has_discussion')) else ''
            cards += f"""      <a href="/articles/{html_mod.escape(e['slug'])}" class="card" data-section="{pi['slug']}">
        <div class="card-kicker" style="color:{pi['color']}">{pi['label']} {chart_badge}{audio_badge}</div>
      <h3>{html_mod.escape(e['title'])}</h3>
      <p>{truncate_excerpt(e['excerpt'], 160)}</p>
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

    # ── Listen to History teaser (homepage) ──
    # Show 5 newest audio articles as cards + CTA to /listen
    audio_essays = [e for e in essays if e.get('has_audio') or e.get('has_discussion')]
    audio_essays.sort(key=lambda e: (PARTS.get(e['part'], {}).get('order', 99), e['title']))
    audio_article_count = len(audio_essays)

    # Calculate total listen time across all audio articles
    total_listen_mins = 0
    for ae in audio_essays:
        if ae.get('has_audio'):
            total_listen_mins += max(1, round(ae['reading_time'] * 250 / 189))
        else:
            total_listen_mins += 10
    total_listen_hours = round(total_listen_mins / 60)

    # Pick 5 newest audio articles (by mtime) for the teaser
    audio_by_mtime = sorted(audio_essays, key=lambda e: e.get('mtime', 0), reverse=True)
    teaser_essays = audio_by_mtime[:5]

    teaser_cards_html = ""
    teaser_queue_items = []
    for ae in teaser_essays:
        pi = PARTS.get(ae['part'], PARTS['Society'])
        section_label = f"{pi['label']} · {ae['part']}"
        has_narration = ae.get('has_audio', False)
        has_disc = ae.get('has_discussion', False)

        if has_narration:
            listen_time = max(1, round(ae['reading_time'] * 250 / 189))
            queue_url = f"/audio/{ae['slug']}.mp3"
        else:
            listen_time = 10
            queue_url = f"/audio/discussions/{ae['slug']}.mp3"

        if has_narration and has_disc:
            type_badge = '<span class="listen-card-type">Narration + Discussion</span>'
        elif has_narration:
            type_badge = '<span class="listen-card-type">Narration</span>'
        else:
            type_badge = '<span class="listen-card-type">Discussion</span>'

        teaser_cards_html += f'''      <a href="/articles/{html_mod.escape(ae['slug'])}" class="listen-card" style="--card-accent:{pi['color']}">
        <div class="listen-card-top">
          <svg class="listen-card-play" viewBox="0 0 24 24" fill="{pi['color']}"><path d="M8 5v14l11-7z"/></svg>
          <span class="listen-card-time">{listen_time} min</span>
        </div>
        <div class="listen-card-title">{html_mod.escape(ae['title'])}</div>
        <div class="listen-card-kicker" style="color:{pi['color']}">{pi['label']} &middot; {html_mod.escape(ae['part'])}</div>
        {type_badge}
        <button class="q-add-btn" data-queue-slug="{html_mod.escape(ae['slug'])}" data-queue-title="{html_mod.escape(ae['title'])}" data-queue-section="{html_mod.escape(section_label)}" data-queue-color="{pi['color']}" data-queue-url="{queue_url}" aria-label="Add to queue">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
          <span class="q-add-label">Add to Queue</span>
        </button>
      </a>\n'''
        teaser_queue_items.append({
            'slug': ae['slug'],
            'title': ae['title'],
            'section': section_label,
            'color': pi['color'],
            'url': queue_url,
        })

    teaser_queue_json = html_mod.escape(json.dumps(teaser_queue_items))

    listen_section_html = ""
    if audio_article_count > 0:
        listen_section_html = f"""
<div class="listen-wrap">
  <div class="listen-inner">
    <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.75rem;margin-bottom:0.3rem;">
      <div>
        <h2 class="listen-title">Listen to History</h2>
        <p class="listen-intro" style="margin-bottom:0">Every article, narrated in full. Queue them up and listen on the go.</p>
      </div>
      <button class="q-play-all" id="queueAllBtn" data-items="{teaser_queue_json}">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        Queue All
      </button>
    </div>
    <div class="listen-scroll">
{teaser_cards_html}    </div>
    <div class="listen-teaser-cta">
      <a href="/listen" class="listen-browse-link">
        <span class="listen-browse-stats">{audio_article_count} articles &middot; {total_listen_hours}+ hours of audio</span>
        <span class="listen-browse-action">Browse the full collection &rarr;</span>
      </a>
    </div>
  </div>
</div>
"""

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
<script src="/js/chart.umd.min.js"></script>
<script src="/js/chartjs-plugin-annotation.min.js"></script>
</head>
<body>

{make_nav()}

{make_search_overlay()}

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
    {"" if audio_article_count == 0 else f'<div class="stat"><span class="stat-num">{audio_article_count}</span><span class="stat-label">Audio Articles</span></div>'}
  </div>
</div>
{listen_section_html}
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
      {"" if not get_hero_image("the-great-emptying-how-collapsing-birth-rates-will-reshape-power-politics-and-people") else '<img src="' + get_hero_image("the-great-emptying-how-collapsing-birth-rates-will-reshape-power-politics-and-people") + '" alt="" class="featured-img" loading="lazy">'}
      <div class="featured-text">
        <div class="featured-badge">Featured &middot; 10 interactive charts</div>
        <h2>The Great Emptying: How Collapsing Birth Rates Will Reshape Power, Politics And People</h2>
        <p>No country in human history has recovered from a sustained fertility rate below 1.5. The forces that drive the decline &mdash; urbanisation, education, contraception &mdash; are things we call progress. The clock is already at zero.</p>
        <span class="featured-cta">Read the full analysis &rarr;</span>
      </div>
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

def build_listen_page(essays):
    """Build the dedicated /listen page with filterable audio catalogue."""
    audio_essays = [e for e in essays if e.get('has_audio') or e.get('has_discussion')]
    audio_essays.sort(key=lambda e: (PARTS.get(e['part'], {}).get('order', 99), e['title']))
    audio_count = len(audio_essays)

    # Calculate total listen time
    total_mins = 0
    for ae in audio_essays:
        if ae.get('has_audio'):
            total_mins += max(1, round(ae['reading_time'] * 250 / 189))
        else:
            total_mins += 10
    total_hours = round(total_mins / 60)

    # Count by section
    section_counts = {}
    for ae in audio_essays:
        pn = ae['part']
        section_counts[pn] = section_counts.get(pn, 0) + 1

    # Build queue-all data
    all_queue_items = []
    for ae in audio_essays:
        pi = PARTS.get(ae['part'], PARTS['Society'])
        section_label = f"{pi['label']} · {ae['part']}"
        if ae.get('has_audio'):
            queue_url = f"/audio/{ae['slug']}.mp3"
        else:
            queue_url = f"/audio/discussions/{ae['slug']}.mp3"
        all_queue_items.append({
            'slug': ae['slug'],
            'title': ae['title'],
            'section': section_label,
            'color': pi['color'],
            'url': queue_url,
        })
    queue_all_json = html_mod.escape(json.dumps(all_queue_items))

    # Build filter tabs
    filter_tabs = '<button class="lp-tab active" data-filter="all">All</button>\n'
    for pn in sorted(PARTS.keys(), key=lambda p: PARTS[p]['order']):
        pi = PARTS[pn]
        count = section_counts.get(pn, 0)
        if count > 0:
            filter_tabs += f'      <button class="lp-tab" data-filter="{html_mod.escape(pi["slug"])}" style="--tab-color:{pi["color"]}">{pi["label"].replace("Part ", "").strip()}: {html_mod.escape(pn)} <span class="lp-tab-count">{count}</span></button>\n'

    # Build list rows
    rows_html = ""
    for ae in audio_essays:
        pi = PARTS.get(ae['part'], PARTS['Society'])
        section_label = f"{pi['label']} · {ae['part']}"
        has_narration = ae.get('has_audio', False)
        has_disc = ae.get('has_discussion', False)

        if has_narration:
            listen_time = max(1, round(ae['reading_time'] * 250 / 189))
            queue_url = f"/audio/{ae['slug']}.mp3"
        else:
            listen_time = 10
            queue_url = f"/audio/discussions/{ae['slug']}.mp3"

        if has_narration and has_disc:
            type_label = "Narration + Discussion"
            audio_type_filter = "both"
        elif has_narration:
            type_label = "Narration"
            audio_type_filter = "narration"
        else:
            type_label = "Discussion"
            audio_type_filter = "discussion"

        excerpt_text = truncate_excerpt(ae.get('excerpt', ''), 120)

        rows_html += f'''    <a href="/articles/{html_mod.escape(ae['slug'])}" class="lp-row" data-section="{html_mod.escape(pi['slug'])}" data-audio-type="{audio_type_filter}">
      <svg class="lp-row-play" viewBox="0 0 24 24" fill="{pi['color']}"><path d="M8 5v14l11-7z"/></svg>
      <div class="lp-row-main">
        <div class="lp-row-title">{html_mod.escape(ae['title'])}</div>
        <div class="lp-row-excerpt">{excerpt_text}</div>
      </div>
      <span class="lp-row-section" style="color:{pi['color']};border-color:{pi['color']}">{html_mod.escape(pi['label'])}</span>
      <span class="lp-row-duration">{listen_time} min</span>
      <span class="lp-row-type">{type_label}</span>
      <button class="q-add-btn" data-queue-slug="{html_mod.escape(ae['slug'])}" data-queue-title="{html_mod.escape(ae['title'])}" data-queue-section="{html_mod.escape(section_label)}" data-queue-color="{pi['color']}" data-queue-url="{queue_url}" aria-label="Add to queue">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
        <span class="q-add-label">Queue</span>
      </button>
    </a>\n'''

    breadcrumbs = make_breadcrumbs([
        ('Home', '/'),
        ('Listen', None),
    ])

    filter_script = '''<script>
(function(){
  var tabs = document.querySelectorAll('.lp-tab');
  var typeBtns = document.querySelectorAll('.lp-type-btn');
  var rows = document.querySelectorAll('.lp-row');
  var countEl = document.getElementById('lpVisibleCount');
  var currentSection = 'all';
  var currentType = 'all';

  function applyFilters(){
    var visible = 0;
    rows.forEach(function(r){
      var matchSection = currentSection === 'all' || r.dataset.section === currentSection;
      var matchType = currentType === 'all' || r.dataset.audioType === currentType || (currentType === 'narration' && r.dataset.audioType === 'both') || (currentType === 'discussion' && r.dataset.audioType === 'both');
      if(matchSection && matchType){ r.style.display = ''; visible++; }
      else { r.style.display = 'none'; }
    });
    if(countEl) countEl.textContent = visible;
  }

  tabs.forEach(function(t){
    t.addEventListener('click', function(){
      tabs.forEach(function(x){ x.classList.remove('active'); });
      t.classList.add('active');
      currentSection = t.dataset.filter;
      applyFilters();
      var hash = currentSection === 'all' ? '' : '#' + currentSection;
      history.replaceState(null, '', '/listen' + hash);
    });
  });

  typeBtns.forEach(function(b){
    b.addEventListener('click', function(){
      typeBtns.forEach(function(x){ x.classList.remove('active'); });
      b.classList.add('active');
      currentType = b.dataset.type;
      applyFilters();
    });
  });

  // Restore filter from URL hash
  var hash = location.hash.replace('#','');
  if(hash){
    tabs.forEach(function(t){
      if(t.dataset.filter === hash){
        t.click();
      }
    });
  }

  // Stop queue button clicks from navigating to the article
  document.querySelectorAll('.lp-row .q-add-btn').forEach(function(btn){
    btn.addEventListener('click', function(e){ e.preventDefault(); e.stopPropagation(); });
  });
})();
</script>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{make_head("Listen to History — History Future Now", f"{audio_count} articles available as audio narration. {total_hours}+ hours of content.", "/listen")}
</head>
<body>

{make_nav("Listen")}

{make_search_overlay()}

<section class="lp-hero">
  <div class="lp-hero-inner">
    {breadcrumbs}
    <h1 class="lp-hero-title">Listen to History</h1>
    <p class="lp-hero-desc">Every article, narrated in full with two alternating British voices. Queue them up and listen on the go.</p>
    <div class="lp-hero-stats">
      <span class="lp-stat"><strong>{audio_count}</strong> articles</span>
      <span class="lp-stat-sep">&middot;</span>
      <span class="lp-stat"><strong>{total_hours}+</strong> hours</span>
      <span class="lp-stat-sep">&middot;</span>
      <span class="lp-stat"><strong>4</strong> sections</span>
    </div>
    <button class="q-play-all lp-queue-all" id="queueAllBtn" data-items="{queue_all_json}">
      <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
      Queue All {audio_count} Articles
    </button>
  </div>
</section>

<div class="lp-filters">
  <div class="lp-filters-inner">
    <div class="lp-filter-group">
      <span class="lp-filter-label">Section</span>
      {filter_tabs}
    </div>
    {'<div class="lp-filter-group"><span class="lp-filter-label">Type</span><button class="lp-type-btn active" data-type="all">All</button><button class="lp-type-btn" data-type="narration">Narration</button><button class="lp-type-btn" data-type="discussion">Discussion</button></div>' if ENABLE_DISCUSSIONS else ''}
  </div>
</div>

<div class="lp-list-wrap">
  <div class="lp-list-inner">
    <div class="lp-list-header">
      <span class="lp-showing">Showing <strong id="lpVisibleCount">{audio_count}</strong> articles</span>
    </div>
    <div class="lp-list">
{rows_html}    </div>
  </div>
</div>

{make_footer()}
{filter_script}
</body>
</html>'''


def build_library():
    """Build the /library page — an intellectual map of the reading behind HFN."""
    from library_data import THEMES, BOOKS, get_books_by_theme

    by_theme = get_books_by_theme()

    breadcrumbs = make_breadcrumbs([('Home', '/'), ('Library', None)])

    # ── Theme cards with books shown by default ──
    theme_cards = ""
    for tid in sorted(THEMES.keys(), key=lambda t: THEMES[t]["order"]):
        theme = THEMES[tid]
        books = by_theme.get(tid, [])
        book_items = ""
        for b in books:
            import urllib.parse
            search_query = urllib.parse.quote_plus(f'{b["title"]} {b["author"]}')
            book_items += f'''      <div class="lib-book-item">
        <span class="lib-book-title">{html_mod.escape(b["title"])}</span>
        <span class="lib-book-author">{html_mod.escape(b["author"])}</span>
        <a class="lib-book-amazon" href="https://www.amazon.co.uk/s?k={search_query}" data-query="{search_query}" target="_blank" rel="noopener noreferrer">Amazon</a>
      </div>\n'''

        theme_cards += f'''    <div class="lib-theme-card" style="--theme-color:{theme["color"]}">
      <div class="lib-theme-header">
        <span class="lib-theme-icon">{theme["icon"]}</span>
        <div class="lib-theme-info">
          <div class="lib-theme-name">{theme["name"]}</div>
          <div class="lib-theme-count">{len(books)} titles</div>
        </div>
      </div>
      <p class="lib-theme-desc">{theme["desc"]}</p>
      <div class="lib-book-list">
{book_items}      </div>
    </div>\n'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{make_head("The Library — History Future Now", "A curated selection from over 1,300 books — the intellectual inputs behind every article. Organised by theme.", "/library")}
</head>
<body>

{make_nav("Library")}

{make_search_overlay()}

<section class="lib-hero">
  <div class="lib-hero-inner">
    {breadcrumbs}
    <h1 class="lib-hero-title">The Library</h1>
    <p class="lib-hero-desc">The intellectual inputs behind every article on this site.</p>
  </div>
</section>

<div class="lib-intro-wrap">
  <p class="lib-disclaimer">Inclusion is not endorsement. A serious reader engages with arguments they find uncomfortable. Understanding a position is not the same as agreeing with it.</p>
</div>

<div class="lib-themes-wrap">
  <div class="lib-themes-grid">
{theme_cards}  </div>
</div>

{make_footer()}

<script>
(function() {{
  var isUK = false;
  try {{
    var tz = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
    isUK = tz === 'Europe/London' || tz === 'Europe/Belfast' || tz === 'Europe/Guernsey' || tz === 'Europe/Isle_of_Man' || tz === 'Europe/Jersey';
  }} catch(e) {{}}
  if (!isUK) {{
    var links = document.querySelectorAll('.lib-book-amazon');
    for (var i = 0; i < links.length; i++) {{
      var q = links[i].getAttribute('data-query');
      links[i].href = 'https://www.amazon.com/s?k=' + q;
    }}
  }}
}})();
</script>
</body>
</html>'''


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

    print("Building listen page...")
    (OUTPUT_DIR / "listen.html").write_text(build_listen_page(essays), encoding='utf-8')
    print("  Built listen page")

    print("Building library page...")
    (OUTPUT_DIR / "library.html").write_text(build_library(), encoding='utf-8')
    print("  Built library page")

    # ── SEO files ──
    print("Building SEO files...")
    all_charts = get_all_charts()

    # sitemap.xml
    urls = [f'  <url><loc>{SITE_URL}/</loc><priority>1.0</priority><changefreq>weekly</changefreq></url>']
    urls.append(f'  <url><loc>{SITE_URL}/listen</loc><priority>0.8</priority><changefreq>weekly</changefreq></url>')
    urls.append(f'  <url><loc>{SITE_URL}/library</loc><priority>0.7</priority><changefreq>monthly</changefreq></url>')
    for pi in PARTS.values():
        urls.append(f'  <url><loc>{SITE_URL}/{pi["slug"]}</loc><priority>0.8</priority><changefreq>weekly</changefreq></url>')
    for e in essays:
        lastmod = f'<lastmod>{e["pub_date"]}</lastmod>' if e.get('pub_date') else ''
        urls.append(f'  <url><loc>{SITE_URL}/articles/{e["slug"]}</loc>{lastmod}<priority>0.7</priority><changefreq>monthly</changefreq></url>')
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
        if e.get('pub_date'):
            llms_lines.append(f"- Published: {e['pub_date']}")
        llms_lines.append(f"- Reading time: {e['reading_time']} min")
        llms_lines.append(f"- {e['excerpt'][:200]}")
        llms_lines.append("")

    (OUTPUT_DIR / "llms.txt").write_text("\n".join(llms_lines), encoding='utf-8')

    # search-index.json for client-side search
    search_index = []
    for e in essays:
        pi = PARTS[e['part']]
        n_charts = len(all_charts.get(e['slug'], []))
        entry = {
            "title": e['title'],
            "slug": e['slug'],
            "section": e['part'],
            "sectionSlug": pi['slug'],
            "label": pi['label'],
            "color": pi['color'],
            "excerpt": e['excerpt'][:200],
            "readingTime": e['reading_time'],
            "chartCount": n_charts,
            "hasAudio": e.get('has_audio', False) or e.get('has_discussion', False),
        }
        if e.get('pub_date'):
            entry["pubDate"] = e['pub_date']
        search_index.append(entry)
    (OUTPUT_DIR / "search-index.json").write_text(
        json.dumps(search_index, ensure_ascii=False), encoding='utf-8')

    # RSS feed (Atom)
    from datetime import datetime
    sorted_by_date = sorted(
        [e for e in essays if e.get('pub_date')],
        key=lambda e: e['pub_date'],
        reverse=True
    )
    rss_items = []
    for e in sorted_by_date[:20]:
        pi = PARTS[e['part']]
        pub_dt = datetime.strptime(e['pub_date'], '%Y-%m-%d')
        rfc822 = pub_dt.strftime('%a, %d %b %Y 00:00:00 +0000')
        hero_img = get_hero_image(e['slug'])
        enclosure = f'\n      <enclosure url="{SITE_URL}{hero_img}" type="image/png" />' if hero_img else ''
        rss_items.append(f'''    <item>
      <title>{html_mod.escape(e["title"])}</title>
      <link>{SITE_URL}/articles/{e["slug"]}</link>
      <guid isPermaLink="true">{SITE_URL}/articles/{e["slug"]}</guid>
      <pubDate>{rfc822}</pubDate>
      <description>{html_mod.escape(e["excerpt"][:500])}</description>
      <category>{html_mod.escape(e["part"])}</category>{enclosure}
    </item>''')

    latest_date = sorted_by_date[0]['pub_date'] if sorted_by_date else '2026-02-16'
    latest_dt = datetime.strptime(latest_date, '%Y-%m-%d')
    latest_rfc822 = latest_dt.strftime('%a, %d %b %Y 00:00:00 +0000')

    rss_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>History Future Now</title>
    <link>{SITE_URL}</link>
    <description>Data-driven analysis of the structural forces — demographic, technological, economic — that will shape the next century.</description>
    <language>en-gb</language>
    <lastBuildDate>{latest_rfc822}</lastBuildDate>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />
    <image>
      <url>{SITE_URL}/favicon.svg</url>
      <title>History Future Now</title>
      <link>{SITE_URL}</link>
    </image>
{chr(10).join(rss_items)}
  </channel>
</rss>'''
    (OUTPUT_DIR / "feed.xml").write_text(rss_xml, encoding='utf-8')

    print("  Built sitemap.xml, robots.txt, llms.txt, search-index.json, feed.xml")

    total = len(essays) + len(PARTS) + 1
    print(f"\n✅ Site built: {total} HTML pages")
    print(f"   Output: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
