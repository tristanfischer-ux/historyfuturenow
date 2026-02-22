#!/usr/bin/env python3
"""
History Future Now — Static Site Builder v2
Enhanced: reading time, related articles, pull quotes, OG tags, section theming, favicon
"""

import os, re, sys, yaml, markdown, json, math, random, hashlib
import html as html_mod
from pathlib import Path
from chart_defs import get_all_charts, COLORS as CHART_COLORS
from issues import ISSUES, get_issue_for_slug, get_issue_by_number, get_current_issue, build_slug_to_issue_map

ESSAYS_DIR = Path(__file__).parent / "essays"
OUTPUT_DIR = Path(__file__).parent.parent / "hfn-site-output"
ARTICLES_DIR = OUTPUT_DIR / "articles"
MANIFEST_PATH = Path(__file__).parent / "original_articles.txt"

MAX_NEW_ARTICLES = 10

# Feature flag: set to False to disable debate/discussion players across the site.
# Discussion scripts and audio files are preserved on disk — just not rendered.
ENABLE_DISCUSSIONS = False

# Articles pulled from public site for editorial review. They remain accessible
# at their direct URLs (with noindex) and are listed on a hidden /review/ page.
REVIEW_SLUGS = {
    'the-young-continent-how-africas-billion-person-surge-will-reshape-the-global-order',
    'the-severed-circuit-how-the-us-china-tech-war-is-splitting-the-world-in-two',
    'the-elephant-awakens-why-indias-rise-will-reshape-the-world-more-than-chinas-did',
    'why-the-scissors-opened-nine-hypotheses-for-the-gender-ideology-split',
    'the-narrow-lens-how-what-britain-teaches-its-children-shapes-how-adults-see-the-world',
}

# Articles that were under review and have been released to the public site.
RELEASED_FROM_REVIEW = {
    'the-atom-returns-why-the-worlds-most-feared-energy-source-is-its-best-hope',
    'the-last-drop-why-every-civilisation-that-ran-out-of-water-collapsed',
    'the-great-divergence-why-young-men-and-women-no-longer-see-the-same-world',
    'the-price-of-admission-what-the-netherlands-and-denmark-reveal-about-the-true-cost-of-immigration',
    'the-ladder-and-the-lie-why-every-great-economy-was-built-on-tariffs-and-free-trade-only-serves-the-already-dominant',
    'the-empty-throne-why-the-west-no-longer-believes-in-its-own-institutions',
}

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
    "a-nation-transformed-britains-demographic-revolution-1948-2050": "2026-02-18",
    "the-invisible-judge-why-guilt-and-shame-societies-are-incompatible": "2026-02-20",
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

    # Sources: list of book titles cited in this article
    sources = meta.get('sources', []) or []

    return {
        'title': title, 'slug': slug, 'part': part, 'excerpt': excerpt,
        'body_html': body_html, 'reading_time': reading_time,
        'pull_quote': pull_quote, 'filepath': filepath,
        'has_audio': has_audio, 'has_discussion': has_discussion,
        'share_summary': share_summary,
        'pub_date': pub_date,
        'sources': sources,
    }

def get_related(essay, all_essays, n=1):
    """Return n random articles from the same section (deterministic per slug)."""
    same = [e for e in all_essays if e['part'] == essay['part'] and e['slug'] != essay['slug']]
    random.seed(hash(essay['slug']))
    return random.sample(same, min(n, len(same)))


def get_newest_article(essay, all_essays):
    """Most recently published article across all sections (excluding the current one)."""
    others = [e for e in all_essays if e['slug'] != essay['slug'] and e.get('pub_date')]
    if not others:
        return None
    others.sort(key=lambda e: e['pub_date'], reverse=True)
    return others[0]

IMAGES_DIR = OUTPUT_DIR / "images" / "articles"

def get_hero_image(slug):
    """Check if a hero image exists for this article and return its path."""
    for ext in ['png', 'webp', 'jpg']:
        img_path = IMAGES_DIR / slug / f"hero.{ext}"
        if img_path.exists():
            return f"/images/articles/{slug}/hero.{ext}"
    return None

def make_card_controls(essay, pi):
    """Generate play button + bookmark HTML for article cards."""
    slug = html_mod.escape(essay['slug'])
    title_esc = html_mod.escape(essay['title'])
    section_label = html_mod.escape(f"{pi['label']} · {essay['part']}")
    color = pi['color']
    article_url = f"/articles/{slug}"

    bookmark_btn = (
        f'<button class="card-bookmark-btn" data-bookmark-slug="{slug}" '
        f'data-bookmark-title="{title_esc}" data-bookmark-url="{article_url}" '
        f'data-bookmark-section="{section_label}" data-bookmark-color="{color}" '
        f'aria-label="Bookmark">'
        '<svg class="bk-outline" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>'
        '<svg class="bk-filled" viewBox="0 0 24 24" fill="currentColor"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>'
        '</button>'
    )

    has_audio = essay.get('has_audio') or essay.get('has_discussion')
    if has_audio:
        if essay.get('has_audio'):
            queue_url = f"/audio/{essay['slug']}.mp3"
        else:
            queue_url = f"/audio/discussions/{essay['slug']}.mp3"
        play_btn = (
            f'<button class="card-play-btn" '
            f'data-queue-slug="{slug}" data-queue-title="{title_esc}" '
            f'data-queue-section="{section_label}" data-queue-color="{color}" '
            f'data-queue-url="{queue_url}" aria-label="Play options">'
            '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>'
            '</button>'
        )
        return f'<div class="card-controls">{play_btn}{bookmark_btn}</div>'

    return f'<div class="card-controls">{bookmark_btn}</div>'


def make_head(title, desc="", og_url="", part_color=None, json_ld=None, og_image=None, pub_date=None, noindex=False):
    te = html_mod.escape(title)
    de = html_mod.escape(desc[:300]) if desc else ""
    tc = part_color or "#c43425"
    canonical = f'<link rel="canonical" href="{SITE_URL}{og_url}">' if og_url else ""
    og = f'<meta property="og:url" content="{SITE_URL}{og_url}">' if og_url else ""
    og_img = f'<meta property="og:image" content="{SITE_URL}{og_image}">\n<meta name="twitter:image" content="{SITE_URL}{og_image}">' if og_image else ""
    og_date = f'\n<meta property="article:published_time" content="{pub_date}">' if pub_date else ""
    ld = f'<script type="application/ld+json">{json.dumps(json_ld, ensure_ascii=False)}</script>' if json_ld else ""
    robots = "noindex, nofollow" if noindex else "index, follow"
    css_v = _asset_hash("css", "style.css")
    return f'''<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
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
<meta name="robots" content="{robots}">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.json">
<link rel="alternate" type="application/rss+xml" title="History Future Now" href="/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Source+Sans+3:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/style.css?v={css_v}">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-6PS9DYS2PZ"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-6PS9DYS2PZ');</script>
<script>if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js');</script>
{ld}'''

def make_nav(active=None):
    secs = [("Home","/",None),("Issues","/issues",None),("Charts","/charts",None),
            ("Natural Resources","/natural-resources","Natural Resources"),
            ("Power","/balance-of-power","Global Balance of Power"),
            ("Economy","/jobs-economy","Jobs & Economy"),("Society","/society","Society"),
            ("Listen","/listen",None),("Library","/library",None),("Saved","/saved",None)]
    li = ""
    for label, href, part in secs:
        ac = ' class="active"' if (part and part == active) or (label == active) else ''
        li += f'      <li><a href="{href}"{ac}>{label}</a></li>\n'
    return f'''<nav class="site-nav">
  <div class="nav-inner">
    <div class="nav-top-row">
      <a class="nav-logo" href="/">History Future <span>Now</span></a>
      <div class="nav-right">
        <button class="nav-theme-btn" id="themeToggle" aria-label="Switch theme">
          <svg id="themeIconSun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
          <svg id="themeIconBook" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:none"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
          <svg id="themeIconMoon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:none"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
        </button>
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
    <div class="q-center">
      <div class="q-center-top">
        <div class="q-track-info">
          <div class="q-track-title" id="queueTitle">No track loaded</div>
          <div class="q-track-section" id="queueSection"></div>
        </div>
        <div class="q-speed" id="queueSpeed" title="Playback speed">1.25&times;</div>
        <button class="q-toggle-btn" id="queueToggle" aria-label="Queue" title="View queue">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>
          <span class="q-badge" id="queueCount">0</span>
        </button>
        <button class="q-bar-close" id="queueBarClose" aria-label="Close queue" title="Close queue">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="q-center-bottom">
        <div class="q-progress-wrap" id="queueProgressWrap">
          <div class="q-progress-track"><div class="q-progress-bar" id="queueProgressBar"></div></div>
          <div class="scrub-thumb" id="queueThumb"></div>
        </div>
        <div class="q-time" id="queueTime">0:00</div>
      </div>
    </div>
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


def _asset_hash(subdir, filename):
    """Short content hash for cache-busting static assets."""
    p = OUTPUT_DIR / subdir / filename
    if p.exists():
        return hashlib.md5(p.read_bytes()).hexdigest()[:8]
    return "0"

def _js_hash(filename):
    return _asset_hash("js", filename)

def make_footer():
    nav_v = _js_hash("nav.js")
    search_v = _js_hash("search.js")
    queue_v = _js_hash("queue.js")
    softnav_v = _js_hash("soft-nav.js")
    pwa_v = _js_hash("pwa-install.js")
    return '''<section class="about-author">
  <div class="about-author-inner">
    <p><strong>By Tristan Fischer.</strong> A lifelong fascination with history, science, and technology led to a simple observation: the deeper you understand how the past unfolded, the more clearly you can see the future. These essays trace historical patterns and technological trajectories to work out what comes next.</p>
  </div>
</section>
<footer class="site-footer">
  <div class="footer-inner">
    <p class="footer-tagline">The longer the run-up, the further the leap.</p>
    <ul class="footer-links">
      <li><a href="/">Home</a></li>
      <li><a href="/issues">Issues</a></li>
      <li><a href="/charts">Charts</a></li>
      <li><a href="/natural-resources">Natural Resources</a></li>
      <li><a href="/balance-of-power">Power</a></li>
      <li><a href="/jobs-economy">Economy</a></li>
      <li><a href="/society">Society</a></li>
      <li><a href="/listen">Listen</a></li>
      <li><a href="/library">Library</a></li>
      <li><a href="/saved">Saved</a></li>
    </ul>
    <p class="footer-theme">Theme: <button type="button" class="theme-btn active" data-theme="default" aria-pressed="true">Default</button> <button type="button" class="theme-btn" data-theme="reading" aria-pressed="false">Reading</button> <button type="button" class="theme-btn" data-theme="dark" aria-pressed="false">Dark</button></p>
    <p>&copy; 2012&ndash;2026 History Future Now &middot; Tristan Fischer</p>
  </div>
