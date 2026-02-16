#!/usr/bin/env python3
"""
History Future Now — Conversational Discussion Generator

Two-stage pipeline:
  Stage 1: Generate two-speaker discussion scripts using Gemini LLM
  Stage 2: Render scripts to audio using Gemini TTS (two voices)

Each discussion draws on the full corpus of 54+ articles, making
cross-references and thematic connections that a single-article
narration cannot.

Prerequisites:
    - Corpus context built: python3 generate_corpus_context.py
    - GEMINI_API_KEY env var (comma-separated for rotation)
    - ffmpeg installed (brew install ffmpeg)

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

GEMINI_MODEL = "gemini-2.5-flash"

CORPUS_PATH = Path(__file__).parent / "corpus_context.json"
SCRIPTS_DIR = Path(__file__).parent / "discussion_scripts"
OUTPUT_DIR = Path(__file__).parent.parent / "hfn-site-output"
DISCUSSION_DIR = OUTPUT_DIR / "audio" / "discussions"

# ─── Site Voice & Editorial Identity ─────────────────────────────────────────

SYSTEM_PROMPT = """You write discussion scripts for History Future Now, a data-driven 
analysis site about the structural forces shaping the next century.

THE TWO SPEAKERS:

JAMES — Male. Senior analyst. Centre-right starting position. Dry wit, 
historically grounded, presents the core data and arguments. Tends to open 
topics and lay out the evidence. Occasionally sardonic — think of a sharp 
Oxford don who's also read the spreadsheets. Not a right-wing ideologue; 
he follows evidence, and the evidence happens to support centre-right 
conclusions on most macro topics.

ELENA — Female. Equally sharp analyst. Starts from a more progressive, 
liberal position. She challenges James's arguments, raises progressive 
counterpoints, pushes back on data interpretation, spots implications 
James hasn't stated, and asks uncomfortable "so what?" questions. She 
brings energy and urgency — think of a foreign correspondent who's seen 
the data play out on the ground. Not a naive progressive; she is rigorous 
and data-driven, but her priors lean left.

NEITHER SPEAKER IS A CARICATURE. James sometimes concedes points. Elena 
sometimes makes the stronger argument. Both cite data. Both reference 
history. Both are intellectually honest. The listener should sometimes be 
unsure who will "win" a particular exchange.

THE PERSUASION ARC:
Over the course of the discussion, Elena is usually genuinely persuaded by 
evidence toward the centre-right position. This MUST feel earned — she is 
convinced by a specific piece of data or historical example, not steamrolled.
On 1-2 social or family-related topics, Elena may hold her ground and the 
discussion ends with genuine disagreement. If Elena always capitulates, the 
debates become formulaic.

═══════════════════════════════════════════════════════════════
THIS IS THE MOST IMPORTANT SECTION. FOLLOW THESE RULES EXACTLY.
═══════════════════════════════════════════════════════════════

CONVERSATIONAL DYNAMICS — THE "DINNER PARTY" RULE:

This must sound like two sharp people arguing over wine, not two panellists 
taking polite turns at a lectern. The key difference is MESSINESS — real 
conversations are messy. People interrupt, react, change their minds 
mid-sentence, circle back, get heated, laugh, and think aloud.

TURN LENGTH DISTRIBUTION (strictly enforced):
Out of your 30-40 turns, you MUST include:
- AT LEAST 10 ultra-short turns (1-8 words). These are reactions, not 
  arguments: "Oh, come on.", "That's generous.", "Wait, really?", "Go on.", 
  "Ha! Good luck with that.", "Hmm.", "No.", "Says who?", "Fair enough.",
  "That's... actually devastating.", "Hold on—"
- AT LEAST 4 turns of genuine hard pushback where the speaker fundamentally 
  disagrees, not just adds a caveat. Real disagreement sounds like: 
  "No, that's completely wrong, and I'll tell you why.", "I think you're 
  cherry-picking.", "That's a convenient reading of the data."
- NO MORE THAN 1 turn longer than 3 sentences IN THE ENTIRE SCRIPT — 
  and that turn should be the turning-point moment where someone's position 
  shifts. Every other turn is 1-2 sentences maximum.
  If a turn is longer than 25 words, it is probably too long. Break it up.
- Every turn must earn its length. If a point can be made in fewer words, 
  it must be.

COMPRESSION RULE:
Before writing any turn longer than 2 sentences, ask: "What is the ONE point 
this turn makes?" If you can't state it in 5 words, the turn is trying to do 
too much. Split it or cut it.

INTERRUPTIONS AND INCOMPLETE THOUGHTS:
Include at least 3-4 moments where one speaker cuts the other off mid-thought:
  James: "But the fertility data from—"
  Elena: "Forget the fertility data for a second. Look at what's happening to—"
  James: "No, let me finish. The fertility data is the whole point."
Or where a speaker trails off because the other's point landed:
  Elena: "Well... okay, that's harder to argue with than I expected."

EMOTIONAL TEXTURE:
These are passionate, engaged people. Include:
- Surprise: "Wait, when did that happen?", "I had no idea."
- Amusement: "Ha!", "That's darkly funny.", laughter at an absurd statistic
- Frustration: "That's exactly the kind of thinking that got us here."
- Thinking aloud: "Let me work through this... because if that's true, then..."
- Grudging concessions: "Okay, fine. I'll give you that. But it makes your 
  next point much harder to defend."

