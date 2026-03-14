"""HFN Promote — Database v3.4. With feedback learning, scheduling, Article Studio, and Strategic Series."""
import sqlite3, json, re
from contextlib import contextmanager
from datetime import date, datetime, timedelta
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
    chart_defs TEXT DEFAULT '',
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
CREATE TABLE IF NOT EXISTS studio_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    series_id INTEGER DEFAULT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT UNIQUE,
    status TEXT DEFAULT 'planning',
    thesis TEXT DEFAULT '',
    strategic_goal TEXT DEFAULT '',
    audience TEXT DEFAULT '',
    narrative_arc TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS chat_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER,
    series_id INTEGER,
    filename TEXT NOT NULL,
    mime_type TEXT DEFAULT '',
    file_size INTEGER DEFAULT 0,
    extracted_text TEXT DEFAULT '',
    is_image INTEGER DEFAULT 0,
    image_base64 TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS series_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id INTEGER NOT NULL,
    draft_id INTEGER DEFAULT NULL,
    position INTEGER DEFAULT 0,
    working_title TEXT NOT NULL,
    role TEXT DEFAULT '',
    brief TEXT DEFAULT '',
    key_arguments TEXT DEFAULT '',
    connects_to TEXT DEFAULT '',
    status TEXT DEFAULT 'planned',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (series_id) REFERENCES series(id),
    FOREIGN KEY (draft_id) REFERENCES article_drafts(id)
);
CREATE TABLE IF NOT EXISTS post_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL UNIQUE,
    clicks_7d INTEGER DEFAULT 0,
    clicks_30d INTEGER DEFAULT 0,
    users_7d INTEGER DEFAULT 0,
    users_30d INTEGER DEFAULT 0,
    bounce_rate REAL DEFAULT NULL,
    avg_session_duration REAL DEFAULT NULL,
    last_fetched TEXT DEFAULT '',
    FOREIGN KEY (post_id) REFERENCES posts(id)
);
CREATE TABLE IF NOT EXISTS strategy_wins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    winning_strategy TEXT NOT NULL,
    losing_strategy TEXT NOT NULL,
    win_clicks INTEGER DEFAULT 0,
    lose_clicks INTEGER DEFAULT 0,
    decided_at TEXT DEFAULT (datetime('now')),
    UNIQUE(article_id, platform, winning_strategy, losing_strategy)
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

@contextmanager
def get_db_ctx():
    """Context manager for DB connections — guarantees close on exception."""
    conn = get_db()
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    # Migrations for older dbs
    for col, tbl in [("scheduled_at", "posts"), ("edit_reason", "posts")]:
        try:
            conn.execute(f"SELECT {col} FROM {tbl} LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} TEXT DEFAULT ''")
    # Add chart_defs column for existing DBs
    for col, tbl in [("chart_defs", "article_drafts")]:
        try:
            conn.execute(f"SELECT {col} FROM {tbl} LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} TEXT DEFAULT ''")
    # Add series_article_id to article_drafts
    for col, tbl, default in [("series_article_id", "article_drafts", "NULL"),
                               ("series_id", "studio_messages", "NULL")]:
        try:
            conn.execute(f"SELECT {col} FROM {tbl} LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} INTEGER DEFAULT {default}")
    # Hook strategy + A/B testing columns
    for col, tbl, default in [("hook_strategy", "posts", "''"),
                               ("variant_group", "posts", "''")]:
        try:
            conn.execute(f"SELECT {col} FROM {tbl} LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} TEXT DEFAULT {default}")
    # Article lifecycle columns
    for col, tbl, default in [("published_at", "articles", "''"),
                               ("last_promoted_at", "articles", "''")]:
        try:
            conn.execute(f"SELECT {col} FROM {tbl} LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} TEXT DEFAULT {default}")
    # Engagement depth columns on post_performance
    for col, tbl in [("bounce_rate", "post_performance"),
                      ("avg_session_duration", "post_performance")]:
        try:
            conn.execute(f"SELECT {col} FROM {tbl} LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} REAL DEFAULT NULL")
    # Error tracking columns
    for col, tbl, default in [("last_error", "posts", "''"),
                               ("error_category", "posts", "''"),
                               ("retry_count", "posts", "0"),
                               ("last_attempt_at", "posts", "''")]:
        try:
            conn.execute(f"SELECT {col} FROM {tbl} LIMIT 1")
        except sqlite3.OperationalError:
            if default in ("0",):
                conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} INTEGER DEFAULT {default}")
            else:
                conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} TEXT DEFAULT {default}")
    # Confidence score for auto-confirm
    for col, tbl, default in [("confidence_score", "posts", "0.0")]:
        try:
            conn.execute(f"SELECT {col} FROM {tbl} LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} REAL DEFAULT {default}")
    # Migrate legacy 'audio' stage to 'images' (audio decoupled from pipeline)
    conn.execute("UPDATE article_drafts SET stage='images' WHERE stage='audio'")
    # Article archive/soft-delete columns
    for col, tbl, default in [("status", "articles", "'published'"),
                               ("archived_at", "articles", "NULL")]:
        try:
            conn.execute(f"SELECT {col} FROM {tbl} LIMIT 1")
        except sqlite3.OperationalError:
            if "NULL" in default:
                conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} TEXT DEFAULT {default}")
            else:
                conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} TEXT DEFAULT {default}")
    # Backfill status for existing articles (one-time)
    conn.execute("UPDATE articles SET status='published' WHERE status IS NULL OR status=''")
    # Backfill published_at from indexed_at for existing articles (one-time)
    conn.execute("UPDATE articles SET published_at=indexed_at WHERE published_at IS NULL OR published_at=''")
    conn.commit()
    conn.close()