</footer>
<script>
(function(){
  var key='hfn_theme',root=document.documentElement,themes=['default','reading','dark'];
  var icons={default:'themeIconSun',reading:'themeIconBook',dark:'themeIconMoon'};
  function apply(t){
    if(t==='sepia')t='reading';
    if(themes.indexOf(t)<0)t='default';
    root.dataset.theme=t||'default';
    document.querySelectorAll('.theme-btn').forEach(function(b){b.classList.toggle('active',b.dataset.theme===t);b.setAttribute('aria-pressed',b.dataset.theme===t);});
    for(var k in icons){var el=document.getElementById(icons[k]);if(el)el.style.display=k===t?'':'none';}
  }
  try{var s=localStorage.getItem(key);if(s)apply(s);}catch(e){}
  document.querySelectorAll('.theme-btn').forEach(function(b){b.addEventListener('click',function(){var t=this.dataset.theme;try{localStorage.setItem(key,t);}catch(e){}apply(t);});});
  var tb=document.getElementById('themeToggle');
  if(tb)tb.addEventListener('click',function(){var cur=root.dataset.theme||'default';var i=themes.indexOf(cur);var next=themes[(i+1)%themes.length];try{localStorage.setItem(key,next);}catch(e){}apply(next);});
})();
</script>
''' + make_queue_bar() + f'''
<script src="/js/nav.js?v={nav_v}"></script>
<script src="/js/search.js?v={search_v}"></script>
<script src="/js/queue.js?v={queue_v}"></script>
<script src="/js/soft-nav.js?v={softnav_v}"></script>
<script src="/js/pwa-install.js?v={pwa_v}" defer></script>'''

def inject_pull_quote(body_html, pq):
    if not pq: return body_html
    pq_clean = html_mod.unescape(pq)
    pq_html = f'<aside class="pull-quote"><p>{html_mod.escape(pq_clean)}</p></aside>'
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
    """Inline JavaScript for the article audio player (narration + discussion).

    The narration player routes through the queue bar so a persistent bottom
    player appears while the reader scrolls.  The discussion player (currently
    disabled) keeps standalone playback as a fallback.
    """
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
    var si=1;
    var dragging=false;

    var qRouted=false;
    var qAudio=null;
    var qMeta=null;

    if(audioId==='audioElement'&&window.HFNQueue&&HFNQueue._getAudio){
      var qBtn=document.querySelector('.q-add-btn-light[data-queue-slug]');
      if(qBtn){
        qMeta={slug:qBtn.dataset.queueSlug,title:qBtn.dataset.queueTitle,
               section:qBtn.dataset.queueSection||'',color:qBtn.dataset.queueColor||'',
               url:qBtn.dataset.queueUrl};
      }
    }

    function cur(){return qRouted&&qAudio?qAudio:audio;}

    function fmt(s){
      if(isNaN(s))return'0:00';
      var m=Math.floor(s/60);
      var sec=Math.floor(s%60);
      return m+':'+(sec<10?'0':'')+sec;
    }

    function updateBar(pct){
      var p=(pct*100)+'%';
      bar.style.width=p;
      if(thumb)thumb.style.left=p;
    }

    function seekTo(e){
      var a=cur();if(!a.duration)return;
      var rect=wrap.getBoundingClientRect();
      var pct=Math.max(0,Math.min(1,(e.clientX-rect.left)/rect.width));
      a.currentTime=pct*a.duration;
      updateBar(pct);
    }

    function seekToTouch(e){
      var a=cur();if(!a.duration)return;
      var rect=wrap.getBoundingClientRect();
      var touch=e.touches[0];
      var pct=Math.max(0,Math.min(1,(touch.clientX-rect.left)/rect.width));
      a.currentTime=pct*a.duration;
      updateBar(pct);
    }

    function syncIcons(playing){
      iconPlay.style.display=playing?'none':'block';
      iconPause.style.display=playing?'block':'none';
    }

    function bindQueueEvents(){
      qAudio.addEventListener('timeupdate',function(){
        if(dragging)return;
        if(HFNQueue.getCurrentSlug&&HFNQueue.getCurrentSlug()!==qMeta.slug)return;
        if(!qAudio.duration)return;
        var pct=qAudio.currentTime/qAudio.duration;
        updateBar(pct);
        timeEl.textContent=fmt(qAudio.currentTime)+' / '+fmt(qAudio.duration);
      });
      qAudio.addEventListener('play',function(){
        if(HFNQueue.getCurrentSlug&&HFNQueue.getCurrentSlug()===qMeta.slug)syncIcons(true);
      });
      qAudio.addEventListener('pause',function(){
        if(HFNQueue.getCurrentSlug&&HFNQueue.getCurrentSlug()===qMeta.slug)syncIcons(false);
      });
      qAudio.addEventListener('ended',function(){syncIcons(false);updateBar(0);});
    }

    function routeToQueue(){
      if(qRouted||!qMeta)return false;
      HFNQueue.playNow(qMeta.slug,qMeta.title,qMeta.section,qMeta.color,qMeta.url);
      qAudio=HFNQueue._getAudio();
      if(!qAudio){return false;}
      qRouted=true;
      if(speedEl){qAudio.playbackRate=speeds[si];}
      syncIcons(true);
      bindQueueEvents();
      return true;
    }

    // On load: if queue is already playing this track, sync to it
    if(qMeta&&window.HFNQueue&&HFNQueue.getCurrentSlug&&HFNQueue.getCurrentSlug()===qMeta.slug&&HFNQueue._getAudio){
      qAudio=HFNQueue._getAudio();
      qRouted=true;
      syncIcons(!qAudio.paused);
      bindQueueEvents();
      if(qAudio.duration){
        var pct0=qAudio.currentTime/qAudio.duration;
        updateBar(pct0);
        timeEl.textContent=fmt(qAudio.currentTime)+' / '+fmt(qAudio.duration);
      }
    }

    btn.onclick=function(){
      if(qMeta&&!qRouted){if(routeToQueue())return;}
      var a=cur();
      if(a.paused){a.play().then(function(){syncIcons(true);}).catch(function(){});}
      else{a.pause();syncIcons(false);}
    };

    audio.ontimeupdate=function(){
      if(qRouted||dragging)return;
      if(audio.duration){
        updateBar(audio.currentTime/audio.duration);
        timeEl.textContent=fmt(audio.currentTime)+' / '+fmt(audio.duration);
      }
    };

    audio.onended=function(){
      if(qRouted)return;
      syncIcons(false);updateBar(0);
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
      var a0=cur();a0.playbackRate=speeds[si];
      speedEl.textContent=speeds[si]+'\\u00d7';
      speedEl.onclick=function(){
        si=(si+1)%speeds.length;
        var a=cur();
        a.playbackRate=speeds[si];
        speedEl.textContent=speeds[si]+'\\u00d7';
      };
    }
  }

  initPlayer('audioElement','audioPlayBtn','audioProgressBar','audioProgressWrap','audioTime','audioSpeed','audioThumb');
  if(document.getElementById('discussionElement')){initPlayer('discussionElement','discussionPlayBtn','discussionProgressBar','discussionProgressWrap','discussionTime','discussionSpeed','discussionThumb');}
})();
</script>'''

ALL_CHARTS = get_all_charts()


def _fix_js_string_newlines(js):
    """Fix literal newlines inside JS string literals.

    Python triple-quoted strings convert \\n to literal newlines, which breaks
    JS string literals (single- and double-quoted). This walks the JS char by
    char, tracking string context, and re-escapes literal newlines to \\n.
    """
    out = []
    i = 0
    n = len(js)
    while i < n:
        ch = js[i]
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            i += 1
            while i < n:
                c = js[i]
                if c == '\\' and i + 1 < n:
                    out.append(c)
                    out.append(js[i + 1])
                    i += 2
                elif c == '\n':
                    out.append('\\n')
                    i += 1
                elif c == quote:
                    out.append(c)
                    i += 1
                    break
                else:
                    out.append(c)
                    i += 1
        else:
            out.append(ch)
            i += 1
    return ''.join(out)


def _charts_for_article(slug):
    """Return chart list for an article, excluding data_story entries (homepage carousel only)."""
    return [c for c in ALL_CHARTS.get(slug, []) if not c.get('data_story')]


def auto_wrap_chart(chart_def, auto_id):
    """Produce a mini-chart JS from a full chart definition by swapping canvas ID.

    Visual stripping (axes, legends, tooltips, annotations) is handled globally
    by the sparklineMode Chart.js plugin registered in chart_defs.COLORS.
    """
    original_id = chart_def.get('id', '')
    if not original_id:
        return ""
    js = _fix_js_string_newlines(chart_def.get('js', ''))
    js = js.replace(f"getElementById('{original_id}')", f"getElementById('{auto_id}')")
    return js


def collect_data_stories(essays, all_charts):
    """Build data stories list: curated entries first, then auto-generated from first chart of each article with charts."""
    stories = []
    for essay in essays:
        slug = essay['slug']
        charts = all_charts.get(slug, [])
        # Only real charts (exclude data_story dicts when counting for "has charts")
        real_charts = [c for c in charts if not c.get('data_story')]
        if not real_charts:
            continue

        ds_entry = next((c for c in charts if c.get('data_story')), None)
        part = essay.get('part', 'Society')
        color = PARTS.get(part, PARTS['Society'])['color']

        if ds_entry:
            stories.append({
                'slug': slug,
                'chart_id': ds_entry['chart_id'],
                'headline': ds_entry['headline'],
                'sub': essay['title'],
                'color': color,
                'js': ds_entry['js'],
                'curated': True,
            })
        else:
            first = real_charts[0]
            auto_id = f'dsAuto{len(stories)}'
            stories.append({
                'slug': slug,
                'chart_id': auto_id,
                'headline': first.get('title', essay['title']),
                'sub': essay['title'],
                'color': color,
                'js': auto_wrap_chart(first, auto_id),
                'curated': False,
            })

    curated = [s for s in stories if s['curated']]
    auto = [s for s in stories if not s['curated']]
    return curated + auto


# SVG icons for share buttons (inline, no external deps)
_SHARE_ICONS = {
    'x': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>',
    'linkedin': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>',
    'whatsapp': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>',
    'email': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>',
    'copy': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
}

