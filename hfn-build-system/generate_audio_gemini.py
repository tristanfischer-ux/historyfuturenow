#!/usr/bin/env python3
"""
History Future Now — Audio Narration Generator

Generates MP3 narrations for all essays using Gemini TTS.
Two alternating British voices (male + female) read the article straight through,
switching at section boundaries for a varied listening experience.

Prerequisites:
    - GEMINI_API_KEY env var (comma-separated for rotation)
    - ffmpeg installed (brew install ffmpeg)

Usage:
    python3 generate_audio.py                    # Generate all missing audio
    python3 generate_audio.py --article SLUG     # Generate for one article
    python3 generate_audio.py --force            # Regenerate all (overwrite)
    python3 generate_audio.py --dry-run          # Preview without API calls
"""

import os
import re
import io
import sys
import json
import time
import yaml
import argparse
import requests
import base64
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

GEMINI_API_KEYS = [
    k.strip() for k in
    os.environ.get("GEMINI_API_KEY", "").split(",")
    if k.strip()
]
_key_index = 0

def _next_gemini_key() -> str:
    global _key_index
    if not GEMINI_API_KEYS:
        return ""
    key = GEMINI_API_KEYS[_key_index % len(GEMINI_API_KEYS)]
    _key_index += 1
    return key

GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"

# Two British voices for alternating narration
VOICE_MALE = "Puck"     # Upbeat, lively British male
VOICE_FEMALE = "Kore"   # Clear, engaging British female

ESSAYS_DIR = Path(__file__).parent / "essays"
OUTPUT_DIR = Path(__file__).parent.parent / "hfn-site-output"
AUDIO_DIR = OUTPUT_DIR / "audio"

# Max chars per TTS request (Gemini TTS has token limits)
TTS_MAX_CHARS = 4500


# ─── Text Extraction ─────────────────────────────────────────────────────────

