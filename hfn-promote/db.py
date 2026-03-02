"""HFN Promote — Database v3.3. With feedback learning, scheduling, and Article Studio."""
import sqlite3, json, re
from datetime import date, datetime
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    part TEXT DEFAULT '',
    excerpt TEXT DEFAULT '',
    keywords TEXT DEFAULT '[]',
    opening TEXT DEFAULT '',
    full_text TEXT DEFAULT '',
    word_count INTEGER DEFAULT 0,
    url TEXT DEFAULT '',
    indexed_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS charts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_slug TEXT NOT NULL,
    chart_id TEXT NOT NULL,
    figure_num INTEGER DEFAULT 0,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    source TEXT DEFAULT '',
    image_path TEXT DEFAULT '',
    indexed_at TEXT DEFAULT (datetime('now')),
    UNIQUE(article_slug, chart_id)
);
CREATE TABLE IF NOT EXISTS news_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_name TEXT NOT NULL,
    title TEXT NOT NULL,
    link TEXT UNIQUE NOT NULL,
    summary TEXT DEFAULT '',
    published TEXT DEFAULT '',
    matched_chart_id INTEGER,
    matched_article_id INTEGER,
    relevance_score REAL DEFAULT 0,
    hook TEXT DEFAULT '',
    processed INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_item_id INTEGER,
    chart_id INTEGER,
    article_id INTEGER,
    platform TEXT NOT NULL,
    caption TEXT NOT NULL,
    article_context TEXT DEFAULT '',
    article_url TEXT DEFAULT '',
    image_path TEXT DEFAULT '',
    post_type TEXT DEFAULT 'short',
    status TEXT DEFAULT 'draft',
    scheduled_at TEXT,
    posted_at TEXT,
    edit_reason TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS post_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    post_id INTEGER,
    posted_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    chart_id INTEGER,
    article_id INTEGER,
    news_item_id INTEGER,
    action TEXT NOT NULL,
    reason TEXT DEFAULT '',
    original_caption TEXT DEFAULT '',
    edited_caption TEXT DEFAULT '',
    platform TEXT DEFAULT '',
    post_type TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS article_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    section TEXT DEFAULT '',
    excerpt TEXT DEFAULT '',
    share_summary TEXT DEFAULT '',
    markdown TEXT DEFAULT '',
    stage TEXT DEFAULT 'draft',
    has_hero_image INTEGER DEFAULT 0,
    has_audio INTEGER DEFAULT 0,
    image_prompt TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS studio_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,
    draft_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    progress TEXT DEFAULT '',
    error TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT
);
"""

def _dict(row):
    if row is None: return None
    return dict(row)

def _dicts(rows):
    return [dict(r) for r in rows]

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    # Migrations for older dbs
    for col, tbl in [("scheduled_at", "posts"), ("edit_reason", "posts")]:
        try:
            conn.execute(f"SELECT {col} FROM {tbl} LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} TEXT DEFAULT ''")
    conn.commit()
    conn.close()

# ── Articles ──

def upsert_article(slug, title, part="", excerpt="", keywords=None,
                   opening="", full_text="", word_count=0, url=""):
    conn = get_db()
    conn.execute("""
        INSERT INTO articles (slug,title,part,excerpt,keywords,opening,full_text,word_count,url)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(slug) DO UPDATE SET
            title=excluded.title, part=excluded.part, excerpt=excluded.excerpt,
            keywords=excluded.keywords, opening=excluded.opening,
            full_text=excluded.full_text, word_count=excluded.word_count,
            url=excluded.url, indexed_at=datetime('now')
    """, (slug, title, part, excerpt, json.dumps(keywords or []),
          opening, full_text, word_count, url))
    conn.commit()
    rid = conn.execute("SELECT id FROM articles WHERE slug=?", (slug,)).fetchone()[0]
    conn.close()
    return rid

def get_all_articles():
    conn = get_db()
    rows = _dicts(conn.execute("SELECT * FROM articles ORDER BY part, title").fetchall())
    conn.close()
    return rows

def get_article(aid):
    conn = get_db()
    row = _dict(conn.execute("SELECT * FROM articles WHERE id=?", (aid,)).fetchone())
    conn.close()
    return row

def get_article_by_slug(slug):
    conn = get_db()
    row = _dict(conn.execute("SELECT * FROM articles WHERE slug=?", (slug,)).fetchone())
    conn.close()
    return row

# ── Charts ──

def upsert_chart(article_slug, chart_id, figure_num=0, title="",
                 description="", source="", image_path=""):
    conn = get_db()
    conn.execute("""
        INSERT INTO charts (article_slug,chart_id,figure_num,title,description,source,image_path)
        VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(article_slug,chart_id) DO UPDATE SET
            figure_num=excluded.figure_num, title=excluded.title,
            description=excluded.description, source=excluded.source,
            image_path=excluded.image_path, indexed_at=datetime('now')
    """, (article_slug, chart_id, figure_num, title, description, source, image_path))
    conn.commit()
    row = conn.execute("SELECT id FROM charts WHERE article_slug=? AND chart_id=?",
                       (article_slug, chart_id)).fetchone()
    conn.close()
    return row[0] if row else None

def get_all_charts():
    conn = get_db()
    rows = _dicts(conn.execute("SELECT * FROM charts ORDER BY article_slug, figure_num").fetchall())
    conn.close()
    return rows

def clear_charts():
    conn = get_db()
    conn.execute("DELETE FROM charts")
    conn.commit()
    conn.close()

# ── News ──

def insert_news(feed_name, title, link, summary="", published=""):
    conn = get_db()
    try:
        conn.execute("INSERT OR IGNORE INTO news_items (feed_name,title,link,summary,published) VALUES (?,?,?,?,?)",
                     (feed_name, title, link, summary, published))
        conn.commit()
        row = conn.execute("SELECT id FROM news_items WHERE link=?", (link,)).fetchone()
        conn.close()
        return row[0] if row else None
    except:
        conn.close()
        return None

def get_unprocessed_news(limit=50):
    conn = get_db()
    rows = _dicts(conn.execute("SELECT * FROM news_items WHERE processed=0 ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall())
    conn.close()
    return rows

def mark_processed(news_id, chart_id=None, article_id=None, score=0, hook=""):
    conn = get_db()
    conn.execute("UPDATE news_items SET processed=1, matched_chart_id=?, matched_article_id=?, relevance_score=?, hook=? WHERE id=?",
                 (chart_id, article_id, score, hook, news_id))
    conn.commit()
    conn.close()

def get_matched_news(min_score=0.5, limit=30):
    conn = get_db()
    rows = _dicts(conn.execute("SELECT * FROM news_items WHERE processed=1 AND relevance_score>=? ORDER BY relevance_score DESC LIMIT ?",
                               (min_score, limit)).fetchall())
    conn.close()
    return rows

# ── Posts ──

def insert_post(news_item_id=None, chart_id=None, article_id=None,
                platform="x", caption="", article_context="",
                article_url="", image_path="", post_type="short"):
    conn = get_db()
    conn.execute("""
        INSERT INTO posts (news_item_id,chart_id,article_id,platform,caption,article_context,article_url,image_path,post_type)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (news_item_id, chart_id, article_id, platform, caption, article_context, article_url, image_path, post_type))
    conn.commit()
    pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return pid