def make_share_bar(essay, position='top', pi=None):
    """Generate share button bar HTML for an article, with optional bookmark button."""
    slug = html_mod.escape(essay['slug'])
    url = f"{SITE_URL}/articles/{slug}"
    title = html_mod.escape(essay['title'])
    text = html_mod.escape(essay.get('share_summary', '') or essay['excerpt'][:140])
    pos_class = 'share-bar-top' if position == 'top' else 'share-bar-bottom'

    buttons = ''
    for platform, icon in _SHARE_ICONS.items():
        label = {'x': 'Share on X', 'linkedin': 'Share on LinkedIn', 'whatsapp': 'Share on WhatsApp', 'email': 'Share via email', 'copy': 'Copy link'}[platform]
        buttons += f'<button class="share-btn" data-share="{platform}" aria-label="{label}" title="{label}">{icon}</button>\n'

    bookmark_html = ''
    if pi:
        section_label = html_mod.escape(f"{pi['label']} \u00b7 {essay['part']}")
        bookmark_html = (
            f'<button class="card-bookmark-btn share-bookmark-btn" '
            f'data-bookmark-slug="{slug}" data-bookmark-title="{title}" '
            f'data-bookmark-url="/articles/{slug}" '
            f'data-bookmark-section="{section_label}" data-bookmark-color="{pi["color"]}" '
            f'aria-label="Bookmark">'
            '<svg class="bk-outline" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>'
            '<svg class="bk-filled" viewBox="0 0 24 24" fill="currentColor"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>'
            '</button>'
        )

    return f'''<div class="share-bar {pos_class}" data-share-url="{url}" data-share-title="{title}" data-share-text="{text}">
    <span class="share-label">Share</span>
    {buttons}{bookmark_html}
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
    <div class="chart-figure" id="chart-{chart['id']}" data-chart-id="{chart['id']}" data-chart-title="{html_mod.escape(chart['title'])}" data-chart-source="Source: {html_mod.escape(chart['source'])}">
      <div class="chart-share-bar">
        <button class="share-btn chart-share-btn" data-chart-share="copy-data" aria-label="Copy chart data" title="Copy data">CSV</button>
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
    all_js = '\n'.join(_fix_js_string_newlines(ch['js']) for ch in charts)
    needs_geo = any(ch.get('geo') for ch in charts)
    geo_scripts = '\n<script src="/js/chartjs-chart-geo.umd.min.js"></script>' if needs_geo else ''
    geo_data = '\nvar _geoDataPromise=fetch("/js/countries-110m.json").then(r=>r.json());' if needs_geo else ''
    script_block = f'''
<script src="/js/chart.umd.min.js"></script>
<script src="/js/chartjs-plugin-annotation.min.js"></script>{geo_scripts}
<script>
(function(){{{geo_data}
{CHART_COLORS}
{all_js}
}})();
</script>'''

    return body_html, script_block

def build_further_reading_html(sources):
    """Render a 'Further Reading' section from a list of book titles, cross-referenced with the library.

    Returns (html_string, list_of_missing_titles).
    """
    if not sources:
        return '', []
    from library_data import BOOKS
    import urllib.parse

    book_lookup = {b['title'].lower().strip(): b for b in BOOKS}

    items = []
    missing = []
    for title in sources:
        book = book_lookup.get(title.lower().strip())
        if book:
            author = book['author']
            custom_url = book.get('url')
            if custom_url:
                buy_link = f'<a class="further-reading-amazon further-reading-direct" href="{html_mod.escape(custom_url)}" target="_blank" rel="noopener noreferrer">Buy</a>'
            else:
                q = urllib.parse.quote_plus(f'{book["title"]} {book["author"]}')
                amazon_url = f'https://www.amazon.co.uk/s?k={q}'
                buy_link = f'<a class="further-reading-amazon" href="{amazon_url}" data-query="{q}" target="_blank" rel="noopener noreferrer">Buy on Amazon</a>'
            items.append(
                f'<div class="further-reading-item">'
                f'<span class="further-reading-title">{html_mod.escape(book["title"])}</span>'
                f'<span class="further-reading-author">{html_mod.escape(author)}</span>'
                f'{buy_link}'
                f'</div>'
            )
        else:
            missing.append(title)
            items.append(
                f'<div class="further-reading-item further-reading-missing">'
                f'<span class="further-reading-title">{html_mod.escape(title)}</span>'
                f'</div>'
            )

    if not items:
        return '', missing

    items_html = '\n'.join(items)
    return f'''
  <section class="further-reading">
    <h2 class="further-reading-heading">Further Reading</h2>
    <p class="further-reading-desc">Books cited or drawn upon in this article.</p>
    <div class="further-reading-list">
{items_html}
    </div>
  </section>''', missing


def build_article(essay, all_essays, is_review=False):
    pi = PARTS[essay['part']]
    te = html_mod.escape(essay['title'])
    body = inject_pull_quote(essay['body_html'], essay['pull_quote'])
    related = get_related(essay, all_essays)
    next_essay = get_newest_article(essay, all_essays)

    # Inject charts if available for this article (exclude data_story entries — they are for homepage carousel only)
    article_charts = [c for c in ALL_CHARTS.get(essay['slug'], []) if not c.get('data_story')]
    body, chart_script = inject_charts_into_body(body, article_charts)
    chart_count = len(article_charts)

    # Build the two-card "Read next" section: same-section pick + newest article
    read_next_cards = []

    # Card 1: same section
    if related:
        r = related[0]
        rp = PARTS[r['part']]
        r_hero = get_hero_image(r['slug'])
        r_img = f'<img src="{r_hero}" alt="" class="read-next-img" loading="lazy" width="600" height="338">' if r_hero else ''
        r_audio = ' <span class="read-next-audio">Audio</span>' if (r.get('has_audio') or r.get('has_discussion')) else ''
        read_next_cards.append(f'''      <a href="/articles/{html_mod.escape(r['slug'])}" class="read-next-card" style="--section-color:{rp['color']}">
        <div class="read-next-img-wrap">{r_img}</div>
        <div class="read-next-body">
          <span class="read-next-label">More in {html_mod.escape(essay['part'])}</span>
          <span class="read-next-kicker" style="color:{rp['color']}">{rp['label']}</span>
          <h3 class="read-next-title">{html_mod.escape(r['title'])}</h3>
          <span class="read-next-meta">{r['reading_time']} min read{r_audio}</span>
        </div>
      </a>''')

    # Card 2: newest article
    if next_essay:
        np = PARTS[next_essay['part']]
        n_hero = get_hero_image(next_essay['slug'])
        n_img = f'<img src="{n_hero}" alt="" class="read-next-img" loading="lazy" width="600" height="338">' if n_hero else ''
        n_audio = ' <span class="read-next-audio">Audio</span>' if (next_essay.get('has_audio') or next_essay.get('has_discussion')) else ''
        read_next_cards.append(f'''      <a href="/articles/{html_mod.escape(next_essay['slug'])}" class="read-next-card" style="--section-color:{np['color']}">
        <div class="read-next-img-wrap">{n_img}</div>
        <div class="read-next-body">
          <span class="read-next-label">Latest</span>
          <span class="read-next-kicker" style="color:{np['color']}">{np['label']}</span>
          <h3 class="read-next-title">{html_mod.escape(next_essay['title'])}</h3>
          <span class="read-next-meta">{next_essay['reading_time']} min read{n_audio}</span>
        </div>
      </a>''')

    read_next_html = ''
    if read_next_cards:
        cards_joined = '\n'.join(read_next_cards)
        read_next_html = f'''
  <section class="read-next-section" aria-label="Read next">
    <h2 class="read-next-heading">Read next</h2>
    <div class="read-next-grid">
{cards_joined}
    </div>
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
        <div class="audio-label">Listen to this article <span class="ai-narrated-badge">AI narrated <svg viewBox="0 0 16 16" fill="currentColor" width="12" height="12"><circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8 7v4M8 5.5v-.01"/></svg></span></div>
        <div class="audio-meta">{est_listen} min</div>
      </div>
      <div class="audio-progress-wrap" id="audioProgressWrap">
        <div class="audio-progress-track"><div class="audio-progress-bar" id="audioProgressBar"></div></div>
        <div class="scrub-thumb" id="audioThumb"></div>
      </div>
      <div class="audio-time" id="audioTime">0:00</div>
      <div class="audio-speed" id="audioSpeed" title="Playback speed">1.25&times;</div>
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
      <div class="discussion-speed" id="discussionSpeed" title="Playback speed">1.25&times;</div>
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

    further_reading_html, further_reading_missing = build_further_reading_html(essay.get('sources', []))

    issue = get_issue_for_slug(essay['slug'])
    issue_badge_html = ''
    if issue:
        from datetime import datetime as _dt
        _issue_date = _dt.strptime(issue['date'], '%Y-%m-%d').strftime('%B %Y')
        issue_badge_html = f'\n    <div class="article-issue-badge"><a href="/issues/{issue["number"]}">Issue {issue["number"]} &middot; {_issue_date}</a></div>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{make_head(f"{essay['title']} — History Future Now", essay['excerpt'], f"/articles/{essay['slug']}", pi['color'], json_ld, og_image=hero_img, pub_date=essay.get('pub_date'), noindex=is_review)}
</head>
<body>

{make_nav(essay['part'])}
<div class="back-bar" id="backBar" data-section-href="/{pi['slug']}" data-section-label="{html_mod.escape(essay['part'])}" data-section-color="{pi['color']}">
  <div class="back-bar-inner">
    <a href="/{pi['slug']}" style="color:{pi['color']}">&larr; {html_mod.escape(essay['part'])}</a>
  </div>
</div>

{make_search_overlay()}

<article class="page-container" data-pagefind-body>
  {breadcrumbs}
  <header class="article-header">
    <div class="article-kicker" style="color:{pi['color']}" data-pagefind-meta="section:{html_mod.escape(essay['part'])}" data-pagefind-filter="section:{html_mod.escape(essay['part'])}">{pi['label']} &middot; {html_mod.escape(essay['part'])}</div>{issue_badge_html}
    <h1 data-pagefind-meta="title">{te}</h1>
    <div class="article-meta" data-pagefind-ignore>
      <span class="article-reading-time">{essay['reading_time']} min read</span>
      {f'<span class="meta-sep">&middot;</span><time class="article-date" datetime="{essay["pub_date"]}">{format_date_human(essay["pub_date"])}</time>' if essay.get('pub_date') else ''}
    </div>{chart_badge}
  </header>{hero_img_html}
{audio_player}
  {make_share_bar(essay, 'top', pi)}
  <div class="article-body">
    {body_before_refs}
  </div>
