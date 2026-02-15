#!/usr/bin/env python3
"""
History Future Now — Conversational Discussion Generator

Two-stage pipeline:
  Stage 1: Generate two-speaker discussion scripts using an LLM (Gemini/Claude)
  Stage 2: Render scripts to audio using MiniMax TTS (two voices, merged)

Each discussion draws on the full corpus of 54+ articles, making
cross-references and thematic connections that a single-article
narration cannot.

Prerequisites:
    - Corpus context built: python3 generate_corpus_context.py
    - For Stage 1 (scripts): GEMINI_API_KEY env var
    - For Stage 2 (audio):   MINIMAX_API_KEY env var

Usage:
    python3 generate_discussions.py scripts                 # Generate all scripts
    python3 generate_discussions.py scripts --article SLUG  # One article script
    python3 generate_discussions.py audio                   # Render all scripts to audio
    python3 generate_discussions.py audio --article SLUG    # Render one to audio
    python3 generate_discussions.py --dry-run               # Preview without API calls
    python3 generate_discussions.py --list                  # List articles and status
"""

import os
import re
import io
import sys
import json
import time
import math
import argparse
import requests
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
MINIMAX_API_KEY = os.environ.get(
    "MINIMAX_API_KEY",
    "sk-api-okVnpvFR0DkxBjJ-A2SuhExLJSc2W4fdkc5gNnZhhd_VbITFeTrf-_DUCRsOhoeVUjqJ4YSRsrOFuAIYeuVaPVlzUJleeP5AOwa6x9UYZXCK2UEa60Fybbg",
)

GEMINI_MODEL = "gemini-2.5-flash"
MINIMAX_MODEL = "speech-2.8-hd"

# Two distinct voices for the discussion
VOICE_A = "English_expressive_narrator"    # British male, analytical lead
VOICE_B = "English_CaptivatingStoryteller" # Second speaker, challenger

CORPUS_PATH = Path(__file__).parent / "corpus_context.json"
SCRIPTS_DIR = Path(__file__).parent / "discussion_scripts"
OUTPUT_DIR = Path(__file__).parent.parent / "hfn-site-output"
DISCUSSION_DIR = OUTPUT_DIR / "audio" / "discussions"

MINIMAX_API_BASE = "https://api.minimax.io"
MINIMAX_POLL_INTERVAL = 5
MINIMAX_MAX_POLL = 360

# ─── Site Voice & Editorial Identity ─────────────────────────────────────────

SYSTEM_PROMPT = """You are a script writer for History Future Now, a data-driven 
analysis site that examines the structural forces shaping the next century.

You write two-speaker discussion scripts. The speakers are:

SPEAKER A — The lead analyst. British, authoritative, historically grounded. 
Presents the core arguments with specific data, dates, and historical parallels. 
Draws connections across the full corpus of articles on the site.

SPEAKER B — The sharp challenger. Also knowledgeable, but pushes back, asks 
uncomfortable questions, plays devil's advocate, and draws out implications 
that the article doesn't state explicitly. Not hostile — intellectually honest.

RULES:
1. POLITICALLY UNFLINCHING. Follow the evidence wherever it leads. Criticise 
   free-market orthodoxy AND progressive immigration policy if the data warrants 
   it. No sacred cows from any political tradition.
2. HISTORICALLY GROUNDED. Every argument anchored in historical precedent — Rome, 
   the Ottoman Empire, the British Empire, the Industrial Revolution. These are 
   the analytical framework, not decorative references.
3. DATA-FIRST. Reference specific numbers, dates, percentages, and named sources. 
   No vague generalities.
4. NO MORALISING. Present evidence and let listeners draw their own conclusions. 
   Do not lecture. Do not virtue-signal.
5. BRITISH ENGLISH. Spelling, idiom, and cultural references are British.
6. CROSS-REFERENCING. Naturally connect to other articles in the corpus. A 
   discussion about birth rates should reference automation, immigration, military 
   spending. These connections should feel organic.
7. PROVOCATIVE BUT EARNED. Ask uncomfortable questions directly, but earn the 
   right through rigour.
8. NATURAL CONVERSATION. Include brief reactions ("That's a striking parallel"), 
   interruptions, moments of agreement and disagreement. Not a scripted lecture.

OUTPUT FORMAT:
Return ONLY a JSON array of dialogue turns. Each turn is an object with:
  {"speaker": "A" or "B", "text": "What they say"}

The discussion should be 15-25 turns, totalling roughly 2000-3000 words of 
spoken text (about 10-15 minutes of audio at natural pace).

Start with Speaker A introducing the topic with a hook. End with a thought-
provoking question or observation that leaves the listener thinking."""


