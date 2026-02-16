#!/usr/bin/env python3
"""
History Future Now — Section Editorial Intro Generator

Generates compelling editorial introductions for each section page using
Claude Opus 4.6 (Anthropic API), with Gemini as fallback.

The output is cached to section_intros_cache.json so that build.py can
inject the intros without needing an API key at build time.

Prerequisites:
    - ANTHROPIC_API_KEY env var (preferred) OR GEMINI_API_KEY env var (fallback)
    - Article markdown files in essays/

Usage:
    python3 generate_section_intros.py                    # Regenerate sections with new articles
    python3 generate_section_intros.py --force             # Regenerate all sections
    python3 generate_section_intros.py --section "Society" # Regenerate one section
    python3 generate_section_intros.py --dry-run           # Preview without API calls
    python3 generate_section_intros.py --list              # Show section status
"""

import os
import re
import sys
import json
import yaml
import time
import math
import argparse
from pathlib import Path
from datetime import datetime, timezone

# ─── Configuration ────────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

GEMINI_API_KEYS = [
    k.strip() for k in
    os.environ.get("GEMINI_API_KEY", "").split(",")
    if k.strip()
]
_gemini_key_index = 0
GEMINI_MODEL = "gemini-2.5-flash"

def _next_gemini_key() -> str:
    global _gemini_key_index
    if not GEMINI_API_KEYS:
        return ""
    key = GEMINI_API_KEYS[_gemini_key_index % len(GEMINI_API_KEYS)]
    _gemini_key_index += 1
    return key

ESSAYS_DIR = Path(__file__).parent / "essays"
CACHE_PATH = Path(__file__).parent / "section_intros_cache.json"

