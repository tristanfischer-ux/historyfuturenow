#!/usr/bin/env python3
"""
History Future Now — Conversational Discussion Generator

Generates two-speaker podcast-style discussions for each article using
the Google Cloud Podcast API (NotebookLM Enterprise).

Each discussion draws on the full corpus of 54+ articles, making
cross-references and thematic connections that a single-article
narration cannot.

Prerequisites:
    1. Google Cloud project with Discovery Engine API enabled
    2. IAM role: Podcast API User (roles/discoveryengine.podcastApiUser)
    3. gcloud CLI authenticated: gcloud auth login
    4. Corpus context built: python3 generate_corpus_context.py

Usage:
    python3 generate_discussions.py                     # Generate all missing
    python3 generate_discussions.py --article SLUG      # Generate for one article
    python3 generate_discussions.py --force              # Regenerate all
    python3 generate_discussions.py --dry-run            # Preview without calling API
    python3 generate_discussions.py --list               # List articles and status
"""

import os
import re
import sys
import json
import time
import subprocess
import argparse
import requests
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
API_BASE = "https://discoveryengine.googleapis.com/v1"

CORPUS_PATH = Path(__file__).parent / "corpus_context.json"
OUTPUT_DIR = Path(__file__).parent.parent / "hfn-site-output"
DISCUSSION_DIR = OUTPUT_DIR / "audio" / "discussions"

POLL_INTERVAL_SECONDS = 10
MAX_POLL_ATTEMPTS = 120  # 20 minutes max wait

# Token budget: Google Podcast API accepts up to 100,000 tokens.
# ~4 chars per token. Reserve 20k tokens for the focal article,
# 5k for the focus prompt, and distribute the rest across cross-refs.
MAX_CONTEXT_CHARS = 350_000  # ~87k tokens
FOCAL_ARTICLE_BUDGET = 80_000  # ~20k tokens
CROSS_REF_BUDGET_EACH = 12_000  # ~3k tokens per cross-ref
FOCUS_PROMPT_BUDGET = 20_000  # ~5k tokens

# ─── Site Voice & Editorial Identity ─────────────────────────────────────────

SITE_VOICE = """
EDITORIAL IDENTITY — History Future Now

History Future Now is a data-driven analysis site that examines the structural
forces — demographic, technological, economic, geopolitical — shaping the next
century. It is written by Tristan Fischer, a British analyst.

TONE AND PERSONALITY RULES FOR THIS DISCUSSION:

1. INTELLECTUAL BUT ACCESSIBLE. The writing uses historical parallels, data,
   and long-arc thinking. It is not academic jargon. It reads like a brilliant
   dinner conversation between well-read people who happen to have strong
   opinions backed by evidence.

2. POLITICALLY UNFLINCHING. The site does not take a left or right position.
   It follows the evidence wherever it leads, even when the conclusions are
   uncomfortable for both sides. It will criticise free-market orthodoxy AND
   progressive immigration policy in the same article if the data warrants it.
   It treats sacred cows from ALL political traditions with equal scepticism.

3. HISTORICALLY GROUNDED. Every argument is anchored in historical precedent.
   Rome, the Ottoman Empire, the British Empire, the Industrial Revolution —
   these are not decorative references. They are the analytical framework.
   The site's core thesis is that history doesn't repeat but it rhymes, and
   understanding the pattern is the only way to navigate the future.

4. PROVOCATIVE BUT HONEST. The site asks uncomfortable questions directly:
   "Is democracy the opium of the masses?" "Are Europeans fundamentally
   racist?" "Will robots create a new slave class?" It does not shy away
   from controversy but it earns the right to be provocative through rigour.

5. DATA-FIRST. Claims are backed by charts, statistics, and named sources.
   The discussion should reference specific numbers, dates, and historical
   events — not vague generalities.

6. BRITISH ENGLISH. Spelling, idiom, and cultural references are British.
   "Colour" not "color". "Defence" not "defense". References to British
   history and institutions come naturally.

7. NO MORALISING. The site presents evidence and lets readers draw their own
   conclusions. It does not lecture. It does not virtue-signal. It does not
   tell readers what to think. It shows them what the data says and asks
   "what do you think?"

8. CROSS-REFERENCING. The site's power is in connecting themes across articles.
   A discussion about birth rates should naturally reference the automation
   articles, the immigration articles, the military articles. These connections
   should feel organic, not forced.

DISCUSSION FORMAT:
- Two speakers: one leads the analysis, the other pushes back, asks sharp
  questions, and draws out implications. Neither is a passive listener.
- Both speakers are knowledgeable. This is not an expert-and-novice format.
  It is two well-informed people thinking through a complex problem together.
- The discussion should surface insights that a straight reading of the
  article would miss — especially cross-references to other articles in
  the corpus.
- Keep it intellectually honest. If the data is ambiguous, say so. If the
  conclusion is uncomfortable, lean into it.
""".strip()


