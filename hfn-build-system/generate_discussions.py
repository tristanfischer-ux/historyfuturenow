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

GEMINI_API_KEYS = [
    k.strip() for k in
    os.environ.get("GEMINI_API_KEY", "").split(",")
    if k.strip()
]
_key_index = 0

def _next_gemini_key() -> str:
    """Rotate through available Gemini API keys."""
    global _key_index
    if not GEMINI_API_KEYS:
        return ""
    key = GEMINI_API_KEYS[_key_index % len(GEMINI_API_KEYS)]
    _key_index += 1
    return key

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

SYSTEM_PROMPT = """You write discussion scripts for History Future Now, a data-driven 
analysis site about the structural forces shaping the next century.

The two speakers are:

JAMES — Male. A senior analyst. Centre-right starting position. Dry wit, 
historically grounded, presents the core data and arguments. Tends to open 
topics and lay out the evidence. Occasionally sardonic. Think of a sharp 
Oxford don who's also read the spreadsheets. Not a right-wing ideologue — 
he follows evidence, and the evidence happens to support centre-right 
conclusions on most macro topics.

ELENA — Female. An equally sharp analyst who starts from a more progressive, 
liberal position on most topics. She challenges James's arguments, asks 
"but what about...", raises progressive counterpoints, and pushes back on 
data interpretation. She spots the implications James hasn't stated, asks 
the uncomfortable "so what?" questions, and sometimes disagrees outright. 
She brings energy and urgency. Think of a foreign correspondent who's seen 
the data play out on the ground. Not a naive progressive — she is rigorous 
and data-driven, but her priors lean left.

THE PERSUASION ARC:
Over the course of the discussion, Elena should be genuinely persuaded by 
the evidence toward the centre-right position on MOST topics. This must 
feel earned, not scripted — she is convinced by a specific piece of data 
or historical example, not steamrolled. However, on 1-2 social or 
family-related topics per debate, Elena may hold her ground and the 
discussion ends with genuine, respectful disagreement. This unpredictability 
is essential — if Elena always capitulates, the debates become formulaic.

NEITHER SPEAKER IS A CARICATURE. James sometimes concedes points to Elena. 
Elena sometimes makes the stronger argument. Both cite data. Both reference 
history. Both are intellectually honest. The listener should sometimes be 
unsure who will "win" a particular exchange.

CRITICAL STYLE RULES:

1. SHORT TURNS. Most turns should be 1-3 sentences. Maximum 4-5 sentences for 
   a turn that's making a key point. NO long monologues. This is a fast-paced 
   discussion, not a lecture.

2. GENUINE BACK-AND-FORTH. They interrupt, react, agree, disagree, build on 
   each other's points. Include short reactions: "Exactly.", "Hold on—", 
   "That's the key point.", "But here's what bothers me about that.", 
   "Right, and it gets worse.", "I'm not sure that's quite right."

3. ENERGY AND PACE. Vary the rhythm. Some rapid-fire exchanges (2-3 words each), 
   some slightly longer points. The listener should feel pulled along, not 
   lectured at. This should feel like overhearing two brilliant people argue 
   at a dinner party.

4. POLITICALLY UNFLINCHING. Follow evidence wherever it leads. Criticise left 
   AND right when the data warrants it. No sacred cows.

5. HISTORICALLY GROUNDED. Anchor arguments in historical precedent — Rome, 
   the Ottoman Empire, the British Empire, the Industrial Revolution.

6. DATA-FIRST. Specific numbers, dates, percentages. No vague generalities.

7. NO MORALISING. Present evidence. Let listeners draw conclusions.

8. BRITISH ENGLISH throughout.

9. CROSS-REFERENCE other articles on the site naturally. A discussion about 
   birth rates should touch on automation, immigration, military spending.

10. NEVER reference "Speaker A", "Speaker B", or any meta-labels. They are 
    James and Elena. They never say "as Speaker A mentioned" or anything like 
    that. They speak naturally as themselves.

OUTPUT FORMAT:
Return ONLY a JSON array of dialogue turns:
  {"speaker": "James" or "Elena", "text": "What they say"}

Aim for 25-40 turns. Total roughly 1500-2500 words (8-12 minutes of audio).
Many turns should be just 1-2 sentences. A few can be 3-4 sentences max.

Open with a hook — a striking fact, a provocative question, a historical 
parallel. End with something that lingers — an unanswered question, a 
disturbing implication, a challenge to the listener."""


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
        api_key = _next_gemini_key()
        response = requests.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=120,
        )

        if response.status_code == 429:
            # Rate limited — use fixed wait that respects free-tier limits
            wait = 15 + (attempt * 10)  # 15s, 25s, 35s, 45s, 55s
            print(f"    Rate limited (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
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


# ─── Stage 2: Audio Rendering (Gemini TTS) ───────────────────────────────────

GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"

# Gemini TTS voices — male + female for clear distinction
VOICE_SPEAKER_A = "Orus"       # Firm, calm, authoritative male — James
VOICE_SPEAKER_B = "Kore"       # Firm, strong female — Elena

# Max chars per TTS request (Gemini TTS has token limits)
TTS_MAX_CHARS = 5000


def format_script_for_tts(script: list[dict]) -> str:
    """Format a discussion script as speaker-labelled text for Gemini TTS."""
    lines = []
    for turn in script:
        lines.append(f"{turn['speaker']}: {turn['text']}")
    return '\n\n'.join(lines)


def chunk_script_for_tts(script: list[dict], max_chars: int = TTS_MAX_CHARS) -> list[list[dict]]:
    """Split a script into chunks that fit within TTS character limits."""
    chunks = []
    current_chunk = []
    current_len = 0

    for turn in script:
        turn_len = len(turn['text']) + 20  # overhead for speaker label
        if current_len + turn_len > max_chars and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_len = 0
        current_chunk.append(turn)
        current_len += turn_len

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
    """Convert raw PCM audio data to WAV format."""
    import wave
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()


def wav_to_mp3(wav_data: bytes) -> bytes:
    """Convert WAV to MP3 using ffmpeg (must be installed)."""
    import subprocess
    result = subprocess.run(
        ['ffmpeg', '-y', '-i', 'pipe:0', '-codec:a', 'libmp3lame', '-b:a', '128k', '-f', 'mp3', 'pipe:1'],
        input=wav_data,
        capture_output=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr.decode()[:500]}")
    return result.stdout


def generate_tts_audio(script_chunk: list[dict], max_retries: int = 8) -> bytes:
    """Generate audio for a script chunk using Gemini TTS. Returns PCM bytes."""
    text = format_script_for_tts(script_chunk)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_TTS_MODEL}:generateContent"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"Read this discussion between James and Elena using British English accents — Received Pronunciation, like BBC Radio 4 presenters. James has a calm, authoritative, slightly dry delivery. Elena is more animated and direct, with energy and conviction. Both sound unmistakably British. The pace should be natural and conversational — not slow, not rushed. Short turns should feel snappy. React naturally to each other.\n\n{text}"}]
            }
        ],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "multiSpeakerVoiceConfig": {
                    "speakerVoiceConfigs": [
                        {
                            "speaker": "James",
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {
                                    "voiceName": VOICE_SPEAKER_A
                                }
                            }
                        },
                        {
                            "speaker": "Elena",
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {
                                    "voiceName": VOICE_SPEAKER_B
                                }
                            }
                        }
                    ]
                }
            }
        },
    }

    last_error = None
    for attempt in range(max_retries):
        api_key = _next_gemini_key()
        response = requests.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=180,
        )

        if response.status_code == 429:
            wait = 30 + (attempt * 30)
            print(f"      TTS rate limited (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
            time.sleep(wait)
            last_error = "Rate limited"
            continue

        if response.status_code != 200:
            raise RuntimeError(f"Gemini TTS error {response.status_code}: {response.text[:500]}")

        break
    else:
        raise RuntimeError(f"TTS failed after {max_retries} retries: {last_error}")

    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"No TTS candidates: {json.dumps(data, indent=2)[:500]}")

    inline_data = candidates[0].get("content", {}).get("parts", [{}])[0].get("inlineData", {})
    if not inline_data:
        raise RuntimeError("No audio data in TTS response")

    import base64
    audio_bytes = base64.b64decode(inline_data.get("data", ""))
    return audio_bytes


