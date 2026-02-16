#!/usr/bin/env python3
"""
Batch audio renderer — processes discussion scripts in parallel batches of N,
deploying after each batch completes.

Uses a shared rate limiter to prevent thundering-herd rate limit issues
when multiple threads hit the Gemini TTS API simultaneously.

Usage:
    python3 batch_audio.py                    # All 61, batches of 5, deploy after each
    python3 batch_audio.py --batch-size 3     # Batches of 3
    python3 batch_audio.py --dry-run          # Preview without API calls
    python3 batch_audio.py --no-deploy        # Skip deploy between batches
"""

import os
import io
import sys
import json
import time
import base64
import subprocess
import threading
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

sys.path.insert(0, str(Path(__file__).parent))
from generate_discussions import (
    SCRIPTS_DIR, DISCUSSION_DIR, GEMINI_API_KEYS,
    GEMINI_TTS_MODEL, VOICE_SPEAKER_A, VOICE_SPEAKER_B,
    TTS_MAX_CHARS,
    format_script_for_tts, chunk_script_for_tts,
    pcm_to_wav, wav_to_mp3,
    _next_gemini_key,
)

PROJECT_ROOT = Path(__file__).parent.parent
DEPLOY_SCRIPT = PROJECT_ROOT / "scripts" / "deploy.sh"

# Shared rate limiter: only 1 TTS request at a time, with enforced gap
_tts_lock = threading.Lock()
_last_tts_time = 0.0
TTS_MIN_GAP_SECONDS = 4  # minimum seconds between TTS API calls


def rate_limited_tts_call(script_chunk: list[dict], max_retries: int = 8) -> bytes:
    """Generate TTS audio with shared rate limiting across threads."""
    global _last_tts_time

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
        # Acquire lock and enforce minimum gap between API calls
        with _tts_lock:
            now = time.time()
            elapsed = now - _last_tts_time
            if elapsed < TTS_MIN_GAP_SECONDS:
                wait = TTS_MIN_GAP_SECONDS - elapsed
                time.sleep(wait)
            _last_tts_time = time.time()

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
            if response.status_code == 500 and attempt < max_retries - 1:
                wait = 15 + (attempt * 15)
                print(f"      TTS 500 error (attempt {attempt+1}/{max_retries}), retrying in {wait}s...")
                time.sleep(wait)
                last_error = f"Server error 500"
                continue
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

    audio_bytes = base64.b64decode(inline_data.get("data", ""))
    return audio_bytes


