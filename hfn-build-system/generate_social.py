#!/usr/bin/env python3
"""
Social content generator for History Future Now.

Reads all essays and generates per-article and per-issue social media posts
for X (Twitter) and LinkedIn.

Usage:
    python3 generate_social.py
"""

import json
import os
import re
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
ESSAYS_DIR = SCRIPT_DIR / "essays"
OUTPUT_DIR = SCRIPT_DIR / "social_content"
SITE_OUTPUT = SCRIPT_DIR.parent / "hfn-site-output"
IMAGES_DIR = SITE_OUTPUT / "images" / "articles"

SITE_URL = "https://www.historyfuturenow.com"

HOOK_TRIGGER_WORDS = {
    "first", "never", "every", "only", "no", "zero", "last", "single",
    "lowest", "highest", "largest", "oldest", "youngest", "most", "fewest",
    "unprecedented", "collapsed", "doubled", "tripled", "halved", "billion",
    "million", "trillion", "century", "centuries", "thousand",
}

QUOTE_POWER_WORDS = {
    "collapse", "collapsed", "transform", "transformed", "revolution",
    "unprecedented", "catastrophe", "empire", "civilisation", "civilization",
    "democracy", "extinction", "survival", "crisis", "radical", "destroyed",
    "permanent", "irreversible", "impossible", "inevitable", "paradox",
    "illusion", "silence", "vanish", "disappeared", "forgotten", "betrayed",
    "unravelled", "shattered", "define", "reshape", "rewrite", "devour",
}

YEAR_RE = re.compile(r"\b\d{4}\b")
NUMBER_RE = re.compile(r"\b\d[\d,.]+\b")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
HEADING_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)

HASHTAG_MAP = {
    "Energy": ["#Energy", "#ClimateChange", "#Sustainability"],
    "Jobs & Economy": ["#Economy", "#FutureOfWork", "#Automation"],
    "Geopolitics": ["#Geopolitics", "#InternationalRelations"],
    "Society": ["#Society", "#Demographics", "#Culture"],
    "Defence": ["#Defence", "#Security", "#Geopolitics"],
    "Immigration": ["#Immigration", "#Demographics", "#Policy"],
    "Technology": ["#Technology", "#Innovation", "#AI"],
}


# ── Parsing ──────────────────────────────────────────────


def parse_essay(filepath):
    """Parse a markdown essay into frontmatter dict and body string."""
    text = filepath.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None, text
    body = text[m.end():]
    return fm, body


def clean_slug(slug):
    """Remove artefact prefixes that sometimes appear in slugs."""
    slug = slug.replace("strong", "").replace("nbsp", "").strip("-").strip()
    return slug


def extract_paragraphs(body):
    """Split body into paragraphs (non-empty, non-heading lines)."""
    paragraphs = []
    current = []
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#"):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def extract_sections(body):
    """Split body into (heading, text) sections by ## headings."""
    parts = HEADING_RE.split(body)
    sections = []
    # parts[0] is intro before first heading
    intro = parts[0].strip()
    if intro:
        sections.append(("Introduction", intro))
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        text = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections.append((heading, text))
    return sections


def extract_sentences(text):
    """Split text into sentences, handling common abbreviations."""
    cleaned = re.sub(r"\*+", "", text)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    # Crude sentence splitter that respects Mr./Dr./etc.
    raw = re.split(r"(?<=[.!?])\s+(?=[A-Z\"])", cleaned)
    return [s.strip() for s in raw if len(s.strip()) > 20]


def article_url(slug):
    return f"{SITE_URL}/articles/{slug}"


# ── Chart helpers ────────────────────────────────────────


def load_charts():
    """Import chart_defs and return the slug->charts dict."""
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        from chart_defs import get_all_charts
        return get_all_charts()
    except Exception:
        return {}


def chart_image_path(slug, chart_id):
    """Return the relative path to a chart PNG, or None if missing."""
    p = IMAGES_DIR / slug / f"chart-{chart_id}.png"
    if p.exists():
        return str(p.relative_to(SITE_OUTPUT))
    return None