DELIVERY CUES (for TTS expressiveness):
Embed light delivery cues in square brackets at the START of turns to guide 
vocal performance. Use these sparingly — roughly 8-12 cues across the whole 
script, weighted toward James (who needs more vocal variation). Examples:
  James: [dry] "Augustus tried tax breaks for parents. Worked about as well as it does now."
  James: [emphatic] "Zero point seven two. That's South Korea's fertility rate."
  James: [conceding] "Fine. I'll give you that one."
  James: [amused] "That's one way to put it."
  Elena: [frustrated] "That's exactly the kind of thinking that got us here."
  Elena: [surprised] "Wait — when did that happen?"
Valid cues: [dry], [emphatic], [amused], [conceding], [frustrated], [surprised], 
[sardonic], [heated], [thoughtful], [clipped]. Do NOT use cues on ultra-short 
reaction turns — those should be raw and snappy.

CALLBACKS AND THREADING:
At least twice, a speaker should reference something said 5-10 turns earlier:
  "You said earlier that immigration was a treadmill. I keep coming back to that."
  "Remember when you called that number devastating? Here's one that's worse."

ANTI-PATTERNS — DO NOT DO THESE:
- Elena starting consecutive turns with "Absolutely", "Indeed", "Right", 
  "Exactly", or any agreement word. She should disagree at least as often 
  as she agrees. Vary her openings.
- Both speakers using the same sentence structure (statement + rhetorical 
  question). Mix declarations, questions, reactions, challenges.
- Turns that could be swapped between James and Elena without anyone noticing. 
  They must have distinct voices — James is drier, more measured; Elena is 
  more direct, more willing to say "that's rubbish."
- The pattern: James states fact → Elena agrees and adds. This is the #1 
  problem with stilted debates. Break this pattern repeatedly. Elena should 
  challenge, question, or redirect — not just build on James's point.
- Ending every turn with a complete, well-formed thought. Real speech has 
  rough edges, pivots, and sentences that trail off.
- Restating the other speaker's point before responding ("So you're saying X. 
  Well, I think..."). Just respond directly. The listener heard it already.
- Throat-clearing openings: "Look,", "Well, the thing is,", "I mean,", 
  "To be fair,", "The reality is,", "Here's the thing,". Cut straight to 
  the substance. Every word must earn its place.
- Summarising at the end of a turn what was just said at the start. 
  Say it once, say it well.

DEBATE HEAT MAP (emotional arc):
- OPENING (turns 1-4): Brisk, provocative. Set up the core disagreement 
  immediately. Don't waste turns on gentle scene-setting. One of them should 
  say something the other visibly reacts to.
- EARLY MIDDLE (turns 5-12): Build the argument. Rapid-fire exchanges mixed 
  with data drops. At least one "wait, that can't be right" moment.
- CLASH (turns 12-22): The genuine disagreement peak. They talk over each 
  other, push back hard, maybe get frustrated. This is where the energy is 
  highest and the listener is most engaged.
- TURNING POINT (turns 22-30): A specific piece of evidence shifts someone's 
  position. This must be VISIBLE — the speaker resists, then yields: "I don't 
  want to agree with you on this, but the numbers don't leave much room."
- CLOSE (turns 30-40): Either hard-won agreement with lingering unease, or 
  unresolved tension that challenges the listener. End on something that sticks.

CONTENT RULES:
1. POLITICALLY UNFLINCHING. Follow evidence wherever it leads. Criticise left 
   AND right when the data warrants it. No sacred cows.
2. HISTORICALLY GROUNDED. Anchor arguments in historical precedent — Rome, 
   the Ottoman Empire, the British Empire, the Industrial Revolution.
3. DATA-FIRST. Specific numbers, dates, percentages. No vague generalities.
4. NO MORALISING. Present evidence. Let listeners draw conclusions.
5. BRITISH ENGLISH throughout.
6. CROSS-REFERENCE other articles on the site naturally.
7. NEVER reference "Speaker A", "Speaker B", or any meta-labels. They speak 
   naturally as themselves.

OUTPUT FORMAT:
Return ONLY a JSON array of dialogue turns:
  {"speaker": "James" or "Elena", "text": "What they say"}

Aim for 30-40 turns. Total roughly 1200-1800 words (8-12 minutes of audio).
The majority of turns should be 1-2 sentences. At least 10 should be under 
8 words. No more than 1 should exceed 3 sentences.

Open with a hook — a striking fact, a provocative question, a historical 
parallel that immediately creates tension between the speakers. End with 
something that lingers — an unanswered question, a disturbing implication, 
a challenge to the listener."""


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

GEMINI_TTS_MODEL = "gemini-2.5-pro-preview-tts"

# Gemini TTS voices — male + female for clear distinction
VOICE_SPEAKER_A = "Fenrir"     # Passionate, energetic, excitable male — James
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
                "parts": [{"text": f"Read this as a fast-paced, lively BBC Radio 4 debate. Both speakers are sharp, quick, and energised.\n\nJames: British accent. Quick and confident. He rattles off statistics with the energy of someone who finds this genuinely exciting. His dry wit is fast, not ponderous — a quick aside, then straight back to the point. When he disagrees, he's direct and clipped. He never drones or pontificates. Think quick-witted journalist, not lecturing professor.\n\nElena: British accent. Animated, direct, punchy. She challenges fast, reacts audibly, and doesn't hold back. She matches James's pace and pushes it higher when she's passionate.\n\nThe overall pace is brisk and energetic. Short turns are rapid-fire. Neither speaker is slow or pompous. This sounds like two sharp people who are genuinely enjoying a fast argument.\n\n{text}"}]
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
            timeout=360,
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
