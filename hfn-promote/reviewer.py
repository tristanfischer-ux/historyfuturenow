"""
HFN Promote — Post Review System
Interactive terminal UI for reviewing draft posts including X Articles.
"""
import asyncio
import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from db import (
    init_db, get_posts_by_status, update_post_status,
    get_posts_today, get_post_stats
)
from poster import post_sync, has_session
from config import MAX_POSTS_X, MAX_POSTS_LINKEDIN, MAX_ARTICLES_X

console = Console()


def review_posts():
    """Interactive review of draft posts."""
    init_db()
    drafts = get_posts_by_status("draft")

    if not drafts:
        console.print("[dim]No draft posts to review. Run 'hfn generate' first.[/dim]")
        return

    console.print(f"\n[bold cyan]📝 {len(drafts)} draft posts to review[/bold cyan]\n")

    x_today = get_posts_today("x")
    xa_today = get_posts_today("x_article")
    li_today = get_posts_today("linkedin")
    console.print(f"  Today: 𝕏 Articles {xa_today}/{MAX_ARTICLES_X} | 𝕏 Tweets {x_today}/{MAX_POSTS_X} | LinkedIn {li_today}/{MAX_POSTS_LINKEDIN}\n")

    for post in drafts:
        if post["platform"] == "x_article":
            color, label = "magenta", "𝕏 ARTICLE"
        elif post["platform"] == "x":
            color, label = "cyan", "𝕏 Tweet"
        else:
            color, label = "blue", "LinkedIn"

        type_label = ""
        if post["post_type"] == "reactive":
            type_label = " ⚡ reactive"
        elif post["post_type"] == "promo_tweet":
            type_label = " 📢 promo"

        char_count = len(post["content"])

        # Show title for X Articles
        content_display = post["content"]
        if post["platform"] == "x_article":
            if post.get("title"):
                content_display = f"📰 {post['title']}\n{'─' * 40}\n{content_display}"
            if len(content_display) > 800:
                content_display = content_display[:800] + f"\n\n[dim]... ({char_count} chars total)[/dim]"

        panel = Panel(
            content_display,
            title=f"[{color}]{label}[/{color}] #{post['id']}{type_label} ({char_count} chars)",
            subtitle=f"Article: {post.get('article_title', 'Unknown')[:60]}",
            border_style=color,
            width=90,
        )
        console.print(panel)

        console.print("  [green]a[/green]=approve  [red]r[/red]=reject  [yellow]s[/yellow]=skip  [magenta]p[/magenta]=post now  [dim]q[/dim]=quit")
        choice = Prompt.ask("  Action", choices=["a", "r", "s", "p", "q"], default="s")

        if choice == "a":
            update_post_status(post["id"], "approved")
            console.print(f"  [green]✓ Approved[/green]\n")
        elif choice == "r":
            update_post_status(post["id"], "rejected")
            console.print(f"  [red]✗ Rejected[/red]\n")
        elif choice == "p":
            platform_key = "x" if post["platform"] in ("x", "x_article") else "linkedin"
            if not has_session(platform_key):
                console.print(f"  [red]No {platform_key} session. Run 'hfn login {platform_key}' first.[/red]\n")
                continue

            console.print(f"  [yellow]Posting to {label}...[/yellow]")
            success = post_sync(post["platform"], post["content"], post.get("title"))
            if success:
                update_post_status(post["id"], "posted")
                console.print(f"  [bold green]✓ Posted![/bold green]\n")
            else:
                console.print(f"  [red]✗ Failed to post. Check session.[/red]\n")
        elif choice == "q":
            break
        else:
            console.print(f"  [dim]Skipped[/dim]\n")


def post_approved():
    """Post all approved posts respecting daily limits. X Articles posted first."""
    init_db()

    # Post X Articles first (they're the anchor content)
    for platform, max_posts in [("x_article", MAX_ARTICLES_X), ("x", MAX_POSTS_X), ("linkedin", MAX_POSTS_LINKEDIN)]:
        approved = get_posts_by_status("approved", platform)
        if not approved:
            continue

        posted_today = get_posts_today(platform)
        remaining = max_posts - posted_today

        if remaining <= 0:
            labels = {"x_article": "𝕏 Articles", "x": "𝕏 Tweets", "linkedin": "LinkedIn"}
            console.print(f"[yellow]{labels[platform]}: Daily limit reached ({posted_today}/{max_posts})[/yellow]")
            continue

        session_key = "x" if platform in ("x", "x_article") else "linkedin"
        if not has_session(session_key):
            console.print(f"[red]No {session_key} session. Run 'hfn login {session_key}' first.[/red]")
            continue

        to_post = approved[:remaining]
        labels = {"x_article": "𝕏 Articles", "x": "𝕏 Tweets", "linkedin": "LinkedIn"}
        console.print(f"\n[bold cyan]Posting {len(to_post)} to {labels[platform]}...[/bold cyan]")

        for post_data in to_post:
            desc = post_data.get("title", post_data["content"][:60])
            console.print(f"  Posting #{post_data['id']}: {desc}...")

            success = post_sync(platform, post_data["content"], post_data.get("title"))
            if success:
                update_post_status(post_data["id"], "posted")
                console.print(f"  [green]✓ Done[/green]")
            else:
                console.print(f"  [red]✗ Failed[/red]")

            time.sleep(5)  # Human-like delay


def show_stats(days=30):
    """Show posting statistics."""
    init_db()
    stats = get_post_stats(days)

    draft_count = len(get_posts_by_status("draft"))
    approved_count = len(get_posts_by_status("approved"))
    posted_count = len(get_posts_by_status("posted"))
    rejected_count = len(get_posts_by_status("rejected"))

    console.print("\n[bold cyan]📊 Post Statistics[/bold cyan]\n")
    console.print(f"  Drafts:   [yellow]{draft_count}[/yellow]")
    console.print(f"  Approved: [green]{approved_count}[/green]")
    console.print(f"  Posted:   [bold green]{posted_count}[/bold green]")
    console.print(f"  Rejected: [red]{rejected_count}[/red]")

    x_today = get_posts_today("x")
    xa_today = get_posts_today("x_article")
    li_today = get_posts_today("linkedin")
    console.print(f"\n  Today: 𝕏 Articles {xa_today}/{MAX_ARTICLES_X} | 𝕏 Tweets {x_today}/{MAX_POSTS_X} | LinkedIn {li_today}/{MAX_POSTS_LINKEDIN}")

    if stats:
        console.print(f"\n[bold]Last {days} days:[/bold]")
        table = Table()
        table.add_column("Date", style="dim")
        table.add_column("𝕏 Articles", style="magenta", justify="right")
        table.add_column("𝕏 Tweets", style="cyan", justify="right")
        table.add_column("LinkedIn", style="blue", justify="right")

        by_date = {}
        for s in stats:
            date = s["post_date"]
            if date not in by_date:
                by_date[date] = {"x_article": 0, "x": 0, "linkedin": 0}
            by_date[date][s["platform"]] = s["count"]

        for date in sorted(by_date.keys(), reverse=True)[:14]:
            table.add_row(
                date,
                str(by_date[date].get("x_article", 0)),
                str(by_date[date].get("x", 0)),
                str(by_date[date].get("linkedin", 0)),
            )
        console.print(table)
    console.print()


if __name__ == "__main__":
    review_posts()
