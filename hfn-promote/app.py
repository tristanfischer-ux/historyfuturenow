"""HFN Promote v3.11 — Library: Promote Article to generate posts."""
import sys, json
from datetime import date, datetime, timedelta
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, send_file, abort, Response
import db
from config import (FLASK_PORT, MAX_X_PER_DAY, MAX_LI_PER_DAY, MAX_POSTS_PER_DAY,
                    HFN_SOURCE_DIR, HFN_ARTICLE_IMAGES, HFN_SITE_OUTPUT,
                    HFN_CONTENT_DIR, HFN_AUDIO_DIR, MONITOR_INTERVAL,
                    MATCH_MODEL, GEN_MODEL, SESSIONS_DIR)

# Import issues from build system
_build_sys = str(Path(__file__).resolve().parent.parent / "hfn-build-system")
if _build_sys not in sys.path:
    sys.path.insert(0, _build_sys)
from issues import ISSUES, build_slug_to_issue_map

# ── Style guide + article catalog loaders for Studio chat ──

_style_guide_cache = None

def load_style_guides():
    """Load all editorial rules and style guides from disk (cached after first call)."""
    global _style_guide_cache
    if _style_guide_cache:
        return _style_guide_cache

    rules_dir = Path(HFN_SOURCE_DIR).parent / ".cursor" / "rules"
    editorial = Path(HFN_SOURCE_DIR).parent / "CLAUDE.md"

    parts = []
    if editorial.exists():
        parts.append(f"# EDITORIAL RULES\n\n{editorial.read_text()}")

    if rules_dir.is_dir():
        for f in sorted(rules_dir.glob("*.mdc")):
            name = f.stem.replace("-", " ").title()
            content = f.read_text()
            # Strip .mdc frontmatter (---\n...\n---)
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    content = content[end + 3:].strip()
            parts.append(f"## {name}\n\n{content}")

    _style_guide_cache = "\n\n---\n\n".join(parts)
    return _style_guide_cache


def build_article_catalog():
    """Build a compact article catalog from the DB for cross-referencing."""
    articles = db.get_all_articles()
    lines = ["# Existing HFN Articles (for cross-referencing)\n"]
    lines.append("IMPORTANT: When writing or discussing articles, actively reference relevant "
                 "existing articles using markdown links: [Title](/articles/slug). Every new "
                 "article should cross-reference at least 2 existing articles. Suggest thematic "
                 "connections the author may not have considered.\n")
    for a in articles:
        part = a.get("part", "")
        excerpt = (a.get("excerpt", "") or "")[:120]
        lines.append(f"- **{a['title']}** ({part}) `/articles/{a['slug']}` — {excerpt}")
    return "\n".join(lines)

_library_catalog_cache = None