def get_post(pid):
    conn = get_db()
    row = _dict(conn.execute("SELECT * FROM posts WHERE id=?", (pid,)).fetchone())
    conn.close()
    return row

def get_drafts():
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT p.*, c.title as chart_title, c.description as chart_desc,
               a.title as article_title, a.slug as article_slug, a.part as article_part,
               n.title as news_title, n.link as news_link, n.relevance_score
        FROM posts p
        LEFT JOIN charts c ON p.chart_id = c.id
        LEFT JOIN articles a ON p.article_id = a.id
        LEFT JOIN news_items n ON p.news_item_id = n.id
        WHERE p.status='draft' ORDER BY n.relevance_score DESC, p.created_at DESC
    """).fetchall())
    conn.close()
    return rows

def get_posted():
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT p.*, c.title as chart_title, a.title as article_title, n.title as news_title
        FROM posts p
        LEFT JOIN charts c ON p.chart_id = c.id
        LEFT JOIN articles a ON p.article_id = a.id
        LEFT JOIN news_items n ON p.news_item_id = n.id
        WHERE p.status='posted' ORDER BY p.posted_at DESC
    """).fetchall())
    conn.close()
    return rows

def get_posted_extended(limit=200):
    """Posted items with full context for calendar view."""
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT p.*, c.title as chart_title, c.description as chart_desc, c.image_path as chart_image,
               a.title as article_title, a.slug as article_slug, a.part as article_part,
               n.title as news_title, n.link as news_link
        FROM posts p
        LEFT JOIN charts c ON p.chart_id = c.id
        LEFT JOIN articles a ON p.article_id = a.id
        LEFT JOIN news_items n ON p.news_item_id = n.id
        WHERE p.status='posted' ORDER BY p.posted_at DESC LIMIT ?
    """, (limit,)).fetchall())
    conn.close()
    return rows

def get_posted_filtered(platform=None, days=None, offset=0, limit=50):
    """Filtered posted items with total count for pagination."""
    conn = get_db()
    where = ["p.status='posted'"]
    params = []
    if platform:
        where.append("p.platform=?")
        params.append(platform)
    if days:
        where.append("p.posted_at >= datetime('now', ?)")
        params.append(f"-{days} days")
    where_sql = " AND ".join(where)
    total = conn.execute(f"SELECT COUNT(*) FROM posts p WHERE {where_sql}", params).fetchone()[0]
    params_q = params + [limit, offset]
    rows = _dicts(conn.execute(f"""
        SELECT p.*, c.title as chart_title, c.description as chart_desc, c.image_path as chart_image,
               a.title as article_title, a.slug as article_slug, a.part as article_part,
               n.title as news_title, n.link as news_link
        FROM posts p
        LEFT JOIN charts c ON p.chart_id = c.id
        LEFT JOIN articles a ON p.article_id = a.id
        LEFT JOIN news_items n ON p.news_item_id = n.id
        WHERE {where_sql} ORDER BY p.posted_at DESC LIMIT ? OFFSET ?
    """, params_q).fetchall())
    conn.close()
    return rows, total

def get_scheduled():
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT p.*, c.title as chart_title, c.description as chart_desc,
               a.title as article_title, a.slug as article_slug, a.part as article_part,
               n.title as news_title, n.link as news_link
        FROM posts p
        LEFT JOIN charts c ON p.chart_id = c.id
        LEFT JOIN articles a ON p.article_id = a.id
        LEFT JOIN news_items n ON p.news_item_id = n.id
        WHERE p.status='scheduled' ORDER BY p.scheduled_at ASC
    """).fetchall())
    conn.close()
    return rows

