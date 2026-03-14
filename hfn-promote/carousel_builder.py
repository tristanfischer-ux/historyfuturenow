"""HFN Promote — LinkedIn PDF Carousel Builder.

Pure-function PDF generator. Takes structured slide data in, outputs a branded
4:5 portrait PDF optimised for LinkedIn document posts.
"""
from pathlib import Path
from PIL import Image
from fpdf import FPDF

FONTS_DIR = Path(__file__).resolve().parent / "assets" / "fonts"

# ── Brand colours (from hfn-site-output/css/style.css) ──
ACCENT = (196, 52, 37)      # #c43425
TEXT = (26, 24, 21)          # #1a1815
BG = (248, 247, 246)         # #f8f7f6
DIM = (138, 132, 121)        # #8a8479
CARD = (250, 248, 245)       # #faf8f5
WHITE = (255, 255, 255)
DARK = (26, 24, 21)          # #1a1815

# 4:5 portrait in mm (1080×1350 px at ~170 dpi)
W_MM = 162
H_MM = 202.5
MARGIN = 12  # mm
CONTENT_W = W_MM - 2 * MARGIN  # usable width

# Layout zones
DOTS_Y = H_MM - 10
WORDMARK_Y = H_MM - 12
BOTTOM_RESERVED = 18  # mm reserved for wordmark + dots


def _init_pdf():
    """Create FPDF instance with custom fonts and page size."""
    pdf = FPDF(unit="mm", format=(W_MM, H_MM))
    pdf.set_auto_page_break(auto=False)
    for name, fname in [("Playfair", "PlayfairDisplay-Bold.ttf"),
                        ("SourceSans", "SourceSans3-Regular.ttf")]:
        fpath = FONTS_DIR / fname
        if not fpath.exists():
            raise FileNotFoundError(
                f"Missing font: {fpath}. Download from Google Fonts into assets/fonts/")
        pdf.add_font(name, "", str(fpath))
    return pdf


def _set_color(pdf, rgb):
    pdf.set_text_color(*rgb)


def _draw_wordmark(pdf, y, color=WHITE):
    """Draw 'HISTORY FUTURE NOW' wordmark."""
    _set_color(pdf, color)
    pdf.set_font("SourceSans", size=7)
    pdf.set_xy(MARGIN, y)
    pdf.cell(0, 5, "HISTORY FUTURE NOW", align="L")


def _draw_dots(pdf, current, total):
    """Draw slide position dots at bottom centre."""
    dot_r = 1.5 if total <= 12 else 1.0
    gap = 5 if total <= 12 else 3.5
    total_w = total * gap
    start_x = (W_MM - total_w) / 2
    for i in range(total):
        cx = start_x + i * gap + dot_r
        if i == current:
            pdf.set_fill_color(*ACCENT)
        else:
            pdf.set_fill_color(*DIM)
        pdf.ellipse(cx - dot_r, DOTS_Y - dot_r, dot_r * 2, dot_r * 2, style="F")



def _title_slide(pdf, title, section, hero_path, total_slides):
    """Slide 1: hero image top 60%, solid dark block bottom 40% with title."""
    pdf.add_page()

    hero_zone_h = H_MM * 0.58  # top portion for hero
    dark_zone_y = hero_zone_h
    dark_zone_h = H_MM - hero_zone_h

    # Hero image — crop to fill top zone
    if hero_path and Path(hero_path).exists():
        try:
            pdf.image(str(hero_path), x=0, y=0, w=W_MM, h=hero_zone_h)
        except Exception:
            pdf.set_fill_color(*BG)
            pdf.rect(0, 0, W_MM, hero_zone_h, style="F")
    else:
        pdf.set_fill_color(*BG)
        pdf.rect(0, 0, W_MM, hero_zone_h, style="F")

    # Solid dark block — bottom 42%
    pdf.set_fill_color(*DARK)
    pdf.rect(0, dark_zone_y, W_MM, dark_zone_h, style="F")

    # Section label in accent
    text_start_y = dark_zone_y + 8
    if section:
        _set_color(pdf, ACCENT)
        pdf.set_font("SourceSans", size=9)
        pdf.set_xy(MARGIN, text_start_y)
        pdf.cell(CONTENT_W, 5, section.upper(), align="L")
        text_start_y = pdf.get_y() + 7

    # Title in white
    _set_color(pdf, WHITE)
    pdf.set_font("Playfair", size=22)
    pdf.set_xy(MARGIN, text_start_y)
    pdf.multi_cell(CONTENT_W, 10, title, align="L")

    # Wordmark + dots
    _draw_wordmark(pdf, WORDMARK_Y)
    _draw_dots(pdf, 0, total_slides)