# ─── Auth ─────────────────────────────────────────────────────────────────────

def get_access_token() -> str:
    """Get a Google Cloud access token via gcloud CLI."""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True, text=True, timeout=15,
        )
        token = result.stdout.strip()
        if not token:
            raise RuntimeError(f"gcloud returned empty token. stderr: {result.stderr}")
        return token
    except FileNotFoundError:
        raise RuntimeError(
            "gcloud CLI not found. Install it: https://cloud.google.com/sdk/docs/install"
        )


def api_headers() -> dict:
    """Build API request headers with fresh auth token."""
    return {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
    }


# ─── Corpus Loading ──────────────────────────────────────────────────────────

def load_corpus() -> dict:
    """Load the pre-built corpus context."""
    if not CORPUS_PATH.exists():
        print("ERROR: Corpus context not found. Run: python3 generate_corpus_context.py")
        sys.exit(1)
    return json.loads(CORPUS_PATH.read_text(encoding='utf-8'))


def find_article(corpus: dict, slug: str) -> dict | None:
    """Find an article in the corpus by slug (partial match)."""
    for article in corpus['articles']:
        if slug in article['slug']:
            return article
    return None


# ─── Context Assembly ─────────────────────────────────────────────────────────

def build_focus_prompt(article: dict, cross_refs: list[dict]) -> str:
    """
    Build the focus prompt that guides the podcast generation.
    This tells the AI what kind of discussion to produce.
    """
    cross_ref_titles = [ref['title'] for ref in cross_refs[:5]]
    cross_ref_str = '\n'.join(f'  - {t}' for t in cross_ref_titles)

    prompt = f"""Generate a deep, intellectually rigorous discussion about this article:
"{article['title']}"

This article is part of History Future Now, a site that analyses structural
forces shaping the next century through historical parallels and data.

The discussion MUST:
- Be between two knowledgeable speakers who both have strong, evidence-based views
- Draw specific connections to these related articles from the same site:
{cross_ref_str}
- Reference specific data points, dates, and historical events from the article
- Challenge assumptions — if the article makes a bold claim, one speaker should
  push back with counter-evidence or alternative interpretations
- Feel like two sharp analysts at a think tank debating over drinks, not a
  scripted interview
- Use British English throughout
- NOT moralise or tell the listener what to think — present the evidence and
  let the listener decide
- Surface at least 2-3 cross-cutting themes that connect this article to the
  broader corpus (demographics, automation, geopolitics, energy, economics)

The tone should be: intellectually provocative, historically grounded,
data-driven, politically unflinching, and genuinely engaging.
"""
    return prompt[:FOCUS_PROMPT_BUDGET]


