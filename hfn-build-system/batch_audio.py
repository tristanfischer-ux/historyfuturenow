#!/usr/bin/env python3
"""
Batch audio renderer — generates audio sequentially (to respect rate limits)
but deploys in batches of N as files complete.

The Gemini TTS free tier is very rate-limited, so true parallel TTS calls
cause thundering-herd failures. Instead, we process sequentially but deploy
incrementally so the site updates in chunks rather than all-at-once.

Usage:
    python3 batch_audio.py                    # All articles, deploy every 5
    python3 batch_audio.py --deploy-every 10  # Deploy every 10 completions
    python3 batch_audio.py --no-deploy        # Skip deploys, just generate
    python3 batch_audio.py --dry-run          # Preview only
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
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


def deploy(batch_num: int, count: int) -> bool:
    """Run deploy script."""
    msg = f"feat: regenerate debate audio batch {batch_num} ({count} files)"

    print(f"\n  {'='*50}")
    print(f"  DEPLOYING batch {batch_num} ({count} audio files)...")
    print(f"  {'='*50}")

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
        print(f"  ⚠ Deploy exit={result.returncode}")
        if "Pushed" in stdout:
            print(f"  ✓ At least pushed to git\n")
            return True
        print(f"    tail: {stdout[-200:]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Sequential audio with batch deploys")
    parser.add_argument("--deploy-every", type=int, default=5, help="Deploy after N completions")
    parser.add_argument("--no-deploy", action="store_true", help="Skip deploys")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    args = parser.parse_args()

    if not GEMINI_API_KEYS and not args.dry_run:
        print("ERROR: GEMINI_API_KEY not set.")
        sys.exit(1)

    DISCUSSION_DIR.mkdir(parents=True, exist_ok=True)

    all_slugs = get_all_slugs()
    total = len(all_slugs)

    print(f"Total scripts: {total}")
    print(f"Deploy every: {args.deploy_every} completions")
    print(f"API keys: {len(GEMINI_API_KEYS)}")
    print(f"Deploy: {'no' if args.no_deploy else 'yes'}")
    print()

    done = 0
    failed = 0
    failed_slugs = []
    batch_num = 0
    since_last_deploy = 0

    for i, slug in enumerate(all_slugs, 1):
        short = slug[:60]
        print(f"[{i}/{total}] {short}")

        if args.dry_run:
            script_path = SCRIPTS_DIR / f"{slug}.json"
            script = json.loads(script_path.read_text(encoding='utf-8'))
            words = sum(len(t['text'].split()) for t in script)
            print(f"  [dry-run] {len(script)} turns, {words} words")
            done += 1
            since_last_deploy += 1
            continue

        script_path = SCRIPTS_DIR / f"{slug}.json"
        output_path = DISCUSSION_DIR / f"{slug}.mp3"

        try:
            script = json.loads(script_path.read_text(encoding='utf-8'))
            render_script_to_audio(script, output_path)
            size_mb = round(output_path.stat().st_size / (1024 * 1024), 2)
            print(f"  ✓ {size_mb} MB")
            done += 1
            since_last_deploy += 1
        except Exception as e:
            print(f"  ✗ FAILED: {str(e)[:200]}")
            failed += 1
            failed_slugs.append(slug)
            since_last_deploy += 1

        # Deploy every N completions
        if since_last_deploy >= args.deploy_every and not args.no_deploy:
            batch_num += 1
            deploy(batch_num, since_last_deploy)
            since_last_deploy = 0

        # Rate limit gap between articles
        if i < total and not args.dry_run:
            time.sleep(2)

    # Final deploy for remaining
    if since_last_deploy > 0 and not args.no_deploy and not args.dry_run:
        batch_num += 1
        deploy(batch_num, since_last_deploy)

    print(f"\n{'='*60}")
    print(f"COMPLETE: {done} generated, {failed} failed")
    if failed_slugs:
        print(f"\nFailed ({len(failed_slugs)}):")
        for s in failed_slugs:
            print(f"  - {s}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