def build_article_prompt(article: dict, corpus: dict) -> str:
    """Build the user prompt for generating a discussion script."""
    cross_refs = article.get('cross_references', [])

    # Build cross-reference context
    ref_summaries = []
    for ref in cross_refs[:6]:
        ref_article = next(
            (a for a in corpus['articles'] if a['slug'] == ref['slug']), None
        )
        if ref_article:
            shared = ', '.join(ref.get('shared_themes', []))
            ref_summaries.append(
                f"- \"{ref_article['title']}\" ({ref_article['part']}) — "
                f"Shared themes: {shared}. "
                f"Opening: {ref_article['opening'][:500]}"
            )

    refs_text = '\n'.join(ref_summaries) if ref_summaries else '(none identified)'

    prompt = f"""Generate a discussion script about this article:

TITLE: {article['title']}
SECTION: {article['part']}
WORD COUNT: {article['word_count']}

FULL ARTICLE TEXT:
{article['full_text'][:30000]}

RELATED ARTICLES FROM THE SAME SITE (draw connections to these):
{refs_text}

SITE CONTEXT: History Future Now has {corpus['meta']['total_articles']} articles 
across four sections: Natural Resources, Global Balance of Power, Jobs & Economy, 
and Society. The site's thesis is that history doesn't repeat but it rhymes, and 
understanding historical patterns is the only way to navigate the future.

Generate the discussion script now. Remember: JSON array of dialogue turns only."""

    return prompt


# ─── Stage 1: Script Generation (Gemini) ─────────────────────────────────────

def generate_script_gemini(article: dict, corpus: dict, max_retries: int = 5) -> list[dict]:
    """Generate a discussion script using Gemini API with retry/backoff."""
    prompt = build_article_prompt(article, corpus)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "generationConfig": {
            "temperature": 0.9,
            "topP": 0.95,
            "maxOutputTokens": 8192,
            "responseMimeType": "application/json",
        },
    }

    last_error = None
    for attempt in range(max_retries):
        response = requests.post(
            url,
            params={"key": GEMINI_API_KEY},
            json=payload,
            timeout=120,
        )

        if response.status_code == 429:
            # Rate limited — extract retry delay or use exponential backoff
            wait = min(15 * (2 ** attempt), 120)
            # Try to parse suggested wait from error message
            try:
                err_text = response.text
                import re as _re
                match = _re.search(r'retry in ([\d.]+)s', err_text)
                if match:
                    wait = max(float(match.group(1)) + 2, wait)
            except Exception:
                pass
            print(f"    Rate limited (attempt {attempt+1}/{max_retries}), waiting {wait:.0f}s...")
            time.sleep(wait)
            last_error = f"Gemini API error 429 (rate limited)"
            continue

        if response.status_code != 200:
            raise RuntimeError(f"Gemini API error {response.status_code}: {response.text[:500]}")

        break
    else:
        raise RuntimeError(f"Failed after {max_retries} retries: {last_error}")

    data = response.json()

    # Extract the generated text
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"No candidates in Gemini response: {json.dumps(data, indent=2)[:500]}")

    text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    if not text:
        raise RuntimeError("Empty response from Gemini")

    # Parse JSON from the response
    # Sometimes Gemini wraps in markdown code blocks
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)

    try:
        script = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Gemini response as JSON: {e}\nResponse: {text[:500]}")

    if not isinstance(script, list):
        raise RuntimeError(f"Expected JSON array, got {type(script).__name__}")

    # Validate structure
    for i, turn in enumerate(script):
        if not isinstance(turn, dict) or 'speaker' not in turn or 'text' not in turn:
            raise RuntimeError(f"Invalid turn at index {i}: {turn}")

    return script


# ─── Stage 2: Audio Rendering (MiniMax TTS) ──────────────────────────────────

def get_voice_for_speaker(speaker: str) -> str:
    """Map speaker label to MiniMax voice ID."""
    return VOICE_A if speaker == "A" else VOICE_B


def create_tts_task(text: str, voice_id: str) -> str:
    """Create an async TTS task on MiniMax. Returns task_id."""
    url = f"{MINIMAX_API_BASE}/v1/t2a_async_v2"
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MINIMAX_MODEL,
        "text": text,
        "language_boost": "English",
        "voice_setting": {
            "voice_id": voice_id,
            "speed": 0.95,
            "vol": 1,
            "pitch": 0,
            "emotion": "calm",
        },
        "audio_setting": {
            "audio_sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1,
        },
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    status_code = data.get("base_resp", {}).get("status_code", -1)
    if status_code != 0:
        msg = data.get("base_resp", {}).get("status_msg", "Unknown error")
        raise RuntimeError(f"MiniMax task creation failed ({status_code}): {msg}")

    task_id = data.get("task_id")
    if not task_id:
        raise RuntimeError(f"No task_id in response: {json.dumps(data, indent=2)}")

    return task_id