<div data-pagefind-ignore>
{further_reading_html}
{end_of_article_cta}
  <div class="article-references">
    {body_refs}
  </div>
  {make_share_bar(essay, 'bottom', pi)}

  <div class="article-footer">
    <a href="/{pi['slug']}" class="back-to-section" style="color:{pi['color']}">&larr; All {html_mod.escape(essay['part'])} articles</a>
    <a href="#" class="back-to-top" onclick="window.scrollTo({{top:0,behavior:'smooth'}});return false;">&uarr; Back to top</a>
  </div>
{read_next_html}
</div>
</article>

{make_footer()}
{chart_script}
{make_audio_player_script() if (has_audio or has_discussion) else ''}
<script src="/js/share.js?v={_js_hash('share.js')}"></script>
{'<script>(function(){var isUK=false;try{var tz=Intl.DateTimeFormat().resolvedOptions().timeZone||"";isUK=tz==="Europe/London"||tz==="Europe/Belfast"||tz==="Europe/Guernsey"||tz==="Europe/Isle_of_Man"||tz==="Europe/Jersey";}catch(e){}if(!isUK){var links=document.querySelectorAll(".further-reading-amazon");for(var i=0;i<links.length;i++){var q=links[i].getAttribute("href").split("?k=")[1];if(q)links[i].href="https://www.amazon.com/s?k="+q;}}})();</script>' if essay.get('sources') else ''}
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

def _split_intro_paragraphs(html):
    """Split intro HTML into first paragraph and rest (each <p>...</p>). Returns (first, rest_html)."""
    first = ""
    rest_parts = []
    remaining = html.strip()
    in_first = True
    while remaining:
        if remaining.startswith("<p>"):
            end = remaining.find("</p>", 3)
            if end == -1:
                break
            para = remaining[: end + 4]
            remaining = remaining[end + 4 :].lstrip()
            if in_first:
                first = para
                in_first = False
            else:
                rest_parts.append(para)
        else:
            break
    rest_html = "\n".join(rest_parts) if rest_parts else ""
    return first, rest_html


def _build_section_editorial(part_name, pi):
    """Build the editorial intro HTML block for a section page, including charts."""
    intro_html, chart_ids = _get_section_intro(part_name)
    if not intro_html:
        return "", ""

    first_para, rest_html = _split_intro_paragraphs(intro_html)
    if rest_html:
        prose_block = f'''    <div class="section-editorial-prose">
{first_para}
    </div>
    <div class="section-editorial-more" id="sectionEditorialMore" hidden>
{rest_html}
    </div>
    <p class="section-editorial-toggle-wrap">
      <button type="button" class="section-editorial-toggle" id="sectionEditorialToggle" aria-expanded="false">Continue reading</button>
    </p>'''
    else:
        prose_block = f'''    <div class="section-editorial-prose">
{first_para}
    </div>'''

    # Build chart figures for the editorial
    chart_figures = ""
    chart_js_parts = []
    for chart_id in chart_ids:
        # Find the chart definition across all articles (skip data_story entries)
        for slug_charts in ALL_CHARTS.values():
            for ch in slug_charts:
                if ch.get('data_story') or 'id' not in ch:
                    continue
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
{prose_block}
{chart_figures}
  </div>
</div>'''

    # Build chart script block
    chart_script = ""
    if chart_js_parts:
        all_js = "\n".join(_fix_js_string_newlines(js) for js in chart_js_parts)
        chart_script = f'''
<script src="/js/chart.umd.min.js"></script>
<script src="/js/chartjs-plugin-annotation.min.js"></script>
<script>
(function(){{
{CHART_COLORS}
{all_js}
}})();
</script>'''

    return editorial_block, chart_script


def build_section(part_name, essays, new_slugs=None):
    if new_slugs is None:
        new_slugs = set()
    pi = PARTS[part_name]
    se = [e for e in essays if e['part'] == part_name]

    # Build editorial intro (from cached LLM-generated content)
    editorial_block, editorial_chart_script = _build_section_editorial(part_name, pi)

    # Build card grid: first article featured, rest in 3-column grid
    def make_card(e, featured=False):
        chart_count = len(ALL_CHARTS.get(e['slug'], []))
        chart_tag = f'<span>{chart_count} chart{"s" if chart_count != 1 else ""}</span>' if chart_count > 0 else ''
        audio_tag = '<span>Audio</span>' if (e.get('has_audio') or e.get('has_discussion')) else ''
        new_badge = '<span class="card-new-badge">New</span> ' if e['slug'] in new_slugs else ''
        hero_img = get_hero_image(e['slug'])
        img_html = f'<img src="{hero_img}" alt="" class="section-card-img" loading="lazy" width="400" height="220">' if hero_img else ''
        if featured:
            img_html = f'<img src="{hero_img}" alt="" class="section-card-img section-featured-img" loading="lazy" width="1100" height="280">' if hero_img else ''
        cls = "section-featured-card" if featured else "section-card"
        controls = make_card_controls(e, pi)
        return f'''    <a href="/articles/{html_mod.escape(e['slug'])}" class="{cls}">
      <div class="section-card-img-wrap">{img_html}</div>
      <div class="section-card-text">
        <h3>{new_badge}{html_mod.escape(e['title'])}</h3>
        <p>{truncate_excerpt(e['excerpt'], 180)}</p>
        <div class="section-card-meta">
          <span>{e['reading_time']} min read</span>
          {chart_tag}
          {audio_tag}
        </div>
      </div>
      {controls}
    </a>'''

    article_items = ""
    if se:
        article_items = make_card(se[0], featured=True)
        for e in se[1:]:
            article_items += "\n" + make_card(e, featured=False)

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

<div class="section-progress-wrap" id="sectionProgressWrap" data-section-slugs="{html_mod.escape(json.dumps([e['slug'] for e in se]))}">
  <p class="section-progress-text" id="sectionProgressText"></p>
</div>
<div class="card-grid-section">
<div class="section-card-grid">
{article_items}
</div>
</div>

{make_footer()}
<script>
(function(){{ var wrap=document.getElementById('sectionProgressWrap'); if(!wrap) return; try {{ var slugs=JSON.parse(wrap.getAttribute('data-section-slugs')||'[]'); var raw=localStorage.getItem('hfn_read_slugs'); var read=raw?JSON.parse(raw):[]; var set=new Set(read); var n=slugs.filter(function(s){{ return set.has(s); }}).length; var el=document.getElementById('sectionProgressText'); if(el) el.textContent=n+' of '+slugs.length+' articles in this section read'; }} catch(e) {{}} }})();
</script>
{editorial_chart_script}
<script>
(function(){{
  var btn = document.getElementById('sectionEditorialToggle');
  var more = document.getElementById('sectionEditorialMore');
  if (!btn || !more) return;
  btn.addEventListener('click', function(){{
    var expanded = more.hidden;
    more.hidden = !expanded;
    btn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    btn.textContent = expanded ? 'Show less' : 'Continue reading';
  }});
}})();
</script>
</body>
</html>'''