def _insight_slide(pdf, heading, body, slide_num, total_slides):
    """Insight slide: vertically centred content on warm card bg."""
    pdf.add_page()

    # Background
    pdf.set_fill_color(*CARD)
    pdf.rect(0, 0, W_MM, H_MM, style="F")

    # Accent stripe at top
    pdf.set_fill_color(*ACCENT)
    pdf.rect(MARGIN, 0, CONTENT_W, 3, style="F")

    # Measure content height to vertically centre it
    heading_line_h = 11
    body_line_h = 7.5
    gap = 10

    # Estimate heights (chars per line * line height)
    pdf.set_font("Playfair", size=22)
    heading_lines = max(1, len(heading) / (CONTENT_W / 4.5))  # rough chars-per-line
    heading_h = heading_lines * heading_line_h

    pdf.set_font("SourceSans", size=14)
    body_lines = max(1, len(body) / (CONTENT_W / 3.2))
    body_h = body_lines * body_line_h

    total_content_h = heading_h + gap + body_h
    usable_h = H_MM - BOTTOM_RESERVED - 6  # 6mm top stripe area
    start_y = 6 + (usable_h - total_content_h) / 2
    start_y = max(20, start_y)  # don't overlap the stripe

    # Heading
    _set_color(pdf, TEXT)
    pdf.set_font("Playfair", size=22)
    pdf.set_xy(MARGIN, start_y)
    pdf.multi_cell(CONTENT_W, heading_line_h, heading, align="L")

    # Body — clamp to avoid overflow into bottom zone
    body_y = pdf.get_y() + gap
    max_body_y = H_MM - BOTTOM_RESERVED - 4
    if body_y < max_body_y:
        _set_color(pdf, TEXT)
        pdf.set_font("SourceSans", size=14)
        pdf.set_xy(MARGIN, body_y)
        pdf.multi_cell(CONTENT_W, body_line_h, body, align="L")
        # If text overflowed past bottom zone, it's already rendered but dots will overlay
        # This is acceptable — the prompt enforces max 40 words which fits in practice

    # Wordmark + dots
    _draw_wordmark(pdf, WORDMARK_Y, color=DIM)
    _draw_dots(pdf, slide_num, total_slides)


def _get_image_aspect(path):
    """Get width/height ratio of an image."""
    try:
        with Image.open(path) as img:
            w, h = img.size
            return w / h if h > 0 else 1.5
    except Exception:
        return 1.5  # fallback landscape ratio


def _chart_slide(pdf, chart_path, title, context, source, slide_num, total_slides):
    """Chart slide: adaptive chart image + title + context. No duplicate source."""
    pdf.add_page()

    # White background
    pdf.set_fill_color(*WHITE)
    pdf.rect(0, 0, W_MM, H_MM, style="F")

    # Chart title in accent colour
    _set_color(pdf, ACCENT)
    pdf.set_font("Playfair", size=14)
    pdf.set_xy(MARGIN, 12)
    pdf.multi_cell(CONTENT_W, 7, title, align="L")

    title_bottom = pdf.get_y() + 4

    # Adaptive chart sizing based on actual image aspect ratio
    available_h = H_MM - title_bottom - BOTTOM_RESERVED - 30  # 30mm for context below
    chart_w = CONTENT_W

    if chart_path and Path(chart_path).exists():
        aspect = _get_image_aspect(chart_path)
        # Size to fit: constrain by width, then check height
        chart_h_from_w = chart_w / aspect
        chart_h = min(chart_h_from_w, available_h)
        # If height-constrained, shrink width proportionally
        if chart_h < chart_h_from_w:
            chart_w = chart_h * aspect
        # Centre horizontally if narrower than content width
        chart_x = MARGIN + (CONTENT_W - chart_w) / 2
        try:
            pdf.image(str(chart_path), x=chart_x, y=title_bottom,
                      w=chart_w, h=chart_h)
        except Exception:
            chart_h = 0
    else:
        chart_h = 0

    # "So what" context below chart
    context_y = title_bottom + chart_h + 6
    if context_y < H_MM - BOTTOM_RESERVED - 20:
        _set_color(pdf, TEXT)
        pdf.set_font("SourceSans", size=11)
        pdf.set_xy(MARGIN, context_y)
        pdf.multi_cell(CONTENT_W, 6, context, align="L")

    # Source citation omitted — already visible inside the chart PNG itself

    _draw_wordmark(pdf, WORDMARK_Y, color=DIM)
    _draw_dots(pdf, slide_num, total_slides)


