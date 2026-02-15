#!/usr/bin/env python3
"""
History Future Now — Audio Narration Generator

Uses MiniMax's async TTS API to generate MP3 narrations for all essays.
Voice: English_expressive_narrator (British male, ~189 WPM)
Model: speech-2.8-hd (best quality for long-form narration)

Usage:
    python3 generate_audio.py                    # Generate all missing audio
    python3 generate_audio.py --article SLUG     # Generate for one article
    python3 generate_audio.py --force            # Regenerate all (overwrite)
    python3 generate_audio.py --list-voices      # Preview available voices
"""

import os
import re
import sys
import json
import time
import yaml
import argparse
import requests
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

MINIMAX_API_KEY = os.environ.get(
    "MINIMAX_API_KEY",
    "sk-api-okVnpvFR0DkxBjJ-A2SuhExLJSc2W4fdkc5gNnZhhd_VbITFeTrf-_DUCRsOhoeVUjqJ4YSRsrOFuAIYeuVaPVlzUJleeP5AOwa6x9UYZXCK2UEa60Fybbg",
)

API_BASE = "https://api.minimax.io"
VOICE_ID = "English_expressive_narrator"
MODEL = "speech-2.8-hd"

ESSAYS_DIR = Path(__file__).parent / "essays"
OUTPUT_DIR = Path(__file__).parent.parent / "hfn-site-output"
AUDIO_DIR = OUTPUT_DIR / "audio"

# Polling configuration for async tasks
POLL_INTERVAL_SECONDS = 5
MAX_POLL_ATTEMPTS = 360  # 30 minutes max wait

HEADERS = {
    "Authorization": f"Bearer {MINIMAX_API_KEY}",
    "Content-Type": "application/json",
}


# ─── Text Extraction ─────────────────────────────────────────────────────────

def fix_encoding(text: str) -> str:
    """Fix common encoding artifacts from Word/web copy-paste."""
    replacements = {
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '--', '\u2026': '...',
        '\xa0': ' ', '\u00a3': 'GBP ', '\u20ac': 'EUR ',
        'â€™': "'", 'â€˜': "'", 'â€œ': '"', 'â€\x9d': '"',
        'â€"': '--', 'â€"': '-', 'â€¦': '...', 'Â ': ' ', 'Â': '',
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text


def extract_narration_text(filepath: Path) -> tuple[str, str, str]:
    """
    Extract clean narration text from a markdown essay.
    Returns (title, slug, narration_text).
    
    Strips YAML frontmatter, markdown formatting, and produces
    natural spoken-word text suitable for TTS.
    """
    content = filepath.read_text(encoding="utf-8", errors="replace")

    # Parse YAML frontmatter
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

    # Remove the first H1 heading (it's the title, we'll prepend it)
    body = re.sub(r"^\s*#\s+[^\n]+\n", "", body, count=1)

    # Remove trailing "THEN:" sections
    body = re.sub(r"\n---\s*\n\s*##\s*THEN:.*$", "", body, flags=re.DOTALL)

    # Convert markdown to plain narration text
    text = body

    # Remove markdown headings but keep text (add pause marker)
    text = re.sub(r"^#{1,6}\s+(.+)$", r"\n\1.\n", text, flags=re.MULTILINE)

    # Remove markdown formatting
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # bold
    text = re.sub(r"\*(.+?)\*", r"\1", text)  # italic
    text = re.sub(r"_(.+?)_", r"\1", text)  # italic alt
    text = re.sub(r"`(.+?)`", r"\1", text)  # code
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)  # links

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove image references
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    # Prepend title as spoken intro
    narration = f"{title}.\n\nBy Tristan Fischer.\n\n{text}"

    return title, slug, narration


# ─── MiniMax Async TTS API ───────────────────────────────────────────────────

def create_tts_task(text: str, voice_id: str = VOICE_ID) -> str:
    """
    Create an async TTS task on MiniMax.
    Returns the task_id for polling.
    """
    url = f"{API_BASE}/v1/t2a_async_v2"

    payload = {
        "model": MODEL,
        "text": text,
        "language_boost": "English",
        "voice_setting": {
            "voice_id": voice_id,
            "speed": 0.95,  # Slightly slower for analytical content
            "vol": 1,
            "pitch": 0,
            "emotion": "calm",
        },
        "audio_setting": {
            "audio_sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1,  # Mono is fine for narration
        },
    }

    response = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    if data.get("base_resp", {}).get("status_code", -1) != 0:
        raise RuntimeError(
            f"MiniMax task creation failed: {data.get('base_resp', {}).get('status_msg', 'Unknown error')}"
        )

    task_id = data.get("task_id")
    if not task_id:
        raise RuntimeError(f"No task_id in response: {json.dumps(data, indent=2)}")

    return task_id


