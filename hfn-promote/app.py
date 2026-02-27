"""HFN Promote v3.11 — Library: Promote Article to generate posts."""
import sys
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, send_file, abort
import db
from config import (FLASK_PORT, MAX_X_PER_DAY, MAX_LI_PER_DAY,
                    HFN_SOURCE_DIR, HFN_ARTICLE_IMAGES, MONITOR_INTERVAL,
                    MATCH_MODEL, GEN_MODEL, SESSIONS_DIR)

# Import issues from build system
_build_sys = str(Path(__file__).resolve().parent.parent / "hfn-build-system")
if _build_sys not in sys.path:
    sys.path.insert(0, _build_sys)
from issues import ISSUES, build_slug_to_issue_map

app = Flask(__name__)
activity_log = []
scheduler_ref = None
scheduler_on = True
last_post_result = {"time": None, "platform": None, "post_id": None, "ok": None, "msg": ""}

def log(msg):
    activity_log.insert(0, {"t": datetime.now().strftime("%H:%M:%S"), "m": msg})
    if len(activity_log) > 100: activity_log.pop()

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
body.dark .qcal-card{background:var(--card);border-color:var(--border);border-top-color:var(--accent);box-shadow:0 1px 3px rgba(0,0,0,.2)}
body.dark .qcal-card:hover{box-shadow:0 3px 8px rgba(0,0,0,.3)}
body.dark .qcal-dayhead{background:#2a2623;color:#a8a29e;border-color:var(--border)}
body.dark .qcal-dayhead.today{background:#3a2020;color:var(--accent);border-color:var(--accent)}
body.dark .qcal-slots{border-color:var(--border)}
body.dark .qcal-slots.over{background:#3a2020;border-color:var(--accent)}
body.dark .qcal-type{background:#3a3632;color:#a8a29e}
body.dark .qcal-article{color:var(--text)}
.toast a{color:#60a5fa;text-decoration:underline;margin-left:8px;cursor:pointer}
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
          <span style="font-size:.65rem;color:var(--dim)" id="day-count-{{day.idx}}">{% if day.posts|length > 0 %}{{day.posts|length}} post{{ 's' if day.posts|length != 1 else '' }}{% endif %}</span>
        </div>
        <div class="tl-slots" id="day-{{day.idx}}"
             ondragover="event.preventDefault();this.classList.add('over')"
             ondragleave="this.classList.remove('over')"
             ondrop="dropOnDay(event,{{day.idx}},'{{day.iso}}')">
          {% for sp in day.posts %}
          {% if sp.status == 'planned' %}
          <div class="tl-slot {{sp.platform}}" id="sl-{{sp.id}}">
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
          <div class="tl-slot {{sp.platform}} {{sp.status}}" title="{{sp.status|title}} — managed in {{('Review' if sp.status=='generated' else 'Queue')}} tab">
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
          {% endfor %}
          {% set plan_only = day.posts|selectattr('status','equalto','planned')|list %}
          {% if not day.posts %}<div class="tl-empty" id="empty-{{day.idx}}">{% if day.is_today %}← Click a story, pick a chart, drag here{% else %}Drop here{% endif %}</div>{% endif %}
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
  {% if not queue_days %}
  <div class="empty"><div class="ei">📅</div>No posts queued<br><span style="font-size:.78rem;color:var(--dim)">Confirm reviewed posts to add them to the queue</span></div>
  {% else %}
  <div class="qcal">
    {% for day in cal_days %}
    <div class="qcal-day">
      <div class="qcal-dayhead {{ 'today' if day.is_today else '' }}">{{day.label}} {{day.date}}</div>
      <div class="qcal-slots" data-iso="{{day.iso}}" ondragover="event.preventDefault();this.classList.add('over')" ondragleave="this.classList.remove('over')" ondrop="queueDrop(event,this)">
        {% set ns = namespace(found=false) %}
        {% for qd in queue_days if qd.iso == day.iso %}
          {% set ns.found = true %}
          {% for p in qd.posts %}
          <div class="qcal-card" id="qc-{{p.id}}" data-post-id="{{p.id}}" draggable="true" onclick="if(!window._qcalDragged)this.classList.toggle('expanded')">
            <div class="qcal-meta">
              <span class="qcal-time">{{p.time}}</span>
              <span class="plat {{p.platform}}" style="font-size:.52rem;padding:1px 5px">{{ '𝕏' if p.platform=='x' else 'LI' }}</span>
              <span class="qcal-type">{{p.post_type|upper}}</span>
              <span class="rq-countdown" data-sched="{{qd.iso}}T{{p.time}}:00" style="margin-left:auto"></span>
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
          {% endfor %}
        {% endfor %}
        {% if not ns.found %}
        <div class="qcal-empty">no posts</div>
        {% endif %}
      </div>
    </div>
    {% endfor %}
  </div>
  {% endif %}
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
            <span class="opt-pill li-sel" data-v="li" onclick="togglePill(this)">LinkedIn</span>
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
function dropOnDay(event,dayIdx,dayIso){
  event.preventDefault();
  const el=document.getElementById('day-'+dayIdx);
  el.classList.remove('over');
  if(!dragData)return;
  // Assign times: 09:00 for first, 13:00 for second, 17:00 for third, etc
  const existing=el.querySelectorAll('.tl-slot').length;
  const hours=['09:00','13:00','17:00','20:00'];
  const time=hours[Math.min(existing,hours.length-1)];
  for(const plat of dragData.platforms){
    addToPlan(dragData,plat,dragData.post_type,dayIso,time,dayIdx);
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
    const emp=document.getElementById('empty-'+dayIdx);if(emp)emp.remove();
    el.innerHTML+=`<div class="tl-slot ${platform}" id="sl-${d.id}">
      <span class="sl-time">${time}</span>
      <span class="plat ${platform}" style="font-size:.58rem">${platform==='x'?'𝕏':'LI'}</span>
      <div class="sl-body">
        <div class="sl-title">${match.chart_title||match.title||'Post'}</div>
        <div class="sl-hook">${(match.hook||'').substring(0,100)}</div>
      </div>
      <span class="sl-type">${postType.toUpperCase()}</span>
      <button class="btn sm sl-gen" onclick="generateOne(${d.id},this)" title="Generate this post">✍️</button>
      <span class="sl-rm" onclick="removePlan(${d.id})">✕</span></div>`;
    toast('Added to plan');
  }
}
async function removePlan(id){
  await fetch('/api/plan_remove',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
  const el=document.getElementById('sl-'+id);if(el)el.remove();
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
        ${d.charts.some(c=>c.image_path)?'<button class="lib-promote-btn" onclick="promoteArticle(\''+slug+'\',null,this)">⚡ Promote</button>':''}
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
  toast('Generating posts from article...',30000);
  try{
    const r=await fetch('/api/promote_article',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({slug,chart_id:chartId||null})});
    const d=await r.json();
    if(d.ok){toast(d.msg,4000,true);setTimeout(()=>{document.querySelector('.tab[data-t="review"]')?.click()},1500);}
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
async function reorderSlot(slotId,newIso,dayIdx){
  const id=parseInt(slotId.replace('sl-',''));
  const existing=document.getElementById('day-'+dayIdx).querySelectorAll('.tl-slot').length;
  const hours=['09:00','13:00','17:00','20:00'];
  const time=hours[Math.min(existing,hours.length-1)];
  const scheduledAt=newIso+'T'+time;
  const r=await fetch('/api/plan_reorder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,scheduled_at:scheduledAt})});
  const d=await r.json();
  if(d.ok){
    const slot=document.getElementById(slotId);if(slot){
      slot.querySelector('.sl-time').textContent=time;
      const target=document.getElementById('day-'+dayIdx);
      const emp=document.getElementById('empty-'+dayIdx);if(emp)emp.remove();
      target.appendChild(slot);
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
    reorderSlot(slotId,dayIso,dayIdx);return;
  }
  origDropOnDay(event,dayIdx,dayIso);
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
async function queueDrop(event,slotsEl){
  event.preventDefault();slotsEl.classList.remove('over');
  const raw=event.dataTransfer.getData('text/plain');
  if(!raw||!raw.startsWith('qc-'))return;
  const postId=parseInt(raw.replace('qc-',''));
  const card=document.getElementById('qc-'+postId);if(!card)return;
  const newIso=slotsEl.dataset.iso;
  const existing=slotsEl.querySelectorAll('.qcal-card').length;
  const hours=['09:00','13:00','17:00','20:00'];
  const time=hours[Math.min(existing,hours.length-1)];
  const scheduledAt=newIso+'T'+time;
  const r=await fetch('/api/plan_reorder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:postId,scheduled_at:scheduledAt})});
  const d=await r.json();
  if(d.ok){
    // Remove empty placeholder from target
    const emp=slotsEl.querySelector('.qcal-empty');if(emp)emp.remove();
    // Check if old parent needs empty placeholder
    const oldSlots=card.closest('.qcal-slots');
    slotsEl.appendChild(card);
    if(oldSlots&&!oldSlots.querySelector('.qcal-card')){
      const ph=document.createElement('div');ph.className='qcal-empty';ph.textContent='no posts';
      oldSlots.appendChild(ph);
    }
    // Update time label
    const timeEl=card.querySelector('.qcal-time');if(timeEl)timeEl.textContent=time;
    // Update countdown data attribute
    const cdEl=card.querySelector('.rq-countdown');if(cdEl)cdEl.dataset.sched=scheduledAt+':00';
    toast('Moved to '+newIso);
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
        cal_days.append({"date": d.strftime("%d %b"), "label": day_names[d.weekday()],
                         "is_today": d == today, "posts": day_posts,
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

    return render_template_string(HTML,
        sched=scheduler_on,
        match_model=MATCH_MODEL.split("-")[1] if "-" in MATCH_MODEL else MATCH_MODEL[:15],
        gen_model=GEN_MODEL.split("-")[1] if "-" in GEN_MODEL else GEN_MODEL[:15],
        na=len(articles), nc=len(charts), nn=nn, nm=nm,
        ns=len(generated)+len(queued)+len(planned), np=len(posted),
        xt=db.posts_today("x"), lt=db.posts_today("linkedin"),
        mx=MAX_X_PER_DAY, ml=MAX_LI_PER_DAY,
        news=news,
        posted=posted[:30], cal_days=cal_days,
        review_days=review_days, queue_days=queue_days,
        n_generated=len(generated), n_queued=len(queued),
        articles_with_charts=articles_with_charts,
        total_charts=total_charts, total_images=total_images,
        issues=ISSUES, issues_with_articles=issues_with_articles,
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
    pid = db.insert_planned_post(
        news_item_id=d.get("news_id"), chart_id=d["chart_id"],
        article_id=d.get("article_id"), platform=d["platform"],
        post_type=d.get("post_type","short"), scheduled_at=d["scheduled_at"],
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
    # Schedule for next available slot today
    from datetime import datetime, timedelta
    now = datetime.now()
    # Round up to next hour
    sched = now.replace(minute=0, second=0) + timedelta(hours=1)
    if sched.hour >= 22:
        sched = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0)
    sched_str = sched.strftime("%Y-%m-%dT%H:%M")
    # Create planned post for both platforms
    results = []
    for platform in ["x", "linkedin"]:
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
    # Generate for both platforms using gen_from_chart (handles news matching + generation)
    results = []
    for platform in ["x", "linkedin"]:
        result = gen_from_chart(target["id"], platform, "short")
        if result:
            results.append(result)
    if results:
        log(f"Promoted '{article['title'][:40]}' — {len(results)} post(s) created")
        return jsonify({"ok": True, "count": len(results),
                        "msg": f"{len(results)} post(s) created — check Review"})
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
        x_posts = [p for p in due if p["platform"] == "x"]
        li_posts = [p for p in due if p["platform"] == "linkedin"]

        def _record(platform, pid, ok, msg=""):
            last_post_result.update({"time": datetime.now().isoformat(), "platform": platform,
                                     "post_id": pid, "ok": ok, "msg": msg})

        # Post LinkedIn first (no Chrome conflict)
        for p in li_posts:
            from poster import post_to_linkedin
            text = p["caption"]
            if p.get("article_url"): text += "\n" + p["article_url"]
            ok = post_to_linkedin(text, p.get("image_path"))
            if ok:
                db.update_post_status(p["id"],"posted"); db.log_post(p["platform"],p["id"])
                log(f"Posted #{p['id']} to LinkedIn"); _record("linkedin", p["id"], True)
            else:
                log(f"Failed #{p['id']} LinkedIn"); _record("linkedin", p["id"], False, "post failed")

        # For X posts: close Chrome, post, reopen Chrome
        if x_posts:
            chrome_was_running = False
            try:
                result = subprocess.run(["pgrep", "-x", "Google Chrome"], capture_output=True)
                chrome_was_running = result.returncode == 0
            except: pass

            if chrome_was_running:
                log("Closing Chrome for X posting...")
                subprocess.run(["osascript", "-e", 'tell application "Google Chrome" to quit'], capture_output=True)
                import time; time.sleep(3)

            for p in x_posts:
                from poster import post_to_x
                text = p["caption"]
                if p.get("article_url"): text += "\n" + p["article_url"]
                ok = post_to_x(text, p.get("image_path"))
                if ok:
                    db.update_post_status(p["id"],"posted"); db.log_post(p["platform"],p["id"])
                    log(f"Posted #{p['id']} to X"); _record("x", p["id"], True)
                else:
                    log(f"Failed #{p['id']} X"); _record("x", p["id"], False, "post failed")

            if chrome_was_running:
                log("Reopening Chrome...")
                subprocess.Popen(["open", "-a", "Google Chrome"])
    bg = BackgroundScheduler()
    bg.add_job(post_due, trigger=IntervalTrigger(minutes=5), id="ap")
    bg.start()
    scheduler_ref = bg
    log("Auto-poster started (checks every 5 min)")

if __name__ == "__main__":
    _start_auto_poster()
    log("Started — auto-poster active"); print(f"\n  HFN Promote v3.7: http://localhost:{FLASK_PORT}\n")
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)