# ── Articles ──

def upsert_article(slug, title, part="", excerpt="", keywords=None,
                   opening="", full_text="", word_count=0, url=""):
    conn = get_db()
    conn.execute("""
        INSERT INTO articles (slug,title,part,excerpt,keywords,opening,full_text,word_count,url,published_at)
        VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))
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

def archive_article(slug):
    conn = get_db()
    conn.execute("UPDATE articles SET status='archived', archived_at=datetime('now') WHERE slug=?", (slug,))
    conn.commit()
    conn.close()

def soft_delete_article(slug):
    conn = get_db()
    conn.execute("UPDATE articles SET status='deleted', archived_at=datetime('now') WHERE slug=?", (slug,))
    conn.commit()
    conn.close()

def restore_article(slug):
    conn = get_db()
    conn.execute("UPDATE articles SET status='published', archived_at=NULL WHERE slug=?", (slug,))
    conn.commit()
    conn.close()

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
    except Exception as e:
        print(f"  [!] insert_news error for '{title[:60]}': {e}")
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
                article_url="", image_path="", post_type="short",
                hook_strategy="", variant_group="", confidence_score=0.0):
    conn = get_db()
    conn.execute("""
        INSERT INTO posts (news_item_id,chart_id,article_id,platform,caption,article_context,article_url,image_path,post_type,hook_strategy,variant_group,confidence_score)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (news_item_id, chart_id, article_id, platform, caption, article_context, article_url, image_path, post_type, hook_strategy, variant_group, confidence_score))
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
        SELECT p.*, c.title as chart_title, a.title as article_title, a.url as article_url_joined
        FROM posts p
        LEFT JOIN charts c ON p.chart_id = c.id
        LEFT JOIN articles a ON p.article_id = a.id
        WHERE p.status IN ('queued','scheduled') AND replace(p.scheduled_at,'T',' ') <= datetime('now')
        ORDER BY p.scheduled_at ASC
    """).fetchall())
    conn.close()
    return rows

def get_due_unready_posts():
    """Fetch posts with status planned/generated whose scheduled_at <= now."""
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT p.*, c.title as chart_title, a.title as article_title, a.url as article_url_joined
        FROM posts p
        LEFT JOIN charts c ON p.chart_id = c.id
        LEFT JOIN articles a ON p.article_id = a.id
        WHERE p.status IN ('planned','generated') AND replace(p.scheduled_at,'T',' ') <= datetime('now')
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

def get_articles_with_chart_counts(include_hidden=False):
    conn = get_db()
    where = "" if include_hidden else "WHERE COALESCE(a.status, 'published') != 'deleted'"
    rows = _dicts(conn.execute(f"""
        SELECT a.*, COUNT(c.id) as chart_count,
               SUM(CASE WHEN c.image_path != '' THEN 1 ELSE 0 END) as image_count
        FROM articles a
        LEFT JOIN charts c ON c.article_slug = a.slug
        {where}
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
               "markdown", "stage", "has_hero_image", "has_audio", "image_prompt",
               "chart_defs", "series_article_id"}
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
    conn.execute("DELETE FROM studio_messages WHERE draft_id=?", (did,))
    conn.execute("DELETE FROM chat_documents WHERE draft_id=?", (did,))
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

# ── Studio Messages ──

def add_studio_message(draft_id, role, content):
    conn = get_db()
    conn.execute("INSERT INTO studio_messages (draft_id, role, content) VALUES (?, ?, ?)",
                 (draft_id, role, content))
    conn.commit()
    mid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return mid

def get_studio_messages(draft_id):
    conn = get_db()
    rows = _dicts(conn.execute(
        "SELECT * FROM studio_messages WHERE draft_id=? ORDER BY id ASC",
        (draft_id,)).fetchall())
    conn.close()
    return rows

def clear_studio_messages(draft_id):
    conn = get_db()
    conn.execute("DELETE FROM studio_messages WHERE draft_id=?", (draft_id,))
    conn.commit()
    conn.close()

# ── Strategic Series ──

def create_series(title):
    slug = slugify(title)
    conn = get_db()
    base = slug
    n = 1
    while conn.execute("SELECT 1 FROM series WHERE slug=?", (slug,)).fetchone():
        slug = f"{base}-{n}"
        n += 1
    conn.execute("INSERT INTO series (title, slug) VALUES (?, ?)", (title, slug))
    conn.commit()
    rid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return rid

def get_series(sid):
    conn = get_db()
    row = _dict(conn.execute("SELECT * FROM series WHERE id=?", (sid,)).fetchone())
    conn.close()
    return row

def get_all_series():
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT s.*,
               COUNT(sa.id) as article_count,
               SUM(CASE WHEN sa.status IN ('drafted','published') THEN 1 ELSE 0 END) as written_count
        FROM series s
        LEFT JOIN series_articles sa ON sa.series_id = s.id
        GROUP BY s.id
        ORDER BY s.updated_at DESC
    """).fetchall())
    conn.close()
    return rows

def update_series(sid, **fields):
    if not fields:
        return
    allowed = {"title", "slug", "status", "thesis", "strategic_goal",
               "audience", "narrative_arc"}
    sets = []
    vals = []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k}=?")
            vals.append(v)
    if not sets:
        return
    sets.append("updated_at=datetime('now')")
    vals.append(sid)
    conn = get_db()
    conn.execute(f"UPDATE series SET {', '.join(sets)} WHERE id=?", vals)
    conn.commit()
    conn.close()

def delete_series(sid):
    conn = get_db()
    # Unlink any drafts that were connected to this series
    conn.execute("""UPDATE article_drafts SET series_article_id=NULL
                    WHERE series_article_id IN (SELECT id FROM series_articles WHERE series_id=?)""", (sid,))
    conn.execute("DELETE FROM series_articles WHERE series_id=?", (sid,))
    conn.execute("DELETE FROM studio_messages WHERE series_id=?", (sid,))
    conn.execute("DELETE FROM chat_documents WHERE series_id=?", (sid,))
    conn.execute("DELETE FROM series WHERE id=?", (sid,))
    conn.commit()
    conn.close()

def get_series_articles(sid):
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT sa.*, ad.title as draft_title, ad.stage as draft_stage
        FROM series_articles sa
        LEFT JOIN article_drafts ad ON sa.draft_id = ad.id
        WHERE sa.series_id = ?
        ORDER BY sa.position ASC
    """, (sid,)).fetchall())
    conn.close()
    return rows