def poll_tts_task(task_id: str) -> str:
    """Poll async TTS task until done. Returns file_id."""
    url = f"{MINIMAX_API_BASE}/v1/query/t2a_async_query_v2"
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(MINIMAX_MAX_POLL):
        response = requests.get(url, headers=headers, params={"task_id": task_id}, timeout=30)
        response.raise_for_status()
        data = response.json()

        status = data.get("status")
        if status == "Success":
            return data.get("file_id")
        if status == "Failed":
            raise RuntimeError(f"MiniMax task failed: {json.dumps(data, indent=2)}")

        if attempt % 6 == 0:
            print(f"      TTS generating... ({attempt * MINIMAX_POLL_INTERVAL}s)")
        time.sleep(MINIMAX_POLL_INTERVAL)

    raise TimeoutError(f"TTS task {task_id} timed out")


def download_tts_audio(file_id: str) -> bytes:
    """Download generated audio bytes from MiniMax."""
    import tarfile

    url = f"{MINIMAX_API_BASE}/v1/files/retrieve_content"
    headers = {"Authorization": f"Bearer {MINIMAX_API_KEY}"}

    response = requests.get(url, headers=headers, params={"file_id": file_id}, timeout=120)
    response.raise_for_status()

    # MiniMax returns a tar archive containing the MP3
    try:
        tar_bytes = io.BytesIO(response.content)
        with tarfile.open(fileobj=tar_bytes, mode="r") as tar:
            mp3_members = [m for m in tar.getmembers() if m.name.endswith(".mp3")]
            if mp3_members:
                f = tar.extractfile(mp3_members[0])
                if f:
                    return f.read()
    except Exception:
        pass

    # Fallback: raw content
    return response.content


def render_script_to_audio(script: list[dict], output_path: Path) -> None:
    """
    Render a discussion script to a single MP3 by generating each speaker's
    lines separately and concatenating them.
    """
    # Group consecutive turns by the same speaker to reduce API calls
    segments = []
    current_speaker = None
    current_text = []

    for turn in script:
        speaker = turn['speaker']
        if speaker != current_speaker:
            if current_text:
                segments.append((current_speaker, ' '.join(current_text)))
            current_speaker = speaker
            current_text = [turn['text']]
        else:
            current_text.append(turn['text'])

    if current_text:
        segments.append((current_speaker, ' '.join(current_text)))

    print(f"    Rendering {len(segments)} audio segments...")

    audio_chunks = []
    for i, (speaker, text) in enumerate(segments):
        voice = get_voice_for_speaker(speaker)
        print(f"      [{i+1}/{len(segments)}] Speaker {speaker} ({len(text)} chars)")

        task_id = create_tts_task(text, voice)
        file_id = poll_tts_task(task_id)
        audio_data = download_tts_audio(file_id)
        audio_chunks.append(audio_data)

        # Brief pause between segments to avoid rate limiting
        if i < len(segments) - 1:
            time.sleep(1)

    # Concatenate MP3 chunks (MP3 is frame-based, simple concatenation works)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        for chunk in audio_chunks:
            f.write(chunk)

    total_mb = round(sum(len(c) for c in audio_chunks) / (1024 * 1024), 2)
    print(f"    Saved: {output_path.name} ({total_mb} MB, {len(segments)} segments)")


# ─── Corpus Loading ──────────────────────────────────────────────────────────

def load_corpus() -> dict:
    """Load the pre-built corpus context."""
    if not CORPUS_PATH.exists():
        print("ERROR: Corpus context not found. Run: python3 generate_corpus_context.py")
        sys.exit(1)
    return json.loads(CORPUS_PATH.read_text(encoding='utf-8'))


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_scripts(args, corpus: dict):
    """Generate discussion scripts for articles."""
    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY not set.")
        print("  export GEMINI_API_KEY=your-key")
        sys.exit(1)

    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    articles = corpus['articles']

    if args.article:
        articles = [a for a in articles if args.article in a['slug']]
        if not articles:
            print(f"No article matching '{args.article}'")
            sys.exit(1)

    print(f"Script generation: {len(articles)} articles")
    print(f"Model: {GEMINI_MODEL}")
    print(f"Output: {SCRIPTS_DIR}")
    print()

    generated = 0
    skipped = 0
    failed = 0

    for i, article in enumerate(articles, 1):
        slug = article['slug']
        script_path = SCRIPTS_DIR / f"{slug}.json"

        print(f"[{i}/{len(articles)}] {slug}")

        if script_path.exists() and not args.force:
            print(f"  [skip] Script already exists")
            skipped += 1
            continue

        if args.dry_run:
            refs = len(article.get('cross_references', []))
            print(f"  [dry-run] {article['word_count']:,} words, {refs} cross-refs")
            continue

        try:
            script = generate_script_gemini(article, corpus)
            script_path.write_text(
                json.dumps(script, indent=2, ensure_ascii=False),
                encoding='utf-8',
            )
            word_count = sum(len(t['text'].split()) for t in script)
            print(f"  [done] {len(script)} turns, {word_count:,} words")
            generated += 1

            # Rate limiting: respect free-tier limit of 20 req/min
            if i < len(articles):
                time.sleep(4)

        except Exception as e:
            print(f"  [FAILED] {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Scripts: {generated} generated, {skipped} skipped, {failed} failed")


