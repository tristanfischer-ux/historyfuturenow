"""HFN Promote — Generator v3.3. Deduped, feedback-aware generation with per-article learning and A/B testing."""
import json, re, random, uuid, anthropic
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

HOOK STRATEGY — pick ONE of these five approaches (vary across posts, do NOT default to NUMBER every time):
1. QUESTION: A sharp, specific question the article answers. Not rhetorical waffle — something that makes the reader realise they don't know the answer.
2. HISTORICAL PARALLEL: A vivid past event that mirrors today. "Rome's legions were paid in salt. Your salary still carries the word."
3. CONTRAST: Two facts that clash. "Britain built 6,000 miles of railway in 20 years. HS2 can't finish 130 miles in 30."
4. PROVOCATIVE CLAIM: A counterintuitive assertion the article backs up. Makes the reader think "that can't be right" — then click.
5. NUMBER: A jaw-dropping statistic — but ONLY when the number is genuinely striking. Not every chart has one.

The chart image IS the visual hook. Do NOT repeat what the chart shows — provoke curiosity that makes the reader study the chart.
- Create a "knowledge gap" — hint at an insight the reader can only get by reading the article.
- End with the article URL — never bury the link.

FORBIDDEN:
- Never say "Here's why", "Let's talk about", "It turns out", "In this article", "Dive into"
- Never use "HFN" — always "History Future Now"
- No hashtags on X. 2-3 hashtags on LinkedIn only (at the very end).
- Never start with "Did you know" or "Have you ever wondered"
- Never be generic. Every post must contain at least one specific number or historical reference.
- NEVER include URLs in the caption. The article URL is appended automatically after generation.

When providing the CONTEXT field, write it as: "From [article title] on History Future Now"
"""

PLATFORM_HOOKS = {
    "x": """PLATFORM: X (Twitter)
- Prefer CONTRAST and PROVOCATIVE CLAIM hooks — they drive retweets
- Keep it punchy: 1-2 sentences, no paragraph breaks
- If long-form: structure as numbered points, ~200 chars each""",
    "linkedin": """PLATFORM: LinkedIn
