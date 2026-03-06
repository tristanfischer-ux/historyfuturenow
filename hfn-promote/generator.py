"""HFN Promote — Generator v3.2. Deduped, feedback-aware generation."""
import json, re, anthropic
import db
from config import ANTHROPIC_API_KEY, GEN_MODEL, MIN_RELEVANCE, HFN_BASE_URL

# Only these article parts are allowed on LinkedIn (avoids political content)
LINKEDIN_SAFE_PARTS = {"Jobs & Economy", "Natural Resources"}

def is_linkedin_safe(article):
    """Check if an article's topic is suitable for LinkedIn."""
    return (article.get("part", "") or "") in LINKEDIN_SAFE_PARTS

VOICE = """You are writing social media posts for History Future Now (historyfuturenow.com).

ABOUT THE SITE:
History Future Now puts current events into historical perspective and uses that vantage point to look at the future. It covers four themes: Natural Resources, Global Balance of Power, Jobs & Economy, and Society. Articles are long-form, data-rich essays with interactive charts. The author is Tristan Fischer.

WRITING STYLE — match the History Future Now voice:
- Intellectually confident but accessible. Not academic — conversational authority.
- Opens with a striking fact, provocative question, or counterintuitive observation. Never generic.
- Uses specific numbers, dates, and historical parallels — "Since 2000, China gained 14 million factory jobs while the US lost 5 million" not "jobs have shifted overseas."
- Connects past patterns to present events: "Every civilisation that ran out of water collapsed. We're next."
- Slightly provocative, never partisan. Challenges assumptions from both left and right.
- Direct, clear sentences. No corporate jargon. No "In today's world" or "It's important to note."

HOOK STRATEGY — make people want to click:
- Lead with the most surprising or counterintuitive data point from the chart.
- Create a "knowledge gap" — hint at an insight the reader can only get by reading the article.
- Use patterns like: "[Surprising fact]. [Why it matters]. [What history tells us]."
- End with the article URL — never bury the link.
- The chart image IS the visual hook. The text should make people look at it twice.

FORBIDDEN:
- Never say "Here's why", "Let's talk about", "It turns out", "In this article", "Dive into"
- Never use "HFN" — always "History Future Now"
- No hashtags on X. 2-3 hashtags on LinkedIn only (at the very end).
- Never start with "Did you know" or "Have you ever wondered"
- Never be generic. Every post must contain at least one specific number or historical reference.
- NEVER include URLs in the caption. The article URL is appended automatically after generation.

When providing the CONTEXT field, write it as: "From [article title] on History Future Now"
"""

def get_client():
    if not ANTHROPIC_API_KEY: return None
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def build_feedback_prompt():
    """Build a prompt section from past feedback."""
    fb = db.get_feedback_summary()
    lines = []
    if fb["rejections"]:
        lines.append("USER PREFERENCES (learned from past rejections):")
        for r in fb["rejections"][:10]:
            if r["reason"]:
                lines.append(f"  - Rejected {r['post_type']} on {r['platform']}: {r['reason']}")
    if fb["edits"]:
        lines.append("\nEDIT PATTERNS (user changed these):")
        for e in fb["edits"][:5]:
            lines.append(f"  - Original: {e['original_caption'][:80]}...")
            lines.append(f"    Changed to: {e['edited_caption'][:80]}...")
    return "\n".join(lines) if lines else ""

def gen_post(news, chart, article, platform, post_type="short"):
    """Generate a single post. Unified function for short and long."""
    client = get_client()
    if not client: return None
    url = article["url"] if article else f"{HFN_BASE_URL}/charts"
    feedback = build_feedback_prompt()

    if post_type == "short":
        content_instruction = f"""Write a SHORT post (the chart image will be shown alongside):
1. CAPTION ({"max 220 chars" if platform == "x" else "max 350 chars"}):
   - Open with the single most striking number or contrast from the chart. This is your hook.
   - Then connect it to the news story in one sharp sentence.
   - The reader should think "I need to see that article" after reading.
   {"- No hashtags." if platform == "x" else "- End with 2-3 hashtags."}
2. CONTEXT ({"max 80 chars" if platform == "x" else "max 120 chars"}):
   Write as: "From [article title] on History Future Now"
Return JSON: {{"caption": "...", "context": "..."}}"""
        max_tok = 400
    else:
        article_text = article.get("full_text", article.get("opening", ""))[:4000]
        max_chars = "1800" if platform == "x" else "2500"
        content_instruction = f"""Write a {"thread-style post" if platform == "x" else "LinkedIn article"} (max {max_chars} chars):
- HOOK: Open with the most counterintuitive or surprising data point from the chart. Make it impossible to scroll past.
- BRIDGE: Connect this to today's news headline in one sentence.
- DEPTH: Draw 2-3 historical parallels or insights from the article. Use specific numbers, dates, and comparisons — e.g. "Rome's grain dole fed 200,000 citizens. Our welfare state covers 67 million."
- CLOSE: End with a thought that makes the reader want the full picture. Do NOT include the URL — it is appended automatically.
{"- No hashtags" if platform == "x" else "- End with 2-3 relevant hashtags"}

ARTICLE CONTENT:
{article_text}

Also provide a short CONTEXT line (max 100 chars): "From [article title] on History Future Now"
Return JSON: {{"caption": "...", "context": "..."}}"""
        max_tok = 1500

    prompt = f"""{VOICE}

{feedback}

NEWS: {news['title']}
{news.get('summary', '')[:200]}
CHART: {chart['title']} — {chart['description']}
SOURCE: {chart['source']}
ARTICLE: {article['title']} ({article['part']})

{content_instruction}
JSON only, no markdown fences."""

    try:
        resp = client.messages.create(model=GEN_MODEL, max_tokens=max_tok,
                                      messages=[{"role": "user", "content": prompt}])
        text = resp.content[0].text.strip()
        text = text.replace('```json', '').replace('```', '').strip()
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m: return json.loads(m.group())
    except Exception as ex:
        print(f"  [!] Gen error ({platform} {post_type}): {ex}")
    return None