def build_homepage(essays, new_essays=None):
    if new_essays is None:
        new_essays = []
    from chart_defs import get_all_charts, COLORS
    from datetime import datetime
    all_charts = get_all_charts()

    total_articles = len(essays)
    total_charts = sum(len(_charts_for_article(slug)) for slug in all_charts)
    total_reading = sum(e.get('reading_time', 5) for e in essays)
    total_hours = round(total_reading / 60)

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

    # ── Current Issue section (find latest issue with available articles) ──
    slug_map = {e['slug']: e for e in essays}
    current_issue = None
    for candidate in sorted(ISSUES, key=lambda i: i['number'], reverse=True):
        candidate_essays = [slug_map[s] for s in candidate['articles'] if s in slug_map]
        if candidate_essays:
            current_issue = candidate
            break
    if current_issue is None:
        current_issue = get_current_issue()
    ci_essays = [slug_map[s] for s in current_issue['articles'] if s in slug_map]
    ci_num = current_issue['number']
    ci_date_label = current_issue['label']
    ci_total_reading = sum(e.get('reading_time', 5) for e in ci_essays)

    ci_cards_html = ""
    for i, e in enumerate(ci_essays):
        pi = PARTS[e['part']]
        n_charts = len(_charts_for_article(e['slug']))
        chart_badge = f'<span class="latest-badge">{n_charts} charts</span>' if n_charts else ''
        audio_badge = '<span class="latest-badge latest-audio-badge">Audio</span>' if (e.get('has_audio') or e.get('has_discussion')) else ''
        hero_img = get_hero_image(e['slug'])
        img_html = f'<img src="{hero_img}" alt="" class="latest-card-img" loading="lazy">' if hero_img else ''
        controls_html = make_card_controls(e, pi)
        size_class = "latest-hero" if i == 0 else "latest-secondary"
        ci_cards_html += f"""      <a href="/articles/{html_mod.escape(e['slug'])}" class="latest-card {size_class}" style="--accent:{pi['color']}">
        {img_html}
        <div class="latest-kicker">{pi['label']} &middot; {html_mod.escape(e['part'])} {chart_badge} {audio_badge}</div>
        <h3>{html_mod.escape(e['title'])}</h3>
        <p>{truncate_excerpt(e['excerpt'], 200)}</p>
        <span class="latest-meta">{e['reading_time']} min read &rarr;</span>
        {controls_html}
      </a>\n"""

    # ── Previous issue teaser ──
    prev_issue_html = ""
    if ci_num > 1:
        prev = get_issue_by_number(ci_num - 1)
        if prev:
            prev_label = prev['label']
            prev_essays = [slug_map[s] for s in prev['articles'] if s in slug_map]
            prev_titles = "".join(
                f'<li>{html_mod.escape(e["title"])}</li>' for e in prev_essays[:3]
            )
            if len(prev_essays) > 3:
                prev_titles += f'<li class="prev-issue-more">+ {len(prev_essays) - 3} more</li>'
            prev_issue_html = f"""
<div class="prev-issue-teaser">
  <div class="prev-issue-inner">
    <div class="prev-issue-header">
      <span class="prev-issue-label">Previous Issue</span>
      <a href="/issues/{ci_num - 1}" class="prev-issue-link">Issue {ci_num - 1} &middot; {prev_label} &rarr;</a>
    </div>
    <ul class="prev-issue-titles">{prev_titles}</ul>
  </div>
</div>"""

    # ── New: 20 most recent articles by pub_date ──
    def _sort_key_pub_date(e):
        d = e.get('pub_date', '')
        return d if d else '0000-00-00'
    recent_essays = sorted(essays, key=_sort_key_pub_date, reverse=True)[:20]
    by_pub = sorted(essays, key=_sort_key_pub_date, reverse=True)
    # "You might have missed" section removed

    new_cards_html = ""
    for i, e in enumerate(recent_essays):
        pi = PARTS[e['part']]
        n_charts = len(_charts_for_article(e['slug']))
        chart_badge = f'<span class="latest-badge">{n_charts} charts</span>' if n_charts else ''
        audio_badge = '<span class="latest-badge latest-audio-badge">Audio</span>' if (e.get('has_audio') or e.get('has_discussion')) else ''
        hero_img = get_hero_image(e['slug'])
        img_html = f'<img src="{hero_img}" alt="" class="latest-card-img" loading="lazy">' if hero_img else ''
        controls_html = make_card_controls(e, pi)
        size_class = "latest-hero" if i == 0 else "latest-secondary"
        new_cards_html += f"""      <a href="/articles/{html_mod.escape(e['slug'])}" class="latest-card {size_class}" style="--accent:{pi['color']}">
        {img_html}
        <div class="latest-kicker">{pi['label']} &middot; {html_mod.escape(e['part'])} {chart_badge} {audio_badge}</div>
        <h3>{html_mod.escape(e['title'])}</h3>
        <p>{truncate_excerpt(e['excerpt'], 200)}</p>
        <span class="latest-meta">{e['reading_time']} min read &rarr;</span>
        {controls_html}
      </a>\n"""

    # Hero chart removed

    # ── Section teasers ──
    section_chart_picks = {
        'Natural Resources': {'slug':'the-renewables-and-battery-revolution','chart_id':'secChart1',
         'js':"""_regChart('secChart1',()=>{const ctx=document.getElementById('secChart1');new Chart(ctx,{type:'line',data:{labels:['2010','2012','2014','2016','2018','2020','2022','2024'],datasets:[{data:[1100,700,500,350,200,140,110,90],borderColor:'#0d9a5a',backgroundColor:'#0d9a5a18',fill:true,tension:.35,pointRadius:0,borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{enabled:false}},scales:{x:{display:false},y:{display:false}}}});});"""},
        'Global Balance of Power': {'slug':'the-long-term-impact-of-covid-19','chart_id':'secChart2',
         'js':"""_regChart('secChart2',()=>{const ctx=document.getElementById('secChart2');const yrs=[1870,1913,1950,1973,2000,2025];new Chart(ctx,{type:'line',data:{datasets:[{data:_xy(yrs,[55,58,52,48,42,30]),borderColor:'#2563eb',backgroundColor:'#2563eb18',fill:true,tension:.35,pointRadius:0,borderWidth:2},{data:_xy(yrs,[18,12,5,5,12,35]),borderColor:'#c43425',backgroundColor:'#c4342518',fill:true,tension:.35,pointRadius:0,borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{enabled:false}},scales:{x:{type:'linear',display:false},y:{display:false}}}});});"""},
        'Jobs & Economy': {'slug':'robotics-and-slavery','chart_id':'secChart3',
         'js':"""_regChart('secChart3',()=>{const ctx=document.getElementById('secChart3');const yrs=[2020,2022,2024,2026,2028,2030,2032,2035];new Chart(ctx,{type:'line',data:{datasets:[{data:_xy(yrs,[15,13,11,8,6,4,3,2]),borderColor:'#b8751a',backgroundColor:'#b8751a18',fill:true,tension:.35,pointRadius:0,borderWidth:2},{data:_xy(yrs,[50,30,18,12,8,5,3,2]),borderColor:'#7c3aed',backgroundColor:'#7c3aed18',fill:true,tension:.35,pointRadius:0,borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{enabled:false}},scales:{x:{type:'linear',display:false},y:{display:false}}}});});"""},
        'Society': {'slug':'what-does-it-take-to-get-europeans-to-have-a-revolution','chart_id':'secChart4',
         'js':"""_regChart('secChart4',()=>{const ctx=document.getElementById('secChart4');new Chart(ctx,{type:'bar',data:{labels:['1640s','1680s','1770s','1780s','1820s','1840s','1910s','1980s'],datasets:[{data:[1,1,1,2,3,8,4,6],backgroundColor:['#2563eb88','#2563eb88','#c4342588','#c4342588','#7c3aed88','#c4342588','#c4342588','#0d9a5a88'],borderRadius:2,borderSkipped:false}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{enabled:false}},scales:{x:{display:false},y:{display:false}}}});});"""},
    }

    sec_chart_js = ""
    secs = ""
    for pn in sorted(PARTS.keys(), key=lambda p: PARTS[p]['order']):
        pi = PARTS[pn]
        se = [e for e in sorted_essays if e['part'] == pn]
        if not se: continue

        cards = ""
        for e in se[:3]:
            n_charts = len(_charts_for_article(e['slug']))
            chart_badge = f' <span class="card-charts">{n_charts} charts</span>' if n_charts > 0 else ''
            audio_badge = ' <span class="card-audio">Audio</span>' if (e.get('has_audio') or e.get('has_discussion')) else ''
            hero_img = get_hero_image(e['slug'])
            img_html = f'<img src="{hero_img}" alt="" class="home-section-card-img" loading="lazy">' if hero_img else ''
            part_badge = f'<span class="card-part-badge" style="--part-color:{pi["color"]}">{pi["label"]}</span>'
            cards += f"""      <a href="/articles/{html_mod.escape(e['slug'])}" class="card home-section-card" data-section="{pi['slug']}">
        {img_html}
        <div class="card-kicker" style="color:{pi['color']}">{part_badge}{chart_badge}{audio_badge}</div>
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

    # ── Press Play teaser (homepage) ──
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

    # Pick 5 newest audio articles (by pub_date) for the teaser
    audio_by_date = sorted(audio_essays, key=lambda e: e.get('pub_date', '') or '0000-00-00', reverse=True)
    teaser_essays = audio_by_date[:5]

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
        <h2 class="listen-title">Press Play</h2>
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
</section>

<div class="latest-wrap">
  <div class="latest-inner">
    <div class="latest-header">
      <div>
        <h2 class="latest-title">Issue {ci_num}</h2>
        <span class="issue-date-sub">{ci_date_label} &middot; {len(ci_essays)} articles &middot; {ci_total_reading} min reading time</span>
      </div>
      <a href="/issues" class="issue-archive-link">All issues &rarr;</a>
    </div>
    <div class="latest-grid">
{ci_cards_html}    </div>
  </div>
</div>
{prev_issue_html}
<div class="latest-wrap">
  <div class="latest-inner">
    <div class="latest-header">
      <div>
        <h2 class="latest-title">New</h2>
        <span class="issue-date-sub">The 20 most recent articles</span>
      </div>
    </div>
    <div class="latest-grid">
{new_cards_html}    </div>
  </div>
</div>
{listen_section_html}

<div class="section-grid">

{secs}
</div>

{make_footer()}
<script>
(function(){{
{CHART_COLORS}
{sec_chart_js}
}})();
</script>
</body>
</html>"""

def _review_card(e, badge_html=""):
    """Render a single review card."""
    pi = PARTS[e['part']]
    hero_img = get_hero_image(e['slug'])
    img_html = f'<img src="{hero_img}" alt="" style="width:100%;height:180px;object-fit:cover;border-radius:8px 8px 0 0" loading="lazy">' if hero_img else ''
    has_audio = e.get('has_audio') or e.get('has_discussion')
    audio_tag = '<span style="color:#059669;font-size:0.85rem">&#9654; Audio</span>' if has_audio else ''
    return f'''    <a href="/articles/{html_mod.escape(e['slug'])}" style="display:block;text-decoration:none;color:inherit;background:#fff;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;transition:box-shadow 0.2s">
      {img_html}
      <div style="padding:1rem">
        {badge_html}
        <div style="font-size:0.8rem;color:{pi['color']};font-weight:600;margin-bottom:0.25rem">{pi['label']} &middot; {html_mod.escape(e['part'])}</div>
        <h3 style="margin:0 0 0.5rem;font-size:1.1rem;line-height:1.3">{html_mod.escape(e['title'])}</h3>
        <p style="margin:0 0 0.5rem;font-size:0.9rem;color:#6b7280;line-height:1.4">{truncate_excerpt(e['excerpt'], 160)}</p>
        <div style="font-size:0.8rem;color:#9ca3af">{e['reading_time']} min read {audio_tag}</div>
      </div>
    </a>\n'''


def build_review_page(review_essays, released_essays=None):
    """Build a hidden review page listing articles under review and recently released."""
    released_essays = released_essays or []

    # Under review section
    review_cards = ""
    for e in review_essays:
        review_cards += _review_card(e)

    # Released section
    released_cards = ""
    for e in released_essays:
        badge = '<div style="display:inline-block;background:#059669;color:#fff;font-size:0.7rem;font-weight:700;padding:2px 8px;border-radius:4px;margin-bottom:0.5rem;letter-spacing:0.03em">LIVE</div>'
        released_cards += _review_card(e, badge_html=badge)

    released_section = ""
    if released_essays:
        released_section = f'''
  <h2 style="font-family:'Playfair Display',serif;font-size:1.5rem;margin:2.5rem 0 0.5rem;color:#059669">Released</h2>
  <p style="color:#6b7280;margin-bottom:1.5rem">{len(released_essays)} article{"s" if len(released_essays) != 1 else ""} approved and live on the public site.</p>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1.5rem">
{released_cards}  </div>'''

    total = len(review_essays) + len(released_essays)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{make_head("Editorial Review — History Future Now", "Articles under editorial review", noindex=True)}
