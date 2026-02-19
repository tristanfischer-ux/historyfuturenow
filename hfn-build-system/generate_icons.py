"""Generate PWA icons from the HFN brand mark (favicon.svg design)."""

from PIL import Image, ImageDraw, ImageFont
import struct
import io
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "hfn-site-output")
ICONS_DIR = os.path.join(OUTPUT_DIR, "icons")

BG_COLOR = "#1a1815"
H_COLOR = "#ffffff"
N_COLOR = "#c43425"


def render_icon(size: int, maskable: bool = False) -> Image.Image:
    """Render the HN brand mark at the given pixel size.

    maskable: if True, fills the entire canvas with the background colour and
    places the logo within the inner 80% safe zone (per the maskable icon spec).
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if maskable:
        draw.rectangle([0, 0, size - 1, size - 1], fill=BG_COLOR)
        safe_inset = int(size * 0.10)
        inner = size - 2 * safe_inset
        offset = safe_inset
    else:
        inner = size
        offset = 0
        corner = int(inner * 6 / 32)
        draw.rounded_rectangle(
            [0, 0, size - 1, size - 1],
            radius=corner,
            fill=BG_COLOR,
        )

    font_size = int(inner * 20 / 32)
    font_bold = ImageFont.truetype("Georgia Bold", font_size)
    font_italic = ImageFont.truetype("Georgia Italic", font_size)

    h_x = offset + int(inner * 4 / 32)
    n_x = offset + int(inner * 17 / 32)
    baseline_y = offset + int(inner * 23 / 32)

    h_bbox = font_bold.getbbox("H")
    n_bbox = font_italic.getbbox("N")
    h_y = baseline_y - h_bbox[3]
    n_y = baseline_y - n_bbox[3]

    draw.text((h_x, h_y), "H", fill=H_COLOR, font=font_bold)
    draw.text((n_x, n_y), "N", fill=N_COLOR, font=font_italic)

    return img


def make_ico(sizes: list[int], path: str) -> None:
    """Create a multi-resolution .ico file."""
    largest = max(sizes)
    base = render_icon(largest)
    resized = [base.resize((s, s), Image.LANCZOS) for s in sorted(sizes)]
    resized[-1].save(path, format="ICO", append_images=resized[:-1])


def main() -> None:
    os.makedirs(ICONS_DIR, exist_ok=True)

    # Standard icons
    for size in (192, 512):
        img = render_icon(size)
        img.save(os.path.join(ICONS_DIR, f"icon-{size}.png"))
        print(f"  icon-{size}.png")

    # Maskable icons (full-bleed background, logo in 80% safe zone)
    for size in (192, 512):
        img = render_icon(size, maskable=True)
        img.save(os.path.join(ICONS_DIR, f"icon-maskable-{size}.png"))
        print(f"  icon-maskable-{size}.png")

    # Apple touch icon
    img = render_icon(180)
    img.save(os.path.join(OUTPUT_DIR, "apple-touch-icon.png"))
    print("  apple-touch-icon.png")

    # favicon.ico (multi-size)
    make_ico([16, 32, 48], os.path.join(OUTPUT_DIR, "favicon.ico"))
    print("  favicon.ico")

    print("Done.")


if __name__ == "__main__":
    main()