def fix_encoding(text: str) -> str:
    replacements = {
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '--', '\u2026': '...',
        '\xa0': ' ', '\u00a3': 'GBP ', '\u20ac': 'EUR ',
        'â\x80\x99': "'", 'â\x80\x98': "'", 'â\x80\x9c': '"', 'â\x80\x9d': '"',
        'â\x80\x93': '--', 'â\x80\x94': '-', 'â\x80\xa6': '...', 'Â ': ' ', 'Â': '',
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text


def extract_narration_text(filepath: Path) -> tuple[str, str, str]:
    """Extract clean narration text from a markdown essay."""
    content = filepath.read_text(encoding="utf-8", errors="replace")

    meta = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                meta = {}
            body = parts[2]

    body = fix_encoding(body)

    title = meta.get("title", filepath.stem.replace("-", " ").title())
    title = re.sub(r"</?strong>", "", title).replace("&nbsp;", " ").replace("\xa0", " ").strip()

    slug = meta.get("slug", filepath.stem)
    slug = slug.replace("strong", "").replace("nbsp", "").strip("-")
    slug = re.sub(r"-+", "-", slug)

    # Remove the first H1 heading
    body = re.sub(r"^\s*#\s+[^\n]+\n", "", body, count=1)
    body = re.sub(r"\n---\s*\n\s*##\s*THEN:.*$", "", body, flags=re.DOTALL)

    # Remove references section (not suitable for audio)
    body = re.sub(r"\n##\s*References\s*\n.*$", "", body, flags=re.DOTALL)

    text = body
    text = re.sub(r"^#{1,6}\s+(.+)$", r"\n\1.\n", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    narration = f"{title}.\n\nBy Tristan Fischer.\n\n{text}"
    return title, slug, narration


# ─── Section Splitting ────────────────────────────────────────────────────────

def split_into_sections(narration: str) -> list[str]:
    """Split narration into sections for alternating voices.
    Splits on paragraph boundaries, merging short chunks."""
    raw_chunks = re.split(r'\n\n+', narration)
    raw_chunks = [c.strip() for c in raw_chunks if c.strip()]

    sections = []
    buffer = ""
    for chunk in raw_chunks:
        if buffer:
            buffer += "\n\n" + chunk
        else:
            buffer = chunk

        if len(buffer) >= 300:
            sections.append(buffer)
            buffer = ""

    if buffer:
        if sections:
            sections[-1] += "\n\n" + buffer
        else:
            sections.append(buffer)

    return sections


def chunk_sections_for_tts(sections: list[str], max_chars: int = TTS_MAX_CHARS) -> list[list[tuple[str, str]]]:
    """Group sections into TTS-sized chunks, preserving voice assignment.
    Returns list of chunks, each chunk is a list of (voice_label, text) tuples."""
    voices = ["Reader1", "Reader2"]
    all_assigned = [(voices[i % 2], sec) for i, sec in enumerate(sections)]

    chunks = []
    current_chunk = []
    current_len = 0

    for voice, text in all_assigned:
        entry_len = len(text) + 30
        if current_len + entry_len > max_chars and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_len = 0
        current_chunk.append((voice, text))
        current_len += entry_len

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# ─── Gemini TTS ──────────────────────────────────────────────────────────────

def pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
    import wave
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()


def wav_to_mp3(wav_data: bytes) -> bytes:
    import subprocess
    result = subprocess.run(
        ['ffmpeg', '-y', '-i', 'pipe:0', '-codec:a', 'libmp3lame', '-b:a', '128k', '-f', 'mp3', 'pipe:1'],
        input=wav_data, capture_output=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {result.stderr.decode()[:500]}")
    return result.stdout


def generate_tts_chunk(chunk: list[tuple[str, str]], max_retries: int = 8) -> bytes:
    """Generate audio for a chunk of sections using Gemini multi-speaker TTS.
    Returns raw PCM bytes."""
    # Format as speaker-labelled text
    lines = []
    for voice, text in chunk:
        lines.append(f"{voice}: {text}")
    formatted = "\n\n".join(lines)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_TTS_MODEL}:generateContent"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"Read this article narration aloud using British English accents — Received Pronunciation, like BBC Radio 4. Reader1 is a calm, authoritative male narrator. Reader2 is a clear, engaging female narrator. Both read at a natural, measured pace suitable for a serious analytical article. This is a straight narration, not a conversation — each reader reads their assigned sections smoothly and professionally.\n\n{formatted}"}]
            }
        ],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "multiSpeakerVoiceConfig": {
                    "speakerVoiceConfigs": [
                        {
                            "speaker": "Reader1",
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {"voiceName": VOICE_MALE}
                            }
                        },
                        {
                            "speaker": "Reader2",
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {"voiceName": VOICE_FEMALE}
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
            url, params={"key": api_key}, json=payload, timeout=180,
        )

        if response.status_code == 429:
            wait = 30 + (attempt * 30)
            print(f"      Rate limited (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
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

    return base64.b64decode(inline_data.get("data", ""))


# ─── Main Generation ─────────────────────────────────────────────────────────

def generate_article_audio(filepath: Path, force: bool = False) -> bool:
    """Generate audio narration with alternating male/female voices."""
    title, slug, narration = extract_narration_text(filepath)
    output_path = AUDIO_DIR / f"{slug}.mp3"

    if output_path.exists() and not force:
        print(f"  [skip] {slug} (already exists)")
        return False

    word_count = len(narration.split())
    char_count = len(narration)
    est_minutes = round(word_count / 160, 1)

    print(f"  [{slug}]")
    print(f"    {word_count:,} words, {char_count:,} chars, ~{est_minutes} min estimated")

    sections = split_into_sections(narration)
    chunks = chunk_sections_for_tts(sections)
    print(f"    {len(sections)} sections → {len(chunks)} TTS chunk(s)")

    all_pcm = bytearray()
    for i, chunk in enumerate(chunks):
        chunk_chars = sum(len(t) for _, t in chunk)
        voices_in_chunk = set(v for v, _ in chunk)
        voice_str = "M+F" if len(voices_in_chunk) > 1 else ("M" if "Reader1" in voices_in_chunk else "F")
        print(f"    [{i+1}/{len(chunks)}] {len(chunk)} sections, {chunk_chars:,} chars ({voice_str})")

        pcm_data = generate_tts_chunk(chunk)
        all_pcm.extend(pcm_data)

        if i < len(chunks) - 1:
            time.sleep(10)

    # Convert PCM → WAV → MP3
    wav_data = pcm_to_wav(bytes(all_pcm))
    mp3_data = wav_to_mp3(wav_data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(mp3_data)

    total_mb = round(len(mp3_data) / (1024 * 1024), 2)
    duration_est = round(len(all_pcm) / (24000 * 2) / 60, 1)
    print(f"    Saved: {output_path.name} ({total_mb} MB, ~{duration_est} min)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate audio narrations for HFN essays")
    parser.add_argument("--article", type=str, help="Generate for a specific article slug")
    parser.add_argument("--force", action="store_true", help="Regenerate even if audio exists")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    args = parser.parse_args()

    if not GEMINI_API_KEYS:
        print("ERROR: GEMINI_API_KEY not set.")
        print("  export GEMINI_API_KEY=key1,key2")
        sys.exit(1)

    # Check ffmpeg
    import shutil
    if not shutil.which('ffmpeg'):
        print("ERROR: ffmpeg not found. Install with: brew install ffmpeg")
        sys.exit(1)

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    essays = sorted(ESSAYS_DIR.glob("*.md"))
    if not essays:
        print(f"No essays found in {ESSAYS_DIR}")
        sys.exit(1)

    if args.article:
        matches = [f for f in essays if args.article in f.stem]
        if not matches:
            print(f"No essay matching '{args.article}' found")
            sys.exit(1)
        essays = matches

    print(f"Audio generation: {len(essays)} essays")
    print(f"Voices: {VOICE_MALE} (male) + {VOICE_FEMALE} (female)")
    print(f"Model: {GEMINI_TTS_MODEL}")
    print(f"Using {len(GEMINI_API_KEYS)} API key(s)")
    print(f"Output: {AUDIO_DIR}")
    print()

    if args.dry_run:
        total_words = 0
        for filepath in essays:
            title, slug, narration = extract_narration_text(filepath)
            words = len(narration.split())
            total_words += words
            exists = (AUDIO_DIR / f"{slug}.mp3").exists()
            status = "[exists]" if exists else "[pending]"
            print(f"  {status} {slug}: {words:,} words")
        print(f"\nTotal: {total_words:,} words, ~{round(total_words/160, 1)} min")
        return

    generated = 0
    skipped = 0
    failed = 0

    for i, filepath in enumerate(essays, 1):
        print(f"\n[{i}/{len(essays)}]")
        try:
            if generate_article_audio(filepath, force=args.force):
                generated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"    [FAILED] {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Done: {generated} generated, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