def add_series_article(sid, working_title, position=None, role="", brief="",
                       key_arguments="", connects_to=""):
    conn = get_db()
    if position is None:
        row = conn.execute("SELECT COALESCE(MAX(position),-1)+1 FROM series_articles WHERE series_id=?",
                          (sid,)).fetchone()
        position = row[0]
    conn.execute("""INSERT INTO series_articles (series_id, position, working_title, role, brief,
                    key_arguments, connects_to) VALUES (?,?,?,?,?,?,?)""",
                (sid, position, working_title, role, brief, key_arguments, connects_to))
    conn.commit()
    rid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    # Update series timestamp
    update_series(sid)
    return rid

def update_series_article(said, **fields):
    if not fields:
        return
    allowed = {"working_title", "role", "brief", "key_arguments", "connects_to",
               "status", "position", "draft_id"}
    sets = []
    vals = []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k}=?")
            vals.append(v)
    if not sets:
        return
    sets.append("updated_at=datetime('now')")
    vals.append(said)
    conn = get_db()
    conn.execute(f"UPDATE series_articles SET {', '.join(sets)} WHERE id=?", vals)
    conn.commit()
    conn.close()

def delete_series_article(said):
    conn = get_db()
    # Unlink any draft
    conn.execute("UPDATE article_drafts SET series_article_id=NULL WHERE series_article_id=?", (said,))
    conn.execute("DELETE FROM series_articles WHERE id=?", (said,))
    conn.commit()
    conn.close()

def reorder_series_article(said, new_position):
    conn = get_db()
    row = conn.execute("SELECT series_id, position FROM series_articles WHERE id=?", (said,)).fetchone()
    if not row:
        conn.close()
        return
    sid = row[0]
    old_pos = row[1]
    if new_position == old_pos:
        conn.close()
        return
    # Shift other articles
    if new_position < old_pos:
        conn.execute("""UPDATE series_articles SET position=position+1
                        WHERE series_id=? AND position>=? AND position<?""",
                    (sid, new_position, old_pos))
    else:
        conn.execute("""UPDATE series_articles SET position=position-1
                        WHERE series_id=? AND position>? AND position<=?""",
                    (sid, old_pos, new_position))
    conn.execute("UPDATE series_articles SET position=? WHERE id=?", (new_position, said))
    conn.commit()
    conn.close()

def start_series_article(said):
    """Create a draft for a series article and link them bidirectionally."""
    conn = get_db()
    sa = _dict(conn.execute("SELECT * FROM series_articles WHERE id=?", (said,)).fetchone())
    if not sa:
        conn.close()
        return None
    if sa.get("draft_id"):
        conn.close()
        return sa["draft_id"]  # Already started
    # Create draft
    title = sa["working_title"]
    slug = slugify(title)
    base = slug
    n = 1
    while conn.execute("SELECT 1 FROM article_drafts WHERE slug=?", (slug,)).fetchone():
        slug = f"{base}-{n}"
        n += 1
    conn.execute("INSERT INTO article_drafts (slug, title, series_article_id) VALUES (?, ?, ?)",
                (slug, title, said))
    conn.commit()
    did = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    # Link back
    conn.execute("UPDATE series_articles SET draft_id=?, status='writing', updated_at=datetime('now') WHERE id=?",
                (did, said))
    conn.commit()
    conn.close()
    return did

def get_series_messages(sid):
    conn = get_db()
    rows = _dicts(conn.execute(
        "SELECT * FROM studio_messages WHERE series_id=? ORDER BY id ASC",
        (sid,)).fetchall())
    conn.close()
    return rows

def add_series_message(sid, role, content):
    conn = get_db()
    conn.execute("INSERT INTO studio_messages (draft_id, role, content, series_id) VALUES (0, ?, ?, ?)",
                (role, content, sid))
    conn.commit()
    mid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return mid

def get_series_for_draft(draft_id):
    """Get series context for a draft that's part of a series."""
    conn = get_db()
    draft = _dict(conn.execute("SELECT series_article_id FROM article_drafts WHERE id=?",
                               (draft_id,)).fetchone())
    if not draft or not draft.get("series_article_id"):
        conn.close()
        return None, None, None
    said = draft["series_article_id"]
    sa = _dict(conn.execute("SELECT * FROM series_articles WHERE id=?", (said,)).fetchone())
    if not sa:
        conn.close()
        return None, None, None
    series = _dict(conn.execute("SELECT * FROM series WHERE id=?", (sa["series_id"],)).fetchone())
    all_articles = _dicts(conn.execute(
        """SELECT sa.*, ad.title as draft_title, ad.stage as draft_stage
           FROM series_articles sa
           LEFT JOIN article_drafts ad ON sa.draft_id = ad.id
           WHERE sa.series_id=? ORDER BY sa.position ASC""",
        (sa["series_id"],)).fetchall())
    conn.close()
    return series, sa, all_articles