def build_context_texts(article: dict, corpus: dict) -> list[dict]:
    """
    Build the context array for the Podcast API.
    Includes: site voice, focal article full text, cross-reference summaries.
    """
    contexts = []

    # 1. Site editorial voice (always first)
    contexts.append({"text": SITE_VOICE})

    # 2. Focal article — full text (truncated to budget)
    focal_text = f"FOCAL ARTICLE: {article['title']}\n\n{article['full_text']}"
    contexts.append({"text": focal_text[:FOCAL_ARTICLE_BUDGET]})

    # 3. Cross-references — opening + headings for related articles
    remaining_budget = MAX_CONTEXT_CHARS - len(SITE_VOICE) - len(focal_text[:FOCAL_ARTICLE_BUDGET])
    cross_refs = article.get('cross_references', [])

    for ref in cross_refs:
        if remaining_budget <= 0:
            break

        ref_article = find_article(corpus, ref['slug'])
        if not ref_article:
            continue

        shared = ', '.join(ref.get('shared_themes', []))
        ref_text = (
            f"RELATED ARTICLE: {ref_article['title']} "
            f"(Section: {ref_article['part']}, Shared themes: {shared})\n\n"
            f"{ref_article['opening']}\n\n"
            f"Section headings: {', '.join(ref_article['headings'][:8])}\n\n"
            f"Key content:\n{ref_article['full_text'][:CROSS_REF_BUDGET_EACH]}"
        )

        truncated = ref_text[:min(len(ref_text), remaining_budget)]
        contexts.append({"text": truncated})
        remaining_budget -= len(truncated)

    return contexts


# ─── Google Cloud Podcast API ─────────────────────────────────────────────────

def create_podcast(article: dict, corpus: dict) -> str:
    """
    Create a podcast generation job via the Google Cloud Podcast API.
    Returns the operation name for polling.
    """
    contexts = build_context_texts(article, corpus)
    focus = build_focus_prompt(article, article.get('cross_references', []))

    total_chars = sum(len(c['text']) for c in contexts) + len(focus)
    est_tokens = total_chars // 4
    print(f"    Context: {len(contexts)} blocks, ~{total_chars:,} chars (~{est_tokens:,} tokens)")

    if est_tokens > 100_000:
        print(f"    [WARN] Estimated {est_tokens:,} tokens exceeds 100k limit. Truncating.")
        while est_tokens > 95_000 and len(contexts) > 2:
            removed = contexts.pop()
            total_chars -= len(removed['text'])
            est_tokens = total_chars // 4

    url = f"{API_BASE}/projects/{GCP_PROJECT_ID}/locations/global/podcasts"

    payload = {
        "podcastConfig": {
            "focus": focus,
            "length": "STANDARD",
            "languageCode": "en-GB",
        },
        "contexts": contexts,
        "title": f"History Future Now: {article['title']}",
        "description": (
            f"A deep discussion about '{article['title']}' from History Future Now, "
            f"drawing connections across the site's corpus of {corpus['meta']['total_articles']} articles "
            f"on demographics, technology, geopolitics, and economics."
        ),
    }

    response = requests.post(url, headers=api_headers(), json=payload, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(
            f"Podcast API error {response.status_code}: {response.text[:500]}"
        )

    data = response.json()
    operation_name = data.get("name")
    if not operation_name:
        raise RuntimeError(f"No operation name in response: {json.dumps(data, indent=2)}")

    return operation_name


def poll_operation(operation_name: str) -> bool:
    """Poll a long-running operation until completion. Returns True if done."""
    url = f"{API_BASE}/{operation_name}"

    for attempt in range(MAX_POLL_ATTEMPTS):
        response = requests.get(url, headers=api_headers(), timeout=30)

        if response.status_code != 200:
            if attempt < 3:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue
            raise RuntimeError(f"Poll error {response.status_code}: {response.text[:300]}")

        data = response.json()

        if data.get("done"):
            if "error" in data:
                raise RuntimeError(f"Operation failed: {data['error']}")
            return True

        if attempt % 6 == 0:
            elapsed = attempt * POLL_INTERVAL_SECONDS
            print(f"    Generating... ({elapsed}s elapsed)")

        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError(
        f"Operation {operation_name} did not complete within "
        f"{MAX_POLL_ATTEMPTS * POLL_INTERVAL_SECONDS}s"
    )


def download_podcast(operation_name: str, output_path: Path) -> None:
    """Download the generated podcast MP3."""
    url = f"{API_BASE}/{operation_name}:download?alt=media"

    response = requests.get(
        url, headers=api_headers(), timeout=120, allow_redirects=True,
    )
    response.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)

    size_mb = round(len(response.content) / (1024 * 1024), 2)
    print(f"    Saved: {output_path.name} ({size_mb} MB)")


