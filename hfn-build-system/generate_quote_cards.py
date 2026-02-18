#!/usr/bin/env python3
"""Generate branded quote card PNGs from social content JSON files."""

import argparse
import json
import os
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont

CANVAS_W = 1080
CANVAS_H = 1080
PADDING = 100
ACCENT_BAR_H = 6
BOTTOM_STRIP_H = 60
SEPARATOR_Y = CANVAS_H - PADDING - BOTTOM_STRIP_H

BG_COLOR = "#fdfcfb"
ACCENT_RED = "#c43425"
TEXT_COLOR = "#1a1815"
MUTED_GREY = "#8a8479"
SEPARATOR_COLOR = "#e8e4e0"

SERIF_PATHS = [
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "C:\\Windows\\Fonts\\georgia.ttf",
]

MONO_PATHS = [
    "/System/Library/Fonts/Supplemental/Courier New.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "C:\\Windows\\Fonts\\cour.ttf",
]

SOCIAL_DIR = os.path.join(os.path.dirname(__file__), "social_content")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "hfn-site-output", "images", "social")


def load_font(paths, size):
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap_quote(draw, text, font, max_width):
    """Find optimal character-wrap width so every line fits within max_width."""
    for chars_per_line in range(60, 10, -1):
        lines = textwrap.fill(text, width=chars_per_line).split("\n")
        if all(draw.textlength(line, font=font) <= max_width for line in lines):
            return lines
    return textwrap.fill(text, width=15).split("\n")


def generate_card(slug, quote_text):
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, CANVAS_W, ACCENT_BAR_H], fill=ACCENT_RED)

    available_w = CANVAS_W - 2 * PADDING
    available_h = SEPARATOR_Y - ACCENT_BAR_H - PADDING - 40  # space for quote marks

    # Auto-scale font size
    for font_size in range(48, 20, -2):
        serif_font = load_font(SERIF_PATHS, font_size)
        lines = wrap_quote(draw, quote_text, serif_font, available_w)
        line_h = font_size * 1.45
        total_text_h = len(lines) * line_h
        if total_text_h <= available_h:
            break

    quote_mark_font = load_font(SERIF_PATHS, font_size + 32)
    open_q = "\u201c"
    close_q = "\u201d"

    open_q_w = draw.textlength(open_q, font=quote_mark_font)

    block_top = ACCENT_BAR_H + PADDING + (available_h - total_text_h) / 2
    quote_mark_offset = (font_size + 32) * 0.25

    draw.text(
        (PADDING - open_q_w - 4, block_top - quote_mark_offset),
        open_q,
        fill=ACCENT_RED,
        font=quote_mark_font,
    )

    y = block_top
    last_line_end_x = CANVAS_W / 2
    for line in lines:
        line_w = draw.textlength(line, font=serif_font)
        x = (CANVAS_W - line_w) / 2
        draw.text((x, y), line, fill=TEXT_COLOR, font=serif_font)
        last_line_end_x = x + line_w
        y += line_h

    draw.text(
        (last_line_end_x + 4, y - line_h - quote_mark_offset),
        close_q,
        fill=ACCENT_RED,
        font=quote_mark_font,
    )

    draw.line(
        [(PADDING, SEPARATOR_Y), (CANVAS_W - PADDING, SEPARATOR_Y)],
        fill=SEPARATOR_COLOR,
        width=1,
    )

    url_font = load_font(MONO_PATHS, 18)
    logo_font = load_font(SERIF_PATHS, 20)

    strip_y = SEPARATOR_Y + (BOTTOM_STRIP_H - 18) / 2
    draw.text((PADDING, strip_y), "historyfuturenow.com", fill=MUTED_GREY, font=url_font)

    logo_text = "HFN"
    logo_w = draw.textlength(logo_text, font=logo_font)
    draw.text((CANVAS_W - PADDING - logo_w, strip_y), logo_text, fill=ACCENT_RED, font=logo_font)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{slug}-quote.png")
    img.save(out_path, "PNG")
    print(f"  ✓ {slug}-quote.png")
    return out_path


def load_social_json(slug):
    path = os.path.join(SOCIAL_DIR, f"{slug}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def extract_quote(data):
    try:
        text = data["posts"]["quote_card"]["text"]
        return text.strip() if text else None
    except (KeyError, TypeError):
        return None


def main():
    parser = argparse.ArgumentParser(description="Generate HFN quote card images")
    parser.add_argument("--slug", help="Generate for a single article slug")
    args = parser.parse_args()

    if args.slug:
        data = load_social_json(args.slug)
        if not data:
            print(f"No social content found for slug: {args.slug}")
            sys.exit(1)
        quote = extract_quote(data)
        if not quote:
            print(f"No quote_card text for: {args.slug}")
            sys.exit(1)
        generate_card(args.slug, quote)
        return

    json_files = sorted(f for f in os.listdir(SOCIAL_DIR) if f.endswith(".json"))
    if not json_files:
        print("No social content JSON files found.")
        sys.exit(1)

    generated = 0
    skipped = 0
    for filename in json_files:
        slug = filename.replace(".json", "")
        with open(os.path.join(SOCIAL_DIR, filename), "r") as f:
            data = json.load(f)
        quote = extract_quote(data)
        if not quote:
            skipped += 1
            continue
        generate_card(slug, quote)
        generated += 1

    print(f"\nDone. Generated {generated} quote cards, skipped {skipped}.")


if __name__ == "__main__":
    main()
