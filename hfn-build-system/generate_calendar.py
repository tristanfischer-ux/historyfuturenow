#!/usr/bin/env python3
"""
Fortnightly social media content calendar generator for History Future Now.

Reads social_content/*.json files and issues.py to produce a two-week
posting schedule that alternates between off-weeks (back catalogue) and
issue weeks (new issue promotion).

Usage:
    python3 generate_calendar.py --start-date 2026-02-23 --cycles 4 --current-issue 16
"""

import argparse
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from issues import ISSUES, get_issue_by_number


BASE_URL = "https://www.historyfuturenow.com"
SOCIAL_DIR = Path(__file__).parent / "social_content"
OUTPUT_DIR = Path(__file__).parent / "social_calendar"
REPEAT_WINDOW_WEEKS = 4


def load_article_content():
    """Load all per-article social content JSONs into a dict keyed by slug."""
    articles = {}
    for path in SOCIAL_DIR.glob("*.json"):
        if path.name.startswith("issue_"):
            continue
        with open(path) as f:
            data = json.load(f)
        slug = data.get("slug", path.stem)
        articles[slug] = data
    return articles


def load_issue_content():
    """Load all per-issue social content JSONs into a dict keyed by issue number."""
    issues = {}
    for path in SOCIAL_DIR.glob("issue_*.json"):
        with open(path) as f:
            data = json.load(f)
        issues[data["issue_number"]] = data
    return issues


def build_slug_to_issue():
    """Map every article slug to its issue number."""
    mapping = {}
    for issue in ISSUES:
        for slug in issue["articles"]:
            mapping[slug] = issue["number"]
    return mapping


def pick_back_catalogue(pool, post_type, recently_used, rng):
    """Pick a random article from the pool that has the given post type and
    hasn't been used recently. Falls back to full pool if all used."""
    candidates = [
        slug for slug in pool
        if slug not in recently_used
        and post_type in pool[slug].get("posts", {})
    ]
    if not candidates:
        candidates = [
            slug for slug in pool
            if post_type in pool[slug].get("posts", {})
        ]
    if not candidates:
        return None
    return rng.choice(candidates)


def make_post(day_name, date_str, platform, post_type, slug, text,
              image=None, link=None):
    """Build a single calendar post dict."""
    return {
        "day": day_name,
        "date": date_str,
        "platform": platform,
        "type": post_type,
        "source_article": slug,
        "text": text,
        "image": image,
        "link": link,
    }


def article_link(slug):
    return BASE_URL + "/articles/" + slug


def generate_week_a(cycle_num, monday, current_issue_num, next_issue_num,
                    back_catalogue, all_articles, issue_content,
                    recently_used, rng):
    """Generate Week A (off-week): back-catalogue promotion + teaser."""
    posts = []
    days = [monday + timedelta(days=i) for i in range(6)]
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    # Mon: hook from back catalogue (X)
    slug = pick_back_catalogue(back_catalogue, "hook", recently_used, rng)
    if slug:
        pd = back_catalogue[slug]["posts"]["hook"]
        posts.append(make_post(
            names[0], days[0].isoformat(), "twitter", "hook", slug,
            pd.get("full", pd["text"]),
            link=article_link(slug),
        ))
        recently_used.add(slug)

    # Tue: chart insight from back catalogue (X + LinkedIn)
    slug = pick_back_catalogue(back_catalogue, "chart_insight", recently_used, rng)
    if slug:
        pd = back_catalogue[slug]["posts"]["chart_insight"]
        posts.append(make_post(
            names[1], days[1].isoformat(), "twitter_linkedin", "chart_insight", slug,
            pd["text"], image=pd.get("image"), link=article_link(slug),
        ))
        recently_used.add(slug)

    # Wed: LinkedIn essay excerpt from back catalogue
    slug = pick_back_catalogue(back_catalogue, "linkedin_essay", recently_used, rng)
    if slug:
        pd = back_catalogue[slug]["posts"]["linkedin_essay"]
        posts.append(make_post(
            names[2], days[2].isoformat(), "linkedin", "linkedin_essay", slug,
            pd["text"], link=article_link(slug),
        ))
        recently_used.add(slug)

    # Thu: provocative question from back catalogue (X)
    slug = pick_back_catalogue(back_catalogue, "provocative_question", recently_used, rng)
    if slug:
        pd = back_catalogue[slug]["posts"]["provocative_question"]
        txt = pd["text"]
        lnk = article_link(slug)
        if not txt.rstrip().endswith(lnk):
            txt = txt + "\n\n" + lnk
        posts.append(make_post(
            names[3], days[3].isoformat(), "twitter", "provocative_question", slug,
            txt, link=lnk,
        ))
        recently_used.add(slug)

    # Fri: "Next issue drops in one week" teaser (X + LinkedIn)
    ni = get_issue_by_number(next_issue_num)
    if ni:
        teaser = ("Issue {} of History Future Now drops next Friday. "
                  "Stay tuned.\n\n{}/issues/{}").format(
                      next_issue_num, BASE_URL, next_issue_num)
    else:
        teaser = ("The next issue of History Future Now is in the works. "
                  "Stay tuned.\n\n{}").format(BASE_URL)
    posts.append(make_post(
        names[4], days[4].isoformat(), "twitter_linkedin", "teaser", None, teaser,
    ))

    # Sat: thread from back catalogue (X)
    slug = pick_back_catalogue(back_catalogue, "thread", recently_used, rng)
    if slug:
        td = back_catalogue[slug]["posts"]["thread"]
        posts.append(make_post(
            names[5], days[5].isoformat(), "twitter", "thread", slug,
            "\n\n".join(td["tweets"]), link=article_link(slug),
        ))
        recently_used.add(slug)

    return {
        "cycle": cycle_num,
        "week": "A",
        "start_date": days[0].isoformat(),
        "end_date": days[5].isoformat(),
        "issue_context": {"current": current_issue_num, "next": next_issue_num},
        "posts": posts,
    }


