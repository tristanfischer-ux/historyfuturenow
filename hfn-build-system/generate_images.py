#!/usr/bin/env python3
"""
History Future Now — Editorial Illustration Generator

Reads image_prompts.json and calls Gemini 3.0 Pro image generation API
to produce editorial illustrations for all articles.

Usage:
    python3 generate_images.py                    # Generate all missing images
    python3 generate_images.py --slug <slug>      # Generate for one article
    python3 generate_images.py --size hero         # Generate only hero sizes
    python3 generate_images.py --dry-run           # Preview without generating

Requires GEMINI_API_KEY environment variable.
"""

import json
import os
import sys
import argparse
import time
from pathlib import Path

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

PROMPTS_PATH = Path(__file__).parent / "image_prompts.json"
OUTPUT_BASE = Path(__file__).parent.parent / "hfn-site-output"
MANIFEST_PATH = Path(__file__).parent / "image_manifest.json"

# Rate limiting: Gemini has per-minute quotas
REQUESTS_PER_MINUTE = 10
SLEEP_BETWEEN = 60.0 / REQUESTS_PER_MINUTE


def load_manifest():
    """Load existing manifest of generated images."""
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {}


def save_manifest(manifest):
    """Save manifest of generated images."""
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def generate_image_gemini(prompt, output_path, width, height):
    """Generate an image using Gemini 3.0 Pro and save it.

    @param prompt: The full image generation prompt.
    @param output_path: Path to save the generated image.
    @param width: Desired image width.
    @param height: Desired image height.
    @returns: True if successful, False otherwise.
    """
    if not HAS_GENAI:
        print("  ERROR: google-generativeai package not installed.")
        print("  Run: pip install google-generativeai")
        return False

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("  ERROR: GEMINI_API_KEY environment variable not set.")
        return False

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="image/webp",
            ),
        )

        # Save the image
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    output_path.write_bytes(part.inline_data.data)
                    return True

        print(f"  WARNING: No image data in response for {output_path.name}")
        return False

    except Exception as e:
        print(f"  ERROR generating image: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate editorial illustrations")
    parser.add_argument("--slug", help="Generate for a specific article slug only")
    parser.add_argument("--size", choices=["hero", "card", "thumb"],
                        help="Generate only one size")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview prompts without generating")
    parser.add_argument("--force", action="store_true",
                        help="Regenerate even if image already exists")
    args = parser.parse_args()

    if not PROMPTS_PATH.exists():
        print("ERROR: image_prompts.json not found. Run generate_image_prompts.py first.")
        sys.exit(1)

    prompts = json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
    manifest = load_manifest()

    # Filter prompts
    if args.slug:
        prompts = [p for p in prompts if p["slug"] == args.slug]
    if args.size:
        prompts = [p for p in prompts if p["size"] == args.size]

    if not prompts:
        print("No prompts match the given filters.")
        sys.exit(0)

    print(f"Processing {len(prompts)} prompts...")

    generated = 0
    skipped = 0
    failed = 0

    for i, prompt_data in enumerate(prompts):
        slug = prompt_data["slug"]
        size = prompt_data["size"]
        output_rel = prompt_data["output_path"]
        output_path = OUTPUT_BASE / output_rel

        manifest_key = f"{slug}/{size}"

        # Skip if already generated
        if not args.force and output_path.exists():
            skipped += 1
            continue

        if args.dry_run:
            print(f"\n[{i+1}/{len(prompts)}] {slug} ({size})")
            print(f"  Prompt: {prompt_data['prompt'][:120]}...")
            print(f"  Output: {output_path}")
            continue

        print(f"\n[{i+1}/{len(prompts)}] Generating {slug} ({size})...")

        success = generate_image_gemini(
            prompt_data["prompt"],
            output_path,
            prompt_data["width"],
            prompt_data["height"],
        )

        if success:
            generated += 1
            manifest[manifest_key] = {
                "path": output_rel,
                "width": prompt_data["width"],
                "height": prompt_data["height"],
                "generated": True,
            }
            save_manifest(manifest)
            print(f"  Saved: {output_path}")
        else:
            failed += 1

        # Rate limiting
        if i < len(prompts) - 1:
            time.sleep(SLEEP_BETWEEN)

    print(f"\nDone: {generated} generated, {skipped} skipped, {failed} failed")
    print(f"Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
