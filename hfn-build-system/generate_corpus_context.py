#!/usr/bin/env python3
"""
History Future Now — Corpus Context Generator

Extracts all 54+ essays into a structured corpus file that can be used
as background context for generating cross-referencing discussions.

For each article, produces:
  - Title, section, slug
  - Key themes and arguments (first 3 paragraphs + headings)
  - Full text (for the focal article)

Output: corpus_context.json — used by generate_discussions.py

Usage:
    python3 generate_corpus_context.py                # Build corpus context
    python3 generate_corpus_context.py --stats         # Show corpus statistics
"""

import os
import re
import sys
import json
import yaml
import math
from pathlib import Path

ESSAYS_DIR = Path(__file__).parent / "essays"
OUTPUT_PATH = Path(__file__).parent / "corpus_context.json"

PARTS = {
    "Natural Resources": {"order": 1, "slug": "natural-resources"},
    "Global Balance of Power": {"order": 2, "slug": "balance-of-power"},
    "Jobs & Economy": {"order": 3, "slug": "jobs-economy"},
    "Society": {"order": 4, "slug": "society"},
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


def fix_encoding(text: str) -> str:
    """Fix common encoding artifacts from Word/web copy-paste."""
    replacements = {
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '--', '\u2026': '...',
        '\xa0': ' ', '\u00a3': 'GBP ', '\u20ac': 'EUR ',
        'a\u0302\u20ac\u2122': "'", 'a\u0302\u20ac\u0153': '"',
        'a\u0302\u20ac\u009d': '"', 'a\u0302\u20ac"': '--',
        'a\u0302\u20ac"': '-', 'a\u0302\u20ac\u00a6': '...',
        '\u00c2 ': ' ', '\u00c2': '',
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text


def strip_markdown(text: str) -> str:
    """Convert markdown to plain text."""
    text = re.sub(r'^#{1,6}\s+(.+)$', r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def extract_headings(body: str) -> list[str]:
    """Extract all section headings from markdown body."""
    headings = []
    for match in re.finditer(r'^#{1,6}\s+(.+)$', body, re.MULTILINE):
        heading = match.group(1).strip()
        heading = re.sub(r'\*\*(.+?)\*\*', r'\1', heading)
        heading = re.sub(r'<[^>]+>', '', heading)
        if heading and heading not in ('THEN:', 'NOW:', 'NEXT:'):
            headings.append(heading)
    return headings


def extract_opening(body: str, n_paragraphs: int = 3) -> str:
    """Extract the first N paragraphs as the article opening."""
    clean = strip_markdown(body)
    paragraphs = [p.strip() for p in clean.split('\n\n') if p.strip() and len(p.strip()) > 40]
    opening = '\n\n'.join(paragraphs[:n_paragraphs])
    return opening


def parse_essay(filepath: Path) -> dict:
    """Parse a single essay markdown file into structured data."""
    content = filepath.read_text(encoding='utf-8', errors='replace')
    content = fix_encoding(content)

    meta = {}
    body = content
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                meta = {}
            body = parts[2]

    title = meta.get('title', filepath.stem.replace('-', ' ').title())
    title = re.sub(r'</?strong>', '', title).replace('&nbsp;', ' ').replace('\xa0', ' ').strip()

    slug = meta.get('slug', filepath.stem)
    slug = slug.replace('strong', '').replace('nbsp', '').strip('-')
    slug = re.sub(r'-+', '-', slug)

    raw_part = meta.get('part', 'Society')
    part = PART_ALIASES.get(raw_part, raw_part)

    excerpt = meta.get('excerpt', '')

    # Remove the title heading
    body = re.sub(r'^\s*#\s+[^\n]+\n', '', body, count=1)
    # Remove THEN/NOW/NEXT sections
    body = re.sub(r'\n---\s*\n\s*##\s*THEN:.*$', '', body, flags=re.DOTALL)
    # Remove related article headings at end
    body = re.sub(r'\n##\s+[^\n]+\s*$', '', body)

    headings = extract_headings(body)
    opening = extract_opening(body)
    full_text = strip_markdown(body)
    word_count = len(full_text.split())

    return {
        'title': title,
        'slug': slug,
        'part': part,
        'excerpt': excerpt,
        'headings': headings,
        'opening': opening,
        'full_text': full_text,
        'word_count': word_count,
    }


def build_cross_reference_map(articles: list[dict]) -> dict[str, list[str]]:
    """
    Build a map of thematic cross-references between articles.
    For each article, identify which other articles share themes.
    """
    theme_keywords = {
        'demographics': ['birth rate', 'fertility', 'population', 'ageing', 'aging', 'demographic', 'migration', 'immigration', 'emigration', 'children', 'longevity'],
        'energy': ['energy', 'oil', 'gas', 'coal', 'renewable', 'solar', 'wind', 'nuclear', 'battery', 'electricity', 'carbon'],
        'automation': ['robot', 'automation', 'AI', 'artificial intelligence', 'jobs', 'employment', 'workforce', 'machine', 'technology'],
        'geopolitics': ['China', 'Russia', 'NATO', 'military', 'war', 'defence', 'defense', 'invasion', 'empire', 'colonial', 'superpower'],
        'economics': ['debt', 'trade', 'GDP', 'economy', 'inflation', 'capitalism', 'inequality', 'wealth', 'poverty', 'tax'],
        'democracy': ['democracy', 'vote', 'election', 'government', 'revolution', 'populism', 'political', 'freedom', 'rights'],
        'environment': ['climate', 'environment', 'food', 'water', 'farming', 'agriculture', 'land', 'resource', 'sustainability'],
        'society': ['family', 'religion', 'culture', 'identity', 'race', 'gender', 'education', 'prison', 'morality', 'slavery'],
        'history': ['Rome', 'Roman', 'empire', 'medieval', 'industrial revolution', 'colonial', 'century', 'ancient', 'historical'],
    }

    article_themes = {}
    for article in articles:
        text_lower = article['full_text'].lower()
        themes = set()
        for theme, keywords in theme_keywords.items():
            matches = sum(1 for kw in keywords if kw.lower() in text_lower)
            if matches >= 2:
                themes.add(theme)
        article_themes[article['slug']] = themes

    cross_refs = {}
    for article in articles:
        my_themes = article_themes[article['slug']]
        refs = []
        for other in articles:
            if other['slug'] == article['slug']:
                continue
            other_themes = article_themes[other['slug']]
            shared = my_themes & other_themes
            if len(shared) >= 2:
                refs.append({
                    'slug': other['slug'],
                    'title': other['title'],
                    'part': other['part'],
                    'shared_themes': sorted(shared),
                })
        refs.sort(key=lambda r: -len(r['shared_themes']))
        cross_refs[article['slug']] = refs[:8]

    return cross_refs


def build_corpus():
    """Build the full corpus context file."""
    essays = sorted(ESSAYS_DIR.glob('*.md'))
    if not essays:
        print(f"No essays found in {ESSAYS_DIR}")
        sys.exit(1)

    articles = []
    for filepath in essays:
        try:
            article = parse_essay(filepath)
            articles.append(article)
        except Exception as e:
            print(f"  [ERROR] {filepath.name}: {e}")

    articles.sort(key=lambda a: (PARTS.get(a['part'], {}).get('order', 99), a['title']))

    cross_refs = build_cross_reference_map(articles)

    corpus = {
        'meta': {
            'total_articles': len(articles),
            'total_words': sum(a['word_count'] for a in articles),
            'sections': {
                name: {
                    'slug': info['slug'],
                    'count': sum(1 for a in articles if a['part'] == name),
                }
                for name, info in PARTS.items()
            },
        },
        'articles': [],
    }

    for article in articles:
        corpus['articles'].append({
            'title': article['title'],
            'slug': article['slug'],
            'part': article['part'],
            'excerpt': article['excerpt'],
            'headings': article['headings'],
            'opening': article['opening'],
            'full_text': article['full_text'],
            'word_count': article['word_count'],
            'cross_references': cross_refs.get(article['slug'], []),
        })

    OUTPUT_PATH.write_text(json.dumps(corpus, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Corpus context written to {OUTPUT_PATH}")
    print(f"  {len(articles)} articles, {corpus['meta']['total_words']:,} total words")
    return corpus


def show_stats():
    """Show corpus statistics."""
    if not OUTPUT_PATH.exists():
        print("No corpus file found. Run without --stats first.")
        sys.exit(1)

    corpus = json.loads(OUTPUT_PATH.read_text(encoding='utf-8'))
    meta = corpus['meta']

    print(f"Corpus: {meta['total_articles']} articles, {meta['total_words']:,} words")
    print()
    for section, info in meta['sections'].items():
        print(f"  {section}: {info['count']} articles")
    print()

    for article in corpus['articles']:
        refs = article.get('cross_references', [])
        ref_str = f" ({len(refs)} cross-refs)" if refs else ""
        print(f"  [{article['part'][:12]:>12}] {article['title'][:60]:<60} {article['word_count']:>6} words{ref_str}")


if __name__ == '__main__':
    if '--stats' in sys.argv:
        show_stats()
    else:
        build_corpus()