def generate_week_b(cycle_num, monday, current_issue_num, next_issue_num,
                    all_articles, issue_content, rng):
    """Generate Week B (issue week): promote the new issue dropping Friday."""
    posts = []
    days = [monday + timedelta(days=i) for i in range(6)]
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    ni = get_issue_by_number(next_issue_num)
    nic = issue_content.get(next_issue_num)
    issue_slugs = ni["articles"] if ni else []
    lead = issue_slugs[0] if issue_slugs else None

    # Mon: hook teaser from lead article (X)
    if lead and lead in all_articles:
        hook = all_articles[lead]["posts"].get("hook")
        if hook:
            posts.append(make_post(
                names[0], days[0].isoformat(), "twitter", "hook", lead,
                hook.get("full", hook["text"]), link=article_link(lead),
            ))

    # Tue: chart insight from upcoming issue (X + LinkedIn) -- prefer one with image
    chart_slug = None
    for s in issue_slugs:
        if s in all_articles and "chart_insight" in all_articles[s].get("posts", {}):
            if all_articles[s]["posts"]["chart_insight"].get("image"):
                chart_slug = s
                break
    if not chart_slug:
        for s in issue_slugs:
            if s in all_articles and "chart_insight" in all_articles[s].get("posts", {}):
                chart_slug = s
                break
    if chart_slug:
        ci = all_articles[chart_slug]["posts"]["chart_insight"]
        posts.append(make_post(
            names[1], days[1].isoformat(), "twitter_linkedin", "chart_insight",
            chart_slug, ci["text"], image=ci.get("image"),
            link=article_link(chart_slug),
        ))

    # Wed: LinkedIn preview -- "This Friday in Issue N..."
    if ni:
        titles = [all_articles[s]["title"] for s in issue_slugs if s in all_articles]
        preview = ("This Friday in Issue {} of History Future Now:\n\n"
                   "{}\n\n{}/issues/{}").format(
                       next_issue_num, " | ".join(titles),
                       BASE_URL, next_issue_num)
    else:
        preview = ("A new issue of History Future Now arrives this Friday."
                   "\n\n{}").format(BASE_URL)
    posts.append(make_post(
        names[2], days[2].isoformat(), "linkedin", "issue_preview", None, preview,
    ))

    # Thu: thread previewing the issue (X)
    if nic and "issue_thread" in nic.get("posts", {}):
        thread_text = "\n\n".join(nic["posts"]["issue_thread"]["tweets"])
    else:
        parts = ["Issue {} of History Future Now drops tomorrow:".format(next_issue_num)]
        for s in issue_slugs:
            if s in all_articles:
                parts.append("{} -- {}".format(all_articles[s]["title"], article_link(s)))
        thread_text = "\n\n".join(parts)
    posts.append(make_post(
        names[3], days[3].isoformat(), "twitter", "issue_thread", None, thread_text,
    ))

    # Fri: ISSUE DROP -- issue_announcement (X + LinkedIn)
    if nic and "issue_announcement" in nic.get("posts", {}):
        ann_text = nic["posts"]["issue_announcement"]["text"]
    else:
        ann_text = ("Issue {} of History Future Now is out."
                    "\n\n{}/issues/{}").format(next_issue_num, BASE_URL, next_issue_num)
    posts.append(make_post(
        names[4], days[4].isoformat(), "twitter_linkedin", "issue_announcement",
        None, ann_text, link="{}/issues/{}".format(BASE_URL, next_issue_num),
    ))

    # Sat: best chart from the new issue (X + LinkedIn) -- different article from Tuesday
    best = None
    for s in issue_slugs:
        if s in all_articles and "chart_insight" in all_articles[s].get("posts", {}):
            ci = all_articles[s]["posts"]["chart_insight"]
            if ci.get("image") and s != chart_slug:
                best = s
                break
    if not best:
        best = chart_slug
    if not best:
        for s in issue_slugs:
            if s in all_articles and "chart_insight" in all_articles[s].get("posts", {}):
                best = s
                break
    if best:
        ci = all_articles[best]["posts"]["chart_insight"]
        posts.append(make_post(
            names[5], days[5].isoformat(), "twitter_linkedin", "chart_insight",
            best, ci["text"], image=ci.get("image"), link=article_link(best),
        ))

    return {
        "cycle": cycle_num,
        "week": "B",
        "start_date": days[0].isoformat(),
        "end_date": days[5].isoformat(),
        "issue_context": {"current": current_issue_num, "next": next_issue_num},
        "posts": posts,
    }


