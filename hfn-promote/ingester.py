"""HFN Promote — Ingester. Reads from corpus_context.json, chart_defs.py, and essay files."""
import json, re, sys, yaml
from pathlib import Path
import db
from config import HFN_BASE_URL, HFN_SOURCE_DIR, HFN_ARTICLE_IMAGES


def _parse_essay_frontmatter(filepath):
    """Extract YAML frontmatter from an essay markdown file."""
    text = filepath.read_text(encoding="utf-8")
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1))
    except Exception:
        return None


def ingest_articles():
    # Phase 1: corpus_context.json (full text + keywords)
    path = HFN_SOURCE_DIR / "corpus_context.json"
    ingested_slugs = set()
    count = 0
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        for art in data.get("articles", []):
            slug = art["slug"]
            keywords = set()
            for ref in art.get("cross_references", []):
                for theme in ref.get("shared_themes", []):
                    keywords.add(theme.lower())
            db.upsert_article(
                slug=slug, title=art.get("title", slug), part=art.get("part", ""),
                excerpt=art.get("excerpt", ""), keywords=sorted(keywords),
                opening=art.get("opening", ""), full_text=art.get("full_text", ""),
                word_count=art.get("word_count", 0),
                url=f"{HFN_BASE_URL}/articles/{slug}")
            ingested_slugs.add(slug)
            count += 1
    else:
        print(f"  WARN: corpus_context.json not found at {path}")

    # Phase 2: scan essays/ for any articles not in corpus_context.json
    essays_dir = HFN_SOURCE_DIR / "essays"
    extras = 0
    if essays_dir.is_dir():
        for md in sorted(essays_dir.glob("*.md")):
            slug = md.stem
            if slug in ingested_slugs:
                continue
            fm = _parse_essay_frontmatter(md)
            if not fm:
                continue
            # Read body for opening paragraph and word count
            text = md.read_text(encoding="utf-8")
            body = re.sub(r'^---.*?---\s*\n', '', text, count=1, flags=re.DOTALL)
            paragraphs = [p.strip() for p in body.split('\n\n') if p.strip() and not p.strip().startswith('#')]
            opening = paragraphs[0] if paragraphs else ""
            word_count = len(body.split())
            db.upsert_article(
                slug=slug, title=fm.get("title", slug), part=fm.get("part", ""),
                excerpt=fm.get("excerpt", ""), keywords=[],
                opening=opening, full_text=body[:10000],
                word_count=word_count,
                url=fm.get("url", f"{HFN_BASE_URL}/articles/{slug}"))
            ingested_slugs.add(slug)
            extras += 1
            count += 1
        if extras:
            print(f"  + {extras} articles from essays/ (not yet in corpus_context.json)")

    return count

def ingest_charts():
    src = str(HFN_SOURCE_DIR)
    if src not in sys.path:
        sys.path.insert(0, src)
    if "chart_defs" in sys.modules:
        del sys.modules["chart_defs"]
    try:
        from chart_defs import get_all_charts
    except ImportError as e:
        print(f"  ERROR: chart_defs.py not found: {e}")
        return 0, 0
    all_charts = get_all_charts()
    db.clear_charts()
    count = 0
    images = 0
    skipped = 0
    for slug, chart_list in all_charts.items():
        for chart in chart_list:
            cid = chart.get("id", "")
            # Skip junk entries: no id, no title, figure_num 0 with no useful data
            if not cid or (chart.get("figure_num", 0) == 0 and not chart.get("title")):
                skipped += 1
                continue
            # Check for pre-rendered image in hfn-site-output
            img = HFN_ARTICLE_IMAGES / slug / f"chart-{cid}.png"
            img_path = str(img) if img.exists() else ""
            if img_path:
                images += 1
            db.upsert_chart(
                article_slug=slug, chart_id=cid,
                figure_num=chart.get("figure_num", 0),
                title=chart.get("title", ""),
                description=chart.get("desc", ""),
                source=chart.get("source", ""),
                image_path=img_path)
            count += 1
    if skipped:
        print(f"  ⊘ {skipped} junk entries skipped (no id or untitled fig 0)")
    return count, images

def ingest_all():
    print("\n=== HFN Promote — Ingestion ===\n")
    print(f"  Source: {HFN_SOURCE_DIR}")
    na = ingest_articles()
    print(f"  ✓ {na} articles")
    nc, ni = ingest_charts()
    print(f"  ✓ {nc} charts ({ni} with images)")
    print(f"\n  Done.\n")
    return na, nc

if __name__ == "__main__":
    ingest_all()