# ── Chat Documents ──

def insert_chat_document(draft_id=None, series_id=None, filename="", mime_type="",
                         file_size=0, extracted_text="", is_image=0, image_base64=""):
    conn = get_db()
    conn.execute("""INSERT INTO chat_documents
        (draft_id, series_id, filename, mime_type, file_size, extracted_text, is_image, image_base64)
        VALUES (?,?,?,?,?,?,?,?)""",
        (draft_id, series_id, filename, mime_type, file_size, extracted_text, is_image, image_base64))
    conn.commit()
    rid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return rid

def list_chat_documents(draft_id=None, series_id=None):
    """List documents (without text/base64 for lightweight listing)."""
    conn = get_db()
    if draft_id:
        rows = _dicts(conn.execute(
            "SELECT id, draft_id, series_id, filename, mime_type, file_size, is_image, created_at FROM chat_documents WHERE draft_id=? ORDER BY created_at ASC",
            (draft_id,)).fetchall())
    elif series_id:
        rows = _dicts(conn.execute(
            "SELECT id, draft_id, series_id, filename, mime_type, file_size, is_image, created_at FROM chat_documents WHERE series_id=? ORDER BY created_at ASC",
            (series_id,)).fetchall())
    else:
        rows = []
    conn.close()
    return rows

def get_chat_documents_for_prompt(draft_id=None, series_id=None):
    """Get full documents (with text + base64) for prompt injection."""
    conn = get_db()
    if draft_id:
        rows = _dicts(conn.execute(
            "SELECT * FROM chat_documents WHERE draft_id=? ORDER BY created_at ASC",
            (draft_id,)).fetchall())
    elif series_id:
        rows = _dicts(conn.execute(
            "SELECT * FROM chat_documents WHERE series_id=? ORDER BY created_at ASC",
            (series_id,)).fetchall())
    else:
        rows = []
    conn.close()
    return rows

def count_chat_documents(draft_id=None, series_id=None):
    conn = get_db()
    if draft_id:
        n = conn.execute("SELECT COUNT(*) FROM chat_documents WHERE draft_id=?", (draft_id,)).fetchone()[0]
    elif series_id:
        n = conn.execute("SELECT COUNT(*) FROM chat_documents WHERE series_id=?", (series_id,)).fetchone()[0]
    else:
        n = 0
    conn.close()
    return n

def delete_chat_document(doc_id):
    conn = get_db()
    conn.execute("DELETE FROM chat_documents WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()

# ── Error tracking ──

def record_post_error(post_id, category, message):
    conn = get_db()
    conn.execute("""UPDATE posts SET last_error=?, error_category=?,
                    retry_count=retry_count+1, last_attempt_at=datetime('now')
                    WHERE id=?""", (message, category, post_id))
    conn.commit()
    conn.close()

def clear_post_error(post_id):
    conn = get_db()
    conn.execute("""UPDATE posts SET last_error='', error_category='',
                    retry_count=0, last_attempt_at='' WHERE id=?""", (post_id,))
    conn.commit()
    conn.close()

def get_error_summary():
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT error_category, platform, COUNT(*) as count
        FROM posts WHERE error_category != '' AND last_attempt_at >= datetime('now', '-1 day')
        GROUP BY error_category, platform
    """).fetchall())
    conn.close()
    return rows

def get_retry_candidates(platform):
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT p.*, c.title as chart_title, a.title as article_title, a.url as article_url_joined
        FROM posts p
        LEFT JOIN charts c ON p.chart_id = c.id
        LEFT JOIN articles a ON p.article_id = a.id
        WHERE p.platform=? AND p.retry_count < 3
        AND p.error_category IN ('rate_limit','network')
        AND p.last_attempt_at < datetime('now', '-15 minutes')
        AND p.status NOT IN ('posted','rejected')
    """, (platform,)).fetchall())
    conn.close()
    return rows

# ── Post performance ──

def upsert_post_performance(post_id, clicks_7d=0, clicks_30d=0, users_7d=0, users_30d=0,
                            bounce_rate=None, avg_session_duration=None):
    conn = get_db()
    conn.execute("""
        INSERT INTO post_performance (post_id, clicks_7d, clicks_30d, users_7d, users_30d,
                                      bounce_rate, avg_session_duration, last_fetched)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(post_id) DO UPDATE SET
            clicks_7d=excluded.clicks_7d, clicks_30d=excluded.clicks_30d,
            users_7d=excluded.users_7d, users_30d=excluded.users_30d,
            bounce_rate=COALESCE(excluded.bounce_rate, post_performance.bounce_rate),
            avg_session_duration=COALESCE(excluded.avg_session_duration, post_performance.avg_session_duration),
            last_fetched=datetime('now')
    """, (post_id, clicks_7d, clicks_30d, users_7d, users_30d, bounce_rate, avg_session_duration))
    conn.commit()
    conn.close()