def render_markdown(cycle_num, week_a, week_b):
    """Render a human-readable markdown file for the full two-week cycle."""
    lines = [
        "# Content Calendar -- Cycle {}".format(cycle_num),
        "",
        "**Issue context:** Current = Issue {}, Next = Issue {}".format(
            week_a["issue_context"]["current"],
            week_a["issue_context"]["next"],
        ),
        "",
    ]

    sections = [
        (week_a, "Week A (off-week)"),
        (week_b, "Week B (issue week)"),
    ]
    for week_data, label in sections:
        lines.append("## {}".format(label))
        lines.append("_{} to {}_".format(week_data["start_date"], week_data["end_date"]))
        lines.append("")

        for post in week_data["posts"]:
            plat = (post["platform"]
                    .replace("twitter_linkedin", "X + LinkedIn")
                    .replace("twitter", "X")
                    .replace("linkedin", "LinkedIn"))
            src = ""
            if post["source_article"]:
                src = " -- *{}*".format(post["source_article"])
            lines.append("### {} {} -- {}".format(post["day"], post["date"], plat))
            lines.append("**Type:** {}{}".format(post["type"], src))
            if post.get("image"):
                lines.append("**Image:** `{}`".format(post["image"]))
            lines.append("")

            text = post["text"]
            if len(text) > 500:
                text = text[:497] + "..."
            lines.append(text)
            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate fortnightly social media content calendar for HFN."
    )
    parser.add_argument(
        "--start-date", required=True,
        help="Monday of the first week (YYYY-MM-DD). Must be a Monday.",
    )
    parser.add_argument(
        "--cycles", type=int, default=4,
        help="Fortnightly cycles to generate (default: 4 = 8 weeks).",
    )
    parser.add_argument(
        "--current-issue", type=int, required=True,
        help="Issue number already published. Next issue = this + 1.",
    )
    args = parser.parse_args()

    start = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    if start.weekday() != 0:
        print("Error: --start-date {} is not a Monday.".format(args.start_date),
              file=sys.stderr)
        sys.exit(1)

    current_issue_num = args.current_issue
    all_articles = load_article_content()
    issue_content = load_issue_content()
    slug_to_issue = build_slug_to_issue()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    recently_used = set()
    total_posts = 0

    for cycle_idx in range(args.cycles):
        cycle_num = cycle_idx + 1
        next_issue_num = current_issue_num + cycle_idx + 1

        week_a_monday = start + timedelta(weeks=cycle_idx * 2)
        week_b_monday = week_a_monday + timedelta(weeks=1)

        rng = random.Random("hfn-{}".format(week_a_monday.isoformat()))

        excluded_issues = {current_issue_num, next_issue_num}
        back_catalogue = {
            slug: data for slug, data in all_articles.items()
            if slug_to_issue.get(slug) not in excluded_issues
        }

        # Clear recently_used every REPEAT_WINDOW_WEEKS / 2 cycles
        if cycle_idx > 0 and cycle_idx % (REPEAT_WINDOW_WEEKS // 2) == 0:
            recently_used.clear()

        week_a = generate_week_a(
            cycle_num, week_a_monday, current_issue_num, next_issue_num,
            back_catalogue, all_articles, issue_content, recently_used, rng,
        )
        week_b = generate_week_b(
            cycle_num, week_b_monday, current_issue_num, next_issue_num,
            all_articles, issue_content, rng,
        )

        wa_path = OUTPUT_DIR / "cycle_{}_week_a.json".format(cycle_num)
        wb_path = OUTPUT_DIR / "cycle_{}_week_b.json".format(cycle_num)
        md_path = OUTPUT_DIR / "cycle_{}.md".format(cycle_num)

        with open(wa_path, "w") as f:
            json.dump(week_a, f, indent=2, ensure_ascii=False)
        with open(wb_path, "w") as f:
            json.dump(week_b, f, indent=2, ensure_ascii=False)
        with open(md_path, "w") as f:
            f.write(render_markdown(cycle_num, week_a, week_b))

        wa_count = len(week_a["posts"])
        wb_count = len(week_b["posts"])
        total_posts += wa_count + wb_count

        print("Cycle {}: Week A ({} to {}) = {} posts, "
              "Week B ({} to {}) = {} posts".format(
                  cycle_num,
                  week_a["start_date"], week_a["end_date"], wa_count,
                  week_b["start_date"], week_b["end_date"], wb_count))

    print("")
    print("Total: {} posts across {} cycles ({} weeks)".format(
        total_posts, args.cycles, args.cycles * 2))
    print("Output: {}/".format(OUTPUT_DIR))


if __name__ == "__main__":
    main()