- Prefer QUESTION and NUMBER hooks — they drive comments
- Use 2-3 short paragraphs with line breaks between them
- LinkedIn truncates after ~210 chars — first line MUST hook on its own
- End with a specific question to prompt engagement"""
}

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
    top = db.get_top_performing_posts(5)
    if top:
        lines.append("\nTOP-PERFORMING POSTS (these drove the most clicks):")
        for t in top:
            lines.append(f"  - {t['platform']} {t.get('post_type','short')}: \"{t['caption'][:80]}...\" — {t['clicks_30d']} clicks")
    conn = db.get_db()
    match_rejects = db._dicts(conn.execute(
        "SELECT reason, platform FROM feedback WHERE action='match_reject' ORDER BY created_at DESC LIMIT 5"
    ).fetchall())
    conn.close()
    if match_rejects:
        lines.append("\nREJECTED MATCHES (user removed these pairings from plan):")
        for r in match_rejects:
            lines.append(f"  - {r['reason']}")
    return "\n".join(lines) if lines else ""

def build_article_feedback_prompt(article_id):
    """Build per-article performance insights for the generation prompt."""
    if not article_id:
        return ""
    feedback = db.get_article_feedback(article_id)
    if not feedback:
        return ""
    lines = ["\nARTICLE-SPECIFIC INSIGHTS (from past posts about THIS article):"]
    # Group by hook_strategy and compute average clicks
    strategy_perf = {}
    for f in feedback:
        hs = f.get("hook_strategy") or "unknown"
        if hs not in strategy_perf:
            strategy_perf[hs] = {"clicks": [], "count": 0}
        strategy_perf[hs]["clicks"].append(f.get("clicks_30d") or 0)
        strategy_perf[hs]["count"] += 1
    if len(strategy_perf) > 1:
        lines.append("  Hook strategy performance:")
        for hs, data in sorted(strategy_perf.items(),
                                key=lambda x: sum(x[1]["clicks"]) / max(len(x[1]["clicks"]), 1),
                                reverse=True):
            avg = sum(data["clicks"]) / max(len(data["clicks"]), 1)
            lines.append(f"    {hs}: {avg:.0f} avg clicks ({data['count']} posts)")
    # Platform comparison
    plat_perf = {}
    for f in feedback:
        plat = f.get("platform", "unknown")
        if plat not in plat_perf:
            plat_perf[plat] = []
        plat_perf[plat].append(f.get("clicks_30d") or 0)
    if len(plat_perf) > 1:
        lines.append("  Platform performance:")
        for plat, clicks in plat_perf.items():
            lines.append(f"    {plat}: {sum(clicks)/len(clicks):.0f} avg clicks")
    # Top performing post example
    top = [f for f in feedback if f.get("clicks_30d", 0) > 0]
    if top:
        best = top[0]
        lines.append(f"  Best post: {best.get('hook_strategy','?')} on {best['platform']} — {best['clicks_30d']} clicks")
        lines.append(f"    Caption start: \"{(best.get('caption','')[:80])}...\"")
    # A/B test results
    wins = db.get_winning_strategies(article_id)
    if wins:
        lines.append("  A/B test results:")
        for w in wins[:3]:
            lines.append(f"    {w['winning_strategy']} beat {w['losing_strategy']} on {w['platform']} ({w['win_clicks']} vs {w['lose_clicks']} clicks)")
    return "\n".join(lines) if len(lines) > 1 else ""

def gen_post(news, chart, article, platform, post_type="short", force_strategy=None):
    """Generate a single post. Unified function for short and long."""
    client = get_client()
    if not client: return None
    url = article["url"] if article else f"{HFN_BASE_URL}/charts"
    feedback = build_feedback_prompt()
    article_feedback = build_article_feedback_prompt(article.get("id") if article else None)

    strategy_instruction = ""
    if force_strategy:
        strategy_instruction = f"\nYou MUST use the {force_strategy} hook strategy. Do not use any other."

    if post_type == "short":
        content_instruction = f"""Write a SHORT post (the chart image will be shown alongside):
1. CAPTION ({"max 220 chars" if platform == "x" else "max 600 chars"}):
   - Pick ONE hook strategy (Question / Historical Parallel / Contrast / Provocative Claim / Number). Vary across posts — do not always lead with a number.{strategy_instruction}
   - The chart is attached as an image. Do not describe what it shows — provoke curiosity about it.
   - Connect to the news story in one sharp sentence. The reader should think "I need to see that article."
   {"- No hashtags." if platform == "x" else "- End with 2-3 hashtags."}
   {"" if platform == "x" else "- Use 2-3 short paragraphs with line breaks."}
2. CONTEXT ({"max 80 chars" if platform == "x" else "max 120 chars"}):
   Write as: "From [article title] on History Future Now"
3. HOOK_STRATEGY: Which strategy you used (QUESTION, HISTORICAL_PARALLEL, CONTRAST, PROVOCATIVE_CLAIM, or NUMBER)
Return JSON: {{"caption": "...", "context": "...", "hook_strategy": "..."}}"""
        max_tok = 400
    else:
        article_text = article.get("full_text", article.get("opening", ""))[:4000]
        max_chars = "1800" if platform == "x" else "2500"
        platform_note = "Structure as numbered points for threadability." if platform == "x" else "Open with scroll-stopping first line. Use paragraph breaks. End with a question."
        content_instruction = f"""Write a {"thread-style post" if platform == "x" else "LinkedIn article"} (max {max_chars} chars):
- HOOK: Pick ONE hook strategy (Question / Historical Parallel / Contrast / Provocative Claim / Number). The chart is attached as an image — do not describe what it shows. Make it impossible to scroll past.{strategy_instruction}
- BRIDGE: Connect this to today's news headline in one sentence.
- DEPTH: Draw 2-3 historical parallels or insights from the article. Use specific numbers, dates, and comparisons — e.g. "Rome's grain dole fed 200,000 citizens. Our welfare state covers 67 million."
- CLOSE: End with a thought that makes the reader want the full picture. Do NOT include the URL — it is appended automatically.
- {platform_note}
{"- No hashtags" if platform == "x" else "- End with 2-3 relevant hashtags"}