def render_script_rate_limited(script: list[dict], output_path: Path) -> None:
    """Render a discussion script to MP3 using rate-limited TTS."""
    chunks = chunk_script_for_tts(script)
    total_chars = sum(len(t['text']) for t in script)
    print(f"    Rendering {len(chunks)} chunk(s) ({total_chars:,} chars)...")

    all_pcm = bytearray()
    for i, chunk in enumerate(chunks):
        chars = sum(len(t['text']) for t in chunk)
        print(f"      [{i+1}/{len(chunks)}] {len(chunk)} turns, {chars:,} chars")
        pcm_data = rate_limited_tts_call(chunk)
        all_pcm.extend(pcm_data)

    wav_data = pcm_to_wav(bytes(all_pcm))
    mp3_data = wav_to_mp3(wav_data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(mp3_data)

    total_mb = round(len(mp3_data) / (1024 * 1024), 2)
    duration_est = round(len(all_pcm) / (24000 * 2) / 60, 1)
    print(f"    ✓ {output_path.name} ({total_mb} MB, ~{duration_est} min)")


def get_all_slugs() -> list[str]:
    """Get all script slugs sorted alphabetically."""
    if not SCRIPTS_DIR.exists():
        return []
    return sorted(p.stem for p in SCRIPTS_DIR.glob("*.json"))


def render_one(slug: str) -> tuple[str, bool, str]:
    """Render a single script to audio. Returns (slug, success, message)."""
    script_path = SCRIPTS_DIR / f"{slug}.json"
    output_path = DISCUSSION_DIR / f"{slug}.mp3"

    try:
        script = json.loads(script_path.read_text(encoding='utf-8'))
        render_script_rate_limited(script, output_path)
        size_mb = round(output_path.stat().st_size / (1024 * 1024), 2)
        return (slug, True, f"{size_mb} MB")
    except Exception as e:
        return (slug, False, str(e)[:200])


def deploy(batch_num: int, completed_slugs: list[str]) -> bool:
    """Run deploy script after a batch completes."""
    count = len(completed_slugs)
    msg = f"feat: regenerate debate audio batch {batch_num} ({count} files)"

    print(f"\n  {'='*50}")
    print(f"  DEPLOYING batch {batch_num} ({count} audio files)...")
    print(f"  {'='*50}\n")

    result = subprocess.run(
        [str(DEPLOY_SCRIPT), msg],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=180,
    )

    stdout = result.stdout
    if "Site is live" in stdout or "Vercel deploy complete" in stdout or "Pushed" in stdout:
        print(f"  ✓ Batch {batch_num} deployed\n")
        return True
    else:
        print(f"  ✗ Deploy may have issues: exit={result.returncode}")
        if result.stderr:
            print(f"    stderr: {result.stderr[:200]}")
        print(f"    stdout (tail): {stdout[-300:]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Batch audio renderer with deploy")
    parser.add_argument("--batch-size", type=int, default=5, help="Parallel batch size")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--no-deploy", action="store_true", help="Skip deploy between batches")
    args = parser.parse_args()

    if not GEMINI_API_KEYS:
        print("ERROR: GEMINI_API_KEY not set.")
        sys.exit(1)

    DISCUSSION_DIR.mkdir(parents=True, exist_ok=True)

    all_slugs = get_all_slugs()
    print(f"Total scripts: {len(all_slugs)}")
    print(f"Batch size: {args.batch_size} parallel")
    print(f"API keys: {len(GEMINI_API_KEYS)}")
    print(f"TTS gap: {TTS_MIN_GAP_SECONDS}s between API calls (shared across threads)")
    print(f"Deploy between batches: {'no' if args.no_deploy else 'yes'}")
    print()

    batches = []
    for i in range(0, len(all_slugs), args.batch_size):
        batches.append(all_slugs[i:i + args.batch_size])

    print(f"Batches: {len(batches)} ({len(all_slugs)} total)")
    print()

    total_done = 0
    total_failed = 0
    failed_slugs = []

    for batch_num, batch in enumerate(batches, 1):
        print(f"{'='*60}")
        print(f"BATCH {batch_num}/{len(batches)} — {len(batch)} articles")
        print(f"{'='*60}")

        for slug in batch:
            print(f"  • {slug[:65]}")
        print()

        if args.dry_run:
            for slug in batch:
                script_path = SCRIPTS_DIR / f"{slug}.json"
                script = json.loads(script_path.read_text(encoding='utf-8'))
                words = sum(len(t['text'].split()) for t in script)
                print(f"  [dry-run] {slug[:50]} — {len(script)} turns, {words} words")
            total_done += len(batch)
            continue

        batch_successes = []
        batch_failures = []

        with ThreadPoolExecutor(max_workers=args.batch_size) as executor:
            futures = {executor.submit(render_one, slug): slug for slug in batch}

            for future in as_completed(futures):
                slug, success, message = future.result()
                short = slug[:55]
                if success:
                    print(f"  ✓ {short} — {message}")
                    batch_successes.append(slug)
                else:
                    print(f"  ✗ {short} — FAILED: {message}")
                    batch_failures.append(slug)

        total_done += len(batch_successes)
        total_failed += len(batch_failures)
        failed_slugs.extend(batch_failures)

        print(f"\n  Batch {batch_num} result: {len(batch_successes)} done, {len(batch_failures)} failed")

        if batch_successes and not args.no_deploy:
            deploy(batch_num, batch_successes)

        if batch_num < len(batches):
            print(f"  Pausing 5s before next batch...\n")
            time.sleep(5)

    # Summary
    print(f"\n{'='*60}")
    print(f"COMPLETE: {total_done} generated, {total_failed} failed")
    if failed_slugs:
        print(f"\nFailed articles ({len(failed_slugs)}):")
        for s in failed_slugs:
            print(f"  - {s}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