def update_post_status(post_id, status):
    conn = get_db()
    if status == "posted":
        conn.execute("UPDATE posts SET status=?, posted_at=datetime('now') WHERE id=?", (status, post_id))
    else:
        conn.execute("UPDATE posts SET status=? WHERE id=?", (status, post_id))
    conn.commit()
    conn.close()

def update_post_caption(post_id, caption, article_context=""):
    conn = get_db()
    if article_context is not None:
        conn.execute("UPDATE posts SET caption=?, article_context=? WHERE id=?",
                     (caption, article_context, post_id))
    else:
        conn.execute("UPDATE posts SET caption=? WHERE id=?", (caption, post_id))
    conn.commit()
    conn.close()

def schedule_post(post_id, scheduled_at):
    conn = get_db()
    conn.execute("UPDATE posts SET status='scheduled', scheduled_at=? WHERE id=?",
                 (scheduled_at, post_id))
    conn.commit()
    conn.close()

def unschedule_post(post_id):
    conn = get_db()
    conn.execute("UPDATE posts SET status='draft', scheduled_at=NULL WHERE id=?", (post_id,))
    conn.commit()
    conn.close()

def delete_post(post_id):
    conn = get_db()
    conn.execute("DELETE FROM posts WHERE id=?", (post_id,))
    conn.commit()
    conn.close()