# ── Post generators ──────────────────────────────────────


def generate_hook(title, paragraphs, url):
    """Find the most surprising sentence from opening paragraphs."""
    candidates = []
    for para in paragraphs[:3]:
        for sentence in extract_sentences(para):
            score = 0
            lower = sentence.lower()
            if YEAR_RE.search(sentence):
                score += 2
            if NUMBER_RE.search(sentence):
                score += 2
            for word in HOOK_TRIGGER_WORDS:
                if word in lower.split():
                    score += 1
            if score > 0:
                candidates.append((score, sentence))

    candidates.sort(key=lambda x: -x[0])

    best = candidates[0][1] if candidates else (paragraphs[0][:200] if paragraphs else title)
    # Trim to fit 250 chars + link
    max_text = 250 - len(url) - 2  # space + link
    if len(best) > max_text:
        best = best[: max_text - 1].rsplit(" ", 1)[0] + "…"

    return {
        "platform": "twitter",
        "text": best,
        "link": url,
        "full": f"{best} {url}",
    }


def generate_thread(title, sections, paragraphs, url):
    """Build a 4-6 tweet thread walking through the article's argument."""
    tweets = []

    # Tweet 1: hook from opening
    hook_sentences = []
    for para in paragraphs[:2]:
        hook_sentences.extend(extract_sentences(para))
    opener = hook_sentences[0] if hook_sentences else title
    if len(opener) > 260:
        opener = opener[:259].rsplit(" ", 1)[0] + "…"
    tweets.append(f"🧵 {opener}")

    # Middle tweets: one per major section (skip intro)
    body_sections = [s for s in sections if s[0] != "Introduction"]

    # If no ## sections found, synthesise sections from paragraph chunks
    if not body_sections and len(paragraphs) > 3:
        chunk_size = max(1, len(paragraphs) // 5)
        for i in range(1, min(5, len(paragraphs)), chunk_size):
            body_sections.append((f"Section {i}", paragraphs[i]))

    for heading, text in body_sections[:4]:
        section_sentences = extract_sentences(text)
        if not section_sentences:
            continue
        scored = []
        for s in section_sentences[:6]:
            score = 0
            if NUMBER_RE.search(s):
                score += 2
            if YEAR_RE.search(s):
                score += 1
            scored.append((score, s))
        scored.sort(key=lambda x: -x[0])
        pick = scored[0][1]
        if len(pick) > 275:
            pick = pick[:274].rsplit(" ", 1)[0] + "…"
        tweets.append(pick)

    # Closing tweet
    closer = f"Full article: {url}"
    tweets.append(closer)

    # Cap at 6 tweets
    if len(tweets) > 6:
        tweets = tweets[:5] + [tweets[-1]]

    return {
        "platform": "twitter",
        "tweets": tweets,
    }


def generate_chart_insight(slug, charts_for_slug):
    """Create a one-line insight caption for the first chart."""
    if not charts_for_slug:
        return None
    chart = charts_for_slug[0]
    chart_title = chart.get("title", "")
    chart_id = chart.get("id", "")
    image = chart_image_path(slug, chart_id)
    desc = chart.get("desc", "")

    text = f"{chart_title}. {desc}" if desc else chart_title
    if len(text) > 250:
        text = text[:249].rsplit(" ", 1)[0] + "…"

    return {
        "platform": "both",
        "text": text,
        "chart_title": chart_title,
        "image": image,
        "source": chart.get("source", ""),
    }


def generate_linkedin_essay(title, sections, paragraphs, url, part):
    """Extract the meatiest historical section into a 150-250 word LinkedIn post."""
    # Try to use the 2nd or 3rd section for historical meat
    target_sections = [s for s in sections if s[0] != "Introduction"]
    source_text = ""
    if len(target_sections) >= 2:
        source_text = target_sections[1][1]
    elif target_sections:
        source_text = target_sections[0][1]
    else:
        source_text = "\n".join(paragraphs[:4])

    source_paras = extract_paragraphs(source_text)
    selected = source_paras[:3]
    body_text = "\n\n".join(selected)

    # Trim to ~250 words
    words = body_text.split()
    if len(words) > 250:
        body_text = " ".join(words[:250]) + "…"
    elif len(words) < 50 and paragraphs:
        # Fall back to opening paragraphs
        body_text = "\n\n".join(paragraphs[:3])
        words = body_text.split()
        if len(words) > 250:
            body_text = " ".join(words[:250]) + "…"

    hashtags = ["#History", "#FutureOfWork"]
    for key, tags in HASHTAG_MAP.items():
        if part and key.lower() in part.lower():
            hashtags = tags[:3]
            break
    hashtags.extend(["#HistoryFutureNow", "#LongRead"])
    hashtags = list(dict.fromkeys(hashtags))[:5]

    full_text = f"{body_text}\n\nRead the full essay: {url}\n\n{' '.join(hashtags)}"

    return {
        "platform": "linkedin",
        "text": full_text,
        "hashtags": hashtags,
    }


def generate_provocative_question(title, paragraphs):
    """Reframe the article thesis as a question under 200 chars."""
    # Strip subtitle after colon if present
    core = title.split(":")[-1].strip() if ":" in title else title

    lower = core.lower()
    if any(w in lower for w in ["how", "why", "what"]):
        question = core.rstrip(".?!") + "?"
    else:
        # Use "What if" prefix, preserving original casing for proper nouns
        stem = core.rstrip(".?!")
        # Only lowercase the first char if it's a common article/determiner
        first_word = stem.split()[0].lower() if stem else ""
        if first_word in ("the", "a", "an", "our", "their", "its", "this", "that"):
            stem = stem[0].lower() + stem[1:]
        question = f"What if {stem}?"

    if len(question) > 195:
        question = question[:194].rsplit(" ", 1)[0] + "…?"

    return {
        "platform": "twitter",
        "text": question,
    }


def generate_quote_card(paragraphs):
    """Find the most quotable single sentence (80-200 chars)."""
    candidates = []
    for para in paragraphs:
        for sentence in extract_sentences(para):
            slen = len(sentence)
            if slen < 80 or slen > 200:
                continue
            score = 0
            lower = sentence.lower()
            for word in QUOTE_POWER_WORDS:
                if word in lower:
                    score += 2
            if YEAR_RE.search(sentence):
                score += 1
            if score > 0:
                candidates.append((score, sentence))

    candidates.sort(key=lambda x: -x[0])
    if not candidates:
        # Relax length constraint
        for para in paragraphs[:5]:
            for sentence in extract_sentences(para):
                if 60 < len(sentence) < 250:
                    candidates.append((0, sentence))
        if not candidates:
            return None

    best = candidates[0][1]
    return {
        "platform": "both",
        "text": best,
        "char_count": len(best),
    }


# ── Issue-level generators ───────────────────────────────


def generate_issue_announcement(issue, article_titles, article_slugs):
    """Create the issue announcement post."""
    num = issue["number"]
    label = issue.get("label", "")
    titles_str = " | ".join(article_titles[:5])
    url = f"{SITE_URL}/issues/{num}"

    text = f"Issue {num} of History Future Now is out."
    if label:
        text = f"Issue {num} ({label}) of History Future Now is out."
    text += f" Inside: {titles_str}."
    text += f"\n\n{url}"

    return {
        "platform": "both",
        "issue_number": num,
        "text": text,
        "article_count": len(article_slugs),
    }


def generate_issue_thread(issue, article_data):
    """One tweet per article hook, as a thread."""
    num = issue["number"]
    label = issue.get("label", "")
    tweets = [f"🧵 Issue {num} of History Future Now — {label}. Here's what's inside:"]

    for slug, data in article_data.items():
        hook = data.get("posts", {}).get("hook", {})
        hook_text = hook.get("text", data.get("title", slug))
        link = hook.get("link", article_url(slug))
        tweet = f"{hook_text} {link}"
        if len(tweet) > 280:
            max_t = 280 - len(link) - 2
            hook_text = hook_text[: max_t - 1].rsplit(" ", 1)[0] + "…"
            tweet = f"{hook_text} {link}"
        tweets.append(tweet)

    return {
        "platform": "twitter",
        "issue_number": num,
        "tweets": tweets,
    }


# ── Main pipeline ────────────────────────────────────────


def process_article(filepath, all_charts):
    """Generate all social posts for a single article."""
    fm, body = parse_essay(filepath)
    if not fm:
        return None

    slug = fm.get("slug", filepath.stem)
    if isinstance(slug, str):
        slug = slug.strip()
    slug = clean_slug(slug)
    title = fm.get("title", slug)
    if isinstance(title, str):
        title = title.strip()
    part = fm.get("part", "")
    url = article_url(slug)

    paragraphs = extract_paragraphs(body)
    sections = extract_sections(body)

    if not paragraphs:
        return None

    charts_for_slug = all_charts.get(slug, [])

    posts = {}
    posts["hook"] = generate_hook(title, paragraphs, url)
    posts["thread"] = generate_thread(title, sections, paragraphs, url)

    chart_insight = generate_chart_insight(slug, charts_for_slug)
    if chart_insight:
        posts["chart_insight"] = chart_insight

    posts["linkedin_essay"] = generate_linkedin_essay(title, sections, paragraphs, url, part)
    posts["provocative_question"] = generate_provocative_question(title, paragraphs)

    quote = generate_quote_card(paragraphs)
    if quote:
        posts["quote_card"] = quote

    return {
        "slug": slug,
        "title": title,
        "url": url,
        "part": part,
        "posts": posts,
    }


def main():
    print("=" * 60)
    print("  History Future Now — Social Content Generator")
    print("=" * 60)
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load charts
    print("Loading chart definitions...")
    all_charts = load_charts()
    print(f"  Found charts for {len(all_charts)} articles")

    # Load issues
    sys.path.insert(0, str(SCRIPT_DIR))
    from issues import ISSUES

    # Process each essay
    essay_files = sorted(ESSAYS_DIR.glob("*.md"))
    print(f"\nProcessing {len(essay_files)} essays...\n")

    article_results = {}
    success = 0
    skipped = 0

    for filepath in essay_files:
        result = process_article(filepath, all_charts)
        if result is None:
            print(f"  SKIP  {filepath.name} (no frontmatter or content)")
            skipped += 1
            continue

        slug = result["slug"]
        out_path = OUTPUT_DIR / f"{slug}.json"
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        article_results[slug] = result

        has_chart = "chart_insight" in result["posts"]
        has_quote = "quote_card" in result["posts"]
        n_thread = len(result["posts"].get("thread", {}).get("tweets", []))
        print(f"  OK    {slug}")
        print(f"        thread={n_thread}t  chart={'Y' if has_chart else '-'}  quote={'Y' if has_quote else '-'}")
        success += 1

    # Process issues
    print(f"\nProcessing {len(ISSUES)} issues...\n")
    issue_count = 0

    for issue in ISSUES:
        num = issue["number"]
        article_slugs = issue.get("articles", [])

        # Collect titles and per-article data for this issue
        titles = []
        issue_article_data = {}
        for slug in article_slugs:
            if slug in article_results:
                titles.append(article_results[slug]["title"])
                issue_article_data[slug] = article_results[slug]
            else:
                titles.append(slug.replace("-", " ").title())

        announcement = generate_issue_announcement(issue, titles, article_slugs)
        thread = generate_issue_thread(issue, issue_article_data)

        issue_data = {
            "issue_number": num,
            "label": issue.get("label", ""),
            "date": issue.get("date", ""),
            "articles": article_slugs,
            "posts": {
                "issue_announcement": announcement,
                "issue_thread": thread,
            },
        }

        out_path = OUTPUT_DIR / f"issue_{num}.json"
        out_path.write_text(json.dumps(issue_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  OK    Issue {num} ({issue.get('label', '')}) — {len(article_slugs)} articles")
        issue_count += 1

    # Summary
    print()
    print("=" * 60)
    print(f"  Done. {success} articles, {issue_count} issues.")
    if skipped:
        print(f"  Skipped: {skipped}")
    print(f"  Output: {OUTPUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