def generate_from_matches():
    """Generate posts from matched news. Smart dedup: 1 post per chart per platform."""
    matched = db.get_matched_news(MIN_RELEVANCE, 30)

    # Track existing posts to avoid regeneration
    existing_keys = set()
    for p in db.get_drafts() + db.get_posted() + db.get_scheduled():
        key = (p.get("chart_id"), p.get("platform"), p.get("post_type"))
        existing_keys.add(key)
        # Also track by news_item_id
        if p.get("news_item_id"):
            existing_keys.add(("news", p["news_item_id"], p["platform"]))

    # Get recently used charts to avoid repetition
    recent_charts = db.get_charts_used_recently(3)

    # Group by chart_id: pick the best news story per chart
    best_per_chart = {}
    for m in matched:
        cid = m.get("matched_chart_id")
        if not cid: continue
        if cid not in best_per_chart or m["relevance_score"] > best_per_chart[cid]["relevance_score"]:
            best_per_chart[cid] = m

    to_gen = list(best_per_chart.values())
    if not to_gen:
        print("  No new chart matches to generate from")
        return 0

    charts = {c["id"]: c for c in db.get_all_charts()}
    generated = 0

    for news in to_gen:
        chart = charts.get(news["matched_chart_id"])
        if not chart or not chart.get("image_path"):
            continue

        article = None
        if news.get("matched_article_id"):
            article = db.get_article(news["matched_article_id"])
        if not article:
            article = db.get_article_by_slug(chart["article_slug"])
        if not article:
            continue

        score = news.get("relevance_score", 0)
        high_relevance = score >= 0.7
        recently_used = chart["id"] in recent_charts

        if recently_used:
            print(f"  ⏭ [{score:.1f}] Skipping (chart used recently): {chart['title'][:50]}")
            continue

        print(f"\n  {'★' if high_relevance else '·'} [{score:.1f}] {news['title'][:55]}...")

        platforms = ["x", "linkedin"] if is_linkedin_safe(article) else ["x"]
        for platform in platforms:
            # Decide: short or long (not both by default)
            post_type = "long" if high_relevance else "short"
            key = (chart["id"], platform, post_type)

            if key in existing_keys:
                continue
            if ("news", news["id"], platform) in existing_keys:
                continue

            result = gen_post(news, chart, article, platform, post_type)
            if result:
                caption = result.get("essay", result.get("caption", ""))
                context = result.get("context", "")
                db.insert_post(
                    news_item_id=news["id"], chart_id=chart["id"],
                    article_id=article["id"], platform=platform,
                    caption=caption, article_context=context,
                    article_url=article["url"],
                    image_path=chart["image_path"],
                    post_type=post_type)
                generated += 1
                print(f"    ✓ {platform} {post_type}")

    print(f"\n  ✓ {generated} posts generated")
    return generated

def gen_from_chart(chart_id, platform="x", post_type="short"):
    """Reverse flow: given a chart, find best recent news hook and generate a post."""
    client = get_client()
    if not client: return None

    chart = db.get_chart(chart_id)
    if not chart: return None
    article = db.get_article_by_slug(chart["article_slug"])
    if not article: return None

    recent = db.get_recent_news_for_matching(30)
    if not recent: return None

    news_list = "\n".join(f"NEWS_{n['id']}: {n['title']}" for n in recent[:20])

    match_prompt = f"""Pick the single best news story to pair with this chart.

CHART: {chart['title']} — {chart['description']}
SOURCE: {chart['source']}
ARTICLE: {article['title']} ({article['part']})

RECENT NEWS:
{news_list}

Return JSON: {{"news_id": <id>, "hook": "<one sentence connecting news to chart>"}}
If no good match, return {{"news_id": null, "hook": "<evergreen hook for this chart>"}}
JSON only, no markdown."""

    from config import MATCH_MODEL
    try:
        resp = client.messages.create(model=MATCH_MODEL, max_tokens=300,
                                      messages=[{"role": "user", "content": match_prompt}])
        text = resp.content[0].text.strip().replace('```json','').replace('```','').strip()
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m: return None
        match = json.loads(m.group())
    except Exception as ex:
        print(f"  [!] Match error: {ex}")
        return None

    news_id = match.get("news_id")
    news = next((n for n in recent if n["id"] == news_id), None) if news_id else None
    if not news:
        news = {"id": None, "title": match.get("hook", ""), "summary": ""}

    result = gen_post(news, chart, article, platform, post_type)
    if not result: return None

    caption = result.get("essay", result.get("caption", ""))
    context = result.get("context", "")
    pid = db.insert_post(
        news_item_id=news.get("id"), chart_id=chart["id"],
        article_id=article["id"], platform=platform,
        caption=caption, article_context=context,
        article_url=article["url"], image_path=chart["image_path"],
        post_type=post_type)
    return {"post_id": pid, "caption": caption, "news_title": news.get("title", "")}