def get_due_posts():
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT p.*, c.title as chart_title, a.title as article_title
        FROM posts p
        LEFT JOIN charts c ON p.chart_id = c.id
        LEFT JOIN articles a ON p.article_id = a.id
        WHERE p.status IN ('queued','scheduled') AND replace(p.scheduled_at,'T',' ') <= datetime('now')
        ORDER BY p.scheduled_at ASC
    """).fetchall())
    conn.close()
    return rows

def log_post(platform, post_id):
    conn = get_db()
    conn.execute("INSERT INTO post_log (platform,post_id) VALUES (?,?)", (platform, post_id))
    conn.commit()
    conn.close()

def posts_today(platform):
    conn = get_db()
    n = conn.execute("""SELECT COUNT(*) FROM post_log pl
                        JOIN posts p ON pl.post_id = p.id
                        WHERE pl.platform=? AND date(p.scheduled_at)=?""",
                     (platform, date.today().isoformat())).fetchone()[0]
    conn.close()
    return n

def count_news():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM news_items").fetchone()[0]
    matched = conn.execute("SELECT COUNT(*) FROM news_items WHERE relevance_score>=0.5").fetchone()[0]
    conn.close()
    return total, matched

# ── Feedback ──

def add_feedback(post_id=None, chart_id=None, article_id=None, news_item_id=None,
                 action="", reason="", original_caption="", edited_caption="",
                 platform="", post_type=""):
    conn = get_db()
    conn.execute("""
        INSERT INTO feedback (post_id,chart_id,article_id,news_item_id,action,reason,
                              original_caption,edited_caption,platform,post_type)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (post_id, chart_id, article_id, news_item_id, action, reason,
          original_caption, edited_caption, platform, post_type))
    conn.commit()
    conn.close()

def get_feedback_summary():
    """Get summary of feedback for prompt injection into generation."""
    conn = get_db()
    rejects = _dicts(conn.execute(
        "SELECT reason, platform, post_type FROM feedback WHERE action='reject' AND reason!='' ORDER BY created_at DESC LIMIT 20"
    ).fetchall())
    edits = _dicts(conn.execute(
        "SELECT original_caption, edited_caption, platform, post_type FROM feedback WHERE action='edit' ORDER BY created_at DESC LIMIT 10"
    ).fetchall())
    conn.close()
    return {"rejections": rejects, "edits": edits}

def get_charts_used_recently(days=3):
    """Get chart IDs used in scheduled/posted in last N days."""
    conn = get_db()
    rows = conn.execute("""
        SELECT DISTINCT chart_id FROM posts
        WHERE status IN ('scheduled','posted')
        AND (scheduled_at >= datetime('now', ?) OR posted_at >= datetime('now', ?))
    """, (f"-{days} days", f"-{days} days")).fetchall()
    conn.close()
    return {r[0] for r in rows}