ARTICLE CONTENT:
{article_text}

Also provide a short CONTEXT line (max 100 chars): "From [article title] on History Future Now"
Also identify your HOOK_STRATEGY (QUESTION, HISTORICAL_PARALLEL, CONTRAST, PROVOCATIVE_CLAIM, or NUMBER).
Return JSON: {{"caption": "...", "context": "...", "hook_strategy": "..."}}"""
        max_tok = 1500

    platform_hook = PLATFORM_HOOKS.get(platform, "")
    prompt = f"""{VOICE}

{platform_hook}

{feedback}
{article_feedback}

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

        # Lifecycle-aware threshold (Feature 2)
        lifecycle = db.get_article_lifecycle(article["id"])
        stage = lifecycle["stage"]
        if stage == "launch":
            threshold = 0.5
        elif stage == "active":
            threshold = 0.6
        else:  # evergreen
            threshold = 0.7
        if score < threshold:
            print(f"  ⏭ [{score:.1f}] Below {stage} threshold ({threshold}): {chart['title'][:50]}")
            continue

        print(f"\n  {'★' if high_relevance else '·'} [{score:.1f}] [{stage}] {news['title'][:55]}...")

        platforms = ["x", "linkedin"] if is_linkedin_safe(article) else ["x"]
        for platform in platforms:
            # Decide: short or long (not both by default)
            post_type = "long" if high_relevance else "short"
            key = (chart["id"], platform, post_type)

            if key in existing_keys:
                continue
            if ("news", news["id"], platform) in existing_keys:
                continue

            # A/B testing: 30% chance on high-relevance matches (Feature 6)
            if high_relevance and random.random() < 0.3:
                variant_group = f"ab_{uuid.uuid4().hex[:8]}"
                strategies = random.sample(["QUESTION", "CONTRAST", "PROVOCATIVE_CLAIM",
                                            "HISTORICAL_PARALLEL", "NUMBER"], 2)
                ab_ok = True
                for strategy in strategies:
                    result = gen_post(news, chart, article, platform, post_type,
                                      force_strategy=strategy)
                    if result:
                        caption = result.get("essay", result.get("caption", ""))
                        context = result.get("context", "")
                        hook_strategy = result.get("hook_strategy", strategy)
                        db.insert_post(
                            news_item_id=news["id"], chart_id=chart["id"],
                            article_id=article["id"], platform=platform,
                            caption=caption, article_context=context,
                            article_url=article["url"],
                            image_path=chart["image_path"],
                            post_type=post_type, hook_strategy=hook_strategy,
                            variant_group=variant_group)
                        generated += 1
                        print(f"    ✓ {platform} {post_type} A/B [{strategy}]")
                    else:
                        ab_ok = False
                if ab_ok:
                    continue  # Skip normal generation

            result = gen_post(news, chart, article, platform, post_type)
            if result:
                caption = result.get("essay", result.get("caption", ""))
                context = result.get("context", "")
                hook_strategy = result.get("hook_strategy", "")
                db.insert_post(
                    news_item_id=news["id"], chart_id=chart["id"],
                    article_id=article["id"], platform=platform,
                    caption=caption, article_context=context,
                    article_url=article["url"],
                    image_path=chart["image_path"],
                    post_type=post_type, hook_strategy=hook_strategy)
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
    hook_strategy = result.get("hook_strategy", "")
    pid = db.insert_post(
        news_item_id=news.get("id"), chart_id=chart["id"],
        article_id=article["id"], platform=platform,
        caption=caption, article_context=context,
        article_url=article["url"], image_path=chart["image_path"],
        post_type=post_type, hook_strategy=hook_strategy)
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