# ─── Main ─────────────────────────────────────────────────────────────────────

def generate_discussion(article: dict, corpus: dict, force: bool = False) -> bool:
    """Generate a discussion for a single article. Returns True if generated."""
    slug = article['slug']
    output_path = DISCUSSION_DIR / f"{slug}.mp3"

    if output_path.exists() and not force:
        print(f"  [skip] {slug} (already exists)")
        return False

    cross_refs = article.get('cross_references', [])
    print(f"  [{slug}]")
    print(f"    {article['word_count']:,} words, {len(cross_refs)} cross-references")

    operation_name = create_podcast(article, corpus)
    print(f"    Operation: {operation_name}")

    poll_operation(operation_name)
    download_podcast(operation_name, output_path)
    return True


def list_articles(corpus: dict):
    """List all articles and their discussion generation status."""
    for article in corpus['articles']:
        slug = article['slug']
        output_path = DISCUSSION_DIR / f"{slug}.mp3"
        status = "[done]" if output_path.exists() else "[pending]"
        refs = len(article.get('cross_references', []))
        print(f"  {status} [{article['part'][:12]:>12}] {article['title'][:55]:<55} {refs} refs")


def main():
    parser = argparse.ArgumentParser(
        description="Generate podcast-style discussions for HFN articles"
    )
    parser.add_argument("--article", type=str, help="Generate for a specific article slug")
    parser.add_argument("--force", action="store_true", help="Regenerate even if audio exists")
    parser.add_argument("--dry-run", action="store_true", help="Preview without calling API")
    parser.add_argument("--list", action="store_true", help="List articles and status")
    args = parser.parse_args()

    corpus = load_corpus()

    if args.list:
        list_articles(corpus)
        return

    if not GCP_PROJECT_ID:
        print("ERROR: GCP_PROJECT_ID not set.")
        print("  export GCP_PROJECT_ID=your-project-id")
        print("  Also ensure: gcloud auth login && gcloud config set project $GCP_PROJECT_ID")
        sys.exit(1)

    DISCUSSION_DIR.mkdir(parents=True, exist_ok=True)

    articles = corpus['articles']

    if args.article:
        matches = [a for a in articles if args.article in a['slug']]
        if not matches:
            print(f"No article matching '{args.article}' found")
            print(f"Available: {', '.join(a['slug'][:40] for a in articles[:10])}...")
            sys.exit(1)
        articles = matches

    print(f"Discussion generation: {len(articles)} articles")
    print(f"Project: {GCP_PROJECT_ID}")
    print(f"Output: {DISCUSSION_DIR}")
    print()

    if args.dry_run:
        total_context_chars = 0
        for article in articles:
            contexts = build_context_texts(article, corpus)
            chars = sum(len(c['text']) for c in contexts)
            total_context_chars += chars
            refs = len(article.get('cross_references', []))
            exists = (DISCUSSION_DIR / f"{article['slug']}.mp3").exists()
            status = "[exists]" if exists else "[pending]"
            print(
                f"  {status} {article['slug'][:50]:<50} "
                f"{article['word_count']:>6} words, {refs} refs, ~{chars // 4:,} tokens"
            )
        print(f"\nTotal context: ~{total_context_chars:,} chars (~{total_context_chars // 4:,} tokens)")
        return

    generated = 0
    skipped = 0
    failed = 0

    for i, article in enumerate(articles, 1):
        print(f"\n[{i}/{len(articles)}]")
        try:
            if generate_discussion(article, corpus, force=args.force):
                generated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"    [FAILED] {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Done: {generated} generated, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