def get_chart_usage_stats():
    """Usage counts per chart for the heatmap: 7d and 30d."""
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT c.id, c.title, c.article_slug, c.image_path,
            SUM(CASE WHEN p.posted_at >= datetime('now','-7 days') THEN 1 ELSE 0 END) as uses_7d,
            SUM(CASE WHEN p.posted_at >= datetime('now','-30 days') THEN 1 ELSE 0 END) as uses_30d
        FROM charts c
        LEFT JOIN posts p ON p.chart_id = c.id AND p.status = 'posted'
        WHERE c.image_path != ''
        GROUP BY c.id
        ORDER BY uses_30d DESC, c.article_slug, c.figure_num
    """).fetchall())
    conn.close()
    return rows

def get_charts_for_article(article_slug):
    conn = get_db()
    rows = _dicts(conn.execute(
        "SELECT * FROM charts WHERE article_slug=? ORDER BY figure_num", (article_slug,)).fetchall())
    conn.close()
    return rows

def get_chart(chart_id):
    conn = get_db()
    row = _dict(conn.execute("SELECT * FROM charts WHERE id=?", (chart_id,)).fetchone())
    conn.close()
    return row

def get_articles_with_chart_counts():
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT a.*, COUNT(c.id) as chart_count,
               SUM(CASE WHEN c.image_path != '' THEN 1 ELSE 0 END) as image_count
        FROM articles a
        LEFT JOIN charts c ON c.article_slug = a.slug
        GROUP BY a.id ORDER BY a.part, a.title
    """).fetchall())
    conn.close()
    return rows

def get_posts_for_chart(chart_id):
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT p.*, n.title as news_title FROM posts p
        LEFT JOIN news_items n ON p.news_item_id = n.id
        WHERE p.chart_id=? AND p.status != 'rejected'
        ORDER BY p.created_at DESC
    """, (chart_id,)).fetchall())
    conn.close()
    return rows

def get_recent_news_for_matching(limit=20):
    """Get recent news items that could be matched to a chart."""
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT * FROM news_items ORDER BY created_at DESC LIMIT ?
    """, (limit,)).fetchall())
    conn.close()
    return rows

def get_news_ranked():
    """Get news items ranked by time-decayed relevance. Newer stories beat stale ones."""
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT n.*,
            (SELECT COUNT(*) FROM news_items n2
             WHERE n2.title = n.title OR n2.link = n.link) as feed_count,
            ROUND(julianday('now') - julianday(n.created_at), 2) as age_days,
            ROUND(
                n.relevance_score * (1.0 / (1.0 + (julianday('now') - julianday(n.created_at)) * 0.5))
            , 3) as decayed_score
        FROM news_items n
        WHERE n.processed = 1 AND n.relevance_score >= 0.3
          AND julianday('now') - julianday(n.created_at) < 7
        ORDER BY decayed_score DESC, feed_count DESC
        LIMIT 60
    """).fetchall())
    conn.close()
    return rows

def get_matches_for_news(news_id):
    """Get chart + article match info for a specific news item."""
    conn = get_db()
    row = _dict(conn.execute("""
        SELECT n.*, c.id as chart_id, c.title as chart_title, c.description as chart_desc,
               c.image_path, c.article_slug,
               a.id as article_id, a.title as article_title, a.part as article_part, a.url as article_url
        FROM news_items n
        LEFT JOIN charts c ON n.matched_chart_id = c.id
        LEFT JOIN articles a ON n.matched_article_id = a.id
        WHERE n.id = ?
    """, (news_id,)).fetchone())
    conn.close()
    return row

def get_all_matches_grouped():
    """Get all matched news grouped by chart for the planner arsenal view.
    Uses article slug to find charts (matched_chart_id may be stale)."""
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT n.id as news_id, n.title as news_title, n.relevance_score, n.hook,
               n.feed_name, n.created_at as news_date,
               c.id as chart_id, c.title as chart_title, c.description as chart_desc,
               c.image_path, c.article_slug,
               a.id as article_id, a.title as article_title, a.part as article_part, a.url as article_url
        FROM news_items n
        JOIN articles a ON n.matched_article_id = a.id
        JOIN charts c ON c.article_slug = a.slug AND c.image_path != ''
        WHERE n.processed = 1 AND n.relevance_score >= 0.4
        ORDER BY n.relevance_score DESC
    """).fetchall())
    conn.close()
    return rows