</head>
<body style="background:#f9fafb;font-family:'Source Sans 3',sans-serif">
<div style="max-width:900px;margin:0 auto;padding:2rem 1rem">
  <div style="margin-bottom:2rem">
    <a href="/" style="color:#6b7280;text-decoration:none;font-size:0.9rem">&larr; Back to site</a>
  </div>
  <h1 style="font-family:'Playfair Display',serif;font-size:2rem;margin-bottom:0.5rem">Editorial Review</h1>
  <p style="color:#6b7280;margin-bottom:0.5rem">{total} articles in this batch &mdash; {len(released_essays)} released, {len(review_essays)} under review.</p>

  <h2 style="font-family:'Playfair Display',serif;font-size:1.5rem;margin:2rem 0 0.5rem;color:#b45309">Under Review</h2>
  <p style="color:#6b7280;margin-bottom:1.5rem">{len(review_essays)} article{"s" if len(review_essays) != 1 else ""} awaiting approval. Not visible on the public site.</p>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:1.5rem">
{review_cards}  </div>
{released_section}
</div>
</body>
</html>'''


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

    # Count by issue
    slug_to_issue = build_slug_to_issue_map()
    issue_counts = {}
    for ae in audio_essays:
        iss_num = slug_to_issue.get(ae['slug'])
        if iss_num is not None:
            issue_counts[iss_num] = issue_counts.get(iss_num, 0) + 1

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

    # Build section filter tabs
    filter_tabs = '<button class="lp-tab active" data-filter="all">All</button>\n'
    for pn in sorted(PARTS.keys(), key=lambda p: PARTS[p]['order']):
        pi = PARTS[pn]
        count = section_counts.get(pn, 0)
        if count > 0:
            filter_tabs += f'      <button class="lp-tab" data-filter="{html_mod.escape(pi["slug"])}" style="--tab-color:{pi["color"]}">{pi["label"].replace("Part ", "").strip()}: {html_mod.escape(pn)} <span class="lp-tab-count">{count}</span></button>\n'

    # Build issue filter tabs (descending order — newest first)
    issue_tabs = '<button class="lp-tab active" data-issue="all">All</button>\n'
    for iss_num in sorted(issue_counts.keys(), reverse=True):
        iss = get_issue_by_number(iss_num)
        if iss:
            count = issue_counts[iss_num]
            issue_tabs += f'      <button class="lp-tab" data-issue="{iss_num}">Issue {iss_num} <span class="lp-tab-count">{count}</span></button>\n'

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

        lp_controls = make_card_controls(ae, pi)
        row_issue = slug_to_issue.get(ae['slug'], '')
        rows_html += f'''    <a href="/articles/{html_mod.escape(ae['slug'])}" class="lp-row" data-section="{html_mod.escape(pi['slug'])}" data-audio-type="{audio_type_filter}" data-issue="{row_issue}">
      <svg class="lp-row-play" viewBox="0 0 24 24" fill="{pi['color']}"><path d="M8 5v14l11-7z"/></svg>
      <div class="lp-row-main">
        <div class="lp-row-title">{html_mod.escape(ae['title'])}</div>
        <div class="lp-row-excerpt">{excerpt_text}</div>
      </div>
      <span class="lp-row-section" style="color:{pi['color']};border-color:{pi['color']}">{html_mod.escape(pi['label'])}</span>
      <span class="lp-row-duration">{listen_time} min</span>
      <span class="lp-row-type">{type_label}</span>
      {lp_controls}
    </a>\n'''

    breadcrumbs = make_breadcrumbs([
        ('Home', '/'),
        ('Listen', None),
    ])

    filter_script = '''<script>