def _cta_slide(pdf, title, url, share_summary, total_slides):
    """Final CTA slide: dark bg, vertically centred read-the-article prompt."""
    pdf.add_page()

    # Dark background
    pdf.set_fill_color(*DARK)
    pdf.rect(0, 0, W_MM, H_MM, style="F")

    # Vertically centre the CTA content
    # Estimate total height: heading + title + summary + url ~ 80mm
    block_start = (H_MM - BOTTOM_RESERVED - 80) / 2
    block_start = max(25, block_start)

    # "Read the full article"
    _set_color(pdf, WHITE)
    pdf.set_font("Playfair", size=20)
    pdf.set_xy(MARGIN, block_start)
    pdf.multi_cell(CONTENT_W, 10, "Read the full article", align="C")

    # Article title
    _set_color(pdf, WHITE)
    pdf.set_font("Playfair", size=16)
    pdf.set_xy(MARGIN, pdf.get_y() + 10)
    pdf.multi_cell(CONTENT_W, 8, title, align="C")

    # Share summary teaser
    if share_summary:
        _set_color(pdf, DIM)
        pdf.set_font("SourceSans", size=11)
        pdf.set_xy(MARGIN, pdf.get_y() + 10)
        pdf.multi_cell(CONTENT_W, 6, share_summary, align="C")

    # URL in accent colour — show clean domain, not full path
    display_url = url.replace("https://", "").replace("http://", "").split("/")[0] if url else "historyfuturenow.com"
    _set_color(pdf, ACCENT)
    pdf.set_font("SourceSans", size=10)
    pdf.set_xy(MARGIN, pdf.get_y() + 12)
    pdf.cell(CONTENT_W, 6, display_url, align="C")

    # Wordmark
    _draw_wordmark(pdf, WORDMARK_Y)
    _draw_dots(pdf, total_slides - 1, total_slides)


def build_carousel(slug, slides_data, hero_path, output_dir=None):
    """Generate branded PDF carousel. Returns path to PDF.

    Args:
        slug: Article slug
        slides_data: dict with keys:
            title, section, share_summary, url,
            slides: list of {"type": "insight"|"chart", ...}
        hero_path: path to hero image
        output_dir: override output directory

    Returns: Path to generated PDF
    """
    from config import HFN_ARTICLE_IMAGES

    if output_dir is None:
        output_dir = HFN_ARTICLE_IMAGES / slug
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    title = slides_data["title"]
    section = slides_data.get("section", "")
    share_summary = slides_data.get("share_summary", "")
    url = slides_data.get("url", "")
    slides = slides_data["slides"]

    # Total slides = title + content slides + CTA
    total = 2 + len(slides)

    pdf = _init_pdf()

    # Title slide
    _title_slide(pdf, title, section, hero_path, total)

    # Content slides
    for i, slide in enumerate(slides):
        slide_num = i + 1  # 0 is title
        if slide["type"] == "insight":
            _insight_slide(pdf, slide["heading"], slide["body"],
                           slide_num, total)
        elif slide["type"] == "chart":
            _chart_slide(pdf, slide.get("chart_path"), slide["title"],
                         slide.get("context", ""), slide.get("source", ""),
                         slide_num, total)

    # CTA slide
    _cta_slide(pdf, title, url, share_summary, total)

    out_path = output_dir / "carousel.pdf"
    pdf.output(str(out_path))
    print(f"  ✓ Carousel PDF: {out_path} ({total} slides)")
    return out_path