def get_arsenal_for_news(news_id):
    """Get all charts from the article matched to a specific news item.
    If article has no charts, returns one entry with article info for text-only posts."""
    conn = get_db()
    news = _dict(conn.execute(
        "SELECT * FROM news_items WHERE id=?", (news_id,)).fetchone())
    if not news or not news.get("matched_article_id"):
        conn.close()
        return []
    article = _dict(conn.execute(
        "SELECT * FROM articles WHERE id=?", (news["matched_article_id"],)).fetchone())
    if not article:
        conn.close()
        return []
    slug = article["slug"]
    # Get all charts for that article (with images)
    charts = _dicts(conn.execute("""
        SELECT c.*, ? as news_id, ? as news_title, ? as hook, ? as relevance_score,
               a.title as article_title, a.part as article_part, a.url as article_url
        FROM charts c
        JOIN articles a ON c.article_slug = a.slug
        WHERE c.article_slug = ? AND c.image_path != ''
        ORDER BY c.figure_num
    """, (news["id"], news["title"], news.get("hook",""), news.get("relevance_score",0),
          slug)).fetchall())
    # If no charts, return article-only entry for text posts
    if not charts:
        charts = [{
            "id": 0, "title": article["title"], "description": article.get("excerpt",""),
            "image_path": "", "article_slug": slug, "figure_num": 0,
            "news_id": news["id"], "news_title": news["title"],
            "hook": news.get("hook",""), "relevance_score": news.get("relevance_score",0),
            "article_title": article["title"], "article_part": article.get("part",""),
            "article_url": article.get("url",""), "article_id": article["id"],
            "text_only": True
        }]
    conn.close()
    return charts

def insert_planned_post(news_item_id, chart_id, article_id, platform, post_type,
                        scheduled_at, image_path="", article_url="", hook=""):
    """Insert a post in 'planned' status — not yet generated."""
    conn = get_db()
    conn.execute("""
        INSERT INTO posts (news_item_id, chart_id, article_id, platform, post_type,
                          status, scheduled_at, image_path, article_url, caption, article_context)
        VALUES (?,?,?,?,?,'planned',?,?,?,?,?)
    """, (news_item_id, chart_id, article_id, platform, post_type,
          scheduled_at, image_path, article_url, hook, ""))
    conn.commit()
    pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return pid

def get_planned_posts():
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT p.*, c.title as chart_title, c.description as chart_desc, c.image_path as chart_image,
               a.title as article_title, a.url as article_url_joined,
               n.title as news_title, n.hook
        FROM posts p
        LEFT JOIN charts c ON p.chart_id = c.id
        LEFT JOIN articles a ON p.article_id = a.id
        LEFT JOIN news_items n ON p.news_item_id = n.id
        WHERE p.status = 'planned'
        ORDER BY p.scheduled_at ASC
    """).fetchall())
    conn.close()
    return rows

def get_generated_posts():
    """Posts with generated text awaiting review/confirmation."""
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT p.*, c.title as chart_title, c.description as chart_desc, c.image_path as chart_image,
               a.title as article_title, a.url as article_url_joined, a.part as article_part,
               n.title as news_title, n.hook
        FROM posts p
        LEFT JOIN charts c ON p.chart_id = c.id
        LEFT JOIN articles a ON p.article_id = a.id
        LEFT JOIN news_items n ON p.news_item_id = n.id
        WHERE p.status = 'generated'
        ORDER BY p.scheduled_at ASC
    """).fetchall())
    conn.close()
    return rows

