"""
HFN Promote — Scheduler Daemon
Runs the monitoring loop in the background on a configurable interval.
"""
import time
import signal
import sys
from datetime import datetime
from rich.console import Console
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import MONITOR_INTERVAL
from db import init_db
from monitor import run_monitor
from generator import generate_from_matches
from reviewer import post_approved

console = Console()
running = True


def signal_handler(sig, frame):
    global running
    console.print("\n[yellow]Shutting down scheduler...[/yellow]")
    running = False
    sys.exit(0)


def monitoring_cycle():
    """One full cycle: monitor → generate → post approved."""
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold cyan]Monitoring cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold cyan]")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

    try:
        # Step 1: Fetch and match news
        run_monitor()

        # Step 2: Generate posts for new matches
        generate_from_matches()

        # Step 3: Post any approved posts
        post_approved()

    except Exception as e:
        console.print(f"[red]Error in monitoring cycle: {e}[/red]")

    console.print(f"\n[dim]Next cycle in {MONITOR_INTERVAL} minutes...[/dim]")


def run_scheduler():
    """Start the background scheduler."""
    init_db()
    signal.signal(signal.SIGINT, signal_handler)

    console.print(f"""
[bold cyan]╔══════════════════════════════════════════╗
║      HFN Promote — Scheduler Daemon      ║
╚══════════════════════════════════════════╝[/bold cyan]

  Monitoring interval: [bold]{MONITOR_INTERVAL} minutes[/bold]
  Press Ctrl+C to stop
""")

    # Run once immediately
    monitoring_cycle()

    # Schedule recurring
    scheduler = BlockingScheduler()
    scheduler.add_job(
        monitoring_cycle,
        IntervalTrigger(minutes=MONITOR_INTERVAL),
        id="monitor_cycle",
        name="News monitoring cycle",
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        console.print("[yellow]Scheduler stopped.[/yellow]")


if __name__ == "__main__":
    run_scheduler()