PARTS = {
    "Natural Resources": {"order": 1, "slug": "natural-resources", "color": "#0d9a5a"},
    "Global Balance of Power": {"order": 2, "slug": "balance-of-power", "color": "#2563eb"},
    "Jobs & Economy": {"order": 3, "slug": "jobs-economy", "color": "#b8751a"},
    "Society": {"order": 4, "slug": "society", "color": "#7c3aed"},
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


# ─── Thematic Guidance Per Section ────────────────────────────────────────────

SECTION_THEMES = {
    "Natural Resources": """EDITORIAL ANGLE FOR THIS SECTION:

You are writing the editorial introduction for the Natural Resources section.
The core position is pro-nuclear and pro-renewables, but realistic about emissions.

Key themes to weave through the prose:
- The energy revolution is real and accelerating. Solar costs fell 99%, batteries are
  following the same curve. This is not speculative -- it is happening.
- Nuclear energy is essential for baseload power. The West should be building more
  reactors, not fewer. The anti-nuclear movement has cost decades of clean energy.
- Be honest about emissions: the West produces a fraction of global greenhouse
  emissions compared to China and India. Western climate policy alone cannot solve
  the problem. This is not an excuse for inaction, but it is a fact that shapes
  what effective policy looks like.
- Food security, water, and land are the underappreciated resources. Africa's land
  deals echo colonial-era extraction patterns.
- Every energy transition in history (wood to coal, coal to oil, oil to renewables)
  reshuffled geopolitical power. The current transition will be no different.
- The whale oil to petroleum transition shows how quickly incumbents can collapse
  when a cheaper alternative arrives.""",

    "Global Balance of Power": """EDITORIAL ANGLE FOR THIS SECTION:

You are writing the editorial introduction for the Global Balance of Power section.
The core thesis is that science, engineering, and manufacturing capability determine
which nations dominate -- economically and militarily.

Key themes to weave through the prose:
- You cannot remain a great power without the triad: SCIENCE to create the ideas,
  ENGINEERING to turn ideas into implementable plans, and MANUFACTURING to turn
  plans into physical products. Lose any leg and you decline.
- Britain after deindustrialisation is the cautionary tale. The Ottoman Empire after
  closing the gates of ijtihad is another. Nations that stop making things stop
  mattering.
- China's rise is fundamentally a manufacturing and engineering story. It is not
  an accident that the world's largest manufacturer is becoming the world's largest
  economy.
- Europe's rearmament cycles show that peace dividends always end. The question is
  whether the industrial base exists to rearm when the threat materialises. After
  1991, Europe hollowed out its defence industry. Now it is scrambling.
- Technology transfer between civilisations (Rome/Persia, China/West, Islamic Golden
  Age/Europe) has always determined the balance of power.
- Geography shapes threat perception: Poland spends 4%+ of GDP on defence because
  Russia is next door. Spain spends 2.1% because it is not.""",

    "Jobs & Economy": """EDITORIAL ANGLE FOR THIS SECTION:

You are writing the editorial introduction for the Jobs & Economy section.
The core thesis is that automation is the answer to demographic decline, not
mass immigration.

Key themes to weave through the prose:
- Ageing nations face a stark choice: import workers or build robots. History
  suggests the second option is safer.
- Rome's reliance on Germanic foederati for labour and military service is the
  cautionary tale. The people you import to do the work eventually replace you.
- Japan chose robots over immigration and preserved social cohesion. Europe chose
  immigration and got social fragmentation. The data supports Japan's approach.
- The economics of AI and humanoid robotics are reaching the tipping point.
  Tesla's Optimus at under $20K, Microsoft predicting most white-collar tasks
  automated within 12-18 months -- this is not science fiction.
- Debt, trade, and the return of state industrial policy are reshaping the global
  economy. Free trade orthodoxy is dying because it failed the working class.
- The first Industrial Revolution caused 150 years of social upheaval before
  living standards broadly improved. We may be at the start of a similar period.""",

    "Society": """EDITORIAL ANGLE FOR THIS SECTION:

You are writing the editorial introduction for the Society section.
The core thesis is that the West and East Asia are dying from demographic collapse,
and this will determine everything else. Immigration makes things worse, not better.

Key themes to weave through the prose:
- Collapsing birth rates are THE defining crisis. South Korea at 0.72, Italy at
  1.24, Japan at 1.20. No civilisation has recovered from sustained fertility
  below 1.5. This is not a policy problem -- it is a civilisational one.
- Immigration does NOT solve the demographic problem. Immigrant fertility converges
  to native rates within one generation. The "immigration as demographic fix" argument
  is mathematically illiterate. Meanwhile, fiscal costs often exceed contributions.
- Every civilisation that controlled speech collapsed (Athens vs Sparta, the Islamic
  Golden Age after closing ijtihad, the Soviet Union). Every civilisation that lost
  control of its borders collapsed (Rome after AD 212, the Western Roman Empire).
  The West is running both experiments simultaneously.
- The nuclear family model is failing. Religion is declining. No replacement social
  glue has emerged. Atomised individuals do not form resilient societies.
- Historical perspective matters: these patterns have played out before. Rome,
  dynastic China, the Islamic Golden Age -- all faced demographic decline,
  immigration pressure, and social fragmentation. The outcomes were not good.""",
}


# ─── Shared System Prompt ────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are the editorial voice of History Future Now, a data-driven
analysis site about the structural forces shaping the next century.

You write in British English. Your voice is measured, authoritative, and occasionally
sardonic -- think The Economist crossed with a sharp Oxford don. You use dry wit,
not breathless enthusiasm. You are educational but never boring.

Your job is to write a compelling editorial introduction for a section page. This
introduction sits between the section header and the list of articles. It should:

1. HOOK the reader immediately with a surprising fact or provocative observation
2. DISTIL the most compelling arguments from the section's articles into a fluid
   narrative -- not a summary of each article, but a synthesis of the big themes
3. LINK to specific articles using HTML anchor tags so readers can dive deeper
4. REFERENCE 2-3 of the section's most striking data points or charts
5. SPARK curiosity -- the reader should finish the intro thinking "I had no idea"
   and wanting to read the articles

CRITICAL RULES:
- Write 4-6 paragraphs of fluid editorial prose. This is a magazine-style essay
  introduction, not a list of article summaries.
- Use <a href="/articles/{slug}"> tags to link to articles inline. Links should
  feel natural in the prose, not forced. Example: "Solar costs have fallen by
  <a href="/articles/the-renewables-and-battery-revolution">99% since 1976</a>"
- Do NOT link to every article. Pick the 4-8 most compelling ones.
- Include at least one moment of dry wit or unexpected historical parallel in the
  first two paragraphs. This is the "chuckle hook" that keeps readers reading.
- Use specific numbers, dates, and facts -- not vague generalities.
- British spelling throughout (organise, colour, defence, centre).
- Do NOT use markdown. Output clean HTML paragraphs (<p> tags).
- Do NOT include headings, lists, or block quotes. Just flowing prose paragraphs.
- Each paragraph should be wrapped in <p> tags.
- The tone should make the reader feel smarter for having read it.

OUTPUT FORMAT:
Return ONLY a JSON object with these fields:
{
  "html": "<p>First paragraph...</p><p>Second paragraph...</p>...",
  "articles_referenced": ["slug-1", "slug-2", ...],
  "chart_ids_suggested": ["chartId1", "chartId2"]
}

The chart_ids_suggested field should list 2-3 chart IDs from the provided chart
list that would be most compelling to embed alongside the editorial text. Pick
charts with broad temporal coverage and clear, striking data."""


# ─── Article Parsing ─────────────────────────────────────────────────────────

def fix_encoding(text: str) -> str:
    replacements = {
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '\u2014': '—', '\u2013': '–', '\u2026': '…', '\xa0': ' ',
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text


def parse_essay_light(filepath: Path) -> dict:
    """Parse an essay markdown file, extracting metadata and first ~500 words."""
    content = filepath.read_text(encoding='utf-8', errors='replace')

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
            except Exception:
                meta = {}
            body = parts[2]
        else:
            meta, body = {}, content
    else:
        meta, body = {}, content

    body = fix_encoding(body)
    title = fix_encoding(meta.get('title', filepath.stem.replace('-', ' ').title()))
    title = re.sub(r'</?strong>', '', title).replace('&nbsp;', '').strip()

    slug = meta.get('slug', filepath.stem)
    slug = slug.replace('strong', '').replace('nbsp', '').strip('-')
    slug = re.sub(r'-+', '-', slug)

    raw_part = meta.get('part', 'Society')
    part = PART_ALIASES.get(raw_part, raw_part)
    if part not in PARTS:
        part = "Society"

    excerpt = fix_encoding(meta.get('excerpt', ''))
    if not excerpt:
        clean = re.sub(r'#.*?\n', '', body).strip()
        paras = [p.strip() for p in clean.split('\n\n') if p.strip() and not p.strip().startswith('#')]
        if paras:
            excerpt = paras[0][:300]

    # Extract first ~500 words for context
    clean_body = re.sub(r'#[^\n]*\n', '', body)
    words = clean_body.split()
    opening = ' '.join(words[:500])

    # Extract all headings for structure
    headings = re.findall(r'^##\s+(.+)$', body, re.MULTILINE)

    share_summary = fix_encoding(meta.get('share_summary', ''))

    return {
        'title': title,
        'slug': slug,
        'part': part,
        'excerpt': excerpt,
        'share_summary': share_summary,
        'opening': opening,
        'headings': headings,
        'word_count': len(words),
    }


def load_all_essays() -> list[dict]:
    """Load all essays from the essays directory."""
    essays = []
    for md in sorted(ESSAYS_DIR.glob("*.md")):
        try:
            essays.append(parse_essay_light(md))
        except Exception as e:
            print(f"  Warning: Could not parse {md.name}: {e}")
    return essays


def get_section_charts(section_name: str) -> list[dict]:
    """Get chart metadata for articles in a section."""
    from chart_defs import get_all_charts
    all_charts = get_all_charts()

    essays = load_all_essays()
    section_slugs = {e['slug'] for e in essays if e['part'] == section_name}

    section_charts = []
    for slug in section_slugs:
        for chart in all_charts.get(slug, []):
            section_charts.append({
                'id': chart['id'],
                'title': chart.get('title', ''),
                'desc': chart.get('desc', ''),
                'source': chart.get('source', ''),
                'article_slug': slug,
            })

    return section_charts


# ─── LLM Generation (Anthropic Claude Opus 4.6) ──────────────────────────────

def generate_intro_anthropic(section_name: str, essays: list[dict],
                              charts: list[dict], max_retries: int = 3) -> dict:
    """Generate an editorial intro using Claude Opus 4.6."""
    import requests

    user_prompt = _build_user_prompt(section_name, essays, charts)

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 4096,
        "system": SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.8,
    }

    last_error = None
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)

            if response.status_code == 429:
                wait = 30 + (attempt * 30)
                print(f"    Rate limited (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
                time.sleep(wait)
                last_error = "Rate limited"
                continue

            if response.status_code != 200:
                raise RuntimeError(
                    f"Anthropic API error {response.status_code}: {response.text[:500]}"
                )

            data = response.json()
            text = data.get("content", [{}])[0].get("text", "")
            if not text:
                raise RuntimeError("Empty response from Anthropic")

            # Parse JSON from response (may be wrapped in markdown code blocks)
            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r'^```(?:json)?\s*', '', text)
                text = re.sub(r'\s*```$', '', text)

            result = json.loads(text)

            if "html" not in result:
                raise RuntimeError(f"Missing 'html' field in response: {list(result.keys())}")

            return result

        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse response as JSON: {e}\nResponse: {text[:500]}")
        except requests.exceptions.Timeout:
            wait = 15 + (attempt * 15)
            print(f"    Timeout (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
            time.sleep(wait)
            last_error = "Timeout"
            continue

    raise RuntimeError(f"Failed after {max_retries} retries: {last_error}")


# ─── LLM Generation (Gemini Fallback) ────────────────────────────────────────

def _build_user_prompt(section_name: str, essays: list[dict], charts: list[dict]) -> str:
    """Build the user prompt shared by both Anthropic and Gemini backends."""
    theme_guidance = SECTION_THEMES.get(section_name, "")

    article_context = []
    for e in essays:
        article_context.append(
            f"TITLE: {e['title']}\n"
            f"SLUG: {e['slug']}\n"
            f"EXCERPT: {e['excerpt']}\n"
            f"SHARE SUMMARY: {e['share_summary']}\n"
            f"WORD COUNT: {e['word_count']}\n"
            f"HEADINGS: {', '.join(e['headings'][:8])}\n"
            f"OPENING:\n{e['opening'][:800]}\n"
        )

    articles_text = "\n---\n".join(article_context)

    chart_context = []
    for c in charts:
        chart_context.append(f"  - ID: {c['id']}, Title: \"{c['title']}\", "
                           f"Source: {c['source']}, Article: {c['article_slug']}")
    charts_text = "\n".join(chart_context) if chart_context else "(no charts available)"

    return f"""Generate the editorial introduction for the "{section_name}" section.

{theme_guidance}

ARTICLES IN THIS SECTION ({len(essays)} total):

{articles_text}

AVAILABLE CHARTS IN THIS SECTION:
{charts_text}

Remember: Return ONLY a JSON object with "html", "articles_referenced", and "chart_ids_suggested" fields.
Write 4-6 paragraphs of compelling editorial prose with inline article links.
Pick 2-3 charts that would be most striking to embed."""


def generate_intro_gemini(section_name: str, essays: list[dict],
                          charts: list[dict], max_retries: int = 5) -> dict:
    """Generate an editorial intro using Gemini as fallback."""
    import requests

    user_prompt = _build_user_prompt(section_name, essays, charts)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": user_prompt}]}
        ],
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "generationConfig": {
            "temperature": 0.8,
            "topP": 0.95,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json",
        },
    }

    last_error = None
    for attempt in range(max_retries):
        api_key = _next_gemini_key()
        try:
            response = requests.post(
                url, params={"key": api_key}, json=payload, timeout=120
            )

            if response.status_code == 429:
                wait = 15 + (attempt * 10)
                print(f"    Rate limited (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
                time.sleep(wait)
                last_error = "Rate limited"
                continue

            if response.status_code != 200:
                raise RuntimeError(
                    f"Gemini API error {response.status_code}: {response.text[:500]}"
                )

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError(f"No candidates in Gemini response")

            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if not text:
                raise RuntimeError("Empty response from Gemini")

            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r'^```(?:json)?\s*', '', text)
                text = re.sub(r'\s*```$', '', text)

            result = json.loads(text)
            if "html" not in result:
                raise RuntimeError(f"Missing 'html' field in response")

            return result

        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Gemini response as JSON: {e}\nResponse: {text[:500]}")
        except requests.exceptions.Timeout:
            wait = 15 + (attempt * 15)
            print(f"    Timeout (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
            time.sleep(wait)
            last_error = "Timeout"
            continue

    raise RuntimeError(f"Gemini failed after {max_retries} retries: {last_error}")


def generate_intro(section_name: str, essays: list[dict], charts: list[dict]) -> dict:
    """Generate an editorial intro, trying Anthropic first then Gemini fallback."""
    if ANTHROPIC_API_KEY:
        print(f"    Using Anthropic ({ANTHROPIC_MODEL})")
        return generate_intro_anthropic(section_name, essays, charts)
    elif GEMINI_API_KEYS:
        print(f"    Using Gemini fallback ({GEMINI_MODEL})")
        return generate_intro_gemini(section_name, essays, charts)
    else:
        raise RuntimeError("No API key available. Set ANTHROPIC_API_KEY or GEMINI_API_KEY.")


# ─── Cache Management ────────────────────────────────────────────────────────

def load_cache() -> dict:
    """Load the cached section intros."""
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding='utf-8'))
    return {"generated_at": None, "sections": {}}


def save_cache(cache: dict) -> None:
    """Save the section intros cache."""
    cache["generated_at"] = datetime.now(timezone.utc).isoformat()
    CACHE_PATH.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )


def sections_needing_update(cache: dict, essays: list[dict]) -> list[str]:
    """Determine which sections need regeneration based on article count changes."""
    needs_update = []
    for section_name in PARTS:
        current_count = sum(1 for e in essays if e['part'] == section_name)
        cached = cache.get("sections", {}).get(section_name, {})
        cached_count = cached.get("article_count_at_generation", 0)

        if current_count != cached_count:
            needs_update.append(section_name)

    return needs_update


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_generate(args):
    """Generate section editorial intros."""
    if not ANTHROPIC_API_KEY and not GEMINI_API_KEYS:
        print("ERROR: No API key set.")
        print("  export ANTHROPIC_API_KEY=sk-ant-...  (preferred)")
        print("  export GEMINI_API_KEY=...            (fallback)")
        sys.exit(1)

    backend = f"Anthropic ({ANTHROPIC_MODEL})" if ANTHROPIC_API_KEY else f"Gemini ({GEMINI_MODEL})"

    print("Loading articles...")
    essays = load_all_essays()
    print(f"  Loaded {len(essays)} articles")

    cache = load_cache()

    # Determine which sections to regenerate
    if args.force:
        sections_to_generate = list(PARTS.keys())
        print("  Force mode: regenerating all sections")
    elif args.section:
        if args.section not in PARTS:
            print(f"ERROR: Unknown section '{args.section}'")
            print(f"  Available: {', '.join(PARTS.keys())}")
            sys.exit(1)
        sections_to_generate = [args.section]
        print(f"  Regenerating: {args.section}")
    else:
        sections_to_generate = sections_needing_update(cache, essays)
        if not sections_to_generate:
            print("  All sections are up to date. Use --force to regenerate.")
            return
        print(f"  Sections needing update: {', '.join(sections_to_generate)}")

    print(f"\nBackend: {backend}")
    print(f"Cache: {CACHE_PATH}")
    print()

    generated = 0
    failed = 0

    for section_name in sections_to_generate:
        section_essays = [e for e in essays if e['part'] == section_name]
        section_charts = get_section_charts(section_name)

        print(f"[{section_name}] {len(section_essays)} articles, {len(section_charts)} charts")

        if args.dry_run:
            print(f"  [dry-run] Would generate intro from {len(section_essays)} articles")
            for e in section_essays:
                print(f"    - {e['title'][:60]}")
            continue

        try:
            result = generate_intro(section_name, section_essays, section_charts)

            cache.setdefault("sections", {})[section_name] = {
                "html": result["html"],
                "chart_ids": result.get("chart_ids_suggested", []),
                "articles_referenced": result.get("articles_referenced", []),
                "article_count_at_generation": len(section_essays),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            save_cache(cache)

            n_refs = len(result.get("articles_referenced", []))
            n_charts = len(result.get("chart_ids_suggested", []))
            html_len = len(result["html"])
            print(f"  [done] {html_len} chars, {n_refs} article refs, {n_charts} charts")
            generated += 1

            # Brief pause between sections to be polite to the API
            if section_name != sections_to_generate[-1]:
                time.sleep(2)

        except Exception as e:
            print(f"  [FAILED] {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Sections: {generated} generated, {failed} failed")
    if generated > 0:
        print(f"Cache saved to: {CACHE_PATH}")


def cmd_list(args):
    """Show section status."""
    essays = load_all_essays()
    cache = load_cache()

    print(f"Cache file: {CACHE_PATH}")
    print(f"Last generated: {cache.get('generated_at', 'never')}")
    print()

    for section_name in sorted(PARTS.keys(), key=lambda p: PARTS[p]['order']):
        current_count = sum(1 for e in essays if e['part'] == section_name)
        cached = cache.get("sections", {}).get(section_name, {})
        cached_count = cached.get("article_count_at_generation", 0)
        has_intro = bool(cached.get("html"))

        status = "up-to-date" if (has_intro and current_count == cached_count) else \
                 "needs update" if has_intro else "not generated"

        n_refs = len(cached.get("articles_referenced", []))
        n_charts = len(cached.get("chart_ids", []))

        print(f"  [{status:>14}] {section_name}")
        print(f"                  Articles: {current_count} current, {cached_count} at generation")
        if has_intro:
            print(f"                  Refs: {n_refs} articles, {n_charts} charts")
            print(f"                  Generated: {cached.get('generated_at', '?')}")
        print()

    needs = sections_needing_update(cache, essays)
    if needs:
        print(f"Sections needing regeneration: {', '.join(needs)}")
    else:
        print("All sections are up to date.")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate editorial intros for HFN section pages"
    )
    parser.add_argument("--force", action="store_true",
                       help="Regenerate all sections regardless of cache")
    parser.add_argument("--section", type=str,
                       help="Regenerate a specific section only")
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview without API calls")
    parser.add_argument("--list", action="store_true",
                       help="Show section status")

    args = parser.parse_args()

    if args.list:
        cmd_list(args)
    else:
        cmd_generate(args)


if __name__ == "__main__":
    main()