def get_queued_posts():
    """Confirmed posts ready to auto-post."""
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT p.*, c.title as chart_title, c.description as chart_desc, c.image_path as chart_image,
               a.title as article_title, a.url as article_url_joined, a.part as article_part,
               n.title as news_title, n.hook
        FROM posts p
        LEFT JOIN charts c ON p.chart_id = c.id
        LEFT JOIN articles a ON p.article_id = a.id
        LEFT JOIN news_items n ON p.news_item_id = n.id
        WHERE p.status = 'queued'
        ORDER BY p.scheduled_at ASC
    """).fetchall())
    conn.close()
    return rows

def confirm_post(post_id):
    """Move a generated post to queued status."""
    conn = get_db()
    conn.execute("UPDATE posts SET status='queued' WHERE id=? AND status='generated'", (post_id,))
    conn.commit()
    conn.close()

def confirm_all():
    """Confirm all generated posts (move to queued)."""
    conn = get_db()
    cur = conn.execute("UPDATE posts SET status='queued' WHERE status='generated'")
    n = cur.rowcount
    conn.commit()
    conn.close()
    return n

def confirm_day(date_iso):
    """Confirm all generated posts for a specific day."""
    conn = get_db()
    conn.execute("""UPDATE posts SET status='queued'
        WHERE status='generated' AND date(scheduled_at)=?""", (date_iso,))
    conn.commit()
    conn.close()

def unqueue_post(post_id):
    """Move a queued post back to generated for re-editing."""
    conn = get_db()
    conn.execute("UPDATE posts SET status='generated' WHERE id=? AND status='queued'", (post_id,))
    conn.commit()
    conn.close()

def delete_planned():
    """Clear all planned posts (reset the plan)."""
    conn = get_db()
    conn.execute("DELETE FROM posts WHERE status='planned'")
    conn.commit()
    conn.close()

# ── Article Studio ──

def slugify(title):
    s = title.lower().strip()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s-]+', '-', s).strip('-')
    return s[:80]

def create_draft(title):
    slug = slugify(title)
    conn = get_db()
    # Ensure unique slug
    base = slug
    n = 1
    while conn.execute("SELECT 1 FROM article_drafts WHERE slug=?", (slug,)).fetchone():
        slug = f"{base}-{n}"
        n += 1
    conn.execute("INSERT INTO article_drafts (slug, title) VALUES (?, ?)", (slug, title))
    conn.commit()
    rid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return rid

def get_draft(did):
    conn = get_db()
    row = _dict(conn.execute("SELECT * FROM article_drafts WHERE id=?", (did,)).fetchone())
    conn.close()
    return row

def get_all_drafts():
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT id, slug, title, section, excerpt, share_summary, stage,
               has_hero_image, has_audio, image_prompt,
               created_at, updated_at,
               CASE WHEN markdown = '' THEN 0
                    ELSE LENGTH(TRIM(markdown)) - LENGTH(REPLACE(TRIM(markdown), ' ', '')) + 1
               END as word_count
        FROM article_drafts ORDER BY updated_at DESC
    """).fetchall())
    conn.close()
    return rows

def update_draft(did, **fields):
    if not fields:
        return
    allowed = {"title", "slug", "section", "excerpt", "share_summary",
               "markdown", "stage", "has_hero_image", "has_audio", "image_prompt"}
    sets = []
    vals = []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k}=?")
            vals.append(v)
    if not sets:
        return
    sets.append("updated_at=datetime('now')")
    vals.append(did)
    conn = get_db()
    conn.execute(f"UPDATE article_drafts SET {', '.join(sets)} WHERE id=?", vals)
    conn.commit()
    conn.close()

def delete_draft(did):
    conn = get_db()
    conn.execute("DELETE FROM article_drafts WHERE id=?", (did,))
    conn.execute("DELETE FROM studio_tasks WHERE draft_id=?", (did,))
    conn.commit()
    conn.close()

def create_studio_task(task_type, draft_id):
    conn = get_db()
    conn.execute("INSERT INTO studio_tasks (task_type, draft_id) VALUES (?, ?)",
                 (task_type, draft_id))
    conn.commit()
    tid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return tid

def get_studio_task(tid):
    conn = get_db()
    row = _dict(conn.execute("SELECT * FROM studio_tasks WHERE id=?", (tid,)).fetchone())
    conn.close()
    return row

def update_studio_task(tid, **fields):
    allowed = {"status", "progress", "error", "completed_at"}
    sets = []
    vals = []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k}=?")
            vals.append(v)
    if not sets:
        return
    vals.append(tid)
    conn = get_db()
    conn.execute(f"UPDATE studio_tasks SET {', '.join(sets)} WHERE id=?", vals)
    conn.commit()
    conn.close()

init_db()
