#!/usr/bin/env python3
"""HFN Promote CLI. Usage: python hfn.py [command]
Commands: ingest, monitor, generate, review, post, login, status, dashboard"""
import sys

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "dashboard"

    if cmd == "ingest":
        from ingester import ingest_all
        ingest_all()
    elif cmd == "monitor":
        from monitor import run_monitor
        run_monitor()
    elif cmd == "generate":
        from generator import generate_from_matches
        generate_from_matches()
    elif cmd == "login":
        platform = sys.argv[2] if len(sys.argv) > 2 else "x"
        from poster import login_interactive
        login_interactive(platform)
    elif cmd == "status":
        import db
        arts = db.get_all_articles()
        charts = db.get_all_charts()
        drafts = db.get_drafts()
        posted = db.get_posted()
        nn, nm = db.count_news()
        print(f"\n  Articles: {len(arts)}  Charts: {len(charts)}")
        print(f"  News: {nn}  Matched: {nm}")
        print(f"  Drafts: {len(drafts)}  Posted: {len(posted)}")
        print(f"  X today: {db.posts_today('x')}  LI today: {db.posts_today('linkedin')}\n")
    elif cmd == "dashboard":
        from app import app, _start_auto_poster
        from config import FLASK_PORT
        _start_auto_poster()
        app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
