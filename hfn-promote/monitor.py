"""HFN Promote — News Monitor. Fetches RSS, matches news to charts."""
import json, re, feedparser, anthropic
import db
from config import RSS_FEEDS, ANTHROPIC_API_KEY, MATCH_MODEL, MIN_RELEVANCE

def fetch_feeds():
    items = []
    for feed in RSS_FEEDS:
        try:
            f = feedparser.parse(feed["url"])
            # Google News/Trends return more items — take up to 25
            max_items = 25 if "google" in feed["url"].lower() else 15
            for e in f.entries[:max_items]:
                title = e.get("title", "").strip()
                # Google News wraps titles with source: "Headline - Source Name"
                # Keep it as-is — the source name helps with matching context
                link = e.get("link", "").strip()
                summary = e.get("summary", e.get("description", "")).strip()[:500]
                if title and link:
                    items.append({"feed": feed["name"], "title": title,
                                  "link": link, "summary": summary,
                                  "published": e.get("published", "")})
        except Exception as ex:
            print(f"  [!] {feed['name']}: {ex}")
    return items

def build_chart_index():
    charts = db.get_all_charts()
    indexed = []
    for c in charts:
        if not c["image_path"]:
            continue
        indexed.append({
            "id": c["id"],
            "slug": c["article_slug"],
            "title": c["title"],
            "desc": c["description"][:80],
            "source": c["source"][:60],
        })
    return indexed

def build_article_index():
    articles = db.get_all_articles()
    return [{"id": a["id"], "slug": a["slug"], "title": a["title"],
             "part": a["part"], "excerpt": a["excerpt"][:150]} for a in articles]

def match_batch(news_items, chart_index, article_index):
    if not ANTHROPIC_API_KEY or not news_items:
        return []
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    all_matches = []

    for i in range(0, len(news_items), 10):
        batch = news_items[i:i+10]
        news_str = "\n".join(
            f"NEWS_{item['id']}: {item['title']}\n  {item.get('summary','')[:150]}" for item in batch)

        prompt = f"""You are matching breaking news to data charts from History Future Now, a website with essays about demographics, geopolitics, economics, energy, and society.

For each news item, find the chart whose data is most relevant. Be generous — if a news story about defence spending could connect to a chart about military expenditure, that's a match. If a story about AI could connect to a chart about technology cost curves, that's a match.

CHARTS:
{json.dumps(chart_index[:120], indent=1)}

ARTICLES (for context on what each chart relates to):
{json.dumps(article_index[:60], indent=1)}

NEWS ITEMS:
{news_str}

Return a JSON array. For EACH news item, include an entry:
{{"news_id": <id as integer>, "chart_id": <chart id or null>, "article_id": <article id or null>, "score": <0.0-1.0>, "hook": "<one sentence connecting the news to the chart data>"}}

Score guide: 0.9 = direct data match, 0.7 = strong thematic connection, 0.5 = reasonable connection.
Include ALL items, even with score 0 if no match. Return news_id as plain integer (not "NEWS_49", just 49). JSON array only, no markdown fences."""

        try:
            resp = client.messages.create(model=MATCH_MODEL, max_tokens=2000,
                                          messages=[{"role": "user", "content": prompt}])
            text = resp.content[0].text.strip()
            # Strip markdown fences
            text = text.replace('```json', '').replace('```', '').strip()
            m = re.search(r"\[.*\]", text, re.DOTALL)
            if m:
                parsed = json.loads(m.group())
                for item in parsed:
                    nid = item.get('news_id', 0)
                    if isinstance(nid, str):
                        nid = int(nid.replace('NEWS_', ''))
                    item['news_id'] = nid
                all_matches.extend(parsed)
        except Exception as ex:
            print(f"  [!] Match API error: {ex}")

    return all_matches

def run_monitor():
    print("\n  Fetching RSS feeds...")
    items = fetch_feeds()
    new = 0
    for item in items:
        if db.insert_news(item["feed"], item["title"], item["link"],
                          item["summary"], item["published"]):
            new += 1
    print(f"  {len(items)} items fetched, {new} new")

    unprocessed = db.get_unprocessed_news(50)
    if not unprocessed:
        print("  No new items to match")
        return 0

    print(f"  Matching {len(unprocessed)} items to charts (using {MATCH_MODEL})...")
    chart_idx = build_chart_index()
    article_idx = build_article_index()
    matches = match_batch(unprocessed, chart_idx, article_idx)
    lookup = {m["news_id"]: m for m in matches}

    matched = 0
    for item in unprocessed:
        m = lookup.get(item["id"], {})
        score = m.get("score", 0)
        db.mark_processed(item["id"], chart_id=m.get("chart_id"),
                          article_id=m.get("article_id"),
                          score=score, hook=m.get("hook", ""))
        if score >= MIN_RELEVANCE:
            matched += 1

    print(f"  ✓ {matched} matches (score >= {MIN_RELEVANCE})")
    return matched

if __name__ == "__main__":
    run_monitor()