def poll_task(task_id: str) -> str:
    """
    Poll an async TTS task until completion.
    Returns the file_id of the generated audio.
    """
    url = f"{API_BASE}/v1/query/t2a_async_query_v2"

    for attempt in range(MAX_POLL_ATTEMPTS):
        response = requests.get(
            url,
            headers=HEADERS,
            params={"task_id": task_id},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("base_resp", {}).get("status_code", -1) != 0:
            raise RuntimeError(
                f"MiniMax poll error: {data.get('base_resp', {}).get('status_msg', 'Unknown')}"
            )

        status = data.get("status")

        if status == "Success":
            file_id = data.get("file_id")
            extra = data.get("extra_info", {})
            duration_ms = extra.get("audio_length", 0)
            duration_min = round(duration_ms / 60000, 1)
            size_bytes = extra.get("audio_size", 0)
            size_mb = round(size_bytes / (1024 * 1024), 2)
            print(f"    Done: {duration_min} min, {size_mb} MB")
            return file_id

        if status == "Failed":
            raise RuntimeError(f"MiniMax task failed: {json.dumps(data, indent=2)}")

        # Still processing
        if attempt % 6 == 0:  # Log every 30 seconds
            print(f"    Generating... ({attempt * POLL_INTERVAL_SECONDS}s elapsed)")

        time.sleep(POLL_INTERVAL_SECONDS)

    raise TimeoutError(f"Task {task_id} did not complete within {MAX_POLL_ATTEMPTS * POLL_INTERVAL_SECONDS}s")


def download_audio(file_id: str, output_path: Path) -> None:
    """Download the generated audio file from MiniMax."""
    url = f"{API_BASE}/v1/files/retrieve_content"

    response = requests.get(
        url,
        headers=HEADERS,
        params={"file_id": file_id},
        timeout=120,
    )
    response.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    size_mb = round(len(response.content) / (1024 * 1024), 2)
    print(f"    Saved: {output_path.name} ({size_mb} MB)")


# ─── Main ────────────────────────────────────────────────────────────────────

def generate_article_audio(filepath: Path, force: bool = False) -> bool:
    """Generate audio for a single article. Returns True if generated."""
    title, slug, narration = extract_narration_text(filepath)
    output_path = AUDIO_DIR / f"{slug}.mp3"

    if output_path.exists() and not force:
        print(f"  [skip] {slug} (already exists)")
        return False

    char_count = len(narration)
    word_count = len(narration.split())
    est_minutes = round(word_count / 189, 1)  # 189 WPM for this voice

    print(f"  [{slug}]")
    print(f"    {word_count:,} words, {char_count:,} chars, ~{est_minutes} min estimated")

    if char_count > 1_000_000:
        print(f"    [ERROR] Text too long ({char_count:,} chars). Max is 1M. Skipping.")
        return False

    # Create async task
    task_id = create_tts_task(narration)
    print(f"    Task created: {task_id}")

    # Poll until done
    file_id = poll_task(task_id)

    # Download
    download_audio(file_id, output_path)
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate audio narrations for HFN essays")
    parser.add_argument("--article", type=str, help="Generate for a specific article slug")
    parser.add_argument("--force", action="store_true", help="Regenerate even if audio exists")
    parser.add_argument("--list-voices", action="store_true", help="List available English voices")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without calling API")
    args = parser.parse_args()

    if args.list_voices:
        print("Recommended English voices for narration:")
        print("  English_expressive_narrator  - British male, expressive narrator (SELECTED)")
        print("  English_Trustworth_Man       - Trustworthy male")
        print("  English_WiseScholar          - Wise scholar")
        print("  English_Deep-VoicedGentleman - Deep-voiced gentleman")
        print("  English_magnetic_voiced_man  - Magnetic-voiced male")
        print("  English_CaptivatingStoryteller - Captivating storyteller")
        print("  English_Steadymentor         - Reliable male mentor")
        print("  English_PatientMan           - Patient male")
        return

    if not MINIMAX_API_KEY:
        print("ERROR: MINIMAX_API_KEY not set. Export it or add to .env")
        sys.exit(1)

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # Collect essays
    essays = sorted(ESSAYS_DIR.glob("*.md"))
    if not essays:
        print(f"No essays found in {ESSAYS_DIR}")
        sys.exit(1)

    if args.article:
        # Filter to specific article
        matches = [f for f in essays if args.article in f.stem]
        if not matches:
            print(f"No essay matching '{args.article}' found")
            print(f"Available: {', '.join(f.stem[:40] for f in essays[:10])}...")
            sys.exit(1)
        essays = matches

    print(f"Audio generation: {len(essays)} essays")
    print(f"Voice: {VOICE_ID} | Model: {MODEL}")
    print(f"Output: {AUDIO_DIR}")
    print()

    if args.dry_run:
        total_chars = 0
        total_words = 0
        for filepath in essays:
            title, slug, narration = extract_narration_text(filepath)
            chars = len(narration)
            words = len(narration.split())
            total_chars += chars
            total_words += words
            exists = (AUDIO_DIR / f"{slug}.mp3").exists()
            status = "[exists]" if exists else "[pending]"
            print(f"  {status} {slug}: {words:,} words, {chars:,} chars")
        est_total_min = round(total_words / 189, 1)
        print(f"\nTotal: {total_words:,} words, {total_chars:,} chars")
        print(f"Estimated total audio: ~{est_total_min} min (~{round(est_total_min/60, 1)} hours)")
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