(function(){
  var sectionTabs = document.querySelectorAll('.lp-section-tabs .lp-tab');
  var issueTabs = document.querySelectorAll('.lp-issue-tabs .lp-tab');
  var typeBtns = document.querySelectorAll('.lp-type-btn');
  var rows = document.querySelectorAll('.lp-row');
  var countEl = document.getElementById('lpVisibleCount');
  var currentSection = 'all';
  var currentIssue = 'all';
  var currentType = 'all';

  function applyFilters(){
    var visible = 0;
    rows.forEach(function(r){
      var matchSection = currentSection === 'all' || r.dataset.section === currentSection;
      var matchIssue = currentIssue === 'all' || r.dataset.issue === currentIssue;
      var matchType = currentType === 'all' || r.dataset.audioType === currentType || (currentType === 'narration' && r.dataset.audioType === 'both') || (currentType === 'discussion' && r.dataset.audioType === 'both');
      if(matchSection && matchIssue && matchType){ r.style.display = ''; visible++; }
      else { r.style.display = 'none'; }
    });
    if(countEl) countEl.textContent = visible;
  }

  sectionTabs.forEach(function(t){
    t.addEventListener('click', function(){
      sectionTabs.forEach(function(x){ x.classList.remove('active'); });
      t.classList.add('active');
      currentSection = t.dataset.filter;
      applyFilters();
      updateHash();
    });
  });

  issueTabs.forEach(function(t){
    t.addEventListener('click', function(){
      issueTabs.forEach(function(x){ x.classList.remove('active'); });
      t.classList.add('active');
      currentIssue = t.dataset.issue;
      applyFilters();
      updateHash();
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

  function updateHash(){
    var parts = [];
    if(currentSection !== 'all') parts.push('section=' + currentSection);
    if(currentIssue !== 'all') parts.push('issue=' + currentIssue);
    var hash = parts.length ? '#' + parts.join('&') : '';
    history.replaceState(null, '', '/listen' + hash);
  }

  // Restore filters from URL hash
  var hash = location.hash.replace('#','');
  if(hash){
    hash.split('&').forEach(function(pair){
      var kv = pair.split('=');
      if(kv[0] === 'section' && kv[1]){
        sectionTabs.forEach(function(t){ if(t.dataset.filter === kv[1]) t.click(); });
      }
      if(kv[0] === 'issue' && kv[1]){
        issueTabs.forEach(function(t){ if(t.dataset.issue === kv[1]) t.click(); });
      }
    });
    // Legacy support: bare hash without key=value is a section filter
    if(hash.indexOf('=') === -1){
      sectionTabs.forEach(function(t){ if(t.dataset.filter === hash) t.click(); });
    }
  }

  // Stop control button clicks from navigating to the article
  document.querySelectorAll('.lp-row .q-add-btn, .lp-row .card-play-btn, .lp-row .card-bookmark-btn').forEach(function(btn){
    btn.addEventListener('click', function(e){ e.preventDefault(); e.stopPropagation(); });
  });
})();
</script>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{make_head("Press Play — History Future Now", f"{audio_count} articles available as audio narration. {total_hours}+ hours of content.", "/listen")}
</head>
<body>

{make_nav("Listen")}

{make_search_overlay()}

<section class="lp-hero">
  <div class="lp-hero-inner">
    {breadcrumbs}
    <h1 class="lp-hero-title">Press Play</h1>
    <p class="lp-hero-desc">Every article, narrated in full with two alternating voices. Queue them up and listen on the go.</p>
    <div class="lp-hero-stats">
      <span class="lp-stat"><strong>{audio_count}</strong> articles</span>
      <span class="lp-stat-sep">&middot;</span>
      <span class="lp-stat"><strong>{total_hours}+</strong> hours</span>
      <span class="lp-stat-sep">&middot;</span>
      <span class="lp-stat"><strong>4</strong> sections</span>
      <span class="lp-stat-sep">&middot;</span>
      <span class="lp-stat"><strong>{len(issue_counts)}</strong> issues</span>
    </div>
    <button class="q-play-all lp-queue-all" id="queueAllBtn" data-items="{queue_all_json}">
      <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
      Queue All {audio_count} Articles
    </button>
  </div>
</section>

<div class="lp-filters">
  <div class="lp-filters-inner">
    <div class="lp-filter-group lp-section-tabs">
      <span class="lp-filter-label">Section</span>
      {filter_tabs}
    </div>
    <div class="lp-filter-group lp-issue-tabs">
      <span class="lp-filter-label">Issue</span>
      {issue_tabs}
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
            custom_url = b.get('url')
            if custom_url:
                buy_link = f'<a class="lib-book-amazon lib-book-direct" href="{html_mod.escape(custom_url)}" target="_blank" rel="noopener noreferrer">Buy</a>'
            else:
                search_query = urllib.parse.quote_plus(f'{b["title"]} {b["author"]}')
                buy_link = f'<a class="lib-book-amazon" href="https://www.amazon.co.uk/s?k={search_query}" data-query="{search_query}" target="_blank" rel="noopener noreferrer">Amazon</a>'
            book_items += f'''      <div class="lib-book-item">
        <span class="lib-book-title">{html_mod.escape(b["title"])}</span>
        <span class="lib-book-author">{html_mod.escape(b["author"])}</span>
        {buy_link}
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


def build_saved():
    """Build the /saved page — bookmarked articles from localStorage (My Library)."""
    breadcrumbs = make_breadcrumbs([('Home', '/'), ('Saved', None)])
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{make_head("Saved articles — History Future Now", "Articles you have bookmarked for later.", "/saved")}
</head>
<body>

{make_nav("Saved")}

<section class="saved-hero">
  <div class="saved-hero-inner">
    {breadcrumbs}
    <h1 class="saved-hero-title">Saved articles</h1>
    <p class="saved-hero-desc">Articles you have bookmarked. Remove any with the × button.</p>
  </div>
</section>

<div class="page-container">
  <div id="savedGrid" class="saved-grid" aria-live="polite"></div>
  <div id="savedEmpty" class="saved-empty" style="display:none">
    <p>No saved articles yet. Bookmark articles from any article page or the Listen page to see them here.</p>
    <p><a href="/">Browse articles</a> or <a href="/listen">Listen</a>.</p>
  </div>
</div>

{make_footer()}

<script>
(function() {{
  var BOOKMARK_KEY = 'hfn_bookmarks';
  var grid = document.getElementById('savedGrid');
  var empty = document.getElementById('savedEmpty');

  function getBookmarks() {{
    try {{
      var raw = localStorage.getItem(BOOKMARK_KEY);
      return raw ? JSON.parse(raw) : [];
    }} catch (e) {{ return []; }}
  }}

  function setBookmarks(arr) {{
    try {{
      localStorage.setItem(BOOKMARK_KEY, JSON.stringify(arr));
    }} catch (e) {{}}
  }}

  function escapeHtml(s) {{
    var div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }}

  function removeBookmark(slug) {{
    var arr = getBookmarks().filter(function (b) {{ return b.slug !== slug; }});
    setBookmarks(arr);
    render();
    if (window.HFNQueue && typeof HFNQueue._reloadBookmarks === 'function') {{
      HFNQueue._reloadBookmarks();
    }}
  }}

  function render() {{
    var list = getBookmarks();
    if (list.length === 0) {{
      grid.innerHTML = '';
      grid.style.display = 'none';
      empty.style.display = 'block';
      return;
    }}
    empty.style.display = 'none';
    grid.style.display = 'grid';
    grid.innerHTML = list.map(function (b) {{
      var sectionHtml = b.section
        ? '<span class="saved-card-section" style="color:' + escapeHtml(b.color || '') + '">' + escapeHtml(b.section) + '</span>'
        : '';
      return '<article class="saved-card">' +
        '<div class="saved-card-info">' +
          sectionHtml +
          '<a href="' + escapeHtml(b.url) + '" class="saved-card-link">' + escapeHtml(b.title) + '</a>' +
        '</div>' +
        '<button type="button" class="saved-card-remove" aria-label="Remove from saved" data-slug="' + escapeHtml(b.slug) + '">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M18 6L6 18M6 6l12 12"/></svg>' +
        '</button>' +
      '</article>';
    }}).join('');
    grid.querySelectorAll('.saved-card-remove').forEach(function (btn) {{
      btn.addEventListener('click', function () {{
        removeBookmark(this.getAttribute('data-slug'));
      }});
    }});
  }}

  render();
}})();
</script>
</body>
</html>'''


def build_issue_page(issue, essays, all_charts):
    """Build an individual issue page: /issues/N/."""
    slug_map = {e['slug']: e for e in essays}
    issue_essays = [slug_map[s] for s in issue['articles'] if s in slug_map]

    num = issue['number']
    date_label = issue['label']
    total_reading = sum(e.get('reading_time', 5) for e in issue_essays)
    article_count = len(issue_essays)

    breadcrumbs = make_breadcrumbs([
        ('Home', '/'),
        ('Issues', '/issues'),
        (f'Issue {num}', None),
    ])

    def issue_card(e, featured=False):
        pi = PARTS[e['part']]
        chart_count = len(all_charts.get(e['slug'], []))
        chart_tag = f'<span>{chart_count} chart{"s" if chart_count != 1 else ""}</span>' if chart_count > 0 else ''
        audio_tag = '<span>Audio</span>' if (e.get('has_audio') or e.get('has_discussion')) else ''
        hero_img = get_hero_image(e['slug'])
        section_badge = f'<span class="issue-card-section" style="color:{pi["color"]}">{pi["label"]}: {html_mod.escape(e["part"])}</span>'

        if featured:
            img_html = f'<img src="{hero_img}" alt="" class="section-card-img section-featured-img" loading="lazy" width="1100" height="280">' if hero_img else ''
            cls = "section-featured-card"
        else:
            img_html = f'<img src="{hero_img}" alt="" class="section-card-img" loading="lazy" width="400" height="220">' if hero_img else ''
            cls = "section-card"

        controls = make_card_controls(e, pi)
        return f'''    <a href="/articles/{html_mod.escape(e['slug'])}" class="{cls}">
      <div class="section-card-img-wrap">{img_html}</div>
      <div class="section-card-text">
        {section_badge}
        <h3>{html_mod.escape(e['title'])}</h3>
        <p>{truncate_excerpt(e['excerpt'], 180)}</p>
        <div class="section-card-meta">
          <span>{e['reading_time']} min read</span>
          {chart_tag}
          {audio_tag}
        </div>
      </div>
      {controls}
    </a>'''

    article_cards = ""
    if issue_essays:
        article_cards = issue_card(issue_essays[0], featured=True)
        for e in issue_essays[1:]:
            article_cards += "\n" + issue_card(e, featured=False)

    prev_link = ""
    next_link = ""
    if num > 1:
        prev_link = f'<a href="/issues/{num - 1}" class="issue-nav-link issue-nav-prev">&larr; Issue {num - 1}</a>'
    if num < len(ISSUES):
        next_link = f'<a href="/issues/{num + 1}" class="issue-nav-link issue-nav-next">Issue {num + 1} &rarr;</a>'
    issue_nav = f'<div class="issue-page-nav">{prev_link}<span></span>{next_link}</div>' if prev_link or next_link else ''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{make_head(f"Issue {num} — History Future Now", f"Issue {num} ({date_label}): {article_count} articles on history, geopolitics, and the forces shaping the future.", f"/issues/{num}", "#c43425")}
</head>
<body>

{make_nav("Issues")}

{make_search_overlay()}

<section class="issue-hero">
  <div class="issue-hero-inner">
    {breadcrumbs}
    <div class="issue-number-label">Issue {num}</div>
    <h1 class="issue-title">{date_label}</h1>
    <div class="issue-meta">{article_count} articles &middot; {total_reading} min total reading time</div>
  </div>
</section>

<div class="card-grid-section">
<div class="section-card-grid">
{article_cards}
</div>
</div>

{issue_nav}

{make_footer()}
</body>
</html>'''


def build_charts_page(essays, all_charts):
    """Build the charts gallery page: /charts."""
    slug_map = {e['slug']: e for e in essays}

    breadcrumbs = make_breadcrumbs([
        ('Home', '/'),
        ('Charts', None),
    ])

    # Collect all articles with charts, grouped by section
    articles_with_charts = []
    for slug, charts in all_charts.items():
        real_charts = [c for c in charts if not c.get('data_story')]
        if not real_charts:
            continue
        e = slug_map.get(slug)
        if not e:
            continue
        pi = PARTS.get(e['part'], PARTS['Society'])
        articles_with_charts.append({
            'essay': e,
            'charts': real_charts,
            'part': e['part'],
            'pi': pi,
        })

    # Sort by section order, then by title
    part_order = {pn: PARTS[pn]['order'] for pn in PARTS}
    articles_with_charts.sort(key=lambda x: (part_order.get(x['part'], 99), x['essay']['title']))

    # Filter buttons — use subject names, not "Part N"
    filter_buttons = '<button class="charts-filter-btn active" data-filter="all">All</button>'
    for pn in sorted(PARTS.keys(), key=lambda p: PARTS[p]['order']):
        pi = PARTS[pn]
        chart_count = sum(len(a['charts']) for a in articles_with_charts if a['part'] == pn)
        if chart_count > 0:
            filter_buttons += f'<button class="charts-filter-btn" data-filter="{pi["slug"]}">{html_mod.escape(pn)} <span class="charts-filter-count">{chart_count}</span></button>'

    # Check if any chart needs the geo library
    needs_geo = any(c.get('geo') for item in articles_with_charts for c in item['charts'])
    geo_script_tag = '\n<script src="/js/chartjs-chart-geo.umd.min.js"></script>' if needs_geo else ''
    geo_data_var = '\nvar _geoDataPromise=fetch("/js/countries-110m.json").then(r=>r.json());' if needs_geo else ''

    # Build chart cards grouped by section with headers
    deferred_js_lines = []
    cards_html = ""
    current_section = None
    for item in articles_with_charts:
        e = item['essay']
        pi = item['pi']
        slug = e['slug']
        part_slug = pi['slug']
        part_name = item['part']

        if part_name != current_section:
            current_section = part_name
            section_color = pi['color']
            cards_html += f'''  <div class="charts-section-header" data-section="{part_slug}">
    <span class="charts-section-accent" style="background:{section_color}"></span>
    <div>
      <h2 class="charts-section-title">{html_mod.escape(part_name)}</h2>
      <p class="charts-section-desc">{html_mod.escape(pi['desc'])}</p>
    </div>
  </div>
'''

        for idx, c in enumerate(item['charts']):
            orig_id = c['id']
            unique_id = f"chart_{slug}_{orig_id}_{idx}"
            mod_js = _fix_js_string_newlines(c['js']).replace(f"getElementById('{orig_id}')", f"getElementById('{unique_id}')")
            safe_js = mod_js.replace("</script>", "<\\/script>")
            deferred_js_lines.append(f"window.__chartInits['{unique_id}'] = function() {{\n{safe_js}\n}};")

            chart_copy = dict(c)
            chart_copy['id'] = unique_id
            chart_html = make_chart_html(chart_copy)

            chart_anchor = f"chart-{orig_id}"
            article_chart_url = f"/articles/{html_mod.escape(slug)}#{chart_anchor}"
            cards_html += f'''  <div class="charts-card" data-section="{part_slug}">
    {chart_html}
    <a href="{article_chart_url}" class="charts-article-link">Read the full article &rarr;</a>
  </div>
'''

    total_charts = sum(len(item['charts']) for item in articles_with_charts)

    lazy_observer_script = r'''(function(){
  window.__chartInits = window.__chartInits || {};
  function runInit(canvas) {
    var id = canvas.id;
    if (window.__chartInits[id]) {
      try { window.__chartInits[id](); } catch (e) { console.error("[charts] init " + id, e); }
      delete window.__chartInits[id];
    }
  }
  var obs = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        runInit(entry.target);
        obs.unobserve(entry.target);
      }
    });
  }, { rootMargin: '200px' });
  function startObserving() {
    var canvases = document.querySelectorAll('.chart-area canvas');
    canvases.forEach(function(c) {
      obs.observe(c);
    });
    var vh = window.innerHeight || document.documentElement.clientHeight;
    canvases.forEach(function(c) {
      var cr = c.getBoundingClientRect();
      if (cr.top < vh + 200 && cr.bottom > -200) {
        runInit(c);
        obs.unobserve(c);
      }
    });
  }
  if (document.readyState === 'complete') startObserving();
  else window.addEventListener('load', startObserving);
})();'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{make_head("Charts — History Future Now", f"Browse {total_charts} interactive data visualisations from History Future Now. Every chart links to its source article.", "/charts", "#c43425")}
<script src="/js/chart.umd.min.js"></script>
<script src="/js/chartjs-plugin-annotation.min.js"></script>{geo_script_tag}
</head>
<body>

{make_nav("Charts")}

{make_search_overlay()}

<section class="charts-hero">
  <div class="charts-hero-inner">
    {breadcrumbs}
    <h1 class="charts-title">Charts</h1>
    <p class="charts-intro">Interactive data visualisations from every article. Hover for details. Click through to read the analysis.</p>
    <div class="charts-filters">
      {filter_buttons}
    </div>
  </div>
</section>

<div class="charts-grid">
{cards_html}</div>

<section class="charts-bottom-nav">
  <div class="charts-bottom-nav-inner">
    <p class="charts-bottom-nav-label">Jump to section</p>
    <div class="charts-filters charts-filters-bottom">
      {filter_buttons}
    </div>
  </div>
</section>