def get_top_performing_posts(limit=10):
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT p.*, pp.clicks_7d, pp.clicks_30d, pp.users_7d, pp.users_30d,
               pp.bounce_rate, pp.avg_session_duration,
               ROUND(pp.clicks_30d * (1.0 - COALESCE(pp.bounce_rate, 0.5))
                     * MIN(COALESCE(pp.avg_session_duration, 60) / 120.0, 1.0), 1) as quality_score,
               c.title as chart_title, a.title as article_title
        FROM post_performance pp
        JOIN posts p ON pp.post_id = p.id
        LEFT JOIN charts c ON p.chart_id = c.id
        LEFT JOIN articles a ON p.article_id = a.id
        ORDER BY quality_score DESC LIMIT ?
    """, (limit,)).fetchall())
    conn.close()
    return rows

def get_post_performance(post_id):
    conn = get_db()
    row = _dict(conn.execute(
        "SELECT * FROM post_performance WHERE post_id=?", (post_id,)).fetchone())
    conn.close()
    return row

def get_engagement_by_hour(platform=None, days=30):
    """Avg clicks by hour-of-day from posted + post_performance data."""
    conn = get_db()
    where = ["p.status='posted'", "p.posted_at IS NOT NULL",
             "p.posted_at >= datetime('now', ?)"]
    params = [f"-{days} days"]
    if platform:
        where.append("p.platform=?")
        params.append(platform)
    rows = _dicts(conn.execute(f"""
        SELECT CAST(strftime('%H', p.posted_at) AS INTEGER) as hour,
               p.platform,
               COUNT(*) as post_count,
               ROUND(AVG(COALESCE(pp.clicks_30d, 0)), 1) as avg_clicks
        FROM posts p
        LEFT JOIN post_performance pp ON pp.post_id = p.id
        WHERE {' AND '.join(where)}
        GROUP BY hour, p.platform
        ORDER BY hour
    """, params).fetchall())
    conn.close()
    return rows

# ── Per-article performance (Feature 1) ──

def get_article_performance(article_id):
    """Aggregate clicks/users across all posts for one article."""
    conn = get_db()
    row = _dict(conn.execute("""
        SELECT a.id, a.slug, a.title,
            COUNT(DISTINCT p.id) as total_posts,
            SUM(COALESCE(pp.clicks_7d, 0)) as clicks_7d,
            SUM(COALESCE(pp.clicks_30d, 0)) as clicks_30d,
            SUM(COALESCE(pp.users_7d, 0)) as users_7d,
            SUM(COALESCE(pp.users_30d, 0)) as users_30d,
            CASE WHEN COUNT(DISTINCT p.id) > 0
                 THEN ROUND(CAST(SUM(COALESCE(pp.clicks_30d,0)) AS REAL) / COUNT(DISTINCT p.id), 1)
                 ELSE 0 END as clicks_per_post
        FROM articles a
        LEFT JOIN posts p ON p.article_id = a.id AND p.status = 'posted'
        LEFT JOIN post_performance pp ON pp.post_id = p.id
        WHERE a.id = ?
        GROUP BY a.id
    """, (article_id,)).fetchone())
    conn.close()
    return row

def get_all_article_performance():
    """Ranked list of all articles by total clicks."""
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT a.id, a.slug, a.title, a.part,
            COUNT(DISTINCT p.id) as total_posts,
            SUM(COALESCE(pp.clicks_7d, 0)) as clicks_7d,
            SUM(COALESCE(pp.clicks_30d, 0)) as clicks_30d,
            SUM(COALESCE(pp.users_7d, 0)) as users_7d,
            SUM(COALESCE(pp.users_30d, 0)) as users_30d,
            CASE WHEN COUNT(DISTINCT p.id) > 0
                 THEN ROUND(CAST(SUM(COALESCE(pp.clicks_30d,0)) AS REAL) / COUNT(DISTINCT p.id), 1)
                 ELSE 0 END as clicks_per_post
        FROM articles a
        LEFT JOIN posts p ON p.article_id = a.id AND p.status = 'posted'
        LEFT JOIN post_performance pp ON pp.post_id = p.id
        GROUP BY a.id
        ORDER BY clicks_30d DESC
    """).fetchall())
    conn.close()
    return rows

# ── Article lifecycle (Feature 2) ──

def get_article_lifecycle(article_id):
    """Return lifecycle stage: launch/active/evergreen based on published_at."""
    conn = get_db()
    row = conn.execute("""
        SELECT a.published_at, a.indexed_at,
            (SELECT COUNT(*) FROM posts WHERE article_id=a.id AND status='posted') as promo_count,
            (SELECT MAX(posted_at) FROM posts WHERE article_id=a.id AND status='posted') as last_promoted
        FROM articles a WHERE a.id=?
    """, (article_id,)).fetchone()
    conn.close()
    if not row:
        return {"stage": "unknown", "days_old": 0, "promo_count": 0, "last_promoted": None}
    pub = row[0] or row[1]  # fall back to indexed_at
    days = 999
    if pub:
        try:
            pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00").split("+")[0])
            days = (datetime.now() - pub_dt).days
        except Exception:
            pass
    if days < 7:
        stage = "launch"
    elif days < 60:
        stage = "active"
    else:
        stage = "evergreen"
    return {"stage": stage, "days_old": days, "promo_count": row[2] or 0,
            "last_promoted": row[3]}

# ── Per-article feedback (Feature 3) ──

