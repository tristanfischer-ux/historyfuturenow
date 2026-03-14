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

    # Section label in accent — larger so it's visible
    text_start_y = dark_zone_y + 10
    if section:
        _set_color(pdf, ACCENT)
        pdf.set_font("SourceSans", size=11)
        pdf.set_xy(MARGIN, text_start_y)
        pdf.cell(CONTENT_W, 5, section.upper(), align="L")
        text_start_y = pdf.get_y() + 8

    # Title in white — large enough to read on mobile
    _set_color(pdf, WHITE)
    pdf.set_font("Playfair", size=24)
    pdf.set_xy(MARGIN, text_start_y)
    pdf.multi_cell(CONTENT_W, 11, title, align="L")

    # Wordmark + dots
    _draw_wordmark(pdf, WORDMARK_Y)
    _draw_dots(pdf, 0, total_slides)


def _insight_slide(pdf, heading, body, slide_num, total_slides):
    """Insight slide: large text filling the slide. Content should dominate, not whitespace."""
    pdf.add_page()

    # Background
    pdf.set_fill_color(*CARD)
    pdf.rect(0, 0, W_MM, H_MM, style="F")

    # Accent bar left edge (vertical, like a pull-quote indicator — stops above wordmark)
    pdf.set_fill_color(*ACCENT)
    pdf.rect(MARGIN, 0, 3, WORDMARK_Y - 4, style="F")

    # Slide number in accent at top-right
    _set_color(pdf, DIM)
    pdf.set_font("SourceSans", size=9)
    pdf.set_xy(MARGIN, 12)
    pdf.cell(CONTENT_W, 5, f"{slide_num + 1}/{total_slides}", align="R")

    # Heading — large, starting at a fixed position that gives good visual weight
    heading_start_y = 35
    heading_size = 28
    heading_line_h = 13
    body_size = 16
    body_line_h = 8.5
    gap = 14
    text_x = MARGIN + 8  # indent past accent bar
    text_w = CONTENT_W - 8

    _set_color(pdf, TEXT)
    pdf.set_font("Playfair", size=heading_size)
    pdf.set_xy(text_x, heading_start_y)
    pdf.multi_cell(text_w, heading_line_h, heading, align="L")

    # Body — larger text so content fills the slide
    body_y = pdf.get_y() + gap
    max_body_y = H_MM - BOTTOM_RESERVED - 4
    if body_y < max_body_y:
        _set_color(pdf, TEXT)
        pdf.set_font("SourceSans", size=body_size)
        pdf.set_xy(text_x, body_y)
        pdf.multi_cell(text_w, body_line_h, body, align="L")

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
    """Chart slide: chart image fills most of the slide + 'so what' context below."""
    pdf.add_page()

    # White background
    pdf.set_fill_color(*WHITE)
    pdf.rect(0, 0, W_MM, H_MM, style="F")

    # Chart image — starts near top, fills as much width as possible
    # No separate title — the chart PNG already contains its own title
    chart_top = 8
    context_reserve = 35  # mm for context text below chart
    available_h = H_MM - chart_top - BOTTOM_RESERVED - context_reserve
    chart_w = CONTENT_W

    chart_h = 0
    if chart_path and Path(chart_path).exists():
        aspect = _get_image_aspect(chart_path)
        chart_h_from_w = chart_w / aspect
        chart_h = min(chart_h_from_w, available_h)
        if chart_h < chart_h_from_w:
            chart_w = chart_h * aspect
        chart_x = MARGIN + (CONTENT_W - chart_w) / 2
        try:
            pdf.image(str(chart_path), x=chart_x, y=chart_top,
                      w=chart_w, h=chart_h)
        except Exception:
            chart_h = 0

    # "So what" context below chart — this is the carousel's value-add
    context_y = chart_top + chart_h + 8
    if context and context_y < H_MM - BOTTOM_RESERVED - 10:
        _set_color(pdf, TEXT)
        pdf.set_font("SourceSans", size=13)
        pdf.set_xy(MARGIN, context_y)
        pdf.multi_cell(CONTENT_W, 7, context, align="L")

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

    # Domain in accent — just the site name, not the full path
    _set_color(pdf, ACCENT)
    pdf.set_font("SourceSans", size=11)
    pdf.set_xy(MARGIN, pdf.get_y() + 12)
    pdf.cell(CONTENT_W, 6, "historyfuturenow.com", align="C")

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