def build_library_catalog():
    """Build a compact library catalog grouped by theme for the AI to select sources."""
    global _library_catalog_cache
    if _library_catalog_cache:
        return _library_catalog_cache
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "library_data",
            str(HFN_SOURCE_DIR / "library_data.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        by_theme = {}
        theme_names = {t: v.get("name", t) for t, v in mod.THEMES.items()} if hasattr(mod, "THEMES") else {}
        for b in mod.BOOKS:
            t = b.get("themes", ["other"])[0]
            by_theme.setdefault(t, []).append(f"{b['title']} ({b.get('author', '?')})")

        lines = ["# HFN Library — Available Books for Sources\n"]
        lines.append("When writing a draft, include a `sources:` list in the YAML frontmatter with "
                     "at least 3 books from this library that are RELEVANT to the article's topic. "
                     "Use the EXACT title as shown below. Only cite books that genuinely inform the "
                     "article — do not pad with unrelated titles.\n")
        for theme in sorted(by_theme.keys()):
            name = theme_names.get(theme, theme.title())
            lines.append(f"\n## {name}")
            for book in by_theme[theme]:
                lines.append(f"- {book}")

        _library_catalog_cache = "\n".join(lines)
    except Exception:
        _library_catalog_cache = ""
    return _library_catalog_cache


app = Flask(__name__)
activity_log = []
scheduler_ref = None
scheduler_on = True
last_post_result = {"time": None, "platform": None, "post_id": None, "ok": None, "msg": ""}

def log(msg):
    activity_log.insert(0, {"t": datetime.now().strftime("%H:%M:%S"), "m": msg})
    if len(activity_log) > 100: activity_log.pop()

POST_SLOTS = [0, 3, 6, 7, 9, 11, 12, 14, 16, 17, 18, 20, 22]

def next_available_slot():
    """Find next posting slot not already taken by a scheduled/queued/generated post."""
    now = datetime.now()
    conn = db.get_db()
    booked = {r[0] for r in conn.execute(
        "SELECT scheduled_at FROM posts WHERE status IN ('planned','generated','queued','scheduled') AND scheduled_at != ''"
    ).fetchall()}
    conn.close()
    # Try today's remaining slots, then tomorrow's, up to 7 days out
    for day_offset in range(8):
        d = now + timedelta(days=day_offset)
        for h in POST_SLOTS:
            candidate = d.replace(hour=h, minute=0, second=0, microsecond=0)
            if candidate <= now:
                continue
            key = candidate.strftime("%Y-%m-%dT%H:%M")
            if key not in booked:
                return candidate
    # Fallback: next hour
    return now.replace(minute=0, second=0) + timedelta(hours=1)

@app.route("/img/<path:fp>")
def serve_img(fp):
    if "/articles/" in fp: fp = fp.split("/articles/")[-1]
    full = HFN_ARTICLE_IMAGES / fp
    if full.exists(): return send_file(str(full), mimetype="image/png")
    abort(404)

def img_url(image_path):
    if not image_path: return ""
    if "/articles/" in image_path: return "/img/" + image_path.split("/articles/")[-1]
    return "/img/" + image_path

HTML = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>HFN Promote</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@500;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
:root{--bg:#f8f7f6;--card:#fff;--border:#e5e2de;--text:#1a1815;--dim:#8a8479;
--accent:#c43425;--xblk:#0f1419;--li:#0a66c2;--grn:#16a34a;--red:#dc2626;--sched:#7c3aed;
--bg-warm:#faf8f5;--surface:#f5f3ef;--border-light:#e8e4de;--accent-soft:#fef7f6;
--serif:'Playfair Display',Georgia,serif;--mono:'IBM Plex Mono','Courier New',monospace}
*{box-sizing:border-box;margin:0;padding:0}body{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.5;height:100vh;overflow:hidden}
.topbar{background:var(--text);color:#fff;padding:10px 20px;display:flex;align-items:center;justify-content:space-between}
.topbar h1{font-size:1rem;font-weight:700}.topbar .r{font-size:.72rem;color:#a8a29e;display:flex;align-items:center;gap:12px}
.dot{width:7px;height:7px;border-radius:50%;display:inline-block}.dot.on{background:#4ade80}.dot.off{background:#666}
.sess-indicator{font-size:.7rem;color:#a8a29e;display:flex;align-items:center;gap:3px}
.tabs-bar{background:var(--card);border-bottom:1px solid var(--border);padding:0 20px;display:flex;align-items:center;gap:0}
.tab{padding:10px 16px;font-size:.82rem;font-weight:500;cursor:pointer;border-bottom:2px solid transparent;color:var(--dim)}
.tab:hover{color:var(--text)}.tab.on{color:var(--accent);border-color:var(--accent)}
.tab-actions{margin-left:auto;display:flex;gap:6px;padding:6px 0}
.btn{padding:6px 12px;border-radius:7px;border:1px solid var(--border);background:var(--card);color:var(--text);cursor:pointer;font-size:.74rem;font-weight:600;font-family:inherit;transition:all .12s}
.btn:hover{background:#f0efed}.btn.primary{background:var(--accent);color:#fff;border-color:var(--accent)}.btn.primary:hover{background:#a82d20}
.btn.bsc{background:var(--sched);color:#fff;border-color:var(--sched)}.btn.bsv{background:var(--grn);color:#fff;border-color:var(--grn)}
.btn.bx{background:var(--xblk);color:#fff}.btn.bli{background:var(--li);color:#fff}
.btn.sm{padding:4px 8px;font-size:.68rem}.btn.rej{color:var(--red);border-color:#fecaca}
.main{display:flex;height:calc(100vh - 88px);overflow:hidden}
.tc{display:none;width:100%;height:100%;overflow-y:auto}.tc.on{display:flex;flex-direction:column}

/* ═══ PLANNER ═══ */
.planner{display:flex;height:100%;overflow:hidden}
.pl-col{border-right:1px solid var(--border);display:flex;flex-direction:column;min-width:0}
.pl-col.c1{width:28%;min-width:240px}.pl-col.c2{width:32%;min-width:260px}.pl-col.c3{flex:1;min-width:300px}
.pl-head{padding:10px 14px;background:var(--card);border-bottom:1px solid var(--border);font-size:.78rem;font-weight:700;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.pl-head .ph-sub{font-size:.65rem;color:var(--dim);font-weight:400}
.pl-body{flex:1;overflow-y:auto;padding:8px}

/* News items */
.ni{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 12px;margin-bottom:6px;cursor:pointer;transition:all .12s}
.ni:hover{border-color:var(--accent)}.ni.sel{border-color:var(--accent);background:#fef7f6}
.ni-title{font-size:.82rem;font-weight:600;margin-bottom:3px}
.ni-link{color:inherit;text-decoration:none}.ni-link:hover{color:var(--accent);text-decoration:underline}
.ni-meta{font-size:.65rem;color:var(--dim);display:flex;gap:8px}
.ni-score{color:var(--grn);font-weight:700}.ni-feeds{color:var(--dim)}
.ni-age{color:var(--sched);font-weight:500;font-size:.6rem}

/* Arsenal items */
.ai{background:var(--card);border:1px solid var(--border);border-radius:8px;overflow:hidden;margin-bottom:8px;cursor:grab;transition:all .12s}
.ai:hover{border-color:var(--sched)}.ai.dragging{opacity:.4}
.ai-img{width:100%;object-fit:contain;display:block;background:#fafaf9;border-bottom:1px solid var(--border);padding:8px}
.ai-body{padding:10px}
.ai-chart{font-size:.82rem;color:var(--accent);font-weight:700;margin-bottom:5px;line-height:1.3}
.ai-article{font-size:.73rem;color:#444;margin-bottom:5px;line-height:1.35;font-weight:500}
.ai-desc{font-size:.72rem;line-height:1.35;color:#555;margin-bottom:5px;padding:5px 7px;background:#f5f5f0;border-radius:4px}
.ai-hook{font-size:.76rem;line-height:1.4;color:#2563eb;background:#eff6ff;padding:6px 8px;border-radius:6px;margin-bottom:4px;border-left:2px solid #3b82f6;font-style:italic}
.ai-opts{display:flex;gap:4px;margin-top:6px}
.opt-pill{padding:2px 8px;border-radius:12px;font-size:.62rem;font-weight:700;cursor:pointer;border:1px solid var(--border);transition:all .1s}
.opt-pill:hover{border-color:var(--accent)}.opt-pill.sel{background:var(--accent);color:#fff;border-color:var(--accent)}
.opt-pill.x-sel{background:var(--xblk);color:#fff;border-color:var(--xblk)}
.opt-pill.li-sel{background:var(--li);color:#fff;border-color:var(--li)}

/* Timeline */
.tl-day{margin-bottom:12px}
.tl-dayhead{font-size:.75rem;font-weight:700;padding:6px 10px;background:var(--card);border:1px solid var(--border);border-radius:8px 8px 0 0;display:flex;justify-content:space-between}
.tl-dayhead.today{background:#fef7f6;border-color:var(--accent)}
.tl-slots{min-height:50px;background:var(--card);border:1px dashed var(--border);border-top:none;border-radius:0 0 8px 8px;padding:6px}
.tl-slots.over{background:#f0f7ff;border-color:var(--li)}
.tl-slot{padding:7px 8px;border-radius:6px;margin-bottom:5px;font-size:.72rem;display:flex;align-items:flex-start;gap:6px}
.tl-slot.x{background:#f5f5f4;border-left:3px solid var(--xblk)}
.tl-slot.li{background:#eff6ff;border-left:3px solid var(--li)}
.tl-slot .sl-time{font-weight:700;color:var(--dim);font-size:.65rem;min-width:36px;padding-top:1px}
.tl-slot .sl-body{flex:1;min-width:0}
.tl-slot .sl-title{font-weight:600;font-size:.72rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tl-slot .sl-hook{font-size:.66rem;color:#666;line-height:1.3;margin-top:2px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.tl-slot .sl-type{font-size:.55rem;background:var(--bg);padding:2px 6px;border-radius:3px;color:var(--dim);font-weight:700;white-space:nowrap;text-transform:uppercase;letter-spacing:.3px}
.tl-slot .sl-rm{cursor:pointer;color:var(--red);font-size:.7rem;opacity:.5;padding-top:1px}.tl-slot .sl-rm:hover{opacity:1}
.tl-slot .sl-gen{padding:2px 5px;font-size:.6rem;opacity:.6;flex-shrink:0}.tl-slot .sl-gen:hover{opacity:1}
.tl-slot.queued{opacity:.55;border-left-style:solid!important;pointer-events:none}
.tl-slot.queued .sl-badge{font-size:.52rem;padding:1px 5px;border-radius:3px;font-weight:700;text-transform:uppercase;letter-spacing:.3px;background:#dcfce7;color:#166534}
.tl-slot.generated .sl-badge{font-size:.52rem;padding:1px 5px;border-radius:3px;font-weight:700;text-transform:uppercase;letter-spacing:.3px;background:#fef9c3;color:#854d0e}
.tl-slot-empty{padding:3px 8px;font-size:.62rem;color:var(--dim);border-radius:4px;margin-bottom:2px;display:flex;align-items:center;opacity:.5;transition:all .15s}
.tl-slot-empty:hover,.tl-slot-empty.over{background:#f0f7ff;opacity:1;border:1px dashed var(--li)}
.tl-slot-empty .sle-time{font-weight:600;font-size:.6rem;font-family:var(--mono);min-width:36px}
.tl-empty{font-size:.68rem;color:var(--dim);padding:8px;text-align:center;font-style:italic}
.tl-time-sel{display:flex;gap:4px;margin-top:4px}
.tl-time-sel select{font-size:.7rem;padding:2px 4px}

/* Review & Queue */
.rq-head{padding:8px 14px;background:var(--card);border-bottom:1px solid var(--border);font-size:.78rem;font-weight:700;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.rq-head .ph-sub{font-size:.65rem;color:var(--dim);font-weight:400}
.rq-body{flex:1!important;max-height:none!important}
.rq-day{margin-bottom:10px}
.rq-dayhead{font-size:.72rem;font-weight:700;padding:6px 10px;border-radius:6px;display:flex;align-items:center;justify-content:space-between;margin-bottom:4px}
.rq-dayhead.review{background:#fefce8;color:#854d0e}
.rq-dayhead.queued{background:#f0fdf4;color:#166534}
.rq-card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px;margin-bottom:6px}
.rq-card.review{border-left:3px solid #eab308}
.rq-card.queued{border-left:3px solid var(--grn);opacity:.85}
.rq-top{display:flex;align-items:center;gap:6px;margin-bottom:6px;flex-wrap:wrap}
.rq-time{font-size:.65rem;color:var(--dim);font-weight:700}
.rq-chart{font-size:.68rem;color:var(--accent);font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.rq-caption{font-size:.78rem;line-height:1.45;margin-bottom:6px;white-space:pre-wrap}
.rq-caption[contenteditable="true"]{-webkit-line-clamp:unset;outline:none;border:1px solid var(--li);border-radius:6px;padding:8px;background:#f0f7ff}
.rq-caption.locked{color:#555}
.rq-img{width:100%;max-width:704px;object-fit:contain;background:#fafaf9;border:1px solid var(--border);border-radius:6px;margin-bottom:6px;padding:8px;image-rendering:auto}
.rq-chart-title{font-size:.75rem;color:var(--accent);font-weight:700;margin-bottom:4px}
.rq-context{font-size:.74rem;color:#555;font-style:italic;padding:6px 8px;background:#fafaf9;border-radius:5px;border-left:3px solid var(--accent);margin-bottom:6px;line-height:1.4}
.rq-link{display:block;font-size:.7rem;color:#2563eb;text-decoration:none;margin-bottom:6px;word-break:break-all}.rq-link:hover{text-decoration:underline}
.rq-actions{display:flex;gap:4px}
.rq-countdown{font-size:.62rem;font-weight:700;color:var(--sched);background:#ede9fe;padding:1px 7px;border-radius:10px}

/* Queue calendar grid */
.qcal{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;padding:12px}
.qcal-day{min-width:0}
.qcal-dayhead{font-family:var(--mono);font-size:.62rem;font-weight:600;padding:7px 8px;border-radius:8px 8px 0 0;background:var(--bg-warm);color:var(--dim);text-align:center;text-transform:uppercase;letter-spacing:.5px;border:1px solid var(--border-light);border-bottom:none}
.qcal-dayhead.today{background:var(--accent-soft);color:var(--accent);border-color:var(--accent);font-weight:700}
.qcal-slots{min-height:48px;border:1px solid var(--border-light);border-radius:0 0 8px 8px;padding:6px;transition:background .15s,border-color .15s}
.qcal-slots.over{background:var(--accent-soft);border-color:var(--accent);border-style:dashed}
.qcal-card{background:var(--card);border:1px solid var(--border);border-top:3px solid var(--accent);border-radius:10px;padding:8px 9px;margin-bottom:6px;cursor:grab;transition:all .15s;font-size:.7rem;box-shadow:0 1px 3px rgba(0,0,0,.04)}
.qcal-card:hover{border-color:var(--accent);box-shadow:0 3px 8px rgba(0,0,0,.08);transform:translateY(-2px)}
.qcal-card.expanded{border-color:var(--accent)}
.qcal-card.dragging{opacity:.35;transform:scale(.95)}
.qcal-meta{display:flex;align-items:center;gap:4px;flex-wrap:wrap}
.qcal-time{font-family:var(--mono);font-size:.58rem;font-weight:600;color:var(--dim);text-transform:uppercase;letter-spacing:.3px}
.qcal-type{font-family:var(--mono);font-size:.5rem;font-weight:600;text-transform:uppercase;letter-spacing:.3px;padding:1px 5px;border-radius:3px;background:var(--surface);color:var(--dim)}
.qcal-article{font-family:var(--serif);font-size:.72rem;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin:3px 0 1px;color:var(--text);line-height:1.3}
.qcal-title{font-size:.66rem;font-weight:600;color:var(--accent);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin:1px 0}
.qcal-hook{font-size:.6rem;color:var(--dim);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;line-height:1.3}
.qcal-detail{display:none;margin-top:6px;font-size:.72rem;line-height:1.4;white-space:pre-wrap;border-top:1px solid var(--border);padding-top:6px}
.qcal-card.expanded .qcal-detail{display:block}
.qcal-actions{display:flex;gap:4px;margin-top:6px}
.qcal-empty{font-family:var(--mono);font-size:.58rem;color:var(--dim);text-align:center;padding:10px 4px;text-transform:uppercase;letter-spacing:.3px}
.qcal-slot-empty{padding:3px 8px;font-size:.62rem;color:var(--dim);border-radius:4px;margin-bottom:2px;display:flex;align-items:center;opacity:.5;transition:all .15s}
.qcal-slot-empty:hover,.qcal-slot-empty.over{background:var(--accent-soft);opacity:1;border:1px dashed var(--accent)}
.qcal-slot-empty .qse-time{font-weight:600;font-size:.6rem;font-family:var(--mono);min-width:36px}

/* Review page (full-width tab) */
.review-page{max-width:800px;margin:0 auto;padding:16px 20px;height:100%;overflow-y:auto}

/* Platform preview */
.post-preview{border:1px solid var(--border);border-radius:12px;padding:12px;margin:6px 0;background:#fff}
.post-preview.x{border-color:#cfd9de;border-radius:16px}
.post-preview.linkedin{border-color:#d3d9de;border-radius:8px}
.pp-header{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.pp-avatar{width:36px;height:36px;border-radius:50%;background:var(--accent);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;flex-shrink:0}
.post-preview.x .pp-avatar{width:32px;height:32px;font-size:.75rem}
.pp-meta{display:flex;flex-direction:column;line-height:1.2}
.pp-name{font-weight:700;font-size:.78rem}
.pp-handle{font-size:.68rem;color:var(--dim)}
.pp-text{font-size:.82rem;line-height:1.5;white-space:pre-wrap;margin-bottom:8px}
.post-preview.x .pp-text{font-size:.8rem}
.pp-img{width:100%;border-radius:10px;border:1px solid var(--border);margin-bottom:6px;object-fit:contain;background:#fafaf9}
.pp-link{display:block;font-size:.7rem;color:#2563eb;text-decoration:none;word-break:break-all;margin-bottom:4px}.pp-link:hover{text-decoration:underline}
.pp-charcount{font-size:.62rem;color:var(--dim);text-align:right}

/* Platform badges (shared) */
.plat{display:inline-block;padding:2px 7px;border-radius:4px;font-size:.62rem;font-weight:700;text-transform:uppercase}
.plat.x{background:var(--xblk);color:#fff}.plat.li{background:var(--li);color:#fff}

/* Post calendar */
.post-filter-bar{display:flex;gap:8px;align-items:center;margin-bottom:12px;flex-wrap:wrap}
.post-filter-bar select{padding:5px 8px;border:1px solid var(--border);border-radius:6px;font-size:.74rem;font-family:inherit;background:var(--card)}
.post-cal-day{margin-bottom:10px}
.post-cal-dayhead{font-size:.75rem;font-weight:700;padding:8px 12px;background:var(--card);border:1px solid var(--border);border-radius:8px;cursor:pointer;display:flex;justify-content:space-between;align-items:center}
.post-cal-dayhead:hover{background:#f5f4f2}
.post-cal-posts{display:none;border:1px solid var(--border);border-top:none;border-radius:0 0 8px 8px;padding:6px}
.post-cal-posts.open{display:block}
.post-cal-item{display:flex;align-items:flex-start;gap:12px;padding:12px 14px;background:var(--card);border:1px solid var(--border);border-radius:8px;margin-bottom:6px}
.post-cal-item img{width:100px;height:75px;object-fit:contain;border-radius:6px;background:#fafaf9;border:1px solid var(--border);flex-shrink:0}
.post-cal-body{flex:1;min-width:0}
.post-cal-article{font-family:var(--serif);font-size:.76rem;font-weight:600;color:var(--text);margin-bottom:2px}
.post-cal-chart{font-size:.68rem;color:var(--accent);font-weight:600;margin-bottom:2px}
.post-cal-news{font-size:.66rem;color:var(--dim);margin-bottom:4px}
.post-cal-news a{color:#2563eb;text-decoration:none}.post-cal-news a:hover{text-decoration:underline}
.post-cal-caption{font-size:.8rem;line-height:1.5;white-space:pre-wrap;word-break:break-word}

.empty{text-align:center;padding:40px;color:var(--dim)}.empty .ei{font-size:2rem;margin-bottom:8px}

/* Library */
.lib-wrap{display:flex;height:100%;overflow:hidden}
.lib-sidebar{width:340px;min-width:280px;border-right:1px solid var(--border);display:flex;flex-direction:column;background:var(--card)}
.lib-search-box{padding:10px;border-bottom:1px solid var(--border)}
.lib-search-box input{width:100%;padding:7px 10px;border:1px solid var(--border);border-radius:7px;font-size:.78rem;font-family:inherit}
.lib-search-box input:focus{outline:none;border-color:var(--accent)}
.lib-filters{display:flex;gap:6px;padding:8px 10px;border-bottom:1px solid var(--border);align-items:center}
.lib-filter-select{padding:5px 8px;border:1px solid var(--border);border-radius:6px;font-size:.7rem;font-family:var(--mono);background:var(--card);color:var(--text);flex:1;min-width:0}
.lib-filter-select:focus{outline:none;border-color:var(--accent)}
.lib-post-count{font-size:.58rem;font-weight:600;padding:1px 6px;border-radius:8px;white-space:nowrap}
.lib-post-count.has-posts{background:#dcfce7;color:#166534}
.lib-post-count.no-posts{background:#f5f5f4;color:var(--dim)}
.lib-stats{padding:6px 12px;font-size:.65rem;color:var(--dim);border-bottom:1px solid var(--border)}
.lib-list{flex:1;overflow-y:auto;padding:6px}
.lib-item{padding:8px 10px;border-radius:7px;cursor:pointer;margin-bottom:3px;transition:all .1s}
.lib-item:hover{background:#f5f4f2}.lib-item.sel{background:#fef7f6;border-left:3px solid var(--accent)}
.lib-item-title{font-size:.78rem;font-weight:600;line-height:1.35;margin-bottom:2px}
.lib-item-meta{font-size:.62rem;color:var(--dim);display:flex;gap:8px;align-items:center}
.lib-part{background:#ede9fe;color:#5b21b6;padding:1px 5px;border-radius:3px;font-weight:600;font-size:.58rem}
.lib-detail{flex:1;overflow-y:auto;padding:16px}
.lib-placeholder{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;color:var(--dim)}
.lib-article-head{margin-bottom:16px}
.lib-article-head h2{font-size:1rem;font-weight:700;margin-bottom:4px}
.lib-article-head .lib-excerpt{font-size:.78rem;color:#555;line-height:1.5;max-width:700px}
.lib-article-head .lib-url{font-size:.7rem;color:#2563eb;text-decoration:none;word-break:break-all}.lib-url:hover{text-decoration:underline}
.lib-charts-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
.lib-chart-card{background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden;transition:all .12s}
.lib-chart-card:hover{box-shadow:0 2px 10px rgba(0,0,0,.06)}
.lib-chart-card img{width:100%;display:block;object-fit:contain;background:#fafaf9;border-bottom:1px solid var(--border);padding:6px}
.lib-chart-body{padding:10px}
.lib-chart-title{font-size:.8rem;font-weight:700;color:var(--accent);margin-bottom:3px}
.lib-chart-desc{font-size:.72rem;color:#555;line-height:1.4;margin-bottom:4px}
.lib-chart-source{font-size:.62rem;color:var(--dim)}
.lib-chart-tags{display:flex;gap:4px;flex-wrap:wrap;margin-top:6px}
.lib-chart-tag{font-size:.58rem;padding:2px 6px;background:#f5f5f4;border-radius:3px;color:#555}
.lib-promote-btn{display:inline-flex;align-items:center;gap:4px;padding:5px 12px;border-radius:7px;border:1px solid var(--accent);background:var(--accent);color:#fff;cursor:pointer;font-size:.72rem;font-weight:600;font-family:inherit;transition:all .12s}
.lib-promote-btn:hover{background:#a82d20}.lib-promote-btn:disabled{opacity:.5;cursor:wait}
.lib-chart-promote{display:inline-flex;align-items:center;gap:3px;padding:2px 8px;border-radius:5px;border:1px solid var(--border);background:var(--card);color:var(--accent);cursor:pointer;font-size:.62rem;font-weight:600;font-family:inherit;transition:all .12s}
.lib-chart-promote:hover{border-color:var(--accent);background:var(--accent-soft)}.lib-chart-promote:disabled{opacity:.5;cursor:wait}
/* Heatmap */
.heatmap-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px;padding:12px}
.hm-card{border-radius:8px;overflow:hidden;border:1px solid var(--border);text-align:center;font-size:.62rem}
.hm-card img{width:100%;height:80px;object-fit:contain;background:#fafaf9;display:block}
.hm-card .hm-label{padding:4px 6px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hm-0{background:#f0fdf4}.hm-1{background:#fef9c3}.hm-2{background:#fed7aa}.hm-3{background:#fecaca}

.qp-btn{float:right;font-size:.62rem!important;padding:1px 6px!important;background:#fff3e0!important;border-color:#f59e0b!important;color:#92400e!important}
.qp-btn:hover{background:#fde68a!important}
.toast{position:fixed;bottom:20px;right:20px;background:var(--text);color:#fff;padding:10px 18px;border-radius:10px;font-size:.82rem;transform:translateY(80px);opacity:0;transition:all .3s;z-index:100}
.toast.show{transform:translateY(0);opacity:1}
.logbox{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px;max-height:300px;overflow-y:auto;font-size:.78rem;margin:12px 20px}
.logr{padding:3px 0;border-bottom:1px solid #f5f5f4}.logt{color:var(--dim);font-family:monospace;font-size:.7rem;margin-right:8px}
@media(max-width:900px){
.planner{flex-direction:column}.pl-col{width:100%!important;height:auto;border-right:none;border-bottom:1px solid var(--border)}.pl-body{max-height:300px}
.tabs-bar{flex-wrap:wrap}.tab{padding:8px 10px;font-size:.75rem}
.lib-wrap{flex-direction:column}.lib-sidebar{width:100%;min-width:0;max-height:250px;border-right:none;border-bottom:1px solid var(--border)}
.lib-charts-grid{grid-template-columns:1fr}
.btn,.opt-pill{min-height:44px;min-width:44px}
.post-cal-item img{width:60px;height:45px}
.heatmap-grid{grid-template-columns:repeat(auto-fill,minmax(100px,1fr))}
.rq-card,.post-preview{max-width:100%}
.pp-img,.rq-img{max-width:100%}
.qcal{grid-template-columns:repeat(2,1fr)}
.qcal-card{cursor:pointer}
}

/* Lightbox */
#lightbox{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.85);z-index:200;cursor:zoom-out;align-items:center;justify-content:center}
#lightbox.open{display:flex}
#lightbox img{max-width:90vw;max-height:90vh;object-fit:contain;border-radius:8px}
.pp-img,.ai-img,.lib-chart-card img,.post-cal-item img{cursor:zoom-in}

/* Dark mode */
body.dark{--bg:#1a1815;--card:#252220;--border:#3a3632;--text:#e8e4de;--dim:#8a8479;--accent:#e05545;--bg-warm:#252220;--surface:#2a2825;--border-light:#3a3632;--accent-soft:#3a2020}
body.dark .topbar{background:#0f0e0c}
body.dark .post-preview{background:var(--card);border-color:var(--border)}
body.dark .pp-img,body.dark .ai-img,body.dark .lib-chart-card img{background:#1a1815;border-color:var(--border)}
body.dark .btn{background:var(--card);color:var(--text);border-color:var(--border)}
body.dark .btn.primary{background:var(--accent);color:#fff}
body.dark .toast{background:#e8e4de;color:#1a1815}
body.dark input,body.dark select,body.dark .lib-filter-select{background:var(--card);color:var(--text);border-color:var(--border)}
body.dark .lib-post-count.has-posts{background:#1a3a2a;color:#4ade80}
body.dark .lib-post-count.no-posts{background:#2a2825;color:#666}
body.dark .rq-caption[contenteditable="true"]{background:#2a2825;border-color:var(--li);color:var(--text)}
.rq-card.rq-focused{outline:2px solid var(--accent);outline-offset:2px}
.tl-slot[draggable]{cursor:grab}.tl-slot.dragging{opacity:.4}
.img-fallback{display:flex;align-items:center;justify-content:center;background:#f5f5f4;border:1px dashed var(--border);border-radius:6px;color:var(--dim);font-size:.72rem;padding:16px;min-height:60px}
body.dark .img-fallback{background:#2a2825}
body.dark .tl-slot-empty:hover,body.dark .tl-slot-empty.over{background:#2a2825;border-color:var(--li)}
body.dark .qcal-card{background:var(--card);border-color:var(--border);border-top-color:var(--accent);box-shadow:0 1px 3px rgba(0,0,0,.2)}
body.dark .qcal-card:hover{box-shadow:0 3px 8px rgba(0,0,0,.3)}
body.dark .qcal-dayhead{background:#2a2623;color:#a8a29e;border-color:var(--border)}
body.dark .qcal-dayhead.today{background:#3a2020;color:var(--accent);border-color:var(--accent)}
body.dark .qcal-slots{border-color:var(--border)}
body.dark .qcal-slots.over{background:#3a2020;border-color:var(--accent)}
body.dark .qcal-type{background:#3a3632;color:#a8a29e}
body.dark .qcal-article{color:var(--text)}
.toast a{color:#60a5fa;text-decoration:underline;margin-left:8px;cursor:pointer}

/* ═══ ARTICLE STUDIO ═══ */
.st-wrap{height:100%;overflow-y:auto;padding:16px 20px}
.st-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
.st-header h2{font-size:1rem;font-weight:700}
.st-pills{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}
.st-pill{font-size:.62rem;font-weight:700;padding:3px 10px;border-radius:12px;text-transform:uppercase;letter-spacing:.3px}
.st-pill.draft{background:#f5f5f4;color:#666}.st-pill.factcheck{background:#fef3c7;color:#92400e}
.st-pill.charts{background:#dbeafe;color:#1e40af}.st-pill.images{background:#fef3c7;color:#92400e}.st-pill.review{background:#ede9fe;color:#5b21b6}
.st-pill.deployed{background:#dcfce7;color:#166534}
.st-table{width:100%;border-collapse:collapse}
.st-table th{text-align:left;font-size:.68rem;color:var(--dim);font-weight:600;padding:8px 10px;border-bottom:2px solid var(--border);text-transform:uppercase;letter-spacing:.3px}
.st-table td{padding:8px 10px;border-bottom:1px solid var(--border);font-size:.78rem;vertical-align:middle}
.st-table tr:hover{background:#fafaf9}
.st-table .st-title-link{color:var(--text);font-weight:600;cursor:pointer;text-decoration:none}.st-title-link:hover{color:var(--accent)}
.st-table .st-del{color:var(--red);cursor:pointer;opacity:.4;font-size:.8rem}.st-del:hover{opacity:1}
.st-badge{font-size:.58rem;font-weight:700;padding:2px 8px;border-radius:10px;text-transform:uppercase;letter-spacing:.3px;white-space:nowrap}
.st-badge.draft{background:#f5f5f4;color:#666}.st-badge.factcheck{background:#fef3c7;color:#92400e}
.st-badge.charts{background:#dbeafe;color:#1e40af}.st-badge.images{background:#fef3c7;color:#92400e}.st-badge.review{background:#ede9fe;color:#5b21b6}
.st-badge.deployed{background:#dcfce7;color:#166534}
.st-assets{display:flex;gap:4px;font-size:.75rem}
.st-assets .dim{opacity:.25}.st-assets .on{opacity:1}
.st-empty{text-align:center;padding:60px 20px;color:var(--dim)}
.st-empty .st-icon{font-size:2.5rem;margin-bottom:10px}

/* Studio Editor */
.st-editor{height:100%;display:flex;flex-direction:column}
.st-ed-top{display:flex;align-items:center;gap:10px;padding:10px 16px;background:var(--card);border-bottom:1px solid var(--border);flex-shrink:0}
.st-back{cursor:pointer;font-size:1.1rem;color:var(--dim);padding:4px}.st-back:hover{color:var(--accent)}
.st-ed-title{font-size:.9rem;font-weight:700;flex:1}
.st-ed-slug{font-size:.65rem;color:var(--dim);font-family:var(--mono)}
.st-ed-save{font-size:.62rem;color:var(--grn);font-weight:600}

/* Pipeline stepper */
.st-stepper{display:flex;align-items:flex-start;gap:0;padding:12px 16px 28px 16px;background:var(--card);border-bottom:1px solid var(--border);flex-shrink:0}
.st-step{display:flex;flex-direction:column;align-items:center;gap:0;position:relative}
.st-step-dot{width:28px;height:28px;border-radius:50%;border:2px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:.6rem;font-weight:700;color:var(--dim);background:var(--card);transition:all .2s}
.st-step-dot.active{border-color:var(--accent);color:var(--accent);background:var(--accent-soft)}
.st-step-dot.done{border-color:var(--grn);color:#fff;background:var(--grn)}
.st-step-dot.done:hover,.st-step-dot.active:hover{transform:scale(1.15);box-shadow:0 0 0 3px rgba(0,0,0,.1)}
.st-step-line{width:24px;height:2px;background:var(--border);margin-top:13px}
.st-step-line.done{background:var(--grn)}
.st-step-label{font-size:.55rem;color:var(--dim);text-align:center;margin-top:2px;position:absolute;top:100%;left:50%;transform:translateX(-50%);white-space:nowrap}

/* Next-step action bar */
.st-next-bar{display:flex;align-items:center;gap:12px;padding:10px 16px;background:#fffbeb;border-bottom:1px solid #fde68a;flex-shrink:0}
.st-next-text{flex:1;font-size:.78rem;color:#92400e;font-weight:500}
.st-next-bar .btn{flex-shrink:0}
.st-next-bar .btn.secondary{background:var(--card);color:var(--text);border:1px solid var(--border)}
.st-next-bar .btn.secondary:hover{background:#f0efed}
body.dark .st-next-bar{background:#3a3020;border-color:#5a4a20}
body.dark .st-next-text{color:#fbbf24}

/* Editor layout */
.st-ed-body{display:flex;flex:1;overflow:hidden}
.st-ed-left{width:45%;min-width:320px;border-right:1px solid var(--border);overflow:hidden;display:flex;flex-direction:column}
.st-ed-right{flex:1;display:flex;flex-direction:column;overflow:hidden}

/* Chat pane */
.st-chat{display:flex;flex-direction:column;height:100%}
.st-chat-messages{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px}
.st-chat-messages:empty::before{content:'Start a conversation about your article idea...';color:var(--dim);font-size:.82rem;text-align:center;margin-top:40%;font-style:italic}
.st-msg{max-width:88%;padding:10px 14px;border-radius:12px;font-size:.82rem;line-height:1.55;word-wrap:break-word}
.st-msg.user{align-self:flex-end;background:var(--accent-soft);border:1px solid #f0d4d0;border-bottom-right-radius:4px}
.st-msg.assistant{align-self:flex-start;background:var(--card);border:1px solid var(--border);border-bottom-left-radius:4px}
.st-msg .st-msg-content p{margin-bottom:6px}.st-msg .st-msg-content p:last-child{margin-bottom:0}
.st-msg .st-msg-content h1,.st-msg .st-msg-content h2,.st-msg .st-msg-content h3{font-size:.88rem;font-weight:700;margin:8px 0 4px}
.st-msg .st-msg-content code{background:#f5f5f4;padding:1px 4px;border-radius:3px;font-family:var(--mono);font-size:.78em}
.st-msg .st-msg-content pre{background:#f5f5f4;padding:8px;border-radius:4px;overflow-x:auto;margin:6px 0;font-size:.76rem}
.st-msg .st-msg-content blockquote{border-left:3px solid var(--accent);padding-left:10px;color:#555;margin:6px 0}
.st-msg .st-msg-content ul,.st-msg .st-msg-content ol{margin:4px 0;padding-left:20px}
.st-msg .st-msg-content li{margin-bottom:2px}
.st-msg.streaming .st-cursor{display:inline-block;width:2px;height:14px;background:var(--accent);animation:blink .8s infinite;vertical-align:text-bottom;margin-left:2px}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
.st-draft-indicator{background:#dcfce7;color:#166534;font-size:.68rem;font-weight:600;padding:3px 10px;border-radius:6px;text-align:center;animation:fadeInUp .3s ease}
@keyframes fadeInUp{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
@keyframes editorFlash{0%{box-shadow:inset 0 0 0 2px transparent}30%{box-shadow:inset 0 0 0 2px #4ade80}100%{box-shadow:inset 0 0 0 2px transparent}}
.st-md-area.flash{animation:editorFlash 1.2s ease}
.st-chat-input-row{display:flex;gap:8px;padding:10px 12px;border-top:1px solid var(--border);background:var(--card);align-items:flex-end}
.st-chat-input-row textarea{flex:1;resize:none;border:1px solid var(--border);border-radius:8px;padding:8px 12px;font-size:.82rem;font-family:inherit;line-height:1.4;max-height:120px;overflow-y:auto;background:var(--card);color:var(--text)}
.st-chat-input-row textarea:focus{outline:none;border-color:var(--accent)}
.st-chat-input-row button{padding:8px 14px;border-radius:8px;font-size:.9rem;min-width:40px;flex-shrink:0}

/* Details panel (collapsible) */
.st-details-panel{display:none;padding:10px 14px;border-bottom:1px solid var(--border);background:var(--bg-warm);overflow-y:auto;max-height:320px}
.st-details-panel.open{display:block}
.st-details-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.st-details-grid .st-field:nth-child(3),.st-details-grid .st-field:nth-child(4),.st-details-grid .st-field:nth-child(5){grid-column:span 2}
.st-details-actions{display:flex;gap:4px;margin-top:8px;flex-wrap:wrap}
.st-details-actions .st-action-btn{padding:5px 10px;font-size:.68rem;flex:none}

/* Metadata card */
.st-meta-card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:12px}
.st-meta-card h3{font-size:.75rem;font-weight:700;margin-bottom:8px;color:var(--dim);text-transform:uppercase;letter-spacing:.3px}
.st-field{margin-bottom:10px}
.st-field label{display:block;font-size:.68rem;font-weight:600;color:var(--dim);margin-bottom:3px}
.st-field input,.st-field select,.st-field textarea{width:100%;padding:6px 8px;border:1px solid var(--border);border-radius:6px;font-size:.78rem;font-family:inherit;background:var(--card);color:var(--text)}
.st-field input:focus,.st-field select:focus,.st-field textarea:focus{outline:none;border-color:var(--accent)}
.st-field textarea{resize:vertical;min-height:60px}
.st-char-count{font-size:.58rem;color:var(--dim);text-align:right;margin-top:2px}
.st-char-count.over{color:var(--red)}

/* Pipeline buttons */
.st-actions{display:flex;flex-direction:column;gap:6px;margin-bottom:12px}
.st-action-btn{display:flex;align-items:center;gap:8px;padding:8px 12px;border-radius:7px;border:1px solid var(--border);background:var(--card);cursor:pointer;font-size:.74rem;font-weight:600;font-family:inherit;transition:all .12s;color:var(--text)}
.st-action-btn:hover{border-color:var(--accent);background:var(--accent-soft)}
.st-action-btn:disabled{opacity:.4;cursor:not-allowed}
.st-action-btn .st-act-icon{font-size:.9rem}

/* Task status */
.st-task-status{background:#fafaf9;border:1px solid var(--border);border-radius:6px;padding:8px 10px;margin-bottom:12px;font-size:.72rem;display:none}
.st-task-status.visible{display:block}
.st-task-status .st-task-label{font-weight:600;margin-bottom:2px}
.st-task-status .st-task-progress{color:var(--dim)}
.st-task-status.error{border-color:#fecaca;background:#fef2f2}
.st-task-status.error .st-task-label{color:var(--red)}

/* Hero image + audio preview */
.st-hero-img{width:100%;border-radius:6px;border:1px solid var(--border);margin-bottom:8px;display:none}
.st-hero-img.visible{display:block}
.st-audio{width:100%;margin-bottom:8px;display:none}
.st-audio.visible{display:block}

/* Chart summary */
.st-charts-summary{margin-bottom:10px;padding:8px 10px;background:#fafaf9;border:1px solid var(--border);border-radius:6px;display:none;font-size:.72rem}
.st-charts-summary.visible{display:block}
.st-charts-summary h4{margin:0 0 6px;font-size:.72rem;font-weight:700;color:var(--text)}
.st-charts-summary ol{margin:0;padding-left:18px}
.st-charts-summary li{margin-bottom:4px;line-height:1.4}
.st-charts-summary li strong{color:var(--text)}
.st-charts-summary li span{color:var(--dim)}
body.dark .st-charts-summary{background:#2a2825}

/* Hero preview (below next-bar) */
.st-hero-preview{width:100%;max-height:200px;object-fit:cover;border-radius:8px;border:1px solid var(--border);display:none;flex-shrink:0}
.st-hero-preview.visible{display:block}

/* Markdown editor */
.st-md-toolbar{display:flex;align-items:center;gap:4px;padding:6px 10px;background:var(--card);border-bottom:1px solid var(--border);flex-shrink:0}
.st-md-btn{padding:3px 8px;border:1px solid var(--border);border-radius:4px;background:var(--card);cursor:pointer;font-size:.72rem;font-weight:700;font-family:var(--mono);color:var(--dim)}
.st-md-btn:hover{border-color:var(--accent);color:var(--accent)}
.st-md-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.st-md-wc{margin-left:auto;font-size:.62rem;color:var(--dim);font-family:var(--mono)}
/* Editor area — supports edit/split/preview modes */
.st-md-area{flex:1;overflow:hidden;position:relative;display:flex}
.st-md-area textarea{width:100%;height:100%;border:none;padding:12px 16px;font-size:.82rem;line-height:1.7;font-family:var(--mono);resize:none;background:var(--card);color:var(--text);flex:1}
.st-md-area textarea:focus{outline:none}
.st-md-area iframe{border:none;flex:1;background:#fff}
/* Mode: edit (default) — textarea visible, iframe hidden */
.st-md-area[data-mode="edit"] textarea{display:block;width:100%}
.st-md-area[data-mode="edit"] iframe{display:none}
/* Mode: split — 50/50 side by side */
.st-md-area[data-mode="split"] textarea{display:block;width:50%;border-right:1px solid var(--border)}
.st-md-area[data-mode="split"] iframe{display:block;width:50%}
/* Mode: preview — full-width iframe, textarea hidden */
.st-md-area[data-mode="preview"] textarea{display:none}
.st-md-area[data-mode="preview"] iframe{display:block;width:100%}
/* Mode buttons separator */
.st-md-toolbar .st-mode-sep{width:1px;height:16px;background:var(--border);margin:0 4px}
/* Old preview div — no longer used */
.st-md-preview{display:none}

body.dark .st-table tr:hover{background:#2a2825}
body.dark .st-field input,body.dark .st-field select,body.dark .st-field textarea{background:var(--card);color:var(--text);border-color:var(--border)}
body.dark .st-md-area textarea{background:var(--card);color:var(--text)}
body.dark .st-md-preview{color:var(--text)}
body.dark .st-md-preview code,body.dark .st-md-preview pre{background:#2a2825}
body.dark .st-action-btn{background:var(--card);color:var(--text);border-color:var(--border)}
body.dark .st-action-btn:hover{background:#3a2020;border-color:var(--accent)}
body.dark .st-meta-card{background:var(--card);border-color:var(--border)}
body.dark .st-task-status{background:#2a2825;border-color:var(--border)}
body.dark .st-msg.user{background:#3a2020;border-color:#5a3030}
body.dark .st-msg.assistant{background:var(--card);border-color:var(--border)}
body.dark .st-msg .st-msg-content code,body.dark .st-msg .st-msg-content pre{background:#2a2825}
body.dark .st-chat-input-row{background:var(--card);border-color:var(--border)}
body.dark .st-chat-input-row textarea{background:var(--card);color:var(--text);border-color:var(--border)}
body.dark .st-details-panel{background:#2a2825}
body.dark .st-draft-indicator{background:#1a3a2a;color:#4ade80}
@media(max-width:900px){.st-ed-body{flex-direction:column}.st-ed-left{width:100%;min-width:0;border-right:none;border-bottom:1px solid var(--border);max-height:50vh}.st-ed-right{min-height:300px}.st-details-grid{grid-template-columns:1fr}}
</style></head><body>

<div class="topbar">
  <h1>📡 HFN Promote</h1>
  <div class="r" style="display:flex;align-items:center;gap:10px">
        <span class="sess-indicator" title="X session"><span class="dot off" id="dot-x"></span> 𝕏</span>
        <span class="sess-indicator" title="LinkedIn session"><span class="dot off" id="dot-li"></span> LI</span>
        <span class="sess-indicator" title="Rate limits today" style="margin-left:4px;font-size:.64rem;color:#a8a29e">𝕏 {{xt}}/{{mx}} · LI {{lt}}/{{ml}}</span>
        <button class="btn sm" onclick="toggleDark()" id="dark-btn" style="font-size:.9rem;padding:4px 8px" title="Toggle dark mode">🌙</button>
        <button class="btn sm" onclick="toggleAutoPost()" id="auto-btn"
          style="font-size:.78rem;padding:5px 14px;border-radius:6px;
          {% if sched %}background:#166534;color:#4ade80;border-color:#22863a{% else %}background:#7f1d1d;color:#fca5a5;border-color:#991b1b{% endif %}">
          {{ '✅ Auto-poster ON' if sched else '⏸ Auto-poster OFF' }}
        </button>
      </div>
</div>

<div class="tabs-bar">
  <div class="tab on" data-tab="planner" onclick="stab(this,'planner')">📋 Planner</div>
  <div class="tab" data-tab="review" onclick="stab(this,'review')">📝 Review{% if n_generated > 0 %} ({{n_generated}}){% endif %}</div>
  <div class="tab" data-tab="queue" onclick="stab(this,'queue')">📅 Queue{% if n_queued > 0 %} ({{n_queued}}){% endif %}</div>
  <div class="tab" data-tab="posted" onclick="stab(this,'posted')">✅ Posted{% if np > 0 %} ({{np}}){% endif %}</div>
  <div class="tab" data-tab="library" onclick="stab(this,'library')">📚 Library ({{na}} articles, {{nc}} charts)</div>
  <div class="tab" data-tab="studio" onclick="stab(this,'studio')">✍️ Studio{% if n_drafts > 0 %} ({{n_drafts}}){% endif %}</div>
  <div class="tab" data-tab="settings" onclick="stab(this,'settings')">⚙️</div>
  <div class="tab-actions">
    <button class="btn sm" onclick="act('ingest')">📚 Ingest</button>
    <button class="btn sm" onclick="act('monitor')">📡 Monitor</button>
  </div>
</div>

<div class="main">

<!-- ═══ PLANNER ═══ -->
<div class="tc on" id="t-planner">
<div class="planner">
  <!-- Col 1: What's Hot -->
  <div class="pl-col c1">
    <div class="pl-head">📰 What's Hot <span class="ph-sub">{{news|length}} stories</span><button onclick="refreshNews()" class="btn-sm" style="float:right;font-size:11px;padding:2px 8px;cursor:pointer" title="Refresh news">🔄 Refresh</button></div>
    <div class="pl-body" id="news-list">
      {% for n in news %}
      <div class="ni" id="n-{{n.id}}" onclick="selectNews({{n.id}})" data-id="{{n.id}}">
        <div class="ni-title">
          <a href="{{n.link}}" target="_blank" onclick="event.stopPropagation()" class="ni-link">{{n.title[:80]}}</a>
        </div>
        <div class="ni-meta">
          <span class="ni-score">{{'{:.0f}'.format((n.decayed_score or n.relevance_score or 0)*100)}}%</span>
          <span class="ni-feeds">{{n.feed_name}}</span>
          {% if n.age_days is defined and n.age_days is not none %}
          <span class="ni-age">{% if n.age_days < 0.05 %}just now{% elif n.age_days < 1 %}{{'{:.0f}'.format(n.age_days * 24)}}h ago{% else %}{{'{:.0f}'.format(n.age_days)}}d ago{% endif %}</span>
          {% endif %}
          <button class="btn sm qp-btn" onclick="event.stopPropagation();quickPost({{n.id}})" title="Auto-match best chart, generate, and add to review">⚡ Quick</button>
        </div>
      </div>
      {% endfor %}
      {% if not news %}<div class="tl-empty">Run Monitor first</div>{% endif %}
    </div>
  </div>

  <!-- Col 2: Our Arsenal -->
  <div class="pl-col c2">
    <div class="pl-head">📊 Our Arsenal <span class="ph-sub" id="arsenal-count">Select a story</span></div>
    <div class="pl-body" id="arsenal"></div>
  </div>

  <!-- Col 3: The Plan -->
  <div class="pl-col c3">
    <div class="pl-head">
      📅 The Plan
      <div style="display:flex;gap:4px">
        <button class="btn primary sm" onclick="generatePlan()" id="gen-btn" style="display:none">✍️ Generate All</button>
        <button class="btn rej sm" onclick="clearPlan()" id="clear-btn" style="display:none">Clear</button>
      </div>
    </div>
    <div class="pl-body" id="timeline">
      {% for day in cal_days %}
      <div class="tl-day">
        <div class="tl-dayhead {{ 'today' if day.is_today else '' }}">
          <span>{{ 'Today' if day.is_today else day.label }} {{day.date}}</span>
          <span style="font-size:.65rem;color:var(--dim)" id="day-count-{{day.idx}}">{% if day.posts|length > 0 %}{{day.posts|length}}/{{max_per_day}}{% endif %}</span>
        </div>
        <div class="tl-slots" id="day-{{day.idx}}"
             ondragover="event.preventDefault();this.classList.add('over')"
             ondragleave="this.classList.remove('over')"
             ondrop="dropOnDay(event,{{day.idx}},'{{day.iso}}')">
          {% for sl in day.slots %}
          {% if sl.post %}
          {% set sp = sl.post %}
          {% if sp.status == 'planned' %}
          <div class="tl-slot {{sp.platform}}" id="sl-{{sp.id}}" data-hour="{{sl.hour}}">
            <span class="sl-time">{{sp.time}}</span>
            <span class="plat {{sp.platform}}" style="font-size:.58rem">{{ '𝕏' if sp.platform=='x' else 'LI' }}</span>
            <div class="sl-body">
              <div class="sl-title">{{sp.chart_title[:50] if sp.chart_title else 'Post'}}</div>
              <div class="sl-hook">{{sp.hook[:100] if sp.hook else (sp.caption[:100] if sp.caption else '')}}</div>
            </div>
            <span class="sl-type">{{sp.post_type|upper if sp.post_type else 'SHORT'}}</span>
            <button class="btn sm sl-gen" onclick="generateOne({{sp.id}},this)" title="Generate this post">✍️</button>
            <span class="sl-rm" onclick="removePlan({{sp.id}})">✕</span>
          </div>
          {% else %}
          <div class="tl-slot {{sp.platform}} {{sp.status}}" data-hour="{{sl.hour}}" title="{{sp.status|title}} — managed in {{('Review' if sp.status=='generated' else 'Queue')}} tab">
            <span class="sl-time">{{sp.time}}</span>
            <span class="plat {{sp.platform}}" style="font-size:.58rem">{{ '𝕏' if sp.platform=='x' else 'LI' }}</span>
            <div class="sl-body">
              <div class="sl-title">{{sp.chart_title[:50] if sp.chart_title else 'Post'}}</div>
              <div class="sl-hook">{% if sp.news_title %}📰 {{sp.news_title[:60]}}{% else %}{{sp.hook[:80] if sp.hook else (sp.caption[:80] if sp.caption else '')}}{% endif %}</div>
            </div>
            <span class="sl-type">{{sp.post_type|upper if sp.post_type else 'SHORT'}}</span>
            <span class="sl-badge">{{ '✅ queued' if sp.status=='queued' else '📝 review' }}</span>
          </div>
          {% endif %}
          {% else %}
          <div class="tl-slot-empty" data-hour="{{sl.hour}}"
               ondragover="event.preventDefault();event.stopPropagation();this.classList.add('over')"
               ondragleave="this.classList.remove('over')"
               ondrop="event.stopPropagation();dropOnSlot(event,{{day.idx}},'{{day.iso}}','{{sl.hour}}')">
            <span class="sle-time">{{sl.hour}}</span>
          </div>
          {% endif %}
          {% endfor %}
        </div>
      </div>
      {% endfor %}
    </div>

  </div>
</div>
</div>

<!-- ═══ REVIEW ═══ -->
<div class="tc" id="t-review">
<div class="review-page" id="review-queue">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
    <h2 style="font-family:var(--serif);font-size:1.1rem;font-weight:700">📝 Review <span style="font-family:var(--mono);font-size:.68rem;color:var(--dim);font-weight:500;text-transform:uppercase;letter-spacing:.3px">{{n_generated}} to review</span></h2>
    {% if n_generated > 0 %}<button class="btn bsv" onclick="confirmAll()">✅ Confirm All</button>{% endif %}
  </div>
  {% if not review_days %}
  <div class="empty"><div class="ei">📝</div>No posts awaiting review<br><span style="font-size:.78rem;color:var(--dim)">Generate posts from the Planner tab</span></div>
  {% endif %}
  {% for rd in review_days %}
  <div class="rq-day">
    <div class="rq-dayhead review">
      <span>📝 {{rd.label}} {{rd.date}} — review</span>
      <button class="btn bsv sm" onclick="confirmDay('{{rd.iso}}')">✅ Confirm all</button>
    </div>
    {% for p in rd.posts %}
    <div class="rq-card review" id="rq-{{p.id}}">
      <div class="rq-top">
        <span class="plat {{p.platform}}" style="font-size:.58rem">{{ '𝕏' if p.platform=='x' else 'LI' }}</span>
        <span class="sl-type">{{p.post_type|upper}}</span>
        <span class="rq-time">{{p.time}}</span>
        <span style="flex:1"></span>
        {% if p.news_title %}<span style="font-size:.62rem;color:var(--dim)">📰 {{p.news_title[:40]}}</span>{% endif %}
      </div>
      <div class="post-preview {{p.platform}}">
        <div class="pp-header">
          <div class="pp-avatar">H</div>
          <div class="pp-meta">
            <span class="pp-name">History Future Now</span>
            <span class="pp-handle">{{ '@histfuturenow' if p.platform=='x' else 'historyfuturenow.com' }}</span>
          </div>
        </div>
        <div class="rq-caption" id="rqcap-{{p.id}}" contenteditable="false" ondblclick="startRqEdit(this,{{p.id}})" oninput="updateCharCount(this,{{p.id}})">{{p.caption if p.caption else '(no text)'}}</div>
        {% if p.image_path %}<img class="pp-img" src="{{img_url(p.image_path)}}" onerror="imgFallback(this)">{% endif %}
        {% if p.article_url %}<a class="pp-link" href="{{p.article_url}}" target="_blank">{{p.article_url}}</a>{% endif %}
        <div class="pp-charcount" id="rqcc-{{p.id}}">
          {{(p.caption|length) if p.caption else 0}}/{{280 if p.platform=='x' else 3000}} chars
          {% if p.caption and ((p.platform=='x' and p.caption|length > 280) or (p.platform=='linkedin' and p.caption|length > 3000)) %}
          <span style="color:var(--red)">⚠ Over limit</span>
          {% endif %}
        </div>
      </div>
      {% if p.chart_title %}<div class="rq-chart-title">📊 {{p.chart_title}}</div>{% endif %}
      <div class="rq-actions">
        <button class="btn bsv sm" onclick="confirmPost({{p.id}})">✅ Confirm</button>
        <button class="btn sm" onclick="startRqEdit(document.getElementById('rqcap-{{p.id}}'),{{p.id}})">✏️ Edit</button>
        <button class="btn sm" onclick="regenerateCaption({{p.id}},this)" title="Regenerate caption">🔄</button>
        <button class="btn {{ 'bx' if p.platform=='x' else 'bli' }} sm" onclick="postNow({{p.id}})">📤 Post Now</button>
        <button class="btn rej sm" onclick="removeReview({{p.id}})">✕ Remove</button>
      </div>
    </div>
    {% endfor %}
  </div>
  {% endfor %}
</div>
</div>

<!-- ═══ QUEUE ═══ -->
<div class="tc" id="t-queue">
<div style="padding:16px 20px;height:100%;overflow-y:auto">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
    <h2 style="font-family:var(--serif);font-size:1.1rem;font-weight:700">📅 Queue <span style="font-family:var(--mono);font-size:.68rem;color:var(--dim);font-weight:500;text-transform:uppercase;letter-spacing:.3px">{{n_queued}} scheduled</span></h2>
  </div>
  <div class="qcal">
    {% for day in cal_days %}
    <div class="qcal-day">
      <div class="qcal-dayhead {{ 'today' if day.is_today else '' }}">{{day.label}} {{day.date}}</div>
      <div class="qcal-slots" data-iso="{{day.iso}}" ondragover="event.preventDefault();this.classList.add('over')" ondragleave="this.classList.remove('over')" ondrop="queueDrop(event,this)">
        {% for sl in day.queue_slots %}
          {% if sl.post %}
          {% set p = sl.post %}
          <div class="qcal-card" id="qc-{{p.id}}" data-post-id="{{p.id}}" draggable="true" onclick="if(!window._qcalDragged)this.classList.toggle('expanded')">
            <div class="qcal-meta">
              <span class="qcal-time">{{p.time}}</span>
              <span class="plat {{p.platform}}" style="font-size:.52rem;padding:1px 5px">{{ '𝕏' if p.platform=='x' else 'LI' }}</span>
              <span class="qcal-type">{{p.post_type|upper}}</span>
              <span class="rq-countdown" data-sched="{{day.iso}}T{{p.time}}:00" style="margin-left:auto"></span>
            </div>
            {% if p.article_title %}<div class="qcal-article" title="{{p.article_title}}">{{p.article_title}}</div>{% endif %}
            <div class="qcal-title">{{p.chart_title[:35] if p.chart_title else '—'}}</div>
            {% if p.news_title %}<div class="qcal-hook" title="{{p.news_title}}">📰 {{p.news_title[:50]}}{{'…' if p.news_title|length > 50 else ''}}</div>{% endif %}
            <div class="qcal-detail">
              <div style="margin-bottom:6px">{{p.caption[:200] if p.caption else '(no text)'}}{{'…' if p.caption and p.caption|length > 200 else ''}}</div>
              <div class="qcal-actions">
                <button class="btn {{ 'bx' if p.platform=='x' else 'bli' }} sm" onclick="event.stopPropagation();postNow({{p.id}})">📤 Post Now</button>
                <button class="btn sm" onclick="event.stopPropagation();unqueuePost({{p.id}})">↩ Unqueue</button>
              </div>
            </div>
          </div>
          {% else %}
          <div class="qcal-slot-empty" data-hour="{{sl.hour}}" data-iso="{{day.iso}}"
               ondragover="event.preventDefault();event.stopPropagation();this.classList.add('over')"
               ondragleave="this.classList.remove('over')"
               ondrop="event.stopPropagation();queueDropSlot(event,this,'{{day.iso}}','{{sl.hour}}')">
            <span class="qse-time">{{sl.hour}}</span>
          </div>
          {% endif %}
        {% endfor %}
      </div>
    </div>
    {% endfor %}
  </div>
</div>
</div>

<!-- ═══ POSTED ═══ -->
<div class="tc" id="t-posted">
<div style="padding:16px 20px;overflow-y:auto;height:100%">
  <div class="post-filter-bar">
    <select id="pf-platform" onchange="loadPosted()">
      <option value="">All platforms</option>
      <option value="x">𝕏 only</option>
      <option value="linkedin">LinkedIn only</option>
    </select>
    <select id="pf-days" onchange="loadPosted()">
      <option value="">All time</option>
      <option value="7">Last 7 days</option>
      <option value="30" selected>Last 30 days</option>
      <option value="90">Last 90 days</option>
    </select>
    <span id="pf-count" style="font-size:.72rem;color:var(--dim)"></span>
    <button class="btn sm" onclick="exportPosted()" style="margin-left:auto">📥 Export CSV</button>
  </div>
  <div id="posted-calendar"></div>
  <div style="text-align:center;padding:12px">
    <button class="btn sm" id="pf-more" onclick="loadPostedMore()" style="display:none">Load more</button>
  </div>
</div></div>

<!-- ═══ SETTINGS ═══ -->
<div class="tc" id="t-library">
<div class="lib-wrap">
  <div class="lib-sidebar" id="lib-sidebar">
    <div class="lib-search-box">
      <input type="text" id="lib-search" placeholder="Search articles..." oninput="filterLibrary()">
    </div>
    <div class="lib-filters">
      <select id="lib-filter-issue" class="lib-filter-select" onchange="filterLibrary()">
        <option value="">All issues</option>
        {% for iss in issues %}{% if iss.number in issues_with_articles %}<option value="{{iss.number}}">Issue {{iss.number}} — {{iss.label}} ({{issues_with_articles[iss.number]}})</option>{% endif %}{% endfor %}
      </select>
      <select id="lib-filter-genre" class="lib-filter-select" onchange="filterLibrary()">
        <option value="">All genres</option>
        <option value="global balance of power">Global Balance of Power</option>
        <option value="jobs & economy">Jobs &amp; Economy</option>
        <option value="natural resources">Natural Resources</option>
        <option value="society">Society</option>
      </select>
    </div>
    <div class="lib-stats" style="display:flex;justify-content:space-between;align-items:center">
      <span>{{articles_with_charts|length}} articles · {{total_charts}} charts ({{total_images}} with images)</span>
      <select id="heatmap-sort" style="font-size:.6rem;padding:2px 4px;border:1px solid var(--border);border-radius:4px;font-family:inherit;display:none" onchange="toggleHeatmap(true)">
        <option value="most">Most used</option>
        <option value="least">Least used</option>
        <option value="alpha">Alphabetical</option>
      </select>
      <button class="btn sm" onclick="toggleHeatmap()" id="heatmap-btn" style="font-size:.6rem">🔥 Heatmap</button>
    </div>
    <div class="lib-list" id="lib-list">
      {% for a in articles_with_charts %}
      <div class="lib-item" data-slug="{{a.slug}}" onclick="selectArticle('{{a.slug}}')" data-search="{{a.title|lower}} {{a.slug|lower}} {{(a.excerpt or '')|lower}}" data-issue="{{a.issue_num}}" data-genre="{{(a.part or '')|lower}}">
        <div class="lib-item-title">{{a.title}}</div>
        <div class="lib-item-meta">
          {% if a.part %}<span class="lib-part">{{a.part}}</span>{% endif %}
          <span>📊 {{a.image_count or 0}} charts</span>
          {% if a.chart_count and not a.image_count %}<span style="color:var(--dim)">(text only)</span>{% endif %}
          <span class="lib-post-count {{ 'has-posts' if a.post_count > 0 else 'no-posts' }}">📤 {{a.post_count}}</span>
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
  <div class="lib-detail" id="lib-detail">
    <div class="lib-placeholder">
      <div style="font-size:2.5rem;margin-bottom:12px">📚</div>
      <div style="font-size:.9rem;font-weight:600;margin-bottom:6px">Your Content Library</div>
      <div style="font-size:.78rem;color:var(--dim);max-width:360px;line-height:1.5">
        {{articles_with_charts|length}} articles with {{total_charts}} charts from History Future Now.
        Click an article to see its charts — these are what get matched to breaking news.
      </div>
    </div>
  </div>
</div>
</div>

<!-- ═══ ARTICLE STUDIO ═══ -->
<div class="tc" id="t-studio">
  <!-- List view (default) -->
  <div class="st-wrap" id="st-list">
    <div class="st-header">
      <h2>Article Studio</h2>
      <span style="font-size:.68rem;color:var(--dim);font-family:var(--mono);background:var(--surface);padding:3px 8px;border-radius:4px;border:1px solid var(--border)">claude-opus-4-6</span>
      <button class="btn primary" onclick="studioNewDraft()">✚ New Article</button>
    </div>
    {% if studio_drafts %}
    <div class="st-pills">
      {% set stages = {'draft':0,'factcheck':0,'charts':0,'images':0,'review':0,'deployed':0} %}
      {% for d in studio_drafts %}{% if stages.update({d.stage: stages[d.stage]+1}) %}{% endif %}{% endfor %}
      {% for s,c in stages.items() %}{% if c > 0 %}
      <span class="st-pill {{s}}">{{s}} {{c}}</span>
      {% endif %}{% endfor %}
    </div>
    <table class="st-table">
      <thead><tr><th>Title</th><th>Section</th><th>Stage</th><th>Assets</th><th>Words</th><th>Updated</th><th></th></tr></thead>
      <tbody>
      {% for d in studio_drafts %}
      <tr id="st-row-{{d.id}}">
        <td><a class="st-title-link" onclick="studioSelectDraft({{d.id}})">{{d.title}}</a></td>
        <td style="font-size:.72rem;color:var(--dim)">{{d.section or '—'}}</td>
        <td><span class="st-badge {{d.stage}}">{{d.stage}}</span></td>
        <td class="st-assets">
          <span class="{{'on' if d.has_hero_image else 'dim'}}" title="Hero image">🖼</span>
          <span class="{{'on' if d.has_audio else 'dim'}}" title="Audio">🔊</span>
        </td>
        <td style="font-size:.72rem;font-family:var(--mono)">{{d.word_count|default(0)}}</td>
        <td style="font-size:.65rem;color:var(--dim)">{{d.updated_at[:16] if d.updated_at else ''}}</td>
        <td><span class="st-del" onclick="studioDeleteDraft({{d.id}},'{{d.title|e}}')" title="Delete">×</span></td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
    {% else %}
    <div class="st-empty">
      <div class="st-icon">✍️</div>
      <div style="font-size:.9rem;font-weight:600;margin-bottom:6px">No articles yet</div>
      <div style="font-size:.78rem;color:var(--dim);max-width:360px;line-height:1.5">
        Click "New Article" to start writing. Pipeline: Draft → Fact-Check → Charts → Image → Build → Deploy.
      </div>
    </div>
    {% endif %}
  </div>

  <!-- Editor view (shown when draft selected) -->
  <div class="st-editor" id="st-editor" style="display:none">
    <div class="st-ed-top">
      <span class="st-back" onclick="studioBack()">←</span>
      <span class="st-ed-title" id="st-ed-title"></span>
      <span class="st-ed-slug" id="st-ed-slug"></span>
      <span class="st-ed-save" id="st-ed-save"></span>
    </div>
    <div class="st-stepper">
      <div class="st-step"><div class="st-step-dot" id="st-dot-0">1</div><div class="st-step-label">Draft</div></div>
      <div class="st-step-line" id="st-line-0"></div>
      <div class="st-step"><div class="st-step-dot" id="st-dot-1">2</div><div class="st-step-label">Fact-Check</div></div>
      <div class="st-step-line" id="st-line-1"></div>
      <div class="st-step"><div class="st-step-dot" id="st-dot-2">3</div><div class="st-step-label">Charts</div></div>
      <div class="st-step-line" id="st-line-2"></div>
      <div class="st-step"><div class="st-step-dot" id="st-dot-3">4</div><div class="st-step-label">Image</div></div>
      <div class="st-step-line" id="st-line-3"></div>
      <div class="st-step"><div class="st-step-dot" id="st-dot-4">5</div><div class="st-step-label">Build</div></div>
      <div class="st-step-line" id="st-line-4"></div>
      <div class="st-step"><div class="st-step-dot" id="st-dot-5">6</div><div class="st-step-label">Deploy</div></div>
    </div>
    <div class="st-next-bar" id="st-next-bar" style="display:none">
      <span class="st-next-text" id="st-next-text"></span>
      <span id="st-next-btns"></span>
    </div>
    <img class="st-hero-preview" id="st-hero-preview" src="" onerror="this.classList.remove('visible')">
    <div class="st-ed-body">
      <!-- Left panel: chat -->
      <div class="st-ed-left">
        <div class="st-chat">
          <div class="st-chat-messages" id="st-chat-messages"></div>
          <div class="st-chat-input-row">
            <textarea id="st-chat-input" rows="1" placeholder="Discuss your article idea..." oninput="this.style.height='auto';this.style.height=Math.min(this.scrollHeight,120)+'px'" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();studioSendChat()}"></textarea>
            <button id="st-chat-send" class="btn primary" onclick="studioSendChat()">→</button>
          </div>
        </div>
      </div>

      <!-- Right panel: markdown editor -->
      <div class="st-ed-right">
        <div class="st-md-toolbar">
          <button class="st-md-btn" onclick="studioInsert('**','**')" title="Bold">B</button>
          <button class="st-md-btn" onclick="studioInsert('*','*')" title="Italic"><em>I</em></button>
          <button class="st-md-btn" onclick="studioInsert('\n## ','\n')" title="Heading">H2</button>
          <button class="st-md-btn" onclick="studioInsert('[','](url)')" title="Link">🔗</button>
          <span class="st-mode-sep"></span>
          <button class="st-md-btn active" id="st-mode-edit" onclick="studioSetMode('edit')" title="Editor only">Edit</button>
          <button class="st-md-btn" id="st-mode-split" onclick="studioSetMode('split')" title="Editor + Preview">Split</button>
          <button class="st-md-btn" id="st-mode-preview" onclick="studioSetMode('preview')" title="Preview only">Preview</button>
          <span class="st-mode-sep"></span>
          <button class="st-md-btn" id="st-details-btn" onclick="studioToggleDetails()" title="Metadata & Pipeline">Details</button>
          <span class="st-md-wc" id="st-md-wc">0 words</span>
        </div>

        <!-- Collapsible metadata & pipeline panel -->
        <div class="st-details-panel" id="st-details-panel">
          <div class="st-details-grid">
            <div class="st-field">
              <label>Title</label>
              <input type="text" id="st-f-title" onchange="studioAutoSave()" oninput="studioAutoSave();studioSchedulePreviewUpdate()">
            </div>
            <div class="st-field">
              <label>Section</label>
              <select id="st-f-section" onchange="studioAutoSave();studioSchedulePreviewUpdate()">
                <option value="">— None —</option>
                <option value="Geopolitics">Geopolitics</option>
                <option value="Economics">Economics</option>
                <option value="Technology">Technology</option>
                <option value="Society">Society</option>
                <option value="Environment">Environment</option>
                <option value="History">History</option>
              </select>
            </div>
            <div class="st-field">
              <label>Excerpt</label>
              <textarea id="st-f-excerpt" rows="2" onchange="studioAutoSave()" oninput="studioAutoSave();studioSchedulePreviewUpdate()"></textarea>
            </div>
            <div class="st-field">
              <label>Share Summary</label>
              <textarea id="st-f-share" rows="1" maxlength="140" onchange="studioAutoSave()" oninput="studioShareCount()"></textarea>
              <div class="st-char-count" id="st-share-count">0/140</div>
            </div>
            <div class="st-field">
              <label>Image Prompt</label>
              <textarea id="st-f-imgprompt" rows="2" placeholder="Describe the hero image style..." onchange="studioAutoSave()" oninput="studioAutoSave()"></textarea>
            </div>
          </div>
          <div class="st-charts-summary" id="st-charts-summary"></div>
          <div class="st-details-actions">
            <button class="st-action-btn" onclick="studioAction('save_to_disk')"><span class="st-act-icon">💾</span> Save to Disk</button>
            <button class="st-action-btn" onclick="studioAction('generate_image')"><span class="st-act-icon">🖼</span> Generate Image</button>
            <button class="st-action-btn" onclick="studioAction('generate_audio')"><span class="st-act-icon">🔊</span> Generate Audio</button>
            <button class="st-action-btn" onclick="studioAction('build')"><span class="st-act-icon">🔨</span> Build for Deploy</button>
            <button class="st-action-btn" onclick="studioAction('deploy')"><span class="st-act-icon">🚀</span> Deploy</button>
          </div>
          <div class="st-task-status" id="st-task-status">
            <div class="st-task-label" id="st-task-label">Running...</div>
            <div class="st-task-progress" id="st-task-progress"></div>
          </div>
          <img class="st-hero-img" id="st-hero-img" src="" onerror="this.classList.remove('visible')">
          <audio class="st-audio" id="st-audio" controls src=""></audio>
        </div>

        <div class="st-md-area" data-mode="edit" id="st-md-area">
          <textarea id="st-md-textarea" placeholder="Start writing your article..." oninput="studioAutoSave();studioUpdateWc();studioSchedulePreviewUpdate()"></textarea>
          <iframe id="st-preview-iframe" sandbox="allow-scripts allow-same-origin"></iframe>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- ═══ SETTINGS (actual) ═══ -->
<div class="tc" id="t-settings">
<div style="padding:16px 20px">
  <div style="display:flex;gap:8px;margin-bottom:16px">
    <button class="btn sm" onclick="act('schedule')">{{ '⏹ Stop' if sched else '▶ Start' }} Auto-Post</button>
    <button class="btn sm" onclick="act('ingest')">🔄 Ingest</button>
  </div>
  <h3 style="font-size:.85rem;margin-bottom:8px">Auto-poster Status</h3>
  <div id="auto-status" style="background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:16px;font-size:.78rem">
    <div style="display:flex;gap:16px;flex-wrap:wrap">
      <div><strong>Scheduler:</strong> <span id="as-sched">—</span></div>
      <div><strong>Queue:</strong> <span id="as-queue">—</span></div>
      <div><strong>Next post:</strong> <span id="as-next">—</span></div>
    </div>
    <div style="margin-top:6px"><strong>Last result:</strong> <span id="as-last">—</span></div>
  </div>
  <h3 style="font-size:.85rem;margin-bottom:8px">Activity</h3>
  <div class="logbox" style="margin:0">
    {% for e in alog %}<div class="logr"><span class="logt">{{e.t}}</span>{{e.m}}</div>{% endfor %}
    {% if not alog %}<div style="color:var(--dim)">—</div>{% endif %}
  </div>
</div></div>

</div><!-- /main -->

<div class="toast" id="toast"></div>
<div id="lightbox" onclick="closeLightbox()"><img id="lb-img" src=""></div>
<script>
// ── Globals ──
let dragData = null;
let pendingRemove = null;
let rqFocusIdx = -1;

// ── Image fallback ──
function imgFallback(img){const d=document.createElement('div');d.className='img-fallback';d.innerHTML='🖼 Image not available';img.parentNode.replaceChild(d,img)}

// ── Tabs ──
function stab(el,id){document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));document.querySelectorAll('.tc').forEach(t=>t.classList.remove('on'));el.classList.add('on');document.getElementById('t-'+id).classList.add('on')}
function toast(m,d,persist){const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),d||3000);if(persist)sessionStorage.setItem('hfn-toast',m)}
(function(){const pt=sessionStorage.getItem('hfn-toast');if(pt){sessionStorage.removeItem('hfn-toast');toast(pt,3000)}})();
async function act(a){toast('Running '+a+'...',10000);const r=await fetch('/api/act',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({a})});const d=await r.json();toast(d.msg||'Done',3000,true);setTimeout(()=>location.reload(),1500)}
function refreshNews(){act('monitor')}

// ── Planner: Col 1 — News Selection ──
async function selectNews(newsId){
  document.querySelectorAll('.ni').forEach(n=>n.classList.remove('sel'));
  const el=document.getElementById('n-'+newsId);if(el)el.classList.add('sel');
  // Fetch matching charts from server
  const box=document.getElementById('arsenal');
  document.getElementById('arsenal-count').textContent='loading...';
  box.innerHTML='<div class="tl-empty">Loading charts...</div>';
  try{
    const r=await fetch('/api/arsenal/'+newsId);
    const matches=await r.json();
    const hasCharts=matches.some(m=>!m.text_only);
    document.getElementById('arsenal-count').textContent=hasCharts?matches.length+' chart(s)':'text-only article';
    box.innerHTML=matches.map(m=>`
      <div class="ai${m.text_only?' text-only':''}" draggable="true" ondragstart="startDrag(event,${JSON.stringify(m).replace(/"/g,'&quot;')})"
           data-news="${m.news_id}" data-chart="${m.chart_id}">
        ${m.image_url?'<img class="ai-img" src="'+m.image_url+'" onerror="imgFallback(this)">':''}
        ${m.text_only?'<div style="padding:20px 16px 12px;text-align:center"><div style="font-size:2rem">📝</div><div style="font-size:.7rem;color:var(--dim);margin-top:4px">Text-only post (no chart image)</div></div>':''}
        <div class="ai-body">
          <div class="ai-article">📄 ${m.article_part?'Part '+m.article_part+': ':''}${m.article_title||''}</div>
          ${!m.text_only?'<div class="ai-chart">📊 '+(m.chart_title||m.title||'')+'</div>':''}
          ${m.description?'<div style="font-size:.7rem;color:var(--dim);margin-bottom:4px;line-height:1.35">'+m.description.substring(0,200)+'</div>':''}
          <div class="ai-hook">${m.hook||'Drag to add to plan →'}</div>
          <div class="ai-opts">
            <span class="opt-pill x-sel" data-v="x" onclick="togglePill(this)">𝕏</span>
            <span class="opt-pill${(['Jobs & Economy','Natural Resources'].includes(m.article_part))?' li-sel':''}" data-v="li" onclick="togglePill(this)" ${!['Jobs & Economy','Natural Resources'].includes(m.article_part)?'title="Political articles are not posted on LinkedIn"':''}>${['Jobs & Economy','Natural Resources'].includes(m.article_part)?'LinkedIn':'<s>LinkedIn</s>'}</span>
            <span class="opt-pill sel" data-v="short" onclick="togglePill(this)">Short</span>
            <span class="opt-pill" data-v="long" onclick="togglePill(this)">Long</span>
          </div>
        </div>
      </div>`).join('');
  }catch(e){box.innerHTML='<div class="tl-empty">Error loading charts</div>';}
}
function togglePill(el){
  const v=el.dataset.v;
  if(v==='x'||v==='li'){el.classList.toggle(v+'-sel')}
  else if(v==='short'||v==='long'){
    const sibs=el.parentElement.querySelectorAll('[data-v=short],[data-v=long]');
    sibs.forEach(s=>s.classList.remove('sel'));el.classList.add('sel');
  }
}

// ── Planner: Drag & Drop ──
function startDrag(event,match){
  const card=event.target.closest('.ai');
  const platforms=[];
  card.querySelectorAll('.opt-pill.x-sel').forEach(()=>platforms.push('x'));
  card.querySelectorAll('.opt-pill.li-sel').forEach(()=>platforms.push('linkedin'));
  const postType=card.querySelector('.opt-pill.sel[data-v=short]')?'short':'long';
  dragData={...match,platforms,post_type:postType};
  event.dataTransfer.effectAllowed='copy';
  event.dataTransfer.setData('text/plain','');
}
const MAX_PER_DAY={{max_per_day}};
function dropOnDay(event,dayIdx,dayIso){
  event.preventDefault();
  const el=document.getElementById('day-'+dayIdx);
  el.classList.remove('over');
  if(!dragData)return;
  const filled=el.querySelectorAll('.tl-slot').length;
  if(filled+dragData.platforms.length>MAX_PER_DAY){toast('Daily limit reached ('+MAX_PER_DAY+' posts)');dragData=null;return;}
  // Find first empty slot
  const emptySlot=el.querySelector('.tl-slot-empty');
  const time=emptySlot?emptySlot.dataset.hour:'22:00';
  for(const plat of dragData.platforms){
    addToPlan(dragData,plat,dragData.post_type,dayIso,time,dayIdx);
  }
  dragData=null;
updateGenButton();
}
function dropOnSlot(event,dayIdx,dayIso,hour){
  event.preventDefault();
  const el=document.getElementById('day-'+dayIdx);
  const slotEl=event.currentTarget;
  slotEl.classList.remove('over');
  if(!dragData)return;
  const filled=el.querySelectorAll('.tl-slot').length;
  if(filled+dragData.platforms.length>MAX_PER_DAY){toast('Daily limit reached ('+MAX_PER_DAY+' posts)');dragData=null;return;}
  for(const plat of dragData.platforms){
    addToPlan(dragData,plat,dragData.post_type,dayIso,hour,dayIdx);
  }
  dragData=null;
  updateGenButton();
}
async function addToPlan(match,platform,postType,dayIso,time,dayIdx){
  const schedAt=dayIso+'T'+time;
  const r=await fetch('/api/plan_add',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({news_id:match.news_id,chart_id:match.chart_id,article_id:match.article_id,
      platform,post_type:postType,scheduled_at:schedAt,image_path:match.image_path||'',
      article_url:match.article_url||'',hook:match.hook||''})});
  const d=await r.json();
  if(d.ok){
    const el=document.getElementById('day-'+dayIdx);
    // Replace the empty slot placeholder for this time
    const emptySlot=el.querySelector(`.tl-slot-empty[data-hour="${time}"]`);
    const newHtml=`<div class="tl-slot ${platform}" id="sl-${d.id}" data-hour="${time}">
      <span class="sl-time">${time}</span>
      <span class="plat ${platform}" style="font-size:.58rem">${platform==='x'?'𝕏':'LI'}</span>
      <div class="sl-body">
        <div class="sl-title">${match.chart_title||match.title||'Post'}</div>
        <div class="sl-hook">${(match.hook||'').substring(0,100)}</div>
      </div>
      <span class="sl-type">${postType.toUpperCase()}</span>
      <button class="btn sm sl-gen" onclick="generateOne(${d.id},this)" title="Generate this post">✍️</button>
      <span class="sl-rm" onclick="removePlan(${d.id})">✕</span></div>`;
    if(emptySlot){emptySlot.insertAdjacentHTML('afterend',newHtml);emptySlot.remove();}
    else{el.insertAdjacentHTML('beforeend',newHtml);}
    toast('Added to plan');
    // Update count
    const cnt=el.querySelectorAll('.tl-slot').length;
    const cntEl=document.getElementById('day-count-'+dayIdx);
    if(cntEl)cntEl.textContent=cnt+'/'+MAX_PER_DAY;
  } else {
    toast(d.msg||'Failed to add');
  }
}
async function removePlan(id){
  await fetch('/api/plan_remove',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
  const el=document.getElementById('sl-'+id);
  if(el){
    const hour=el.dataset.hour;
    const parent=el.closest('.tl-slots');
    // Insert empty slot placeholder back
    const ph=document.createElement('div');ph.className='tl-slot-empty';ph.dataset.hour=hour;
    ph.setAttribute('ondragover',"event.preventDefault();event.stopPropagation();this.classList.add('over')");
    ph.setAttribute('ondragleave',"this.classList.remove('over')");
    const dayIdx=parent.id.replace('day-','');
    const dayIso=parent.closest('.tl-day').querySelector('.tl-dayhead span').nextElementSibling||'';
    ph.innerHTML=`<span class="sle-time">${hour}</span>`;
    el.replaceWith(ph);
    // Update count
    const cnt=parent.querySelectorAll('.tl-slot').length;
    const cntEl=document.getElementById('day-count-'+dayIdx);
    if(cntEl)cntEl.textContent=cnt>0?cnt+'/'+MAX_PER_DAY:'';
  }
updateGenButton();toast('Removed');
}
function updateGenButton(){
  const slots=document.querySelectorAll('.tl-slot').length;
  document.getElementById('gen-btn').style.display=slots>0?'':'none';
  document.getElementById('clear-btn').style.display=slots>0?'':'none';
}
async function generatePlan(){
  const slots=document.querySelectorAll('.tl-slot');
  if(!slots.length)return;
  if(!confirm('Generate post text for '+slots.length+' planned items? This uses Opus credits.'))return;
  const btn=document.getElementById('gen-btn');
  btn.disabled=true;
  let done=0,failed=0,total=slots.length;
  btn.textContent='⏳ 0/'+total+'...';
  for(const slot of slots){
    const id=parseInt(slot.id.replace('sl-',''));
    if(!id){failed++;done++;btn.textContent='⏳ '+done+'/'+total+'...';continue;}
    try{
      const r=await fetch('/api/plan_generate_one',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
      const d=await r.json();
      done++;
      if(d.ok){slot.style.opacity='.4';slot.insertAdjacentHTML('afterbegin','<span style="color:var(--grn);font-weight:700;margin-right:4px">✓</span>');}
      else{failed++;slot.style.borderColor='var(--red)';}
    }catch(e){done++;failed++;slot.style.borderColor='var(--red)';}
    btn.textContent='⏳ '+done+'/'+total+'...';
  }
  if(failed===0)toast('All '+total+' generated',3000,true);
  else toast('Generated '+(total-failed)+'/'+total+' — '+failed+' failed',5000,true);
  setTimeout(()=>location.reload(),1500);
}
async function generateOne(id,btn){
  btn.disabled=true;btn.textContent='⏳';
  toast('Generating...',30000);
  const r=await fetch('/api/plan_generate_one',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
  const d=await r.json();
  toast(d.msg||'Done');
  if(d.ok){setTimeout(()=>location.reload(),1000);}
  else{btn.disabled=false;btn.textContent='✍️';}
}
async function clearPlan(){
  if(!confirm('Clear the entire plan?'))return;
  await fetch('/api/plan_clear',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({})});
  toast('Cleared',3000,true);setTimeout(()=>location.reload(),800);
}

// ── Review & Queue ──
async function confirmPost(id){
  await fetch('/api/confirm_post',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
  toast('Confirmed — queued for posting',3000,true);setTimeout(()=>location.reload(),800);
}
async function confirmAll(){
  if(!confirm('Confirm all generated posts?'))return;
  await fetch('/api/confirm_all',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({})});
  toast('All confirmed — queued for posting',3000,true);setTimeout(()=>location.reload(),800);
}
async function confirmDay(iso){
  if(!confirm('Confirm all posts for '+iso+'?'))return;
  await fetch('/api/confirm_day',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({date:iso})});
  toast('Day confirmed',3000,true);setTimeout(()=>location.reload(),800);
}
async function unqueuePost(id){
  await fetch('/api/unqueue_post',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
  toast('Moved back to review',3000,true);setTimeout(()=>location.reload(),800);
}
async function removeReview(id){
  // If another remove is pending, execute it immediately
  if(pendingRemove){clearTimeout(pendingRemove.timeout);fetch('/api/plan_remove',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:pendingRemove.id})});pendingRemove=null}
  const card=document.getElementById('rq-'+id);if(!card)return;
  card.style.display='none';
  const t=document.getElementById('toast');
  t.innerHTML='Removed — <a onclick="undoRemove()">Undo</a>';t.classList.add('show');
  pendingRemove={id,card,timeout:setTimeout(()=>{
    fetch('/api/plan_remove',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
    card.remove();pendingRemove=null;t.classList.remove('show');
  },5000)};
}
function undoRemove(){
  if(!pendingRemove)return;clearTimeout(pendingRemove.timeout);
  pendingRemove.card.style.display='';pendingRemove=null;
  const t=document.getElementById('toast');t.classList.remove('show');toast('Restored');
}
function startRqEdit(el,id){
  el.contentEditable='true';el.style.webkitLineClamp='unset';el.focus();
  const card=el.closest('.rq-card');
  const acts=card?card.querySelector('.rq-actions'):null;
  if(acts&&!document.getElementById('rqsv-'+id)){
    const s=document.createElement('button');s.id='rqsv-'+id;s.className='btn bsv sm';
    s.textContent='💾 Save';s.onclick=()=>saveRqEdit(id);acts.prepend(s);
  }
}
async function saveRqEdit(id){
  const el=document.getElementById('rqcap-'+id);
  el.contentEditable='false';document.getElementById('rqsv-'+id)?.remove();
  await fetch('/api/edit',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id,caption:el.innerText.trim()})});
  toast('Saved');
}

// ── Library ──
function filterLibrary(){
  const q=(document.getElementById('lib-search').value||'').toLowerCase();
  const issue=document.getElementById('lib-filter-issue').value;
  const genre=document.getElementById('lib-filter-genre').value;
  let shown=0;
  document.querySelectorAll('.lib-item').forEach(el=>{
    const matchText=!q||el.dataset.search.includes(q);
    const matchIssue=!issue||el.dataset.issue===issue;
    const matchGenre=!genre||el.dataset.genre===genre;
    const vis=matchText&&matchIssue&&matchGenre;
    el.style.display=vis?'':'none';
    if(vis)shown++;
  });
  // Update stats count
  const total=document.querySelectorAll('.lib-item').length;
  const statsEl=document.querySelector('.lib-stats span');
  if(statsEl&&(q||issue||genre)){
    statsEl.textContent=shown+' of '+total+' articles';
  }
}
async function selectArticle(slug){
  document.querySelectorAll('.lib-item').forEach(el=>el.classList.remove('sel'));
  document.querySelector(`.lib-item[data-slug="${slug}"]`)?.classList.add('sel');
  const detail=document.getElementById('lib-detail');
  detail.innerHTML='<div class="lib-placeholder"><div>Loading...</div></div>';
  try{
    const r=await fetch('/api/library/'+encodeURIComponent(slug));
    const d=await r.json();
    // Get post count from sidebar item
    const sideItem=document.querySelector(`.lib-item[data-slug="${slug}"]`);
    const postCount=sideItem?sideItem.querySelector('.lib-post-count')?.textContent.replace(/[^0-9]/g,''):'0';
    const issueNum=sideItem?sideItem.dataset.issue:'';
    let html=`<div class="lib-article-head">
      <h2>${d.article.title}${d.article.part?' <span class="lib-part">'+d.article.part+'</span>':''}</h2>
      ${d.article.excerpt?'<div class="lib-excerpt">'+d.article.excerpt+'</div>':''}
      ${d.article.url?'<a class="lib-url" href="'+d.article.url+'" target="_blank">'+d.article.url+'</a>':''}
      <div style="font-size:.7rem;color:var(--dim);margin-top:6px;display:flex;align-items:center;gap:10px">
        <span>${d.charts.length} chart(s) · ${d.charts.filter(c=>c.image_path).length} with images · 📤 ${postCount} post(s)${issueNum?' · Issue '+issueNum:''}</span>
        ${d.charts.some(c=>c.image_path)?'<select id="lib-post-type" style="padding:4px 6px;border:1px solid var(--border);border-radius:5px;font-size:.68rem;font-family:inherit"><option value="short">Short</option><option value="long">Long</option></select><button class="lib-promote-btn" onclick="promoteArticle(\''+slug+'\',null,this)">⚡ Promote</button>':''}
      </div>
    </div>`;
    if(d.charts.length){
      html+='<div class="lib-charts-grid">';
      for(const c of d.charts){
        html+=`<div class="lib-chart-card">
          ${c.image_url?'<img src="'+c.image_url+'" onerror="imgFallback(this)">':'<div style="padding:30px;text-align:center;color:var(--dim)">No image</div>'}
          <div class="lib-chart-body">
            <div class="lib-chart-title">Fig ${c.figure_num}: ${c.title||'Untitled'}</div>
            ${c.description?'<div class="lib-chart-desc">'+c.description.substring(0,200)+'</div>':''}
            ${c.source?'<div class="lib-chart-source">Source: '+c.source+'</div>':''}
            <div class="lib-chart-tags">
              <span class="lib-chart-tag">ID: ${c.id}</span>
              ${c.image_path?'<span class="lib-chart-tag" style="background:#dcfce7;color:#166534">✓ Image</span>':'<span class="lib-chart-tag" style="background:#fef2f2;color:#991b1b">✕ No image</span>'}
              ${c.times_used>0?'<span class="lib-chart-tag" style="background:#ede9fe;color:#5b21b6">Used '+c.times_used+'x</span>':''}
              ${c.image_path?'<button class="lib-chart-promote" onclick="event.stopPropagation();promoteArticle(\''+slug+'\','+c.id+',this)">📤 Promote</button>':''}
            </div>
          </div>
        </div>`;
      }
      html+='</div>';
    }else{
      html+='<div class="lib-placeholder" style="height:auto;padding:40px"><div style="font-size:1.5rem">📝</div><div>Text-only article — no charts</div></div>';
    }
    detail.innerHTML=html;
  }catch(e){detail.innerHTML='<div class="lib-placeholder"><div>Error loading article</div></div>';}
}

async function promoteArticle(slug,chartId,btn){
  if(btn){btn.disabled=true;btn.textContent='⏳ Generating...';}
  const postType=(document.getElementById('lib-post-type')||{}).value||'short';
  toast('Generating '+postType+' posts from article...',30000);
  try{
    const r=await fetch('/api/promote_article',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({slug,chart_id:chartId||null,post_type:postType})});
    const d=await r.json();
    if(d.ok){toast(d.msg,4000,true);if(btn){btn.textContent='✓ Done';}setTimeout(()=>{document.querySelector('.tab[data-tab="review"]')?.click()},1500);}
    else{toast(d.msg||'Failed',4000);if(btn){btn.disabled=false;btn.textContent='⚡ Promote';}}
  }catch(e){toast('Network error',3000);if(btn){btn.disabled=false;btn.textContent='⚡ Promote';}}
}

// ── Regenerate caption ──
async function regenerateCaption(id,btn){
  btn.disabled=true;btn.textContent='⏳';
  toast('Regenerating caption...',30000);
  const r=await fetch('/api/plan_generate_one',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
  const d=await r.json();
  if(d.ok){toast(d.msg||'Regenerated',3000,true);setTimeout(()=>location.reload(),1000);}
  else{toast(d.msg||'Failed');btn.disabled=false;btn.textContent='🔄';}
}

// ── Heatmap ──
let heatmapVisible=false;
async function toggleHeatmap(forceRefresh){
  const detail=document.getElementById('lib-detail');
  const sortSel=document.getElementById('heatmap-sort');
  if(heatmapVisible&&!forceRefresh){
    heatmapVisible=false;detail.innerHTML='<div class="lib-placeholder"><div style="font-size:2.5rem;margin-bottom:12px">📚</div><div style="font-size:.9rem;font-weight:600">Select an article</div></div>';
    document.getElementById('heatmap-btn').style.background='';sortSel.style.display='none';return;
  }
  heatmapVisible=true;document.getElementById('heatmap-btn').style.background='#fef3c7';sortSel.style.display='';
  detail.innerHTML='<div class="lib-placeholder"><div>Loading heatmap...</div></div>';
  try{
    const r=await fetch('/api/chart_usage');let stats=await r.json();
    const sort=sortSel.value;
    if(sort==='least')stats.sort((a,b)=>(a.uses_30d||0)-(b.uses_30d||0));
    else if(sort==='alpha')stats.sort((a,b)=>(a.title||'').localeCompare(b.title||''));
    else stats.sort((a,b)=>(b.uses_30d||0)-(a.uses_30d||0));
    let html='<div style="padding:12px"><h3 style="font-size:.85rem;margin-bottom:8px">Chart Usage Heatmap <span style="font-size:.65rem;color:var(--dim)">(30 days)</span></h3>';
    html+='<div style="font-size:.65rem;color:var(--dim);margin-bottom:8px">🟢 unused → 🟡 light → 🟠 moderate → 🔴 heavy</div>';
    html+='<div class="heatmap-grid">';
    for(const s of stats){
      const u=s.uses_30d||0;const heat=u===0?0:u<=2?1:u<=5?2:3;
      html+=`<div class="hm-card hm-${heat}">
        ${s.image_url?'<img src="'+s.image_url+'" onerror="imgFallback(this)">':'<div style="height:80px;display:flex;align-items:center;justify-content:center;color:var(--dim)">No img</div>'}
        <div class="hm-label">${(s.title||'').substring(0,40)}</div>
        <div style="font-size:.58rem;padding:0 4px 4px;color:var(--dim)">${s.uses_7d||0} (7d) · ${u} (30d)</div>
      </div>`;
    }
    html+='</div></div>';detail.innerHTML=html;
  }catch(e){detail.innerHTML='<div class="lib-placeholder"><div>Error loading heatmap</div></div>';}
}

// ── Post Now ──
async function postNow(id){
  const card=document.getElementById('rq-'+id);
  const platEl=card?card.querySelector('.plat'):null;
  const platName=platEl&&platEl.classList.contains('li')?'LinkedIn':'X';
  if(!confirm('Post to '+platName+' now?'))return;
  toast('Posting to '+platName+'...',15000);const r=await fetch('/api/post_now',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});const d=await r.json();toast(d.msg||'Done',3000,true);if(d.ok)setTimeout(()=>location.reload(),1500)
}

// ── Quick Post ──
async function quickPost(newsId){
  const btn=event.target;btn.disabled=true;btn.textContent='⏳';
  toast('Quick Post: matching chart & generating...',30000);
  try{
    const r=await fetch('/api/quick_post',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({news_id:newsId})});
    const d=await r.json();
    if(d.ok){toast(d.msg||'Quick post created — check Review',3000,true);setTimeout(()=>location.reload(),1500);}
    else{toast(d.msg||'Failed');btn.disabled=false;btn.textContent='⚡ Quick';}
  }catch(e){toast('Error');btn.disabled=false;btn.textContent='⚡ Quick';}
}

// ── Char count ──
function updateCharCount(el,id){
  const cc=document.getElementById('rqcc-'+id);if(!cc)return;
  const len=el.innerText.trim().length;
  const isX=!!el.closest('.post-preview.x')||!!el.closest('.rq-card')?.querySelector('.plat.x');
  const max=isX?280:3000;
  cc.innerHTML=len+'/'+max+' chars'+(len>max?' <span style="color:var(--red)">⚠ Over limit</span>':'');
}

// ── Countdown timers ──
function updateCountdowns(){
  document.querySelectorAll('.rq-countdown').forEach(el=>{
    const sched=new Date(el.dataset.sched);
    const now=new Date();
    const diff=sched-now;
    if(diff<=0){el.textContent='⏰ Due now';el.style.color='#dc2626';el.style.background='#fef2f2';return;}
    const h=Math.floor(diff/3600000);
    const m=Math.floor((diff%3600000)/60000);
    if(h>24){const d=Math.floor(h/24);el.textContent='in '+d+'d '+(h%24)+'h';}
    else if(h>0){el.textContent='in '+h+'h '+m+'m';}
    else{el.textContent='in '+m+'m';}
  });
}
updateCountdowns();setInterval(updateCountdowns,60000);

function toggleAutoPost(){fetch("/api/act",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({a:"schedule"})}).then(r=>r.json()).then(d=>{alert(d.msg||"Toggled");location.reload()})}
updateGenButton();

// ── Posted calendar ──
let postedOffset=0;
async function loadPosted(reset=true){
  if(reset)postedOffset=0;
  const plat=document.getElementById('pf-platform').value;
  const days=document.getElementById('pf-days').value;
  const params=new URLSearchParams();
  if(plat)params.set('platform',plat);
  if(days)params.set('days',days);
  params.set('offset',postedOffset);params.set('limit',50);
  let d;
  try{const r=await fetch('/api/posted?'+params);d=await r.json();}
  catch(e){document.getElementById('posted-calendar').innerHTML='<div class="empty"><div class="ei">⚠️</div>Failed to load posts</div>';return;}
  document.getElementById('pf-count').textContent=d.total+' post(s)';
  const cal=document.getElementById('posted-calendar');
  if(reset)cal.innerHTML='';
  // Group by date
  const byDay={};
  for(const p of d.posts){
    const dt=p.posted_at?p.posted_at.substring(0,10):'unknown';
    if(!byDay[dt])byDay[dt]=[];byDay[dt].push(p);
  }
  for(const[dt,posts] of Object.entries(byDay)){
    let dayEl=document.getElementById('pcal-'+dt);
    if(!dayEl){
      dayEl=document.createElement('div');dayEl.className='post-cal-day';dayEl.id='pcal-'+dt;
      const dayLabel=new Date(dt+'T12:00').toLocaleDateString('en-GB',{weekday:'short',day:'numeric',month:'short'});
      dayEl.innerHTML=`<div class="post-cal-dayhead" onclick="this.nextElementSibling.classList.toggle('open')">
        <span>${dayLabel}</span><span style="font-size:.65rem;color:var(--dim)">${posts.length} post(s)</span>
      </div><div class="post-cal-posts open"></div>`;
      cal.appendChild(dayEl);
    }
    const container=dayEl.querySelector('.post-cal-posts');
    for(const p of posts){
      const time=p.posted_at?p.posted_at.substring(11,16):'';
      const esc=s=>(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      container.innerHTML+=`<div class="post-cal-item">
        <div style="display:flex;flex-direction:column;align-items:center;gap:6px;flex-shrink:0">
          <span class="plat ${p.platform}" style="font-size:.58rem">${p.platform==='x'?'𝕏':'LI'}</span>
          ${p.image_url?'<img src="'+p.image_url+'" onerror="imgFallback(this)">':''}
          <span style="font-size:.62rem;color:var(--dim)">${time}</span>
        </div>
        <div class="post-cal-body">
          ${p.article_title?'<div class="post-cal-article">'+esc(p.article_title)+'</div>':''}
          ${p.chart_title?'<div class="post-cal-chart">'+esc(p.chart_title)+'</div>':''}
          ${p.news_title?'<div class="post-cal-news">📰 '+esc(p.news_title)+(p.news_link?' <a href="'+esc(p.news_link)+'" target="_blank">↗</a>':'')+'</div>':''}
          <div class="post-cal-caption">${esc(p.caption||'(no caption)')}</div>
        </div>
      </div>`;
    }
  }
  // Auto-expand today's date group
  if(reset){
    const today=new Date().toISOString().substring(0,10);
    const todayEl=document.getElementById('pcal-'+today);
    if(todayEl){const posts=todayEl.querySelector('.post-cal-posts');if(posts)posts.classList.add('open')}
  }
  const more=document.getElementById('pf-more');
  more.style.display=(postedOffset+d.posts.length<d.total)?'':'none';
  postedOffset+=d.posts.length;
}
function loadPostedMore(){loadPosted(false)}
// Load posted on tab switch
const origStab=stab;
stab=function(el,id){origStab(el,id);if(id==='posted'&&!document.getElementById('posted-calendar').children.length)loadPosted()};

// ── Session health ──
async function loadSessionStatus(){
  try{
    const r=await fetch('/api/session_status');const d=await r.json();
    document.getElementById('dot-x').className='dot '+(d.x?'on':'off');
    document.getElementById('dot-li').className='dot '+(d.linkedin?'on':'off');
  }catch(e){}
}
loadSessionStatus();setInterval(loadSessionStatus,300000);

// ── Auto-poster status ──
async function loadAutoStatus(){
  try{
    const r=await fetch('/api/autoposter_status');const d=await r.json();
    document.getElementById('as-sched').innerHTML=d.scheduler_on?'<span style="color:var(--grn)">ON</span>':'<span style="color:var(--red)">OFF</span>';
    document.getElementById('as-queue').textContent=d.queue_count+' post(s)';
    if(d.next_post){
      const s=d.next_post.scheduled_at||'';
      document.getElementById('as-next').textContent=(d.next_post.chart_title||'Post #'+d.next_post.id)+' — '+s.replace('T',' ');
    }else{document.getElementById('as-next').textContent='none';}
    const lr=d.last_result;
    if(lr&&lr.time){
      const ok=lr.ok?'✅':'❌';
      document.getElementById('as-last').innerHTML=ok+' '+lr.platform+' #'+lr.post_id+' at '+lr.time.substring(11,16)+(lr.msg?' — '+lr.msg:'');
    }else{document.getElementById('as-last').textContent='no posts yet';}
  }catch(e){}
}
loadAutoStatus();setInterval(loadAutoStatus,60000);

// ── Lightbox ──
function openLightbox(src){document.getElementById('lb-img').src=src;document.getElementById('lightbox').classList.add('open')}
function closeLightbox(){document.getElementById('lightbox').classList.remove('open');document.getElementById('lb-img').src=''}
document.addEventListener('click',e=>{
  const img=e.target.closest('.pp-img,.ai-img,.lib-chart-card img,.post-cal-item img');
  if(img&&img.src){e.preventDefault();openLightbox(img.src)}
});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeLightbox()});

// ── Dark mode ──
function toggleDark(){
  document.body.classList.toggle('dark');
  const isDark=document.body.classList.contains('dark');
  localStorage.setItem('hfn-dark',isDark?'1':'0');
  document.getElementById('dark-btn').textContent=isDark?'☀️':'🌙';
}
if(localStorage.getItem('hfn-dark')==='1'){document.body.classList.add('dark');document.getElementById('dark-btn').textContent='☀️'}

// ── Keyboard shortcuts (Item 1) ──
document.addEventListener('keydown',e=>{
  // Skip if editing or if Planner tab not visible
  if(e.target.isContentEditable||e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA'||e.target.tagName==='SELECT')return;
  if(!document.getElementById('t-review').classList.contains('on'))return;
  const cards=document.querySelectorAll('#review-queue .rq-card');
  if(!cards.length)return;
  if(e.key==='j'){e.preventDefault();rqFocusIdx=Math.min(rqFocusIdx+1,cards.length-1);updateRqFocus(cards)}
  else if(e.key==='k'){e.preventDefault();rqFocusIdx=Math.max(rqFocusIdx-1,0);updateRqFocus(cards)}
  else if(e.key==='c'&&rqFocusIdx>=0&&cards[rqFocusIdx]){const b=cards[rqFocusIdx].querySelector('.rq-actions .btn.bsv');if(b)b.click()}
  else if(e.key==='e'&&rqFocusIdx>=0&&cards[rqFocusIdx]){const b=cards[rqFocusIdx].querySelector('.rq-actions .btn:not(.bsv):not(.rej):not(.bx):not(.bli)');if(b&&b.textContent.includes('Edit'))b.click()}
  else if(e.key==='d'&&rqFocusIdx>=0&&cards[rqFocusIdx]){const b=cards[rqFocusIdx].querySelector('.rq-actions .btn.rej');if(b)b.click()}
  else if(e.key==='p'&&rqFocusIdx>=0&&cards[rqFocusIdx]){const b=cards[rqFocusIdx].querySelector('.rq-actions .btn.bx,.rq-actions .btn.bli');if(b)b.click()}
});
function updateRqFocus(cards){cards.forEach(c=>c.classList.remove('rq-focused'));if(rqFocusIdx>=0&&cards[rqFocusIdx]){cards[rqFocusIdx].classList.add('rq-focused');cards[rqFocusIdx].scrollIntoView({block:'nearest',behavior:'smooth'})}}

// ── Drag reorder timeline (Item 8) ──
document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('.tl-slot').forEach(sl=>{
    sl.draggable=true;
    sl.addEventListener('dragstart',e=>{sl.classList.add('dragging');e.dataTransfer.setData('text/plain',sl.id);e.dataTransfer.effectAllowed='move'});
    sl.addEventListener('dragend',()=>sl.classList.remove('dragging'));
  });
});
async function reorderSlot(slotId,newIso,dayIdx,targetHour){
  const id=parseInt(slotId.replace('sl-',''));
  const target=document.getElementById('day-'+dayIdx);
  // Use targeted hour if provided, otherwise find first empty slot
  let time=targetHour;
  if(!time){const emptySlot=target.querySelector('.tl-slot-empty');time=emptySlot?emptySlot.dataset.hour:'22:00';}
  const scheduledAt=newIso+'T'+time;
  const r=await fetch('/api/plan_reorder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,scheduled_at:scheduledAt})});
  const d=await r.json();
  if(d.ok){
    const slot=document.getElementById(slotId);if(slot){
      slot.querySelector('.sl-time').textContent=time;
      slot.dataset.hour=time;
      // Replace empty slot placeholder at target time
      const emptySlot=target.querySelector(`.tl-slot-empty[data-hour="${time}"]`);
      if(emptySlot){emptySlot.replaceWith(slot);}
      else{target.appendChild(slot);}
    }
    toast('Moved');
  }
}
// Patch dropOnDay to handle reorder drops too
const origDropOnDay=dropOnDay;
dropOnDay=function(event,dayIdx,dayIso){
  const slotId=event.dataTransfer.getData('text/plain');
  if(slotId&&slotId.startsWith('sl-')){
    event.preventDefault();document.getElementById('day-'+dayIdx).classList.remove('over');
    reorderSlot(slotId,dayIso,dayIdx,null);return;
  }
  origDropOnDay(event,dayIdx,dayIso);
};
// Patch dropOnSlot to handle reorder drops too
const origDropOnSlot=dropOnSlot;
dropOnSlot=function(event,dayIdx,dayIso,hour){
  const slotId=event.dataTransfer.getData('text/plain');
  if(slotId&&slotId.startsWith('sl-')){
    event.preventDefault();event.currentTarget.classList.remove('over');
    reorderSlot(slotId,dayIso,dayIdx,hour);return;
  }
  origDropOnSlot(event,dayIdx,dayIso,hour);
};

// ── Queue calendar drag-and-drop ──
window._qcalDragged=false;
document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('.qcal-card').forEach(card=>{
    card.addEventListener('dragstart',e=>{
      window._qcalDragged=true;
      card.classList.add('dragging');
      e.dataTransfer.setData('text/plain','qc-'+card.dataset.postId);
      e.dataTransfer.effectAllowed='move';
    });
    card.addEventListener('dragend',()=>{
      card.classList.remove('dragging');
      setTimeout(()=>{window._qcalDragged=false},50);
    });
  });
});
async function queueDropSlot(event,slotEl,iso,hour){
  event.preventDefault();event.stopPropagation();slotEl.classList.remove('over');
  const raw=event.dataTransfer.getData('text/plain');
  if(!raw||!raw.startsWith('qc-'))return;
  const postId=parseInt(raw.replace('qc-',''));
  const card=document.getElementById('qc-'+postId);if(!card)return;
  const scheduledAt=iso+'T'+hour;
  const r=await fetch('/api/plan_reorder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:postId,scheduled_at:scheduledAt})});
  const d=await r.json();
  if(d.ok){
    const oldSlots=card.closest('.qcal-slots');
    // Replace empty slot with the card
    slotEl.parentNode.insertBefore(card,slotEl);
    slotEl.remove();
    // Restore empty slot in old position if needed
    if(oldSlots){
      const oldIso=oldSlots.dataset.iso;
      const oldTime=card.querySelector('.qcal-time').textContent;
      // Check if we need to add back an empty slot
      const hasCards=oldSlots.querySelector('.qcal-card');
      if(!hasCards){
        // Add back empty slots — page will reload cleanly, just add a placeholder
        const ph=document.createElement('div');ph.className='qcal-slot-empty';
        ph.innerHTML='<span class="qse-time">'+oldTime+'</span>';
        oldSlots.appendChild(ph);
      }
    }
    const timeEl=card.querySelector('.qcal-time');if(timeEl)timeEl.textContent=hour;
    const cdEl=card.querySelector('.rq-countdown');if(cdEl)cdEl.dataset.sched=scheduledAt+':00';
    toast('Moved to '+iso+' '+hour);
  }
}
async function queueDrop(event,slotsEl){
  event.preventDefault();slotsEl.classList.remove('over');
  const raw=event.dataTransfer.getData('text/plain');
  if(!raw||!raw.startsWith('qc-'))return;
  const postId=parseInt(raw.replace('qc-',''));
  const card=document.getElementById('qc-'+postId);if(!card)return;
  const newIso=slotsEl.dataset.iso;
  // Find first empty slot in this day
  const emptySlot=slotsEl.querySelector('.qcal-slot-empty');
  if(emptySlot){
    // Drop onto the first empty slot
    const hour=emptySlot.dataset.hour;
    const scheduledAt=newIso+'T'+hour;
    const r=await fetch('/api/plan_reorder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:postId,scheduled_at:scheduledAt})});
    const d=await r.json();
    if(d.ok){
      const oldSlots=card.closest('.qcal-slots');
      emptySlot.parentNode.insertBefore(card,emptySlot);
      emptySlot.remove();
      if(oldSlots&&!oldSlots.querySelector('.qcal-card')){
        const ph=document.createElement('div');ph.className='qcal-slot-empty';
        ph.innerHTML='<span class="qse-time">00:00</span>';
        oldSlots.appendChild(ph);
      }
      const timeEl=card.querySelector('.qcal-time');if(timeEl)timeEl.textContent=hour;
      const cdEl=card.querySelector('.rq-countdown');if(cdEl)cdEl.dataset.sched=scheduledAt+':00';
      toast('Moved to '+newIso+' '+hour);
    }
  } else {
    // All slots full — use last slot time
    const hours=['00:00','03:00','06:00','07:00','09:00','11:00','12:00','14:00','16:00','17:00','18:00','20:00','22:00'];
    const existing=slotsEl.querySelectorAll('.qcal-card').length;
    const time=hours[Math.min(existing,hours.length-1)];
    const scheduledAt=newIso+'T'+time;
    const r=await fetch('/api/plan_reorder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:postId,scheduled_at:scheduledAt})});
    const d=await r.json();
    if(d.ok){
      const oldSlots=card.closest('.qcal-slots');
      slotsEl.appendChild(card);
      if(oldSlots&&!oldSlots.querySelector('.qcal-card')){
        const ph=document.createElement('div');ph.className='qcal-slot-empty';
        ph.innerHTML='<span class="qse-time">00:00</span>';
        oldSlots.appendChild(ph);
      }
      const timeEl=card.querySelector('.qcal-time');if(timeEl)timeEl.textContent=time;
      const cdEl=card.querySelector('.rq-countdown');if(cdEl)cdEl.dataset.sched=scheduledAt+':00';
      toast('Moved to '+newIso+' '+time);
    }
  }
}

// ── Export posted CSV (Item 10) ──
async function exportPosted(){
  toast('Exporting...',5000);
  const r=await fetch('/api/posted?limit=1000');const d=await r.json();
  const rows=[['ID','Platform','Posted At','Caption','Article','Chart','News']];
  for(const p of d.posts){
    rows.push([p.id,p.platform,p.posted_at||'',(p.caption||'').replace(/"/g,'""'),p.article_title||'',p.chart_title||'',p.news_title||'']);
  }
  const csv=rows.map(r=>r.map(c=>'"'+String(c)+'"').join(',')).join('\n');
  const blob=new Blob([csv],{type:'text/csv'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='hfn-posted-'+new Date().toISOString().substring(0,10)+'.csv';
  a.click();URL.revokeObjectURL(a.href);toast('Downloaded');
}

// ═══ ARTICLE STUDIO ═══
let studioCurrentId=null;
let studioSaveTimer=null;
let studioPollTimer=null;
let studioChatStreaming=false;
let studioCurrentAction=null;
const stageOrder=['draft','factcheck','charts','images','review','deployed'];
const stageLabels=['Draft','Fact-Check','Charts','Image','Build','Deploy'];

async function studioNewDraft(){
  const r=await fetch('/api/studio/drafts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:'Untitled'})});
  const d=await r.json();
  if(d.ok){studioSelectDraft(d.id)}else{toast(d.msg||'Failed')}
}

async function studioSelectDraft(id){
  const r=await fetch('/api/studio/drafts/'+id);
  const d=await r.json();
  if(!d||d.error){toast('Draft not found');return}
  studioCurrentId=id;
  document.getElementById('st-list').style.display='none';
  document.getElementById('st-editor').style.display='flex';
  // Populate fields
  document.getElementById('st-ed-title').textContent=d.title;
  document.getElementById('st-ed-slug').textContent=d.slug;
  document.getElementById('st-f-title').value=d.title||'';
  document.getElementById('st-f-section').value=d.section||'';
  document.getElementById('st-f-excerpt').value=d.excerpt||'';
  document.getElementById('st-f-share').value=d.share_summary||'';
  document.getElementById('st-f-imgprompt').value=d.image_prompt||'';
  document.getElementById('st-md-textarea').value=d.markdown||'';
  studioShareCount();
  studioUpdateWc();
  studioUpdateStepper(d.stage);
  // Chart summary + parse for preview
  studioRenderChartSummary(d.chart_defs||'');
  if(d.chart_defs)studioParseCharts(d.chart_defs);
  else{_parsedCharts=null;}
  // Hero image (details panel)
  const heroImg=document.getElementById('st-hero-img');
  heroImg.src='/api/studio/drafts/'+id+'/hero-image';
  heroImg.classList.toggle('visible',!!d.has_hero_image);
  // Hero preview (below next-bar)
  const heroPreview=document.getElementById('st-hero-preview');
  if(d.has_hero_image){heroPreview.src='/api/studio/drafts/'+id+'/hero-image';heroPreview.classList.add('visible')}
  else{heroPreview.classList.remove('visible');heroPreview.src=''}
  // Audio
  const audioEl=document.getElementById('st-audio');
  audioEl.src='/api/studio/drafts/'+id+'/audio';
  audioEl.classList.toggle('visible',!!d.has_audio);
  // Reset task status
  document.getElementById('st-task-status').classList.remove('visible','error');
  document.getElementById('st-ed-save').textContent='';
  // Close details panel
  document.getElementById('st-details-panel').classList.remove('open');
  document.getElementById('st-details-btn').classList.remove('active');
  // Load chat messages
  await studioLoadMessages(id);
  // Focus chat input + schedule preview update
  setTimeout(()=>document.getElementById('st-chat-input').focus(),100);
  studioSchedulePreviewUpdate();
}

async function studioLoadMessages(id){
  const el=document.getElementById('st-chat-messages');
  el.innerHTML='';
  try{
    const r=await fetch('/api/studio/drafts/'+id+'/messages');
    const msgs=await r.json();
    for(const m of msgs){
      studioAppendMessage(m.role, m.content);
    }
    el.scrollTop=el.scrollHeight;
  }catch(e){console.error('Failed to load messages',e)}
}

function studioAppendMessage(role, content, isStreaming){
  const el=document.getElementById('st-chat-messages');
  const div=document.createElement('div');
  div.className='st-msg '+role;
  const inner=document.createElement('div');
  inner.className='st-msg-content';
  if(role==='assistant'){
    inner.innerHTML=(typeof marked!=='undefined'?marked.parse(content):content.replace(/\n/g,'<br>'));
  }else{
    inner.textContent=content;
  }
  if(isStreaming){
    div.classList.add('streaming');
    const cursor=document.createElement('span');
    cursor.className='st-cursor';
    inner.appendChild(cursor);
  }
  div.appendChild(inner);
  el.appendChild(div);
  el.scrollTop=el.scrollHeight;
  return div;
}

async function studioSendChat(opts){
  if(!studioCurrentId||studioChatStreaming)return;
  opts=opts||{};
  const input=document.getElementById('st-chat-input');
  const text=input.value.trim();
  if(!text)return;
  input.value='';
  input.style.height='auto';

  // Show user message
  studioAppendMessage('user',text);

  // Create streaming assistant bubble
  const bubble=studioAppendMessage('assistant','',true);
  const contentEl=bubble.querySelector('.st-msg-content');
  studioChatStreaming=true;
  document.getElementById('st-chat-send').disabled=true;

  let fullText='';
  try{
    const body={message:text};
    if(opts.model)body.model=opts.model;
    const res=await fetch('/api/studio/drafts/'+studioCurrentId+'/chat',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(body)
    });
    const reader=res.body.getReader();
    const decoder=new TextDecoder();
    let buffer='';

    while(true){
      const {done,value}=await reader.read();
      if(done)break;
      buffer+=decoder.decode(value,{stream:true});
      const lines=buffer.split('\n');
      buffer=lines.pop();
      for(const line of lines){
        if(!line.startsWith('data: '))continue;
        try{
          const data=JSON.parse(line.slice(6));
          if(data.delta){
            fullText+=data.delta;
            // Remove cursor, update content, re-add cursor
            const cursor=contentEl.querySelector('.st-cursor');
            if(typeof marked!=='undefined'){
              contentEl.innerHTML=marked.parse(fullText);
            }else{
              contentEl.textContent=fullText;
            }
            if(cursor||bubble.classList.contains('streaming')){
              const c=document.createElement('span');
              c.className='st-cursor';
              contentEl.appendChild(c);
            }
            document.getElementById('st-chat-messages').scrollTop=document.getElementById('st-chat-messages').scrollHeight;
          }
          if(data.done){
            bubble.classList.remove('streaming');
            const cur=contentEl.querySelector('.st-cursor');
            if(cur)cur.remove();
            // Final render
            if(typeof marked!=='undefined'){
              contentEl.innerHTML=marked.parse(fullText);
            }
            // Check for draft in response
            studioCheckForDraft(fullText);
            studioCheckForCharts(fullText);
          }
          if(data.error){
            contentEl.innerHTML='<em style="color:var(--red)">Error: '+data.error+'</em>';
            bubble.classList.remove('streaming');
          }
        }catch(e){}
      }
    }
  }catch(e){
    contentEl.innerHTML='<em style="color:var(--red)">Connection error</em>';
    bubble.classList.remove('streaming');
  }
  studioChatStreaming=false;
  document.getElementById('st-chat-send').disabled=false;
  input.focus();
}

function studioCheckForDraft(text){
  // Detect if the response contains an article draft
  const hasFrontmatter=text.includes('---\ntitle:');
  const startsWithHeading=text.trim().startsWith('# ');
  if(!hasFrontmatter&&!startsWithHeading)return;

  let markdown=text;
  // If there's frontmatter, also try to extract metadata
  if(hasFrontmatter){
    const fmMatch=text.match(/---\n([\s\S]*?)\n---/);
    if(fmMatch){
      const fm=fmMatch[1];
      const titleMatch=fm.match(/title:\s*"?([^"\n]+)"?/);
      const sectionMatch=fm.match(/section:\s*"?([^"\n]+)"?/);
      const excerptMatch=fm.match(/excerpt:\s*"?([^"\n]+)"?/);
      const shareMatch=fm.match(/share_summary:\s*"?([^"\n]+)"?/);
      if(titleMatch){
        document.getElementById('st-f-title').value=titleMatch[1].trim();
        document.getElementById('st-ed-title').textContent=titleMatch[1].trim();
      }
      if(sectionMatch){
        const sec=sectionMatch[1].trim();
        const sel=document.getElementById('st-f-section');
        for(const opt of sel.options){if(opt.value===sec){sel.value=sec;break}}
      }
      if(excerptMatch)document.getElementById('st-f-excerpt').value=excerptMatch[1].trim();
      if(shareMatch){
        document.getElementById('st-f-share').value=shareMatch[1].trim();
        studioShareCount();
      }
    }
  }

  // Put the full text into the editor
  document.getElementById('st-md-textarea').value=markdown;
  studioUpdateWc();
  studioAutoSave();

  // Flash the editor area
  const mdArea=document.getElementById('st-md-textarea').parentElement;
  mdArea.classList.remove('flash');
  void mdArea.offsetWidth; // force reflow
  mdArea.classList.add('flash');

  // Show indicator
  const msgs=document.getElementById('st-chat-messages');
  const ind=document.createElement('div');
  ind.className='st-draft-indicator';
  ind.textContent='Draft loaded into editor — edit freely, then fact-check when ready.';
  msgs.appendChild(ind);
  msgs.scrollTop=msgs.scrollHeight;

  // Show next-step bar
  studioUpdateNextBar('draft');
}

function studioCheckForCharts(text){
  // Detect chart definitions — look for 'id' + 'js' keys regardless of code fence format
  const hasId=text.includes("'id':")||text.includes('"id":');
  const hasJs=text.includes("'js':")||text.includes('"js":');
  if(!hasId||!hasJs)return;

  // Extract: try fenced code block first (closed or unclosed), then fall back to full text
  let block;
  const fenced=text.match(/```\w*\s*\n([\s\S]*?)```/);
  if(fenced){
    block=fenced[1];
  }else{
    // Unclosed fence: take everything after ```python\n
    const unclosed=text.match(/```\w*\s*\n([\s\S]*)/);
    block=unclosed?unclosed[1]:text;
  }
  // Final check the extracted block actually has chart keys
  if(!(block.includes("'id':")||block.includes('"id":'))||!(block.includes("'js':")||block.includes('"js":')))return;

  // Save chart defs to draft via existing update endpoint
  fetch('/api/studio/drafts/'+studioCurrentId,{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({chart_defs:block})
  });

  // Render chart summary in details panel
  studioRenderChartSummary(block);

  // Parse charts for live preview
  studioParseCharts(block);

  // Show indicator in chat
  const msgs=document.getElementById('st-chat-messages');
  const ind=document.createElement('div');
  ind.className='st-draft-indicator';
  ind.textContent='Chart definitions captured — they will be saved when you click Save to Disk.';
  msgs.appendChild(ind);
  msgs.scrollTop=msgs.scrollHeight;

  // Advance stage hint
  studioUpdateNextBar('charts');
}

function studioToggleDetails(){
  const panel=document.getElementById('st-details-panel');
  const btn=document.getElementById('st-details-btn');
  panel.classList.toggle('open');
  btn.classList.toggle('active');
}

function studioBack(){
  studioCurrentId=null;
  studioChatStreaming=false;
  if(studioPollTimer){clearInterval(studioPollTimer);studioPollTimer=null}
  document.getElementById('st-editor').style.display='none';
  document.getElementById('st-list').style.display='block';
  document.getElementById('st-chat-messages').innerHTML='';
  location.reload();
}

function studioAutoSave(){
  if(studioSaveTimer)clearTimeout(studioSaveTimer);
  studioSaveTimer=setTimeout(studioSave,500);
}

async function studioSave(){
  if(!studioCurrentId)return;
  const data={
    title:document.getElementById('st-f-title').value,
    section:document.getElementById('st-f-section').value,
    excerpt:document.getElementById('st-f-excerpt').value,
    share_summary:document.getElementById('st-f-share').value,
    image_prompt:document.getElementById('st-f-imgprompt').value,
    markdown:document.getElementById('st-md-textarea').value
  };
  const saveEl=document.getElementById('st-ed-save');
  saveEl.textContent='Saving...';
  try{
    const r=await fetch('/api/studio/drafts/'+studioCurrentId,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    const d=await r.json();
    saveEl.textContent=d.ok?'Saved ✓':'Save failed';
    document.getElementById('st-ed-title').textContent=data.title;
    setTimeout(()=>{if(saveEl.textContent==='Saved ✓')saveEl.textContent=''},2000);
  }catch(e){saveEl.textContent='Error'}
}

function studioShareCount(){
  const v=document.getElementById('st-f-share').value;
  const el=document.getElementById('st-share-count');
  el.textContent=v.length+'/140';
  el.classList.toggle('over',v.length>140);
}

function studioUpdateWc(){
  const md=document.getElementById('st-md-textarea').value.trim();
  const wc=md?md.split(/\s+/).length:0;
  document.getElementById('st-md-wc').textContent=wc.toLocaleString()+' words';
}

function studioRenderChartSummary(defs){
  const el=document.getElementById('st-charts-summary');
  if(!defs||!defs.trim()){el.classList.remove('visible');el.innerHTML='';return}

  // Use parsed chart data if available
  if(_parsedCharts&&_parsedCharts.length>0){
    let html='<h4>Charts ('+_parsedCharts.length+')</h4><ol>';
    for(const c of _parsedCharts){
      html+='<li><strong>Fig '+c.figure_num+': '+_escHtml(c.title)+'</strong> <span>'+_escHtml(c.position)+'</span></li>';
    }
    html+='</ol>';
    el.innerHTML=html;
    el.classList.add('visible');
    return;
  }

  // Fallback: regex extraction from raw defs
  const titles=[];
  const re=/'title'\s*:\s*'([^']+)'/g;
  let m;
  while((m=re.exec(defs))!==null)titles.push(m[1]);
  if(!titles.length){
    const re2=/"title"\s*:\s*"([^"]+)"/g;
    while((m=re2.exec(defs))!==null)titles.push(m[1]);
  }
  if(!titles.length){el.classList.remove('visible');el.innerHTML='';return}
  let html='<h4>Charts ('+titles.length+')</h4><ol>';
  for(const t of titles)html+='<li><strong>'+t+'</strong></li>';
  html+='</ol>';
  el.innerHTML=html;
  el.classList.add('visible');
}

function studioUpdateStepper(stage){
  const idx=stageOrder.indexOf(stage);
  for(let i=0;i<6;i++){
    const dot=document.getElementById('st-dot-'+i);
    const line=document.getElementById('st-line-'+i);
    dot.classList.remove('active','done');
    if(line)line.classList.remove('done');
    if(i<idx){dot.classList.add('done');if(line)line.classList.add('done')}
    else if(i===idx){dot.classList.add('active')}
    // Make completed and active dots clickable
    if(i<=idx){
      dot.style.cursor='pointer';
      dot.onclick=(function(s){return function(){studioAdvanceStage(s)}})(stageOrder[i]);
    }else{
      dot.style.cursor='default';
      dot.onclick=null;
    }
  }
  studioUpdateNextBar(stage);
}

function studioUpdateNextBar(stage){
  const bar=document.getElementById('st-next-bar');
  const text=document.getElementById('st-next-text');
  const btns=document.getElementById('st-next-btns');
  bar.style.display='flex';
  switch(stage){
    case 'draft':
      text.textContent='Edit in the editor if needed, then fact-check.';
      btns.innerHTML='<button class="btn primary" onclick="studioFactCheck()" style="margin-right:6px">Fact-Check</button><button class="btn secondary" onclick="studioAdvanceStage(\'factcheck\')">Continue \u2192</button>';
      break;
    case 'factcheck':
      text.textContent='Review the report, then apply corrections or continue to Charts.';
      btns.innerHTML='<button class="btn secondary" onclick="studioFactCheck()" style="margin-right:6px">Re-check</button><button class="btn secondary" onclick="studioApplyCorrections()" style="margin-right:6px">Apply Corrections</button><button class="btn primary" onclick="studioAdvanceStage(\'charts\')">Continue \u2192</button>';
      break;
    case 'charts':
      text.textContent='Define 2\u20135 charts in the chat, then continue to hero image.';
      btns.innerHTML='<button class="btn secondary" onclick="studioDefineCharts()" style="margin-right:6px">Define Charts</button><button class="btn primary" onclick="studioAdvanceStage(\'images\')">Continue \u2192</button>';
      break;
    case 'images':
      text.textContent='Generate a hero image for the article.';
      btns.innerHTML='<button class="btn primary" onclick="studioAction(\'generate_image\')" style="margin-right:6px">Generate Image</button><button class="btn secondary" onclick="studioSetMode(\'preview\')" style="margin-right:6px">Review in Preview</button><button class="btn secondary" onclick="studioAdvanceStage(\'review\')">Continue \u2192</button>';
      break;
    case 'review':
      text.textContent='Review your article in the live preview. When satisfied, build for deployment.';
      btns.innerHTML='<button class="btn secondary" onclick="studioSetMode(\'preview\')" style="margin-right:6px">Preview</button><button class="btn primary" onclick="studioAction(\'build\')" style="margin-right:6px">Build for Deploy</button><button class="btn primary" onclick="studioAction(\'deploy\')">Deploy</button>';
      break;
    case 'deployed':
      text.textContent='Article deployed.';
      btns.innerHTML='';
      break;
    default:
      bar.style.display='none';
  }
}

async function studioAdvanceStage(newStage){
  if(!studioCurrentId)return;
  await fetch('/api/studio/drafts/'+studioCurrentId,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({stage:newStage})});
  studioUpdateStepper(newStage);
}

async function studioApplyCorrections(){
  if(!studioCurrentId||studioChatStreaming)return;
  const input=document.getElementById('st-chat-input');
  input.value='Apply all corrections from the fact-check report above to the article. For every INCORRECT claim, replace with the correct fact and source. For every UNCERTAIN claim, soften the language or add a caveat. Keep all CONFIRMED claims as-is. Output the FULL corrected article including complete frontmatter (title, subtitle, summary, share_summary, sources, etc.). Use British English throughout. Do not add commentary — just output the corrected article.';
  studioSendChat({model:'sonnet'});
}

async function studioDefineCharts(){
  if(!studioCurrentId||studioChatStreaming)return;
  const input=document.getElementById('st-chat-input');
  input.value='Define 2-5 charts for this article. Wrap in charts[\\\'slug\\\'] = [...], use single quotes, _regChart wrapper, C.accent/C.blue colors, close the ```python fence. Follow the EXAMPLE FORMAT exactly.';
  studioSendChat();
}

async function studioFactCheck(){
  if(!studioCurrentId||studioChatStreaming)return;
  // Save draft first
  await studioSave();
  // Show user message
  studioAppendMessage('user','[Fact-check requested]');
  // Create streaming assistant bubble
  const bubble=studioAppendMessage('assistant','',true);
  const contentEl=bubble.querySelector('.st-msg-content');
  studioChatStreaming=true;
  document.getElementById('st-chat-send').disabled=true;
  let fullText='';
  try{
    const res=await fetch('/api/studio/drafts/'+studioCurrentId+'/fact-check',{
      method:'POST',headers:{'Content-Type':'application/json'}
    });
    const reader=res.body.getReader();
    const decoder=new TextDecoder();
    let buffer='';
    while(true){
      const {done,value}=await reader.read();
      if(done)break;
      buffer+=decoder.decode(value,{stream:true});
      const lines=buffer.split('\n');
      buffer=lines.pop();
      for(const line of lines){
        if(!line.startsWith('data: '))continue;
        try{
          const data=JSON.parse(line.slice(6));
          if(data.delta){
            fullText+=data.delta;
            const cursor=contentEl.querySelector('.st-cursor');
            if(typeof marked!=='undefined'){
              contentEl.innerHTML=marked.parse(fullText);
            }else{
              contentEl.textContent=fullText;
            }
            if(cursor||bubble.classList.contains('streaming')){
              const c=document.createElement('span');
              c.className='st-cursor';
              contentEl.appendChild(c);
            }
            document.getElementById('st-chat-messages').scrollTop=document.getElementById('st-chat-messages').scrollHeight;
          }
          if(data.done){
            bubble.classList.remove('streaming');
            const cur=contentEl.querySelector('.st-cursor');
            if(cur)cur.remove();
            if(typeof marked!=='undefined'){
              contentEl.innerHTML=marked.parse(fullText);
            }
            // Update stepper to factcheck
            studioUpdateStepper('factcheck');
            // Show indicator
            const msgs=document.getElementById('st-chat-messages');
            const ind=document.createElement('div');
            ind.className='st-draft-indicator';
            ind.textContent='Fact-check complete — review above, then generate image.';
            msgs.appendChild(ind);
            msgs.scrollTop=msgs.scrollHeight;
          }
          if(data.error){
            contentEl.innerHTML='<em style="color:var(--red)">Error: '+data.error+'</em>';
            bubble.classList.remove('streaming');
          }
        }catch(e){}
      }
    }
  }catch(e){
    contentEl.innerHTML='<em style="color:var(--red)">Connection error</em>';
    bubble.classList.remove('streaming');
  }
  studioChatStreaming=false;
  document.getElementById('st-chat-send').disabled=false;
  document.getElementById('st-chat-input').focus();
}

async function studioAction(action){
  if(!studioCurrentId)return;
  studioCurrentAction=action;
  // Save first
  await studioSave();
  // Ensure details panel is open to see progress
  document.getElementById('st-details-panel').classList.add('open');
  document.getElementById('st-details-btn').classList.add('active');
  const statusEl=document.getElementById('st-task-status');
  const labelEl=document.getElementById('st-task-label');
  const progressEl=document.getElementById('st-task-progress');
  statusEl.classList.add('visible');statusEl.classList.remove('error');
  labelEl.textContent='Starting '+action.replace(/_/g,' ')+'...';
  progressEl.textContent='';
  // Show feedback in next-bar for image generation
  if(action==='generate_image'){
    const bar=document.getElementById('st-next-bar');
    bar.style.display='flex';
    document.getElementById('st-next-text').textContent='Generating hero image\u2026';
    document.getElementById('st-next-btns').innerHTML='<button class="btn primary" disabled>Generating\u2026</button>';
  }
  try{
    const r=await fetch('/api/studio/drafts/'+studioCurrentId+'/'+action.replace(/_/g,'-'),{method:'POST'});
    const d=await r.json();
    if(d.ok&&d.task_id){
      studioPollTask(d.task_id);
    }else{
      labelEl.textContent='Error';progressEl.textContent=d.msg||'Unknown error';
      statusEl.classList.add('error');
      if(action==='generate_image')studioUpdateNextBar('images');
    }
  }catch(e){
    labelEl.textContent='Error';progressEl.textContent=e.message;statusEl.classList.add('error');
    if(action==='generate_image')studioUpdateNextBar('images');
  }
}

function studioPollTask(taskId){
  if(studioPollTimer)clearInterval(studioPollTimer);
  const statusEl=document.getElementById('st-task-status');
  const labelEl=document.getElementById('st-task-label');
  const progressEl=document.getElementById('st-task-progress');
  studioPollTimer=setInterval(async()=>{
    try{
      const r=await fetch('/api/studio/tasks/'+taskId);
      const d=await r.json();
      if(!d){clearInterval(studioPollTimer);return}
      progressEl.textContent=d.progress||'';
      if(d.status==='done'){
        clearInterval(studioPollTimer);studioPollTimer=null;
        labelEl.textContent='Complete';progressEl.textContent=d.progress||'Done';
        statusEl.classList.remove('error');
        // Image task: show hero preview + advance stage instead of full reset
        if(studioCurrentAction==='generate_image'&&studioCurrentId){
          const heroPreview=document.getElementById('st-hero-preview');
          heroPreview.src='/api/studio/drafts/'+studioCurrentId+'/hero-image?t='+Date.now();
          heroPreview.classList.add('visible');
          const heroImg=document.getElementById('st-hero-img');
          heroImg.src=heroPreview.src;
          heroImg.classList.add('visible');
          document.getElementById('st-next-text').textContent='Hero image generated.';
          document.getElementById('st-next-btns').innerHTML='<button class="btn primary" onclick="studioAdvanceStage(\'review\')">Continue \u2192</button>';
          studioUpdateStepper('images');
          studioCurrentAction=null;
          studioSchedulePreviewUpdate();
        }else{
          // Other tasks: refresh draft data as before
          if(studioCurrentId)studioSelectDraft(studioCurrentId);
          studioCurrentAction=null;
        }
      }else if(d.status==='error'){
        clearInterval(studioPollTimer);studioPollTimer=null;
        labelEl.textContent='Error';progressEl.textContent=d.error||'Task failed';
        statusEl.classList.add('error');
        if(studioCurrentAction==='generate_image')studioUpdateNextBar('images');
        studioCurrentAction=null;
      }else{
        labelEl.textContent='Running...';
      }
    }catch(e){clearInterval(studioPollTimer)}
  },2000);
}

// ── Live Preview Engine ──

let _previewTimer=null;
let _previewMode='edit';
let _chartBootstrapJs=null;
let _parsedCharts=null;
let _chartParseInFlight=false;

function studioSetMode(mode){
  _previewMode=mode;
  const area=document.getElementById('st-md-area');
  area.setAttribute('data-mode',mode);
  // Update toolbar active state
  ['edit','split','preview'].forEach(m=>{
    const btn=document.getElementById('st-mode-'+m);
    if(btn)btn.classList.toggle('active',m===mode);
  });
  if(mode!=='edit')studioUpdatePreview();
}

function studioSchedulePreviewUpdate(){
  if(_previewMode==='edit')return;
  if(_previewTimer)clearTimeout(_previewTimer);
  _previewTimer=setTimeout(studioUpdatePreview,400);
}

var _libraryBooks=null;
async function _loadLibraryBooks(){
  if(_libraryBooks)return _libraryBooks;
  try{
    const r=await fetch('/api/studio/library-books');
    const d=await r.json();
    _libraryBooks=d.books||[];
  }catch(e){_libraryBooks=[];}
  return _libraryBooks;
}

async function studioUpdatePreview(){
  if(_previewMode==='edit')return;
  const iframe=document.getElementById('st-preview-iframe');
  if(!iframe)return;

  // Gather metadata
  const title=document.getElementById('st-f-title')?.value||'Untitled';
  const section=document.getElementById('st-f-section')?.value||'';
  const excerpt=document.getElementById('st-f-excerpt')?.value||'';
  let md=document.getElementById('st-md-textarea')?.value||'';

  // Extract sources from YAML frontmatter BEFORE stripping it
  let articleSources=[];
  const fmMatch=md.match(/^\s*---\n([\s\S]*?)\n---/);
  if(fmMatch){
    const fmBlock=fmMatch[1];
    const srcMatch=fmBlock.match(/sources:\s*\n((?:\s+-\s+.*\n?)*)/);
    if(srcMatch){
      const lines=srcMatch[1].split('\n');
      for(const line of lines){
        const m=line.match(/^\s+-\s+["']?([^"'\n]+?)["']?\s*$/);
        if(m)articleSources.push(m[1].trim());
      }
    }
  }

  // Strip frontmatter and AI metadata blobs from preview.
  // Pattern 1: Standard YAML frontmatter at start: ---\n...\n---
  md=md.replace(/^\s*---\n[\s\S]*?\n---\s*\n?/,'');
  // Pattern 2: AI preamble like [Using Sonnet...]\n\n--- followed by YAML then ---
  // The \n\n may be literal backslash-n or actual newlines
  md=md.replace(/^\s*\[Using [^\]]*\][\\n\s]*---\n[\s\S]*?\n---\s*\n?/,'');
  // Pattern 3: If above didn't match (no closing ---), strip from [Using...] up to first # heading
  if(/^\s*\[Using /.test(md)){
    md=md.replace(/^[\s\S]*?(?=\n#\s)/,'');
  }

  // Strip leading H1 if it duplicates the metadata title (preview already renders title from metadata)
  if(title){
    const titleNorm=title.trim().toLowerCase();
    md=md.replace(/^\s*#\s+(.+)\n*/,function(match,h1){
      return h1.trim().toLowerCase()===titleNorm?'':match;
    });
  }

  // Render markdown
  let bodyHtml=typeof marked!=='undefined'?marked.parse(md):md.replace(/\n/g,'<br>');

  // Inject charts at correct positions
  if(_parsedCharts&&_parsedCharts.length>0){
    bodyHtml=studioInjectCharts(bodyHtml,_parsedCharts);
  }

  // Hero image — always try to load, onerror hides it
  const heroUrl=studioCurrentId?'/api/studio/drafts/'+studioCurrentId+'/hero-image':'';

  // Audio — always try to load, onerror hides it
  const audioUrl=studioCurrentId?'/api/studio/drafts/'+studioCurrentId+'/audio':'';

  // Load chart bootstrap JS if needed
  if(!_chartBootstrapJs&&_parsedCharts&&_parsedCharts.length>0){
    try{
      const r=await fetch('/api/studio/chart-bootstrap-js');
      _chartBootstrapJs=await r.text();
    }catch(e){_chartBootstrapJs='';}
  }

  // Build Further Reading section
  let furtherReadingHtml='';
  if(articleSources.length>0){
    const books=await _loadLibraryBooks();
    const bookMap={};
    for(const b of books)bookMap[b.title.toLowerCase()]=b;
    let items='';
    for(const src of articleSources){
      const book=bookMap[src.toLowerCase()];
      if(book){
        const q=encodeURIComponent(book.title+' '+book.author);
        const url=book.url||('https://www.amazon.co.uk/s?k='+q);
        const label=book.url?'Buy':'Buy on Amazon';
        items+=`<div class="fr-item"><span class="fr-title">${_escHtml(book.title)}</span><span class="fr-author">${_escHtml(book.author)}</span><a class="fr-amazon" href="${url}" target="_blank" rel="noopener">${label}</a></div>`;
      }else{
        items+=`<div class="fr-item fr-missing"><span class="fr-title">${_escHtml(src)}</span></div>`;
      }
    }
    furtherReadingHtml=`<section class="further-reading"><h2 class="fr-heading">Further Reading</h2><p class="fr-desc">Books cited or drawn upon in this article.</p><div class="fr-list">${items}</div></section>`;
  }

  // Build chart JS block
  let chartScripts='';
  if(_parsedCharts&&_parsedCharts.length>0&&_chartBootstrapJs){
    const allJs=_parsedCharts.map(c=>c.js||'').filter(Boolean).join('\n');
    chartScripts=`
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"><\/script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"><\/script>
<script>
(function(){
// Force light-theme: override _gc so COLORS bootstrap always uses light fallbacks
var _LIGHT_VARS={'--text':'#1a1815','--bg':'#ffffff','--border-light':'#f2eeea','--text-dim':'#8a8479'};
function _gc(v,fb){return _LIGHT_VARS[v]||fb;}
function _refreshC(){}
${_chartBootstrapJs}
// Re-enforce light values after bootstrap runs (overwrite any _gc reads)
C.text='#1a1815';C.grid='#f2eeea';C.dim='#8a8479';C.bg='#ffffff';
// Fix annotation contrast: force white text on ALL annotation labels that have backgrounds
Chart.register({id:'previewAnnotationContrast',beforeDraw:function(chart){
  var ann=chart.options&&chart.options.plugins&&chart.options.plugins.annotation&&chart.options.plugins.annotation.annotations;
  if(!ann)return;
  for(var k in ann){
    var a=ann[k];if(!a)continue;
    // Force label text to white if there's any background
    if(a.label){
      var bg=a.label.backgroundColor||a.backgroundColor||'';
      if(bg&&bg!=='transparent'&&bg!=='rgba(0,0,0,0)'){
        a.label.color='#ffffff';
      }
      // Also force any colored label text to white for readability
      var lc=a.label.color||'';
      if(lc&&lc!=='#ffffff'&&lc!=='#fff'&&lc!=='white'&&lc!=='#1a1815'){
        a.label.color='#ffffff';
      }
    }
    // Force line annotation label colours too
    if(a.type==='line'&&a.label){
      a.label.color='#ffffff';
    }
  }
}});
// Also override tooltipStyle to ensure white text on dark tooltip bg
tooltipStyle.titleColor='#ffffff';tooltipStyle.bodyColor='#ffffff';
${allJs}
})();
<\/script>`;
  }

  const html=`<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@400;500;600&display=swap');
:root,html,html[data-theme="light"]{--text:#1a1815!important;--bg:#ffffff!important;--border-light:#f2eeea!important;--text-dim:#8a8479!important;--accent:#c43425!important}
*{margin:0;padding:0;box-sizing:border-box;color-scheme:light}
body{font-family:'Inter',sans-serif;color:#1a1815;background:#ffffff;padding:24px 32px;line-height:1.7;max-width:720px;margin:0 auto}
.section-kicker{text-transform:uppercase;font-size:.72rem;font-weight:600;color:var(--accent);letter-spacing:.08em;margin-bottom:8px}
h1{font-family:'Playfair Display',serif;font-size:2rem;font-weight:700;line-height:1.2;margin-bottom:12px}
.excerpt{font-size:1.05rem;color:#555;line-height:1.6;margin-bottom:20px;font-style:italic}
.hero-img{width:100%;max-height:420px;object-fit:cover;border-radius:8px;margin-bottom:20px}
audio{width:100%;margin-bottom:20px}
h2{font-family:'Playfair Display',serif;font-size:1.35rem;font-weight:700;margin:28px 0 12px;color:var(--text)}
h3{font-size:1.05rem;font-weight:600;margin:20px 0 8px}
p{margin-bottom:14px;font-size:.95rem}
blockquote{border-left:3px solid var(--accent);padding-left:16px;color:#555;margin:16px 0;font-style:italic}
code{background:#f5f5f4;padding:2px 5px;border-radius:3px;font-size:.85em}
pre{background:#f5f5f4;padding:14px;border-radius:6px;overflow-x:auto;margin:14px 0}
a{color:#2563eb}
ul,ol{margin-bottom:14px;padding-left:24px}
li{margin-bottom:4px;font-size:.95rem}
hr{border:none;border-top:1px solid var(--border-light);margin:24px 0}
.chart-figure{margin:24px 0;padding:16px;background:#fafaf9;border:1px solid #f0ece8;border-radius:8px}
.chart-figure-label{font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:var(--accent);font-weight:600;margin-bottom:4px}
.chart-figure h4{font-family:'Playfair Display',serif;font-size:1.05rem;margin-bottom:4px}
.chart-desc{font-size:.82rem;color:#666;margin-bottom:10px}
.chart-area{position:relative;width:100%;aspect-ratio:16/10}
.chart-area.tall{aspect-ratio:16/14}
.chart-area canvas{width:100%!important;height:100%!important}
.chart-source{font-size:.7rem;color:#999;margin-top:8px}
.further-reading{max-width:680px;margin:2.5rem auto 0;padding:2rem 0 0;border-top:1px solid #f2eeea}
.fr-heading{font-family:'Playfair Display',serif;font-size:1.2rem;font-weight:600;margin:0 0 .35rem}
.fr-desc{font-size:.85rem;color:#8a8479;margin:0 0 1.25rem}
.fr-list{display:flex;flex-direction:column}
.fr-item{display:flex;align-items:baseline;gap:.5rem;padding:.4rem 0;border-bottom:1px solid #f2eeea}
.fr-item:last-child{border-bottom:none}
.fr-title{font-family:'Playfair Display',serif;font-size:.88rem;font-weight:500;font-style:italic;flex:1;line-height:1.4}
.fr-author{font-size:.78rem;color:#8a8479;white-space:nowrap;flex-shrink:0}
.fr-amazon{font-size:.72rem;font-weight:600;color:#b8751a;text-decoration:none;white-space:nowrap;padding:.15rem .45rem;border:1px solid #b8751a;border-radius:3px;flex-shrink:0}
.fr-amazon:hover{background:#b8751a;color:#fff}
.fr-missing .fr-title{color:#8a8479}
</style>
</head>
<body>
${section?'<div class="section-kicker">'+_escHtml(section)+'</div>':''}
<h1>${_escHtml(title)}</h1>
${excerpt?'<p class="excerpt">'+_escHtml(excerpt)+'</p>':''}
${heroUrl?'<img class="hero-img" src="'+heroUrl+'" onerror="this.style.display=\'none\'">':''}
${audioUrl?'<audio controls src="'+audioUrl+'" onerror="this.style.display=\'none\'"></audio>':''}
${bodyHtml}
${furtherReadingHtml}
${chartScripts}
</body>
</html>`;

  // Write to iframe
  const doc=iframe.contentDocument||iframe.contentWindow.document;
  doc.open();
  doc.write(html);
  doc.close();
}

function _escHtml(s){
  const d=document.createElement('div');d.textContent=s;return d.innerHTML;
}

function studioInjectCharts(html,charts){
  if(!charts||!charts.length)return html;

  // Group by position
  const positioned={};
  const endCharts=[];
  for(const ch of charts){
    const pos=ch.position||'before_end';
    if(pos==='before_end'){endCharts.push(ch);continue;}
    if(!positioned[pos])positioned[pos]=[];
    positioned[pos].push(ch);
  }

  // Find </p> positions (simple — not inside chart-figures since we're building fresh)
  const paraEnds=[];
  let idx=0;
  while(true){
    idx=html.indexOf('</p>',idx);
    if(idx===-1)break;
    paraEnds.push(idx+4);
    idx+=4;
  }

  // Build insertions (position, chartHtml) — insert in reverse order
  const insertions=[];
  for(const[pos,chs] of Object.entries(positioned)){
    const chartBlock=chs.map(c=>_makeChartHtml(c)).join('\n');
    if(pos.startsWith('after_para_')){
      const n=parseInt(pos.split('_').pop())||3;
      if(n<=paraEnds.length){
        insertions.push([paraEnds[n-1],chartBlock]);
      }else{
        endCharts.push(...chs);
      }
    }else if(pos.startsWith('after_heading:')){
      const hText=pos.split(':')[1].trim().toLowerCase();
      const hRe=/<h[23][^>]*>([\s\S]*?)<\/h[23]>/gi;
      let hm;
      let found=false;
      while((hm=hRe.exec(html))!==null){
        const clean=hm[1].replace(/<[^>]+>/g,'').trim().toLowerCase();
        if(clean.includes(hText)){
          insertions.push([hm.index+hm[0].length,chartBlock]);
          found=true;
          break;
        }
      }
      if(!found&&paraEnds.length>=3){
        insertions.push([paraEnds[2],chartBlock]);
      }else if(!found){
        endCharts.push(...chs);
      }
    }
  }

  // Sort insertions reverse by position to avoid drift
  insertions.sort((a,b)=>b[0]-a[0]);
  for(const[pos,block] of insertions){
    html=html.slice(0,pos)+'\n'+block+html.slice(pos);
  }

  // Append end charts
  if(endCharts.length){
    html+='\n'+endCharts.map(c=>_makeChartHtml(c)).join('\n');
  }
  return html;
}

function _makeChartHtml(ch){
  return `<div class="chart-figure">
  <div class="chart-figure-label">Figure ${ch.figure_num||'?'}</div>
  <h4>${_escHtml(ch.title||'')}</h4>
  <p class="chart-desc">${_escHtml(ch.desc||'')}</p>
  <div class="chart-area"><canvas id="${ch.id}"></canvas></div>
  <p class="chart-source">Source: ${_escHtml(ch.source||'')}</p>
</div>`;
}

async function studioParseCharts(raw){
  if(!raw||_chartParseInFlight)return;
  _chartParseInFlight=true;
  try{
    const r=await fetch('/api/studio/drafts/'+studioCurrentId+'/parse-charts',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({chart_defs:raw})
    });
    const d=await r.json();
    _parsedCharts=d.charts||[];
    // Clear bootstrap cache so it reloads with chart content
    if(_parsedCharts.length>0&&!_chartBootstrapJs)_chartBootstrapJs=null;
    studioSchedulePreviewUpdate();
  }catch(e){console.error('Parse charts error:',e)}
  finally{_chartParseInFlight=false}
}

function studioInsert(before,after){
  const ta=document.getElementById('st-md-textarea');
  const s=ta.selectionStart,e=ta.selectionEnd;
  const sel=ta.value.substring(s,e);
  ta.value=ta.value.substring(0,s)+before+sel+after+ta.value.substring(e);
  ta.focus();ta.selectionStart=s+before.length;ta.selectionEnd=s+before.length+sel.length;
  studioAutoSave();
}

async function studioDeleteDraft(id,title){
  if(!confirm('Delete "'+title+'"? This cannot be undone.'))return;
  await fetch('/api/studio/drafts/'+id+'/delete',{method:'POST'});
  // Remove row from DOM instead of reloading page
  const row=document.getElementById('st-row-'+id);
  if(row)row.remove();
  // Update the Studio tab count
  const tab=document.querySelector('.tab[onclick*="studio"]');
  if(tab){
    const remaining=document.querySelectorAll('tr[id^="st-row-"]').length;
    tab.innerHTML='✏️ Studio ('+remaining+')';
  }
  // Update stage pills
  const pills=document.querySelector('.st-pills');
  if(pills){
    const rows=document.querySelectorAll('tr[id^="st-row-"]');
    const counts={};
    rows.forEach(r=>{const badge=r.querySelector('.st-badge');if(badge){const s=badge.textContent.trim().toLowerCase();counts[s]=(counts[s]||0)+1}});
    pills.innerHTML=Object.entries(counts).map(([s,c])=>'<span class="st-pill '+s+'">'+s+' '+c+'</span>').join('');
  }
}
</script></body></html>"""

# ── Routes ──

@app.route("/")
def dashboard():
    import json as jsonmod
    articles = db.get_all_articles()
    charts = db.get_all_charts()
    posted = db.get_posted()
    scheduled = db.get_scheduled()
    planned = db.get_planned_posts()
    nn, nm = db.count_news()
    news = db.get_news_ranked()
    generated = db.get_generated_posts()
    queued = db.get_queued_posts()

    # Calendar for plan — show planned, generated, AND queued items
    today = datetime.now().date()
    cal_days = []
    day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    # Combine all active posts with their status
    all_plan_posts = []
    for s in planned:
        all_plan_posts.append({**s, "_status": "planned"})
    for s in generated:
        all_plan_posts.append({**s, "_status": "generated"})
    for s in queued:
        all_plan_posts.append({**s, "_status": "queued"})
    slot_hours = [f"{h:02d}:00" for h in POST_SLOTS]
    for i in range(7):
        d = today + timedelta(days=i)
        day_posts = []
        for s in all_plan_posts:
            sa = s.get("scheduled_at","")
            if sa:
                try:
                    sd = datetime.fromisoformat(sa).date()
                    if sd == d:
                        st = datetime.fromisoformat(sa)
                        day_posts.append({"id": s["id"], "platform": s["platform"],
                            "post_type": s.get("post_type","short"),
                            "caption": s.get("caption",""),
                            "chart_title": s.get("chart_title",""),
                            "article_title": s.get("article_title",""),
                            "news_title": s.get("news_title",""),
                            "hook": s.get("hook","") or s.get("article_context",""),
                            "time": st.strftime("%H:%M"),
                            "status": s["_status"]})
                except: pass
        day_posts.sort(key=lambda x: x["time"])
        # Build slot list: each POST_SLOTS hour -> either filled or empty
        posts_by_time = {}
        for p in day_posts:
            posts_by_time.setdefault(p["time"], []).append(p)
        slots = []
        for hour in slot_hours:
            if hour in posts_by_time:
                for p in posts_by_time[hour]:
                    slots.append({"hour": hour, "post": p})
            else:
                slots.append({"hour": hour, "post": None})
        cal_days.append({"date": d.strftime("%d %b"), "label": day_names[d.weekday()],
                         "is_today": d == today, "posts": day_posts, "slots": slots,
                         "idx": i, "iso": d.isoformat()})

    # Build review days (generated posts grouped by date)
    def build_day_groups(posts):
        days = {}
        for p in posts:
            sa = p.get("scheduled_at","")
            if not sa: continue
            try:
                dt = datetime.fromisoformat(sa)
                d = dt.date()
                iso = d.isoformat()
                if iso not in days:
                    days[iso] = {"date": d.strftime("%d %b"), "label": day_names[d.weekday()],
                                 "iso": iso, "posts": []}
                # Get image - try multiple sources
                img = p.get("image_path","") or p.get("chart_image","")
                if not img and p.get("article_id"):
                    # Fallback: find first chart image from matched article
                    conn = db.get_db()
                    art = conn.execute("SELECT slug FROM articles WHERE id=?", (p["article_id"],)).fetchone()
                    if art:
                        ch = conn.execute("SELECT image_path FROM charts WHERE article_slug=? AND image_path != '' LIMIT 1",
                                         (art[0],)).fetchone()
                        if ch: img = ch[0]
                    conn.close()
                days[iso]["posts"].append({
                    "id": p["id"], "platform": p["platform"],
                    "post_type": p.get("post_type","short"),
                    "caption": p.get("caption",""), "chart_title": p.get("chart_title",""),
                    "hook": p.get("hook","") or p.get("article_context",""),
                    "time": dt.strftime("%H:%M"),
                    "news_title": p.get("news_title",""),
                    "article_title": p.get("article_title",""),
                    "image_path": img,
                    "article_url": p.get("article_url","") or p.get("article_url_joined",""),
                    "article_context": p.get("article_context",""),
                    "article_part": p.get("article_part","")
                })
            except: pass
        for d in days.values():
            d["posts"].sort(key=lambda x: x["time"])
        return sorted(days.values(), key=lambda x: x["iso"])

    review_days = build_day_groups(generated)
    queue_days = build_day_groups(queued)

    # Build queue_slots on each cal_day (same {hour, post} pattern as planner slots)
    for cd in cal_days:
        qd_posts = {}
        for qd in queue_days:
            if qd["iso"] == cd["iso"]:
                for p in qd["posts"]:
                    qd_posts.setdefault(p["time"], []).append(p)
        qslots = []
        for hour in slot_hours:
            if hour in qd_posts:
                for p in qd_posts[hour]:
                    qslots.append({"hour": hour, "post": p})
            else:
                qslots.append({"hour": hour, "post": None})
        cd["queue_slots"] = qslots

    # Library data
    articles_with_charts = db.get_articles_with_chart_counts()
    total_charts = sum(a.get("chart_count", 0) for a in articles_with_charts)
    total_images = sum(a.get("image_count", 0) for a in articles_with_charts)

    # Enrich with issue info and post counts
    slug_to_issue = build_slug_to_issue_map()
    issue_labels = {iss["number"]: iss["label"] for iss in ISSUES}
    # Post counts per article slug via charts join
    conn = db.get_db()
    post_count_rows = conn.execute("""
        SELECT c.article_slug, COUNT(p.id) as cnt
        FROM posts p
        JOIN charts c ON p.chart_id = c.id
        WHERE p.status NOT IN ('rejected','deleted')
        GROUP BY c.article_slug
    """).fetchall()
    conn.close()
    post_counts = {r[0]: r[1] for r in post_count_rows}
    issues_with_articles = {}  # issue_number → count of articles in DB
    for a in articles_with_charts:
        slug = a.get("slug", "")
        inum = slug_to_issue.get(slug)
        a["issue_num"] = inum or 0
        a["issue_label"] = issue_labels.get(inum, "") if inum else ""
        a["post_count"] = post_counts.get(slug, 0)
        if inum:
            issues_with_articles[inum] = issues_with_articles.get(inum, 0) + 1

    studio_drafts = db.get_all_drafts()

    return render_template_string(HTML,
        sched=scheduler_on,
        match_model=MATCH_MODEL.split("-")[1] if "-" in MATCH_MODEL else MATCH_MODEL[:15],
        gen_model=GEN_MODEL.split("-")[1] if "-" in GEN_MODEL else GEN_MODEL[:15],
        na=len(articles), nc=len(charts), nn=nn, nm=nm,
        ns=len(generated)+len(queued)+len(planned), np=len(posted),
        xt=db.posts_today("x"), lt=db.posts_today("linkedin"),
        mx=MAX_X_PER_DAY, ml=MAX_LI_PER_DAY,
        news=news,
        posted=posted[:30], cal_days=cal_days, max_per_day=MAX_POSTS_PER_DAY,
        review_days=review_days, queue_days=queue_days,
        n_generated=len(generated), n_queued=len(queued),
        articles_with_charts=articles_with_charts,
        total_charts=total_charts, total_images=total_images,
        issues=ISSUES, issues_with_articles=issues_with_articles,
        studio_drafts=studio_drafts, n_drafts=len(studio_drafts),
        alog=activity_log[:30], img_url=img_url)

@app.route("/api/act", methods=["POST"])
def api_act():
    global scheduler_ref, scheduler_on
    a = request.json.get("a","")
    if a == "ingest":
        from ingester import ingest_all; na, nc = ingest_all()
        msg = f"Ingested {na} articles, {nc} charts"
    elif a == "monitor":
        from monitor import run_monitor; m = run_monitor()
        msg = f"Monitor: {m} matches"
    elif a == "generate":
        from generator import generate_from_matches; c = generate_from_matches()
        msg = f"Generated {c} posts"
    elif a == "schedule":
        if scheduler_on:
            scheduler_on = False
            if scheduler_ref: scheduler_ref.shutdown(wait=False); scheduler_ref = None
            msg = "Stopped"
        else:
            _start_auto_poster()
            msg = "Auto-poster started"
    else: return jsonify({"ok":False,"msg":"Unknown"})
    log(msg); return jsonify({"ok":True,"msg":msg})

@app.route("/api/session_status")
def api_session_status():
    """Check health of X and LinkedIn sessions."""
    x_ok = False
    li_ok = False
    # X: check Chrome profile dir exists
    chrome_profile = Path.home() / "Library/Application Support/Google/Chrome/Default"
    x_ok = chrome_profile.exists()
    # LinkedIn: try Voyager /api/me
    try:
        from poster import _li_api_session
        session, err = _li_api_session()
        if session:
            r = session.get("https://www.linkedin.com/voyager/api/me", timeout=5)
            li_ok = r.status_code == 200
    except Exception:
        pass
    return jsonify({"x": x_ok, "linkedin": li_ok})

@app.route("/api/autoposter_status")
def api_autoposter_status():
    """Return auto-poster state for the Settings panel."""
    queued = db.get_queued_posts()
    next_post = None
    if queued:
        p = queued[0]
        next_post = {"id": p["id"], "platform": p["platform"],
                     "scheduled_at": p.get("scheduled_at",""),
                     "chart_title": p.get("chart_title","")}
    return jsonify({
        "scheduler_on": scheduler_on,
        "queue_count": len(queued),
        "next_post": next_post,
        "last_result": last_post_result
    })

@app.route("/api/chart_usage")
def api_chart_usage():
    """Chart usage stats for library heatmap."""
    stats = db.get_chart_usage_stats()
    for s in stats:
        s["image_url"] = img_url(s.get("image_path",""))
    return jsonify(stats)

@app.route("/api/posted")
def api_posted():
    """Filtered posted items for calendar view."""
    platform = request.args.get("platform", "")
    days = request.args.get("days", type=int)
    offset = request.args.get("offset", 0, type=int)
    limit = request.args.get("limit", 50, type=int)
    actual_limit = min(limit, 100)
    rows, total = db.get_posted_filtered(
        platform=platform or None, days=days, offset=offset, limit=actual_limit)
    for r in rows:
        r["image_url"] = img_url(r.get("image_path","") or r.get("chart_image",""))
    return jsonify({"posts": rows, "total": total, "offset": offset, "limit": actual_limit})

# Planner APIs
@app.route("/api/arsenal/<int:news_id>")
def api_arsenal(news_id):
    charts = db.get_arsenal_for_news(news_id)
    print(f"[Arsenal] news_id={news_id}, found {len(charts)} items, text_only={charts[0].get('text_only') if charts else 'N/A'}")
    for c in charts:
        if c.get("image_path"):
            c["image_url"] = "/img/" + c["image_path"].replace("\\","/")
        else:
            c["image_url"] = ""
        c["chart_id"] = c.get("chart_id") or c["id"]
        c["chart_title"] = c.get("chart_title") or c.get("title","")
        c["article_id"] = c.get("article_id") or 0
    return jsonify(charts)

@app.route("/api/plan_add", methods=["POST"])
def api_plan_add():
    d = request.json
    sched_at = d.get("scheduled_at", "")
    # Enforce daily limit
    if sched_at:
        day_iso = sched_at[:10]
        conn = db.get_db()
        count = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE scheduled_at LIKE ? AND status IN ('planned','generated','queued','scheduled')",
            (day_iso + "%",)).fetchone()[0]
        conn.close()
        if count >= MAX_POSTS_PER_DAY:
            return jsonify({"ok": False, "msg": f"Daily limit reached ({MAX_POSTS_PER_DAY} posts)"})
    # Block LinkedIn for political articles
    if d.get("platform") == "linkedin" and d.get("article_id"):
        from generator import is_linkedin_safe
        article = db.get_article(d["article_id"])
        if article and not is_linkedin_safe(article):
            return jsonify({"ok": False, "msg": "Political articles are not posted on LinkedIn"})
    pid = db.insert_planned_post(
        news_item_id=d.get("news_id"), chart_id=d["chart_id"],
        article_id=d.get("article_id"), platform=d["platform"],
        post_type=d.get("post_type","short"), scheduled_at=sched_at,
        image_path=d.get("image_path",""), article_url=d.get("article_url",""),
        hook=d.get("hook",""))
    return jsonify({"ok":True,"id":pid})

@app.route("/api/plan_remove", methods=["POST"])
def api_plan_remove():
    db.delete_post(request.json["id"])
    return jsonify({"ok":True})

@app.route("/api/plan_generate", methods=["POST"])
def api_plan_generate():
    from generator import generate_planned
    n = generate_planned()
    log(f"Generated {n} planned posts")
    return jsonify({"ok":True,"msg":f"Generated {n} posts — review below to confirm"})

@app.route("/api/plan_generate_one", methods=["POST"])
def api_plan_generate_one():
    from generator import generate_single
    post_id = request.json.get("id")
    ok = generate_single(post_id)
    if ok:
        log(f"Generated post #{post_id}")
        return jsonify({"ok":True,"msg":"Generated — check Review section"})
    return jsonify({"ok":False,"msg":"Failed to generate — check terminal for details"})

@app.route("/api/quick_post", methods=["POST"])
def api_quick_post():
    """One-click: pick best chart for news, plan it for today, generate, send to review."""
    from generator import generate_single
    news_id = request.json.get("news_id")
    if not news_id:
        return jsonify({"ok": False, "msg": "No news_id"})
    # Get arsenal (matched charts)
    charts = db.get_arsenal_for_news(news_id)
    if not charts:
        return jsonify({"ok": False, "msg": "No matched article for this story"})
    # Pick best chart (first with image, or first text-only)
    best = charts[0]
    for c in charts:
        if c.get("image_path"):
            best = c
            break
    # Schedule for next available slot
    sched = next_available_slot()
    sched_str = sched.strftime("%Y-%m-%dT%H:%M")
    # Create planned post — skip LinkedIn for political articles
    from generator import is_linkedin_safe
    article = db.get_article(best.get("article_id", 0)) if best.get("article_id") else None
    platforms = ["x", "linkedin"] if (article and is_linkedin_safe(article)) else ["x"]
    results = []
    for platform in platforms:
        pid = db.insert_planned_post(
            news_item_id=best.get("news_id", news_id),
            chart_id=best.get("chart_id") or best.get("id", 0),
            article_id=best.get("article_id", 0),
            platform=platform, post_type="short",
            scheduled_at=sched_str,
            image_path=best.get("image_path", ""),
            article_url=best.get("article_url", ""),
            hook=best.get("hook", ""))
        # Generate immediately
        ok = generate_single(pid)
        results.append((platform, pid, ok))
    succeeded = [r for r in results if r[2]]
    if succeeded:
        log(f"Quick post generated for {', '.join(r[0] for r in succeeded)} from news #{news_id}")
        return jsonify({"ok": True, "msg": f"{len(succeeded)} post(s) generated for {sched.strftime('%H:%M')} — review below"})
    else:
        log(f"Quick post generation failed for news #{news_id}")
        return jsonify({"ok": False, "msg": "Created but generation failed — try generating manually"})

@app.route("/api/promote_article", methods=["POST"])
def api_promote_article():
    """Promote an article from Library: pick chart, match to news, generate posts for Review."""
    from generator import gen_from_chart
    d = request.json
    slug = d.get("slug")
    chart_id = d.get("chart_id")
    post_type = d.get("post_type", "short")
    if post_type not in ("short", "long"):
        post_type = "short"
    if not slug:
        return jsonify({"ok": False, "msg": "No article slug"})
    article = db.get_article_by_slug(slug)
    if not article:
        return jsonify({"ok": False, "msg": "Article not found"})
    charts = db.get_charts_for_article(slug)
    charts_with_images = [c for c in charts if c.get("image_path")]
    if not charts_with_images:
        return jsonify({"ok": False, "msg": "No charts with images for this article"})
    # Pick chart: specific one if requested, otherwise least-used with image
    if chart_id:
        target = next((c for c in charts_with_images if c["id"] == chart_id), None)
        if not target:
            return jsonify({"ok": False, "msg": "Chart not found or has no image"})
    else:
        # Pick least-used chart
        for c in charts_with_images:
            c["_uses"] = len(db.get_posts_for_chart(c["id"]))
        charts_with_images.sort(key=lambda c: c["_uses"])
        target = charts_with_images[0]
    # Generate for platforms — skip LinkedIn for political articles
    from generator import is_linkedin_safe
    sched = next_available_slot()
    sched_str = sched.strftime("%Y-%m-%dT%H:%M")
    platforms = ["x", "linkedin"] if is_linkedin_safe(article) else ["x"]
    results = []
    for platform in platforms:
        result = gen_from_chart(target["id"], platform, post_type)
        if result:
            # gen_from_chart inserts as 'draft' — promote to 'generated' with schedule
            pid = result["post_id"]
            conn = db.get_db()
            conn.execute("UPDATE posts SET status='generated', scheduled_at=? WHERE id=?",
                         (sched_str, pid))
            conn.commit()
            conn.close()
            results.append(result)
    if results:
        log(f"Promoted '{article['title'][:40]}' — {len(results)} post(s) created")
        return jsonify({"ok": True, "count": len(results),
                        "msg": f"{len(results)} post(s) created for {sched.strftime('%H:%M')} — check Review"})
    return jsonify({"ok": False, "msg": "Generation failed — check API key and news feed"})

@app.route("/api/plan_reorder", methods=["POST"])
def api_plan_reorder():
    d = request.json
    post_id = d["id"]
    scheduled_at = d["scheduled_at"]
    conn = db.get_db()
    conn.execute("UPDATE posts SET scheduled_at=? WHERE id=?", (scheduled_at, post_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/plan_clear", methods=["POST"])
def api_plan_clear():
    db.delete_planned()
    return jsonify({"ok":True})

@app.route("/api/confirm_post", methods=["POST"])
def api_confirm_post():
    db.confirm_post(request.json["id"])
    return jsonify({"ok":True})

@app.route("/api/confirm_all", methods=["POST"])
def api_confirm_all():
    n = db.confirm_all()
    return jsonify({"ok": True, "count": n})

@app.route("/api/confirm_day", methods=["POST"])
def api_confirm_day():
    db.confirm_day(request.json["date"])
    return jsonify({"ok":True})

@app.route("/api/unqueue_post", methods=["POST"])
def api_unqueue_post():
    db.unqueue_post(request.json["id"])
    return jsonify({"ok":True})

@app.route("/api/library/<path:slug>")
def api_library(slug):
    article = db.get_article_by_slug(slug)
    if not article:
        return jsonify({"error": "Not found"}), 404
    charts = db.get_charts_for_article(slug)
    # Add image URLs and usage counts
    for c in charts:
        c["image_url"] = img_url(c.get("image_path", ""))
        c["times_used"] = len(db.get_posts_for_chart(c["id"])) if c.get("id") else 0
    return jsonify({"article": article, "charts": charts})

# Curate APIs
@app.route("/api/edit", methods=["POST"])
def api_edit():
    d = request.json; post = db.get_post(d["id"])
    if post and post["caption"] != d.get("caption",""):
        db.add_feedback(post_id=d["id"],action="edit",original_caption=post["caption"][:500],
            edited_caption=d["caption"][:500],platform=post["platform"],post_type=post.get("post_type",""))
    db.update_post_caption(d["id"], d.get("caption",""), d.get("context"))
    return jsonify({"ok":True,"msg":"Saved"})

@app.route("/api/reject", methods=["POST"])
def api_reject():
    d = request.json; post = db.get_post(d["id"])
    if post:
        db.add_feedback(post_id=d["id"],action="reject",reason=d.get("reason",""),
            original_caption=post["caption"][:500],platform=post["platform"],post_type=post.get("post_type",""))
    db.delete_post(d["id"]); return jsonify({"ok":True})

@app.route("/api/post_now", methods=["POST"])
def api_post_now():
    post = db.get_post(request.json["id"])
    if not post: return jsonify({"ok":False,"msg":"Post not found"})
    if post["status"] not in ("draft","generated","queued"):
        return jsonify({"ok":False,"msg":f"Cannot post — status is '{post['status']}'"})
    prev_status = post["status"]
    db.update_post_status(post["id"],"approved")
    from poster import post_to_x, post_to_linkedin
    text = post["caption"]
    if post.get("article_url"): text += "\n" + post["article_url"]
    ok = (post_to_x if post["platform"]=="x" else post_to_linkedin)(text, post.get("image_path"))
    if ok:
        db.update_post_status(post["id"],"posted"); db.log_post(post["platform"],post["id"])
        return jsonify({"ok":True,"msg":"Posted!"})
    db.update_post_status(post["id"], prev_status)
    return jsonify({"ok":False,"msg":"Failed — check session"})


# ── Article Studio APIs ──

@app.route("/api/studio/drafts")
def api_studio_drafts():
    return jsonify(db.get_all_drafts())

@app.route("/api/studio/drafts", methods=["POST"])
def api_studio_create_draft():
    title = request.json.get("title", "").strip()
    if not title:
        return jsonify({"ok": False, "msg": "Title is required"})
    did = db.create_draft(title)
    return jsonify({"ok": True, "id": did})

@app.route("/api/studio/drafts/<int:did>")
def api_studio_get_draft(did):
    draft = db.get_draft(did)
    if not draft:
        return jsonify({"error": "Not found"}), 404
    return jsonify(draft)

@app.route("/api/studio/drafts/<int:did>", methods=["POST"])
def api_studio_update_draft(did):
    d = request.json
    fields = {}
    for k in ("title", "section", "excerpt", "share_summary", "markdown", "image_prompt", "stage", "chart_defs"):
        if k in d:
            fields[k] = d[k]
    db.update_draft(did, **fields)
    return jsonify({"ok": True})

@app.route("/api/studio/drafts/<int:did>/delete", methods=["POST"])
def api_studio_delete_draft(did):
    db.delete_draft(did)
    return jsonify({"ok": True})

@app.route("/api/studio/drafts/<int:did>/save-to-disk", methods=["POST"])
def api_studio_save_to_disk(did):
    import studio_runner
    tid = db.create_studio_task("save_to_disk", did)
    studio_runner.start_task(tid, "save_to_disk", did)
    return jsonify({"ok": True, "task_id": tid})

@app.route("/api/studio/drafts/<int:did>/generate-image", methods=["POST"])
def api_studio_generate_image(did):
    import studio_runner
    tid = db.create_studio_task("generate_image", did)
    studio_runner.start_task(tid, "generate_image", did)
    return jsonify({"ok": True, "task_id": tid})

@app.route("/api/studio/drafts/<int:did>/generate-audio", methods=["POST"])
def api_studio_generate_audio(did):
    import studio_runner
    tid = db.create_studio_task("generate_audio", did)
    studio_runner.start_task(tid, "generate_audio", did)
    return jsonify({"ok": True, "task_id": tid})

@app.route("/api/studio/drafts/<int:did>/build", methods=["POST"])
def api_studio_build(did):
    import studio_runner
    tid = db.create_studio_task("build", did)
    studio_runner.start_task(tid, "build", did)
    return jsonify({"ok": True, "task_id": tid})

@app.route("/api/studio/drafts/<int:did>/deploy", methods=["POST"])
def api_studio_deploy(did):
    import studio_runner
    tid = db.create_studio_task("deploy", did)
    studio_runner.start_task(tid, "deploy", did)
    return jsonify({"ok": True, "task_id": tid})

@app.route("/api/studio/tasks/<int:tid>")
def api_studio_task(tid):
    task = db.get_studio_task(tid)
    if not task:
        return jsonify({"error": "Not found"}), 404
    return jsonify(task)

@app.route("/api/studio/drafts/<int:did>/hero-image")
def api_studio_hero(did):
    draft = db.get_draft(did)
    if not draft:
        abort(404)
    img_dir = HFN_ARTICLE_IMAGES / draft["slug"]
    hero = img_dir / "hero.png"
    if hero.exists():
        return send_file(str(hero), mimetype="image/png")
    # Try .jpg
    hero_jpg = img_dir / "hero.jpg"
    if hero_jpg.exists():
        return send_file(str(hero_jpg), mimetype="image/jpeg")
    abort(404)

@app.route("/api/studio/drafts/<int:did>/audio")
def api_studio_audio(did):
    draft = db.get_draft(did)
    if not draft:
        abort(404)
    audio = HFN_AUDIO_DIR / f"{draft['slug']}.mp3"
    if audio.exists():
        return send_file(str(audio), mimetype="audio/mpeg")
    abort(404)

# ── Chart bootstrap JS (serves COLORS constant from chart_defs.py) ──

_chart_bootstrap_cache = None
_library_books_cache = None

@app.route("/api/studio/library-books")
def api_studio_library_books():
    """Serve the HFN library books list as JSON for Further Reading."""
    global _library_books_cache
    if _library_books_cache is None:
        try:
            import importlib, sys as _sys
            spec = importlib.util.spec_from_file_location(
                "library_data",
                str(HFN_SOURCE_DIR / "library_data.py")
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            _library_books_cache = [
                {"title": b["title"], "author": b.get("author", ""),
                 "url": b.get("url", "")}
                for b in mod.BOOKS
            ]
        except Exception as e:
            return jsonify({"books": [], "error": str(e)[:200]})
    return jsonify({"books": _library_books_cache})

@app.route("/api/studio/chart-bootstrap-js")
def api_studio_chart_bootstrap():
    global _chart_bootstrap_cache
    if _chart_bootstrap_cache is None:
        from chart_defs import COLORS as _COLORS_JS
        _chart_bootstrap_cache = _COLORS_JS
    return Response(_chart_bootstrap_cache, mimetype="application/javascript")

# ── Parse chart definitions ──

@app.route("/api/studio/drafts/<int:did>/parse-charts", methods=["POST"])
def api_studio_parse_charts(did):
    import re as _re
    data = request.get_json(silent=True) or {}
    raw = data.get("chart_defs", "")
    if not raw:
        draft = db.get_draft(did)
        if draft:
            raw = draft.get("chart_defs", "")
    if not raw:
        return jsonify({"charts": []})

    charts = []
    # Per-field extraction — fault-tolerant regex parsing of Python dict chart defs
    ids = _re.findall(r"['\"]id['\"]\s*:\s*['\"]([^'\"]+)['\"]", raw)
    fig_nums = _re.findall(r"['\"]figure_num['\"]\s*:\s*(\d+)", raw)
    titles = _re.findall(r"['\"]title['\"]\s*:\s*['\"]([^'\"]+)['\"]", raw)
    descs = _re.findall(r"['\"]desc['\"]\s*:\s*['\"]([^'\"]+)['\"]", raw)
    sources = _re.findall(r"['\"]source['\"]\s*:\s*['\"]([^'\"]+)['\"]", raw)
    positions = _re.findall(r"['\"]position['\"]\s*:\s*['\"]([^'\"]+)['\"]", raw)
    # Extract JS blocks — triple-quoted strings first, then single-quoted
    js_blocks = _re.findall(r'["\']js["\']\s*:\s*"""([\s\S]*?)"""', raw)
    if not js_blocks:
        js_blocks = _re.findall(r"['\"]js['\"]\s*:\s*'((?:[^'\\]|\\.)*)'", raw)

    n = min(len(ids), len(titles)) if ids and titles else 0
    for i in range(n):
        charts.append({
            "id": ids[i],
            "figure_num": int(fig_nums[i]) if i < len(fig_nums) else i + 1,
            "title": titles[i],
            "desc": descs[i] if i < len(descs) else "",
            "source": sources[i] if i < len(sources) else "",
            "position": positions[i] if i < len(positions) else "before_end",
            "js": js_blocks[i] if i < len(js_blocks) else ""
        })

    return jsonify({"charts": charts})

STUDIO_BASE_PROMPT = """You are an editorial collaborator for History Future Now (historyfuturenow.com).

IMPORTANT — YOUR ENVIRONMENT:
You are running inside Article Studio, a full production pipeline with automated actions.
You are NOT a plain chatbot. You have a pipeline behind you that handles:
- Saving files to disk (essays, chart definitions, frontmatter)
- Fact-checking articles (automated via a dedicated pipeline step)
- Generating hero images (automated via generation scripts)
- Generating audio narration (automated via TTS scripts)
- Building the site (automated via build.py)
- Deploying to production (automated via deploy.sh)

The user controls these via pipeline buttons in the UI. Your job is to produce the CONTENT
(article text, chart definitions, image prompts) — the pipeline handles execution.

NEVER tell the user to:
- "Paste this into a file" — you produce it, the pipeline saves it
- "Run this command" — the pipeline runs commands
- "You'll need to..." — the pipeline does it
- Claim you "can't write files" or "can't access the file system" — you can, through the pipeline
- Ask whether you're in "chat mode" or "agent mode" — you are always in the full pipeline

YOUR ROLE:
- Help the author develop article ideas through discussion
- Ask probing questions to sharpen the thesis
- Suggest historical parallels, data points, and structural approaches
- Challenge weak arguments constructively
- Actively cross-reference existing HFN articles — suggest internal links and thematic connections
- When the author says "write the draft", "go ahead", or similar, produce a FULL article draft
- When asked to define charts, produce complete chart definition code ready for chart_defs.py
- When asked about next steps, tell the user to click the pipeline buttons (Fact-Check, Generate Image, Build, Deploy)

WHEN PRODUCING A DRAFT:
- Output complete markdown with YAML frontmatter at the top:
  ---
  title: "Article Title"
  section: "Geopolitics|Economics|Technology|Society|Environment|History"
  excerpt: "2-3 sentence summary"
  share_summary: "Under 140 chars, pithy thesis"
  sources:
    - "Book Title From Library"
    - "Another Relevant Book"
    - "A New Book Not In Library"
  new_books:
    - title: "A New Book Not In Library"
      author: "Author Name"
      themes: ["economics", "politics"]
  ---
- The sources field MUST list at least 3 books. Include books from the HFN Library AND any
  additional real, published books you recommend. These populate the Further Reading section.
  Use exact titles as they appear in the library for existing books.
- The new_books field lists books in your sources that are NOT already in the HFN Library.
  For each new book provide: title (exact match to sources entry), author, and themes.
  Use theme keys from: ancient, medieval, modern, world, geopolitics, economics, politics,
  religion, science, biology, philosophy, fiction.
  Recommend 2-3 genuinely relevant, real published books per article. Do NOT invent titles.
  If all your sources are already in the library, omit the new_books field entirely.
- Include cross-references to at least 2 relevant existing HFN articles as [Title](/articles/slug) links

WHEN PRODUCING CHART DEFINITIONS:
- Wrap ALL charts in: charts['<slug>'] = [ ... ]
- Use SINGLE quotes for Python keys/strings, triple-double-quotes for js field (no r prefix)
- js field must use _regChart('chartId',()=>{ ... }) wrapper — NOT raw (()=>{ try { ... })()
- Color references: use C.accent, C.blue, C.green, C.teal, C.amber, C.purple (NOT COLORS.x)
- Shared helpers: ds(), dxy(), linX(), gridOpts, legend, tooltipStyle, chartPad, yearTick
- Annotation labels must always spread ..._al first: label:{..._al, content:'text', display:true, color:C.dim, ...}
- Year ticks must use `callback: v => String(v)` (never let Chart.js add commas to years)
- Target 2-5 charts per article covering historic-present-future arcs
- Wrap output in a ```python code fence and CLOSE it with ```
- EXAMPLE FORMAT (follow this exactly):
```
charts['article-slug'] = [
    {
        'id': 'slugChart1', 'figure_num': 1,
        'title': 'Chart Title',
        'desc': 'What this chart shows.',
        'source': 'Data source citation',
        'position': 'after_para_6',
        'js': \"""_regChart('slugChart1',()=>{const ctx=document.getElementById('slugChart1');
new Chart(ctx,{type:'line',data:{labels:['2000','2010','2020'],
datasets:[{...ds('Series',data,C.accent)}]},
options:{responsive:true,maintainAspectRatio:false,layout:{padding:chartPad},
plugins:{legend,tooltip:tooltipStyle},scales:gridOpts}});
});\"""
    },
]
```

Follow ALL the editorial rules and style guides below exactly.
"""

@app.route("/api/studio/drafts/<int:did>/messages")
def api_studio_messages(did):
    msgs = db.get_studio_messages(did)
    return jsonify(msgs)

@app.route("/api/studio/drafts/<int:did>/chat", methods=["POST"])
def api_studio_chat(did):
    import anthropic
    from config import ANTHROPIC_API_KEY

    draft = db.get_draft(did)
    if not draft:
        return jsonify({"error": "Draft not found"}), 404

    user_msg = request.json.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "Empty message"}), 400

    model_pref = request.json.get("model", "")  # "sonnet" for edits, default Opus

    db.add_studio_message(did, "user", user_msg)

    history = db.get_studio_messages(did)
    messages = [{"role": m["role"], "content": m["content"]} for m in history]

    # Build full system prompt: base + article catalog + library catalog + style guides + draft context
    # Article catalog comes before style guides so the model attends to it more reliably
    system = (STUDIO_BASE_PROMPT + "\n\n" + build_article_catalog()
              + "\n\n" + build_library_catalog() + "\n\n" + load_style_guides())
    if draft.get("markdown", "").strip():
        system += f"\n\nThe current draft in the editor is:\n\n{draft['markdown'][:6000]}"

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Sonnet for edits/corrections, Opus for original prose (with Sonnet fallback)
    if model_pref == "sonnet":
        MODELS = ["claude-sonnet-4-6"]
    else:
        MODELS = ["claude-opus-4-6", "claude-sonnet-4-6"]

    def generate():
        full_text = ""
        used_model = None
        for i, model in enumerate(MODELS):
            try:
                result = client.messages.create(
                    model=model, max_tokens=8192, system=system, messages=messages,
                )
                full_text = result.content[0].text
                used_model = model
                break
            except Exception as e:
                err_str = str(e)
                is_overloaded = "overloaded" in err_str.lower() or "529" in err_str
                if is_overloaded and i < len(MODELS) - 1:
                    continue  # Try next model
                yield f"data: {json.dumps({'error': err_str})}\n\n"
                yield "data: {\"done\": true}\n\n"
                return

        if used_model and used_model != MODELS[0]:
            yield f"data: {json.dumps({'delta': '[Using Sonnet — Opus temporarily busy]\\n\\n'})}\n\n"

        if full_text:
            # Yield in chunks for progressive rendering
            for i in range(0, len(full_text), 40):
                yield f"data: {json.dumps({'delta': full_text[i:i+40]})}\n\n"
            db.add_studio_message(did, "assistant", full_text)
            if "---\ntitle:" in full_text or full_text.strip().startswith("# "):
                db.update_draft(did, markdown=full_text)

            # Detect chart definitions in response
            _has_id = "'id':" in full_text or '"id":' in full_text
            _has_js = "'js':" in full_text or '"js":' in full_text
            if _has_id and _has_js:
                import re as _re
                # Try fenced block first (closed or unclosed), else use full text
                _m = _re.search(r"```\w*\s*\n([\s\S]*?)```", full_text)
                if not _m:
                    _m = _re.search(r"```\w*\s*\n([\s\S]*)", full_text)
                _block = _m.group(1) if _m else full_text
                _bid = "'id':" in _block or '"id":' in _block
                _bjs = "'js':" in _block or '"js":' in _block
                if _bid and _bjs:
                    db.update_draft(did, chart_defs=_block)

        yield "data: {\"done\": true}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

FACTCHECK_SYSTEM_PROMPT = """You are an editorial fact-checker for History Future Now (historyfuturenow.com).

YOUR TASK:
Systematically fact-check the article draft below. For every verifiable claim:

1. **Extract** the specific claim (quote or paraphrase)
2. **Assess** it as one of: CONFIRMED | LIKELY CORRECT | UNCERTAIN | INCORRECT
3. **Cite** the authoritative source to check against (UN DESA, World Bank, OECD, IEA, Pew, Eurobarometer, IISS, WTO, UNESCO, or other credible primary source)
4. **Suggest corrections** for any INCORRECT or UNCERTAIN claims

OUTPUT FORMAT (structured markdown):
## Fact-Check Report

**Summary:** X claims checked — Y confirmed, Z likely correct, W uncertain, V incorrect

### Claim-by-Claim Analysis

1. **Claim:** "quoted or paraphrased claim"
   - **Assessment:** CONFIRMED
   - **Source:** [Source name, date/edition]
   - **Notes:** Any relevant context

2. **Claim:** "quoted or paraphrased claim"
   - **Assessment:** INCORRECT
   - **Source:** [Source name] says [correct figure/fact]
   - **Suggested correction:** [How to fix it]

...

### Recommendations
- List any claims that need the author's attention
- Note if any claims are unverifiable and should be flagged or removed
"""

@app.route("/api/studio/drafts/<int:did>/fact-check", methods=["POST"])
def api_studio_fact_check(did):
    import anthropic
    from config import ANTHROPIC_API_KEY

    draft = db.get_draft(did)
    if not draft:
        return jsonify({"error": "Draft not found"}), 404

    markdown = (draft.get("markdown") or "").strip()
    if not markdown:
        return jsonify({"error": "No draft content to fact-check"}), 400

    # Record fact-check request as a user message
    db.add_studio_message(did, "user", "[Fact-check requested]")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    fc_models = ["claude-opus-4-6", "claude-sonnet-4-6"]
    fc_messages = [{"role": "user", "content": f"Fact-check this article draft:\n\n{markdown}"}]

    def generate():
        full_text = ""
        used_model = None
        for i, model in enumerate(fc_models):
            try:
                result = client.messages.create(
                    model=model, max_tokens=4096,
                    system=FACTCHECK_SYSTEM_PROMPT, messages=fc_messages,
                )
                full_text = result.content[0].text
                used_model = model
                break
            except Exception as e:
                err_str = str(e)
                is_overloaded = "overloaded" in err_str.lower() or "529" in err_str
                if is_overloaded and i < len(fc_models) - 1:
                    continue
                yield f"data: {json.dumps({'error': err_str})}\n\n"
                yield "data: {\"done\": true}\n\n"
                return

        if used_model and used_model != fc_models[0]:
            yield f"data: {json.dumps({'delta': '[Using Sonnet — Opus temporarily busy]\\n\\n'})}\n\n"

        if full_text:
            for i in range(0, len(full_text), 40):
                yield f"data: {json.dumps({'delta': full_text[i:i+40]})}\n\n"
            db.add_studio_message(did, "assistant", full_text)
            db.update_draft(did, stage="factcheck")

        yield "data: {\"done\": true}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.route("/preview-assets/<path:fp>")
def serve_preview(fp):
    full = HFN_SITE_OUTPUT / fp
    if full.exists():
        return send_file(str(full))
    abort(404)


# ── Auto-start scheduler on boot ──
def _start_auto_poster():
    global scheduler_ref, scheduler_on
    if scheduler_ref:
        return  # Already running
    scheduler_on = True
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    def post_due():
        import subprocess
        due = db.get_due_posts()
        if not due: return
        today_iso = date.today().isoformat()
        x_posts = [p for p in due if p["platform"] == "x"]
        li_posts = [p for p in due if p["platform"] == "linkedin"]

        # Sort: today's scheduled posts first, then overdue (catch-up)
        def _today_first(p):
            return 0 if p.get("scheduled_at", "")[:10] == today_iso else 1
        x_posts.sort(key=_today_first)
        li_posts.sort(key=_today_first)

        def _record(platform, pid, ok, msg=""):
            last_post_result.update({"time": datetime.now().isoformat(), "platform": platform,
                                     "post_id": pid, "ok": ok, "msg": msg})

        # Post LinkedIn first (no Chrome conflict)
        li_remaining = MAX_LI_PER_DAY - db.posts_today("linkedin")
        for p in li_posts:
            if li_remaining <= 0:
                log(f"Skipping #{p['id']} LinkedIn — daily limit reached"); break
            try:
                from poster import post_to_linkedin
                text = p["caption"]
                if p.get("article_url"): text += "\n" + p["article_url"]
                ok = post_to_linkedin(text, p.get("image_path"))
                if ok:
                    db.update_post_status(p["id"],"posted"); db.log_post(p["platform"],p["id"])
                    log(f"Posted #{p['id']} to LinkedIn"); _record("linkedin", p["id"], True)
                    li_remaining -= 1
                else:
                    log(f"Failed #{p['id']} LinkedIn"); _record("linkedin", p["id"], False, "post failed")
            except Exception as ex:
                log(f"Error #{p['id']} LinkedIn: {ex}"); _record("linkedin", p["id"], False, str(ex))

        # Post to X (post_to_x handles Chrome close/reopen internally)
        x_remaining = MAX_X_PER_DAY - db.posts_today("x")
        for p in x_posts:
            if x_remaining <= 0:
                log(f"Skipping #{p['id']} X — daily limit reached"); break
            try:
                from poster import post_to_x
                text = p["caption"]
                if p.get("article_url"): text += "\n" + p["article_url"]
                ok = post_to_x(text, p.get("image_path"))
                if ok:
                    db.update_post_status(p["id"],"posted"); db.log_post(p["platform"],p["id"])
                    log(f"Posted #{p['id']} to X"); _record("x", p["id"], True)
                    x_remaining -= 1
                else:
                    log(f"Failed #{p['id']} X"); _record("x", p["id"], False, "post failed")
            except Exception as ex:
                log(f"Error #{p['id']} X: {ex}"); _record("x", p["id"], False, str(ex))
    bg = BackgroundScheduler()
    bg.add_job(post_due, trigger=IntervalTrigger(minutes=5), id="ap")
    bg.start()
    scheduler_ref = bg
    log("Auto-poster started (checks every 5 min)")

if __name__ == "__main__":
    _start_auto_poster()
    log("Started — auto-poster active"); print(f"\n  HFN Promote v3.7: http://localhost:{FLASK_PORT}\n")
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)