def get_article_feedback(article_id):
    """Get performance data for posts about a specific article."""
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT p.id, p.platform, p.post_type, p.hook_strategy, p.caption,
               pp.clicks_7d, pp.clicks_30d, pp.bounce_rate, pp.avg_session_duration
        FROM posts p
        LEFT JOIN post_performance pp ON pp.post_id = p.id
        WHERE p.article_id = ? AND p.status = 'posted'
        ORDER BY pp.clicks_30d DESC
    """, (article_id,)).fetchall())
    conn.close()
    return rows

# ── Engagement quality (Feature 4) ──

def get_post_quality_score(post_id):
    """Compute engagement quality: clicks * (1 - bounce_rate) * min(avg_duration/120, 1)."""
    perf = get_post_performance(post_id)
    if not perf or not perf.get("clicks_30d"):
        return 0
    bounce = perf.get("bounce_rate") if perf.get("bounce_rate") is not None else 0.5
    duration = perf.get("avg_session_duration") if perf.get("avg_session_duration") is not None else 60
    return round(perf["clicks_30d"] * (1 - bounce) * min(duration / 120, 1), 1)

# ── Priority scoring (Feature 5) ──

def compute_article_priority(article_id):
    """Combined priority score for promotion scheduling. Uses quality scores, not raw clicks."""
    perf = get_article_performance(article_id)
    total_posts = perf["total_posts"] if perf else 0
    # Sum quality scores across all posted posts for this article
    conn = get_db()
    try:
        qrow = conn.execute("""
            SELECT COALESCE(SUM(
                pp.clicks_30d * (1.0 - COALESCE(pp.bounce_rate, 0.5))
                * MIN(COALESCE(pp.avg_session_duration, 60) / 120.0, 1.0)
            ), 0) as total_quality
            FROM posts p
            JOIN post_performance pp ON pp.post_id = p.id
            WHERE p.article_id = ? AND p.status = 'posted'
        """, (article_id,)).fetchone()
        total_quality = qrow[0] if qrow else 0
    finally:
        conn.close()
    conversion = min(total_quality / max(total_posts, 1) / 30, 1.0)  # normalise to 0-1
    lc = get_article_lifecycle(article_id)
    days = lc["days_old"]
    freshness = max(0.2, 1.0 - (days / 90) * 0.8)
    article = get_article(article_id)
    saturation = 0
    if article:
        charts = get_charts_for_article(article["slug"])
        chart_count = len([c for c in charts if c.get("image_path")])
        saturation = min(total_posts / max(chart_count, 1), 3) / 3
    conn = get_db()
    try:
        best_match = conn.execute("""
            SELECT MAX(relevance_score) FROM news_items
            WHERE matched_article_id=? AND created_at >= datetime('now', '-7 days')
        """, (article_id,)).fetchone()
        news_strength = (best_match[0] or 0) if best_match else 0
    finally:
        conn.close()
    priority = (
        conversion * 0.3 +
        freshness * 0.2 +
        (1 - saturation) * 0.2 +
        news_strength * 0.3
    )
    return {
        "article_id": article_id,
        "priority": round(priority, 3),
        "conversion": round(conversion, 1),
        "freshness": round(freshness, 2),
        "saturation": round(saturation, 2),
        "news_strength": round(news_strength, 2),
        "lifecycle": lc["stage"]
    }

def get_all_article_priorities():
    """Compute priorities for all articles, return ranked."""
    articles = get_all_articles()
    priorities = []
    for a in articles:
        p = compute_article_priority(a["id"])
        p["slug"] = a["slug"]
        p["title"] = a["title"]
        p["part"] = a.get("part", "")
        priorities.append(p)
    priorities.sort(key=lambda x: x["priority"], reverse=True)
    return priorities

# ── A/B testing (Feature 6) ──

def get_undecided_ab_tests(min_days=7, max_days=30):
    """Find variant_group pairs where both posted 7+ days ago, no winner declared.
    Tests older than max_days are resolved as ties."""
    conn = get_db()
    # Use ORDER BY p.id inside GROUP_CONCAT to guarantee consistent ordering
    rows = _dicts(conn.execute("""
        SELECT p.variant_group, p.article_id, p.platform,
               GROUP_CONCAT(p.id ORDER BY p.id) as post_ids,
               GROUP_CONCAT(p.hook_strategy ORDER BY p.id) as strategies,
               GROUP_CONCAT(COALESCE(pp.clicks_30d, 0) ORDER BY p.id) as clicks,
               MIN(p.posted_at) as earliest_post
        FROM posts p
        LEFT JOIN post_performance pp ON pp.post_id = p.id
        WHERE p.variant_group != '' AND p.status = 'posted'
        AND p.posted_at <= datetime('now', ?)
        GROUP BY p.variant_group
        HAVING COUNT(*) = 2
    """, (f"-{min_days} days",)).fetchall())
    conn.close()
    decided = set()
    conn2 = get_db()
    for r in conn2.execute("SELECT article_id, platform, winning_strategy, losing_strategy FROM strategy_wins").fetchall():
        decided.add((r[0], r[1], r[2], r[3]))
    conn2.close()
    result = []
    for r in rows:
        strategies = str(r["strategies"]).split(",")
        if len(strategies) != 2:
            continue
        # Check if this exact matchup is already decided
        key1 = (r["article_id"], r["platform"], strategies[0], strategies[1])
        key2 = (r["article_id"], r["platform"], strategies[1], strategies[0])
        if key1 in decided or key2 in decided:
            continue
        # Mark expired tests for tie-breaking
        if r.get("earliest_post"):
            try:
                cutoff = (datetime.now() - timedelta(days=max_days)).isoformat()
                if r["earliest_post"] <= cutoff:
                    r["expired"] = True
            except Exception:
                pass
        result.append(r)
    return result

def record_strategy_win(article_id, platform, winning_strategy, losing_strategy, win_clicks, lose_clicks):
    conn = get_db()
    conn.execute("""
        INSERT OR REPLACE INTO strategy_wins
        (article_id, platform, winning_strategy, losing_strategy, win_clicks, lose_clicks)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (article_id, platform, winning_strategy, losing_strategy, win_clicks, lose_clicks))
    conn.commit()
    conn.close()

