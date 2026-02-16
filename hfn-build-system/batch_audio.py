#!/usr/bin/env python3
"""
Batch audio renderer — processes discussion scripts in parallel batches of N,
deploying after each batch completes.

Usage:
    python3 batch_audio.py                    # All 61, batches of 5, deploy after each
    python3 batch_audio.py --batch-size 3     # Batches of 3
    python3 batch_audio.py --dry-run          # Preview without API calls
    python3 batch_audio.py --no-deploy        # Skip deploy between batches
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

sys.path.insert(0, str(Path(__file__).parent))
from generate_discussions import (
    SCRIPTS_DIR, DISCUSSION_DIR, GEMINI_API_KEYS,
    render_script_to_audio,
)

PROJECT_ROOT = Path(__file__).parent.parent
DEPLOY_SCRIPT = PROJECT_ROOT / "scripts" / "deploy.sh"


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
        render_script_to_audio(script, output_path)
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
        timeout=120,
    )

    if result.returncode == 0 or "Site is live" in result.stdout:
        print(f"  ✓ Batch {batch_num} deployed\n")
        return True
    else:
        # The deploy script exits 1 due to ANTHROPIC_API_KEY but still deploys
        if "Vercel deploy complete" in result.stdout or "Pushed" in result.stdout:
            print(f"  ✓ Batch {batch_num} deployed (with non-critical warning)\n")
            return True
        print(f"  ✗ Deploy failed: {result.stderr[:300]}")
        print(f"    stdout: {result.stdout[-300:]}")
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
    print(f"Deploy between batches: {'no' if args.no_deploy else 'yes'}")
    print()

    # Split into batches
    batches = []
    for i in range(0, len(all_slugs), args.batch_size):
        batches.append(all_slugs[i:i + args.batch_size])

    print(f"Batches: {len(batches)}")
    print()

    total_done = 0
    total_failed = 0

    for batch_num, batch in enumerate(batches, 1):
        print(f"{'='*60}")
        print(f"BATCH {batch_num}/{len(batches)} — {len(batch)} articles")
        print(f"{'='*60}")

        for slug in batch:
            short = slug[:60]
            print(f"  • {short}")
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
                short = slug[:50]
                if success:
                    print(f"  ✓ {short} — {message}")
                    batch_successes.append(slug)
                else:
                    print(f"  ✗ {short} — FAILED: {message}")
                    batch_failures.append(slug)

        total_done += len(batch_successes)
        total_failed += len(batch_failures)

        print(f"\n  Batch {batch_num}: {len(batch_successes)} done, {len(batch_failures)} failed")

        # Deploy after each batch
        if batch_successes and not args.no_deploy:
            deploy(batch_num, batch_successes)

        # Brief pause between batches to avoid rate limit storms
        if batch_num < len(batches):
            print(f"  Pausing 5s before next batch...\n")
            time.sleep(5)

    print(f"\n{'='*60}")
    print(f"COMPLETE: {total_done} generated, {total_failed} failed")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
