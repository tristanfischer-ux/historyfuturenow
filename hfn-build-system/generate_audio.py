#!/usr/bin/env python3
"""
History Future Now — Audio Narration Generator

Generates MP3 narrations for all essays using Google Cloud TTS.
Two alternating British voices (male + female) read the article straight through,
switching at section boundaries for a varied listening experience.

Prerequisites:
    - gcloud CLI authenticated (gcloud auth login)
    - ffmpeg installed (brew install ffmpeg)
    - Cloud TTS API enabled on the GCP project

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
import subprocess
import tempfile
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

GCP_PROJECT = "fractional-6a765"

# Two British Neural2 voices for alternating narration
VOICE_MALE = "en-GB-Neural2-B"
VOICE_FEMALE = "en-GB-Neural2-C"

ESSAYS_DIR = Path(__file__).parent / "essays"
OUTPUT_DIR = Path(__file__).parent.parent / "hfn-site-output"
AUDIO_DIR = OUTPUT_DIR / "audio"

# Max chars per Cloud TTS request
TTS_MAX_CHARS = 4800


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


def assign_voices(sections: list[str]) -> list[tuple[str, str]]:
    """Assign alternating voices to sections.
    Returns list of (voice_name, text) tuples."""
    voices = [VOICE_MALE, VOICE_FEMALE]
    return [(voices[i % 2], sec) for i, sec in enumerate(sections)]


def split_long_section(text: str, max_chars: int = TTS_MAX_CHARS) -> list[str]:
    """Split a section that exceeds max_chars at sentence boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current = ""
    sentences = re.split(r'(?<=[.!?])\s+', text)

    for sentence in sentences:
        if current and len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current.strip())
            current = sentence
        else:
            current = f"{current} {sentence}" if current else sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks


# ─── Google Cloud TTS ────────────────────────────────────────────────────────

_gcloud_token = None
_gcloud_token_time = 0


def _get_gcloud_token() -> str:
    """Get a fresh gcloud access token, caching for 30 minutes."""
    global _gcloud_token, _gcloud_token_time
    if _gcloud_token and (time.time() - _gcloud_token_time) < 1800:
        return _gcloud_token

    result = subprocess.run(
        ['gcloud', 'auth', 'print-access-token'],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gcloud auth failed: {result.stderr[:300]}")

    _gcloud_token = result.stdout.strip()
    _gcloud_token_time = time.time()
    return _gcloud_token


def generate_section_audio(text: str, voice_name: str, max_retries: int = 5) -> bytes:
    """Generate MP3 audio for a single section using Google Cloud TTS.
    Returns raw MP3 bytes."""
    url = "https://texttospeech.googleapis.com/v1/text:synthesize"

    payload = {
        "input": {"text": text},
        "voice": {
            "languageCode": "en-GB",
            "name": voice_name,
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "speakingRate": 1.0,
            "pitch": 0.0,
        },
    }

    last_error = None
    for attempt in range(max_retries):
        token = _get_gcloud_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "x-goog-user-project": GCP_PROJECT,
        }

        response = requests.post(url, headers=headers, json=payload, timeout=120)

        if response.status_code in (429, 403, 500, 503):
            wait = 3 + (attempt * 5)
            print(f"      Retryable error {response.status_code} (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
            time.sleep(wait)
            last_error = f"HTTP {response.status_code}"
            continue

        if response.status_code != 200:
            raise RuntimeError(f"Cloud TTS error {response.status_code}: {response.text[:500]}")
        break
    else:
        raise RuntimeError(f"TTS failed after {max_retries} retries: {last_error}")

    data = response.json()
    audio_content = data.get("audioContent", "")
    if not audio_content:
        raise RuntimeError("No audio content in Cloud TTS response")

    return base64.b64decode(audio_content)


def concatenate_mp3_segments(segments: list[bytes]) -> bytes:
    """Concatenate multiple MP3 segments into one using ffmpeg."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_list = []
        for i, seg in enumerate(segments):
            seg_path = os.path.join(tmpdir, f"seg_{i:04d}.mp3")
            with open(seg_path, 'wb') as f:
                f.write(seg)
            file_list.append(seg_path)

        list_path = os.path.join(tmpdir, "files.txt")
        with open(list_path, 'w') as f:
            for fp in file_list:
                f.write(f"file '{fp}'\n")

        output_path = os.path.join(tmpdir, "output.mp3")
        result = subprocess.run(
            ['ffmpeg', '-y', '-f', 'concat', '-safe', '0',
             '-i', list_path, '-codec:a', 'libmp3lame', '-b:a', '128k', output_path],
            capture_output=True, timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg concat error: {result.stderr.decode()[:500]}")

        with open(output_path, 'rb') as f:
            return f.read()


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
    voiced_sections = assign_voices(sections)
    print(f"    {len(sections)} sections, alternating M/F")

    mp3_segments = []
    total_tts_calls = 0

    for i, (voice, section_text) in enumerate(voiced_sections):
        voice_label = "M" if voice == VOICE_MALE else "F"
        sub_chunks = split_long_section(section_text)

        for j, chunk in enumerate(sub_chunks):
            total_tts_calls += 1
            chunk_label = f"    [{i+1}/{len(voiced_sections)}]"
            if len(sub_chunks) > 1:
                chunk_label += f"({j+1}/{len(sub_chunks)})"
            print(f"{chunk_label} {len(chunk):,} chars ({voice_label})")

            mp3_data = generate_section_audio(chunk, voice)
            mp3_segments.append(mp3_data)

            if total_tts_calls % 20 == 0:
                time.sleep(2)

    final_mp3 = concatenate_mp3_segments(mp3_segments)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(final_mp3)

    total_mb = round(len(final_mp3) / (1024 * 1024), 2)
    print(f"    Saved: {output_path.name} ({total_mb} MB, {total_tts_calls} API calls)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate audio narrations for HFN essays")
    parser.add_argument("--article", type=str, help="Generate for a specific article slug")
    parser.add_argument("--force", action="store_true", help="Regenerate even if audio exists")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    args = parser.parse_args()

    import shutil

    # Check gcloud
    if not shutil.which('gcloud'):
        print("ERROR: gcloud CLI not found. Install from https://cloud.google.com/sdk/docs/install")
        sys.exit(1)

    # Verify gcloud auth
    try:
        _get_gcloud_token()
    except Exception as e:
        print(f"ERROR: gcloud authentication failed: {e}")
        print("  Run: gcloud auth login")
        sys.exit(1)

    # Check ffmpeg
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
    print(f"Backend: Google Cloud TTS (Neural2)")
    print(f"Project: {GCP_PROJECT}")
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