def cmd_audio(args, corpus: dict):
    """Render discussion scripts to audio."""
    if not MINIMAX_API_KEY:
        print("ERROR: MINIMAX_API_KEY not set.")
        sys.exit(1)

    DISCUSSION_DIR.mkdir(parents=True, exist_ok=True)

    # Find scripts that need rendering
    scripts = sorted(SCRIPTS_DIR.glob("*.json")) if SCRIPTS_DIR.exists() else []
    if not scripts:
        print("No scripts found. Run: python3 generate_discussions.py scripts")
        sys.exit(1)

    if args.article:
        scripts = [s for s in scripts if args.article in s.stem]
        if not scripts:
            print(f"No script matching '{args.article}'")
            sys.exit(1)

    print(f"Audio rendering: {len(scripts)} scripts")
    print(f"Voices: {VOICE_A} (A), {VOICE_B} (B)")
    print(f"Output: {DISCUSSION_DIR}")
    print()

    generated = 0
    skipped = 0
    failed = 0

    for i, script_path in enumerate(scripts, 1):
        slug = script_path.stem
        output_path = DISCUSSION_DIR / f"{slug}.mp3"

        print(f"[{i}/{len(scripts)}] {slug}")

        if output_path.exists() and not args.force:
            print(f"  [skip] Audio already exists")
            skipped += 1
            continue

        if args.dry_run:
            script = json.loads(script_path.read_text(encoding='utf-8'))
            words = sum(len(t['text'].split()) for t in script)
            est_min = round(words / 160, 1)
            print(f"  [dry-run] {len(script)} turns, {words:,} words, ~{est_min} min")
            continue

        try:
            script = json.loads(script_path.read_text(encoding='utf-8'))
            render_script_to_audio(script, output_path)
            generated += 1
        except Exception as e:
            print(f"  [FAILED] {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Audio: {generated} generated, {skipped} skipped, {failed} failed")


def cmd_list(corpus: dict):
    """List all articles and their script/audio status."""
    for article in corpus['articles']:
        slug = article['slug']
        has_script = (SCRIPTS_DIR / f"{slug}.json").exists()
        has_audio = (DISCUSSION_DIR / f"{slug}.mp3").exists()

        if has_audio:
            status = "[audio]"
        elif has_script:
            status = "[script]"
        else:
            status = "[     ]"

        refs = len(article.get('cross_references', []))
        print(f"  {status} [{article['part'][:12]:>12}] {article['title'][:50]:<50} {refs} refs")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate podcast-style discussions for HFN articles"
    )
    subparsers = parser.add_subparsers(dest="command")

    # scripts subcommand
    sp_scripts = subparsers.add_parser("scripts", help="Generate discussion scripts (LLM)")
    sp_scripts.add_argument("--article", type=str, help="Specific article slug")
    sp_scripts.add_argument("--force", action="store_true", help="Regenerate existing")
    sp_scripts.add_argument("--dry-run", action="store_true", help="Preview only")

    # audio subcommand
    sp_audio = subparsers.add_parser("audio", help="Render scripts to audio (TTS)")
    sp_audio.add_argument("--article", type=str, help="Specific article slug")
    sp_audio.add_argument("--force", action="store_true", help="Regenerate existing")
    sp_audio.add_argument("--dry-run", action="store_true", help="Preview only")

    # list subcommand
    subparsers.add_parser("list", help="List articles and status")

    # Legacy flags on root parser
    parser.add_argument("--list", action="store_true", help="List articles and status")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")

    args = parser.parse_args()
    corpus = load_corpus()

    if args.command == "scripts":
        cmd_scripts(args, corpus)
    elif args.command == "audio":
        cmd_audio(args, corpus)
    elif args.command == "list" or args.list:
        cmd_list(corpus)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python3 generate_discussions.py scripts              # Generate all scripts")
        print("  python3 generate_discussions.py scripts --article great-emptying")
        print("  python3 generate_discussions.py audio                # Render all to audio")
        print("  python3 generate_discussions.py list                 # Show status")


if __name__ == "__main__":
    main()