def generate_planned():
    """Generate actual post text for all 'planned' posts. Called after user confirms plan."""
    planned = db.get_planned_posts()
    if not planned:
        print("  No planned posts to generate")
        return 0

    charts = {c["id"]: c for c in db.get_all_charts()}
    generated = 0

    for p in planned:
        ok = _generate_one_post(p, charts)
        if ok: generated += 1

    print(f"\n  ✓ {generated}/{len(planned)} posts generated")
    return generated


def generate_single(post_id):
    """Generate text for a single planned post."""
    conn = db.get_db()
    row = db._dict(conn.execute("""
        SELECT p.*, c.title as chart_title, c.description as chart_desc, c.image_path as chart_image,
               a.title as article_title, a.url as article_url_joined,
               n.title as news_title, n.hook
        FROM posts p
        LEFT JOIN charts c ON p.chart_id = c.id
        LEFT JOIN articles a ON p.article_id = a.id
        LEFT JOIN news_items n ON p.news_item_id = n.id
        WHERE p.id = ?
    """, (post_id,)).fetchone())
    conn.close()
    if not row:
        return False
    charts = {c["id"]: c for c in db.get_all_charts()}
    return _generate_one_post(row, charts)


def _generate_one_post(p, charts):
    """Internal: generate text for one post record. Returns True on success."""
    chart = charts.get(p.get("chart_id"))
    article = None

    # Try to find article - multiple fallbacks
    if p.get("article_id"):
        article = db.get_article(p["article_id"])
    if not article and chart and chart.get("article_slug"):
        article = db.get_article_by_slug(chart["article_slug"])
    if not article and p.get("news_item_id"):
        # Look up from the news item's matched article
        conn = db.get_db()
        news_row = conn.execute(
            "SELECT matched_article_id FROM news_items WHERE id=?",
            (p["news_item_id"],)).fetchone()
        conn.close()
        if news_row and news_row[0]:
            article = db.get_article(news_row[0])

    if not article:
        print(f"  ✗ Post #{p['id']}: no article found (article_id={p.get('article_id')}, chart_id={p.get('chart_id')})")
        return False

    # For text-only posts (no chart), find first chart with image from this article
    if not chart:
        slug = article.get("slug","")
        if slug:
            conn = db.get_db()
            row = conn.execute(
                "SELECT * FROM charts WHERE article_slug=? AND image_path != '' ORDER BY figure_num LIMIT 1",
                (slug,)).fetchone()
            conn.close()
            if row:
                chart = dict(row)
            else:
                chart = {"id": 0, "title": article.get("title",""),
                         "description": article.get("excerpt",""),
                         "image_path": "", "article_slug": slug, "source": ""}
        else:
            chart = {"id": 0, "title": article.get("title",""),
                     "description": article.get("excerpt",""),
                     "image_path": "", "article_slug": "", "source": ""}
    elif not chart.get("image_path"):
        # Chart exists but has no image - try to find one from same article
        slug = chart.get("article_slug","")
        if slug:
            conn = db.get_db()
            img_row = conn.execute(
                "SELECT image_path FROM charts WHERE article_slug=? AND image_path != '' LIMIT 1",
                (slug,)).fetchone()
            conn.close()
            if img_row:
                chart["image_path"] = img_row[0]

    news = {"id": p.get("news_item_id"), "title": p.get("news_title", ""),
            "summary": p.get("hook", "")}

    print(f"  Generating {p['platform']} {p.get('post_type','short')} for: {chart['title'][:50]}...")

    result = gen_post(news, chart, article, p["platform"], p.get("post_type", "short"))
    if result:
        caption = result.get("essay", result.get("caption", ""))
        context = result.get("context", "")
        conn = db.get_db()
        conn.execute("""UPDATE posts SET caption=?, article_context=?, article_url=?,
                       image_path=?, status='generated' WHERE id=?""",
                     (caption, context, article.get("url",""),
                      chart.get("image_path",""), p["id"]))
        conn.commit()
        conn.close()
        print(f"    ✓ Done")
        return True
    else:
        print(f"    ✗ Failed")
        return False


if __name__ == "__main__":
    generate_from_matches()