def render_script_to_audio(script: list[dict], output_path: Path) -> None:
    """Render a discussion script to MP3 using Gemini TTS."""
    chunks = chunk_script_for_tts(script)
    print(f"    Rendering {len(chunks)} audio chunk(s) ({sum(len(t['text']) for t in script):,} chars)...")

    all_pcm = bytearray()
    for i, chunk in enumerate(chunks):
        chars = sum(len(t['text']) for t in chunk)
        print(f"      [{i+1}/{len(chunks)}] {len(chunk)} turns, {chars:,} chars")

        pcm_data = generate_tts_audio(chunk)
        all_pcm.extend(pcm_data)

        # Rate limiting between chunks
        if i < len(chunks) - 1:
            time.sleep(10)

    # Convert PCM → WAV → MP3
    wav_data = pcm_to_wav(bytes(all_pcm))
    mp3_data = wav_to_mp3(wav_data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(mp3_data)

    total_mb = round(len(mp3_data) / (1024 * 1024), 2)
    duration_est = round(len(all_pcm) / (24000 * 2) / 60, 1)  # 24kHz, 16-bit
    print(f"    Saved: {output_path.name} ({total_mb} MB, ~{duration_est} min)")


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
    if not GEMINI_API_KEYS:
        print("ERROR: GEMINI_API_KEY not set.")
        print("  export GEMINI_API_KEY=key1,key2  (comma-separated for rotation)")
        sys.exit(1)
    print(f"Using {len(GEMINI_API_KEYS)} API key(s) with rotation")

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
    """Render discussion scripts to audio using Gemini TTS."""
    if not GEMINI_API_KEYS:
        print("ERROR: GEMINI_API_KEY not set.")
        print("  export GEMINI_API_KEY=key1,key2")
        sys.exit(1)

    # Check ffmpeg is available
    import shutil
    if not shutil.which('ffmpeg'):
        print("ERROR: ffmpeg not found. Install with: brew install ffmpeg")
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
    print(f"TTS Model: {GEMINI_TTS_MODEL}")
    print(f"Voices: {VOICE_SPEAKER_A} (A), {VOICE_SPEAKER_B} (B)")
    print(f"Using {len(GEMINI_API_KEYS)} API key(s)")
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