def get_winning_strategies(article_id):
    conn = get_db()
    rows = _dicts(conn.execute(
        "SELECT * FROM strategy_wins WHERE article_id=? ORDER BY decided_at DESC",
        (article_id,)).fetchall())
    conn.close()
    return rows

# ── Re-promotion triggers (Feature 7) ──

def get_repromotion_opportunities():
    """Find articles with no posts in 30+ days that have strong current news matches."""
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT DISTINCT a.id as article_id, a.slug, a.title, a.part,
            n.id as news_id, n.title as news_title, n.relevance_score, n.hook,
            (SELECT MAX(p.posted_at) FROM posts p
             WHERE p.article_id = a.id AND p.status='posted') as last_posted,
            (SELECT COALESCE(SUM(
                pp.clicks_30d * (1.0 - COALESCE(pp.bounce_rate, 0.5))
                * MIN(COALESCE(pp.avg_session_duration, 60) / 120.0, 1.0)
             ), 0) FROM posts p2 JOIN post_performance pp ON pp.post_id = p2.id
             WHERE p2.article_id = a.id) as historical_quality
        FROM news_items n
        JOIN articles a ON n.matched_article_id = a.id
        WHERE n.relevance_score >= 0.8
        AND n.created_at >= datetime('now', '-7 days')
        AND (
            (SELECT MAX(p3.posted_at) FROM posts p3
             WHERE p3.article_id = a.id AND p3.status='posted')
            <= datetime('now', '-30 days')
            OR (SELECT COUNT(*) FROM posts p4
                WHERE p4.article_id = a.id AND p4.status='posted') = 0
        )
        ORDER BY n.relevance_score DESC
    """).fetchall())
    conn.close()
    return rows

# ── Auto-confirm (Improvement 2) ──

def get_auto_confirmable_posts(threshold, lead_hours):
    """Posts with status 'generated', confidence >= threshold, scheduled within lead_hours."""
    conn = get_db()
    rows = _dicts(conn.execute("""
        SELECT * FROM posts
        WHERE status = 'generated'
          AND confidence_score >= ?
          AND scheduled_at IS NOT NULL AND scheduled_at != ''
          AND datetime(replace(scheduled_at,'T',' '), ?) <= datetime('now')
    """, (threshold, f"-{int(lead_hours)} hours")).fetchall())
    conn.close()
    return rows

# ── Stale post archive + waste rate (Improvement 7) ──

def archive_stale_posts(max_age_hours=48):
    """Archive generated/planned posts linked to news older than max_age_hours. Returns count."""
    conn = get_db()
    cur = conn.execute("""
        UPDATE posts SET status='archived'
        WHERE status IN ('draft', 'generated', 'planned')
          AND news_item_id IS NOT NULL
          AND news_item_id IN (
            SELECT id FROM news_items
            WHERE created_at <= datetime('now', ?)
          )
    """, (f"-{max_age_hours} hours",))
    count = cur.rowcount
    conn.commit()
    conn.close()
    return count

def get_waste_rate(days=30):
    """Waste rate: % of generated posts that never got posted."""
    conn = get_db()
    row = conn.execute("""
        SELECT COUNT(*) as total,
            SUM(CASE WHEN status IN ('archived','rejected') THEN 1 ELSE 0 END) as wasted,
            SUM(CASE WHEN status = 'posted' THEN 1 ELSE 0 END) as posted
        FROM posts WHERE created_at >= datetime('now', ?)
    """, (f"-{days} days",)).fetchone()
    conn.close()
    total = row[0] or 0
    wasted = row[1] or 0
    posted = row[2] or 0
    return {"total": total, "wasted": wasted, "posted": posted,
            "waste_rate": round(wasted / max(total, 1), 2)}

# ── Timezone-aware engagement with priors (Improvement 5) ──

def get_engagement_by_hour_with_priors(platform=None, timezone="UTC", days=30):
    """Engagement by hour blended with platform priors when data is sparse."""
    from config import PLATFORM_PRIORS
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(timezone)
        utc_offset_hours = datetime.now(tz).utcoffset().total_seconds() / 3600
    except Exception:
        utc_offset_hours = 0

    raw = get_engagement_by_hour(platform, days)
    # Count posts per platform to determine data sparsity
    plat_counts = {}
    for r in raw:
        p = r.get("platform", "")
        plat_counts[p] = plat_counts.get(p, 0) + r.get("post_count", 0)

    # Build hourly map from real data (adjusted to local tz)
    hourly = {}
    for r in raw:
        local_hour = (r["hour"] + int(utc_offset_hours)) % 24
        key = (local_hour, r.get("platform", ""))
        hourly[key] = r.get("avg_clicks", 0)

    max_real = max(hourly.values()) if hourly else 0
    result = []
    platforms = [platform] if platform else ["x", "linkedin"]
    for plat in platforms:
        count = plat_counts.get(plat, 0)
        alpha = min(count / 20, 1.0)
        priors = PLATFORM_PRIORS.get(plat, {})
        max_prior = max(priors.values()) if priors else 1.0
        for hour in range(24):
            real = hourly.get((hour, plat), 0)
            prior = priors.get(hour, 0) / max(max_prior, 1.0) if priors else 0
            # When real data is all zeros, priors scale to 1.0; otherwise blend with real scale
            blended = alpha * real + (1 - alpha) * prior * (max_real or 1.0)
            result.append({"hour": hour, "platform": plat,
                           "avg_clicks": round(blended, 1),
                           "post_count": count, "alpha": round(alpha, 2)})
    return result

# ── Weekly performance trend (Improvement 3) ──

def get_weekly_performance_trend(weeks=12, platform=None):
    """Avg quality score per week per platform."""
    conn = get_db()
    where = ["p.status='posted'", "p.posted_at IS NOT NULL",
             f"p.posted_at >= datetime('now', '-{weeks * 7} days')"]
    params = []
    if platform:
        where.append("p.platform=?")
        params.append(platform)
    rows = _dicts(conn.execute(f"""
        SELECT strftime('%Y-W%W', p.posted_at) as week,
               p.platform,
               COUNT(*) as posts,
               ROUND(AVG(
                   pp.clicks_30d * (1.0 - COALESCE(pp.bounce_rate, 0.5))
                   * MIN(COALESCE(pp.avg_session_duration, 60) / 120.0, 1.0)
               ), 1) as avg_quality,
               ROUND(AVG(COALESCE(pp.clicks_30d, 0)), 1) as avg_clicks
        FROM posts p
        LEFT JOIN post_performance pp ON pp.post_id = p.id
        WHERE {' AND '.join(where)}
        GROUP BY week, p.platform
        ORDER BY week
    """, params).fetchall())
    conn.close()
    return rows

def get_system_insights():
    """Compute deterministic statistical insights from post performance data."""
    conn = get_db()
    insights = []

    # 1. Hook strategy comparison by platform
    strat_rows = _dicts(conn.execute("""
        SELECT p.hook_strategy, p.platform, COUNT(*) as n,
            ROUND(AVG(
                pp.clicks_30d * (1.0 - COALESCE(pp.bounce_rate, 0.5))
                * MIN(COALESCE(pp.avg_session_duration, 60) / 120.0, 1.0)
            ), 1) as avg_quality
        FROM posts p
        JOIN post_performance pp ON pp.post_id = p.id
        WHERE p.status='posted' AND p.hook_strategy != ''
        GROUP BY p.hook_strategy, p.platform
        HAVING COUNT(*) >= 2
        ORDER BY avg_quality DESC
    """).fetchall())
    by_plat = {}
    for r in strat_rows:
        by_plat.setdefault(r["platform"], []).append(r)
    for plat, strats in by_plat.items():
        if len(strats) >= 2:
            best, worst = strats[0], strats[-1]
            if worst["avg_quality"] and worst["avg_quality"] > 0:
                ratio = round(best["avg_quality"] / worst["avg_quality"], 1)
                insights.append(f"{best['hook_strategy']} hooks on {plat} outperform "
                                f"{worst['hook_strategy']} by {ratio}x "
                                f"(avg quality {best['avg_quality']} vs {worst['avg_quality']})")

    # 2. Article section (part) comparison
    part_rows = _dicts(conn.execute("""
        SELECT a.part, COUNT(*) as n,
            ROUND(AVG(
                pp.clicks_30d * (1.0 - COALESCE(pp.bounce_rate, 0.5))
                * MIN(COALESCE(pp.avg_session_duration, 60) / 120.0, 1.0)
            ), 1) as avg_quality
        FROM posts p
        JOIN post_performance pp ON pp.post_id = p.id
        JOIN articles a ON p.article_id = a.id
        WHERE p.status='posted' AND a.part != ''
        GROUP BY a.part
        HAVING COUNT(*) >= 3
        ORDER BY avg_quality DESC
    """).fetchall())
    if len(part_rows) >= 2:
        best, worst = part_rows[0], part_rows[-1]
        if worst["avg_quality"] and worst["avg_quality"] > 0:
            pct = round((best["avg_quality"] - worst["avg_quality"]) / worst["avg_quality"] * 100)
            insights.append(f"{best['part']} articles convert {pct}% better than "
                            f"{worst['part']} articles")

    # 3. Time-of-day patterns
    hour_rows = _dicts(conn.execute("""
        SELECT CAST(strftime('%H', p.posted_at) AS INTEGER) as hour,
            p.platform,
            ROUND(AVG(
                pp.clicks_30d * (1.0 - COALESCE(pp.bounce_rate, 0.5))
                * MIN(COALESCE(pp.avg_session_duration, 60) / 120.0, 1.0)
            ), 1) as avg_quality,
            COUNT(*) as n
        FROM posts p
        JOIN post_performance pp ON pp.post_id = p.id
        WHERE p.status='posted' AND p.posted_at IS NOT NULL
        GROUP BY hour, p.platform
        HAVING COUNT(*) >= 2
        ORDER BY avg_quality DESC
    """).fetchall())
    by_plat = {}
    for r in hour_rows:
        by_plat.setdefault(r["platform"], []).append(r)
    for plat, hours in by_plat.items():
        if len(hours) >= 2:
            best, worst = hours[0], hours[-1]
            if worst["avg_quality"] and worst["avg_quality"] > 0:
                ratio = round(best["avg_quality"] / worst["avg_quality"], 1)
                insights.append(f"{plat} posts at {best['hour']}:00 get {ratio}x the engagement "
                                f"of {worst['hour']}:00 posts")

    # 4. A/B test wins summary
    wins = _dicts(conn.execute("""
        SELECT winning_strategy, COUNT(*) as wins
        FROM strategy_wins
        GROUP BY winning_strategy
        ORDER BY wins DESC LIMIT 3
    """).fetchall())
    if wins:
        top = wins[0]
        insights.append(f"{top['winning_strategy']} has won {top['wins']} A/B test(s) — "
                        f"most of any strategy")

    # 5. Waste rate
    waste = get_waste_rate(30)
    if waste["total"] > 0:
        insights.append(f"Waste rate: {int(waste['waste_rate']*100)}% of generated posts never posted "
                        f"({waste['wasted']}/{waste['total']} in last 30 days)")

    conn.close()
    return insights

init_db()