{make_footer()}
<script>
(function(){{{geo_data_var}
{CHART_COLORS}
window.__chartInits = window.__chartInits || {{}};
{"\n".join(deferred_js_lines)}
}})();
</script>
<script>
{lazy_observer_script}
</script>
<script>
(function(){{
  const btns = document.querySelectorAll('.charts-filter-btn');
  const cards = document.querySelectorAll('.charts-card');
  const headers = document.querySelectorAll('.charts-section-header');
  const grid = document.querySelector('.charts-grid');
  function applyFilter(f) {{
    btns.forEach(b => {{
      if (b.dataset.filter === f) b.classList.add('active');
      else b.classList.remove('active');
    }});
    cards.forEach(c => {{
      c.style.display = (f === 'all' || c.dataset.section === f) ? '' : 'none';
    }});
    headers.forEach(h => {{
      h.style.display = (f === 'all' || h.dataset.section === f) ? '' : 'none';
    }});
  }}
  btns.forEach(btn => {{
    btn.addEventListener('click', () => {{
      applyFilter(btn.dataset.filter);
      if (btn.closest('.charts-filters-bottom') && grid) {{
        grid.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }}
    }});
  }});
}})();
</script>
<script src="/js/share.js?v={_js_hash('share.js')}"></script>
</body>
</html>'''


def build_issues_archive(essays, all_charts, issues_list=None):
    """Build the issues archive page: /issues/."""
    if issues_list is None:
        issues_list = ISSUES
    slug_map = {e['slug']: e for e in essays}
    from datetime import datetime

    breadcrumbs = make_breadcrumbs([
        ('Home', '/'),
        ('Issues', None),
    ])

    issue_cards = ""
    for issue in sorted(issues_list, key=lambda i: i['number'], reverse=True):
        num = issue['number']
        date_label = issue['label']
        article_count = len(issue['articles'])

        lead_slug = issue['articles'][0] if issue['articles'] else None
        lead_essay = slug_map.get(lead_slug)
        hero_img = get_hero_image(lead_slug) if lead_slug else None
        img_html = f'<img src="{hero_img}" alt="" class="issue-archive-img" loading="lazy" width="400" height="220">' if hero_img else ''

        titles_html = ""
        for slug in issue['articles'][:4]:
            e = slug_map.get(slug)
            if e:
                titles_html += f'<li>{html_mod.escape(e["title"])}</li>'
        if len(issue['articles']) > 4:
            titles_html += f'<li class="issue-archive-more">+ {len(issue["articles"]) - 4} more</li>'

        total_charts = sum(len(all_charts.get(s, [])) for s in issue['articles'])
        chart_note = f' &middot; {total_charts} charts' if total_charts else ''

        issue_cards += f'''  <a href="/issues/{num}" class="issue-archive-card">
    <div class="issue-archive-img-wrap">{img_html}</div>
    <div class="issue-archive-text">
      <div class="issue-archive-number">Issue {num}</div>
      <h3>{date_label}</h3>
      <ul class="issue-archive-titles">{titles_html}</ul>
      <div class="issue-archive-meta">{article_count} articles{chart_note}</div>
    </div>
  </a>
'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
{make_head("All Issues — History Future Now", "Browse all issues of History Future Now — fortnightly collections of data-driven essays on history, geopolitics, and the future.", "/issues", "#c43425")}
</head>
<body>

{make_nav("Issues")}

{make_search_overlay()}

<section class="issue-hero">
  <div class="issue-hero-inner">
    {breadcrumbs}
    <h1 class="issue-title">All Issues</h1>
    <div class="issue-meta">{len(issues_list)} issues &middot; {len(essays)} articles</div>
  </div>
</section>

<div class="issue-archive-grid">
{issue_cards}
</div>

{make_footer()}
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
        e['is_review'] = e['slug'] in REVIEW_SLUGS

    # Split into public and review essays
    public_essays = [e for e in essays if not e.get('is_review')]
    review_essays = [e for e in essays if e.get('is_review')]

    if review_essays:
        print(f"\n  📋 {len(review_essays)} articles under review (hidden from public):")
        for e in review_essays:
            print(f"     [{e['part']}] {e['title'][:60]}")

    # Resolve file mtime for new articles (needed for FIFO ordering)
    for e in public_essays:
        if e['is_new']:
            e['mtime'] = os.path.getmtime(e['filepath'])

    new_essays = sorted(
        [e for e in public_essays if e['is_new']],
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

    # ── Validate sources against library_data ──
    from library_data import BOOKS as _LIB_BOOKS
    _book_titles = {b['title'].lower().strip() for b in _LIB_BOOKS}
    _missing_books = []  # list of (article_title, book_title)
    for e in essays:
        for src in e.get('sources', []):
            if src.lower().strip() not in _book_titles:
                _missing_books.append((e['title'], src))

    if _missing_books:
        print(f"\n  ❌ {len(_missing_books)} book(s) in article sources not found in library_data.py:")
        for article_title, book_title in _missing_books:
            print(f"     • \"{book_title}\" (in: {article_title[:55]})")
        print("     Add missing books to BOOKS in library_data.py before deploying.\n")
        sys.exit(1)

    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

    print("\nBuilding article pages...")
    for e in essays:
        is_review = e.get('is_review', False)
        (ARTICLES_DIR / f"{e['slug']}.html").write_text(
            build_article(e, public_essays, is_review=is_review), encoding='utf-8')
    print(f"  Built {len(essays)} article pages ({len(review_essays)} with noindex)")

    print("Building section pages...")
    for pn, pi in PARTS.items():
        (OUTPUT_DIR / f"{pi['slug']}.html").write_text(build_section(pn, public_essays, new_slugs), encoding='utf-8')
    print(f"  Built {len(PARTS)} section pages")

    # Filter issues: remove review slugs from article lists, skip empty issues
    public_issues = []
    for issue in ISSUES:
        filtered_articles = [s for s in issue['articles'] if s not in REVIEW_SLUGS]
        if filtered_articles:
            public_issue = dict(issue)
            public_issue['articles'] = filtered_articles
            public_issues.append(public_issue)

    print("Building issue pages...")
    all_charts = get_all_charts()
    issues_dir = OUTPUT_DIR / "issues"
    issues_dir.mkdir(parents=True, exist_ok=True)
    for issue in public_issues:
        issue_dir = issues_dir / str(issue['number'])
        issue_dir.mkdir(parents=True, exist_ok=True)
        (issue_dir / "index.html").write_text(build_issue_page(issue, public_essays, all_charts), encoding='utf-8')
    (issues_dir / "index.html").write_text(build_issues_archive(public_essays, all_charts, public_issues), encoding='utf-8')
    print(f"  Built {len(public_issues)} issue pages + archive (skipped {len(ISSUES) - len(public_issues)} empty)")

    print("Building homepage...")
    (OUTPUT_DIR / "index.html").write_text(build_homepage(public_essays, new_essays), encoding='utf-8')
    print("  Built homepage")

    print("Building listen page...")
    (OUTPUT_DIR / "listen.html").write_text(build_listen_page(public_essays), encoding='utf-8')
    print("  Built listen page")

    print("Building library page...")
    (OUTPUT_DIR / "library.html").write_text(build_library(), encoding='utf-8')
    print("  Built library page")

    print("Building saved page...")
    (OUTPUT_DIR / "saved.html").write_text(build_saved(), encoding='utf-8')
    print("  Built saved page")

    print("Building charts page...")
    (OUTPUT_DIR / "charts.html").write_text(build_charts_page(public_essays, all_charts), encoding='utf-8')
    print("  Built charts page")

    # ── Review page (hidden, not linked) ──
    print("Building review page...")
    released_essays = [e for e in public_essays if e['slug'] in RELEASED_FROM_REVIEW]
    review_dir = OUTPUT_DIR / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "index.html").write_text(build_review_page(review_essays, released_essays), encoding='utf-8')
    print(f"  Built review page with {len(review_essays)} under review, {len(released_essays)} released")

    # ── SEO files ──
    print("Building SEO files...")
    all_charts = get_all_charts()

    # sitemap.xml — only public articles
    urls = [f'  <url><loc>{SITE_URL}/</loc><priority>1.0</priority><changefreq>weekly</changefreq></url>']
    urls.append(f'  <url><loc>{SITE_URL}/listen</loc><priority>0.8</priority><changefreq>weekly</changefreq></url>')
    urls.append(f'  <url><loc>{SITE_URL}/library</loc><priority>0.7</priority><changefreq>monthly</changefreq></url>')
    urls.append(f'  <url><loc>{SITE_URL}/saved</loc><priority>0.6</priority><changefreq>weekly</changefreq></url>')
    urls.append(f'  <url><loc>{SITE_URL}/issues</loc><priority>0.8</priority><changefreq>weekly</changefreq></url>')
    urls.append(f'  <url><loc>{SITE_URL}/charts</loc><priority>0.8</priority><changefreq>weekly</changefreq></url>')
    for issue in public_issues:
        urls.append(f'  <url><loc>{SITE_URL}/issues/{issue["number"]}</loc><priority>0.6</priority><changefreq>monthly</changefreq></url>')
    for pi in PARTS.values():
        urls.append(f'  <url><loc>{SITE_URL}/{pi["slug"]}</loc><priority>0.8</priority><changefreq>weekly</changefreq></url>')
    for e in public_essays:
        lastmod = f'<lastmod>{e["pub_date"]}</lastmod>' if e.get('pub_date') else ''
        urls.append(f'  <url><loc>{SITE_URL}/articles/{e["slug"]}</loc>{lastmod}<priority>0.7</priority><changefreq>monthly</changefreq></url>')
    sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>'''
    (OUTPUT_DIR / "sitemap.xml").write_text(sitemap, encoding='utf-8')

    # robots.txt — disallow /review/
    robots = f"""User-agent: *
Allow: /
Disallow: /review/
Sitemap: {SITE_URL}/sitemap.xml

User-agent: GPTBot
Allow: /
Disallow: /review/

User-agent: ChatGPT-User
Allow: /
Disallow: /review/

User-agent: Claude-Web
Allow: /
Disallow: /review/

User-agent: PerplexityBot
Allow: /
Disallow: /review/

User-agent: Google-Extended
Allow: /
Disallow: /review/

User-agent: Applebot-Extended
Allow: /
Disallow: /review/
"""
    (OUTPUT_DIR / "robots.txt").write_text(robots, encoding='utf-8')

    # llms.txt - structured content for AI crawlers
    llms_lines = [
        "# History Future Now",
        f"## {SITE_URL}",
        "",
        "Data-driven analysis of the structural forces — demographic, technological, economic — that will shape the next century.",
        f"Author: Tristan Fischer",
        f"Total articles: {len(public_essays)}",
        "",
        "## Sections",
    ]
    for pn in sorted(PARTS.keys(), key=lambda p: PARTS[p]['order']):
        pi = PARTS[pn]
        se = [e for e in public_essays if e['part'] == pn]
        llms_lines.append(f"### {pn} ({len(se)} articles)")
        llms_lines.append(f"- URL: {SITE_URL}/{pi['slug']}")
        llms_lines.append(f"- {pi['desc']}")
        llms_lines.append("")

    llms_lines.append("## Articles")
    llms_lines.append("")
    for e in public_essays:
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

    # search-index.json for client-side search — only public articles
    search_index = []
    for e in public_essays:
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

    # RSS feed — only public articles
    from datetime import datetime
    sorted_by_date = sorted(
        [e for e in public_essays if e.get('pub_date')],
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

    total = len(essays) + len(PARTS) + 1 + 1  # +1 for review page
    print(f"\n✅ Site built: {total} HTML pages ({len(public_essays)} public, {len(review_essays)} under review)")
    print(f"   Output: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
