#!/usr/bin/env python3
"""
Generate static PNG images of every chart for social sharing OG images.

Uses Puppeteer (via a Node.js subprocess) to open each article page,
wait for Chart.js to render, then screenshot each .chart-figure element.

Also generates per-chart share HTML pages with the chart image as og:image.
"""

import json
import subprocess
import sys
import textwrap
import threading
import http.server
import socketserver
from pathlib import Path
from chart_defs import get_all_charts
import html as html_mod

SITE_DIR = Path(__file__).parent.parent / "hfn-site-output"
IMAGES_BASE = SITE_DIR / "images" / "articles"
ARTICLES_DIR = SITE_DIR / "articles"
SITE_URL = "https://www.historyfuturenow.com"
SERVER_PORT = 8765


def start_local_server():
    """Start a local HTTP server to serve the site for Puppeteer."""
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(SITE_DIR), **kwargs)
        def log_message(self, format, *args):
            pass

    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("", SERVER_PORT), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


def generate_chart_share_page(slug, chart_id, chart_title, chart_desc, chart_source):
    """Generate a lightweight HTML page for a chart with og:image pointing to the chart PNG."""
    chart_dir = ARTICLES_DIR / slug / "chart"
    chart_dir.mkdir(parents=True, exist_ok=True)

    img_path = f"/images/articles/{slug}/chart-{chart_id}.png"
    article_url = f"/articles/{slug}"

    escaped_title = html_mod.escape(chart_title)
    escaped_desc = html_mod.escape(chart_desc)
    escaped_source = html_mod.escape(chart_source)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escaped_title} — History Future Now</title>
<meta name="description" content="{escaped_desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="{escaped_title}">
<meta property="og:description" content="{escaped_desc} — Source: {escaped_source}">
<meta property="og:image" content="{SITE_URL}{img_path}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="{SITE_URL}/articles/{slug}/chart/{chart_id}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escaped_title}">
<meta name="twitter:description" content="{escaped_desc}">
<meta name="twitter:image" content="{SITE_URL}{img_path}">
<script>window.location.replace('{article_url}#chart-{chart_id}');</script>
</head>
<body>
<p>Redirecting to <a href="{article_url}#chart-{chart_id}">the article</a>...</p>
</body>
</html>"""

    out_path = chart_dir / f"{chart_id}.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


def screenshot_charts_for_article(slug, chart_list):
    """Use Puppeteer to screenshot all charts in an article page."""
    article_file = ARTICLES_DIR / f"{slug}.html"
    if not article_file.exists():
        print(f"  [SKIP] Article file not found: {article_file.name}")
        return []

    img_dir = IMAGES_BASE / slug
    img_dir.mkdir(parents=True, exist_ok=True)

    chart_ids = [c["id"] for c in chart_list]
    chart_ids_json = json.dumps(chart_ids)
    output_paths_json = json.dumps(
        [str(img_dir / f"chart-{cid}.png") for cid in chart_ids]
    )

    node_script = textwrap.dedent(f"""\
        const puppeteer = require('puppeteer');
        (async () => {{
            const browser = await puppeteer.launch({{
                headless: 'new',
                args: ['--no-sandbox', '--disable-setuid-sandbox']
            }});
            const page = await browser.newPage();
            await page.setViewport({{ width: 1200, height: 800 }});

            const url = 'http://localhost:{SERVER_PORT}/articles/{slug}.html';
            await page.goto(url, {{ waitUntil: 'networkidle0', timeout: 30000 }});

            // Wait for Chart.js to finish rendering
            await page.waitForFunction(() => {{
                const canvases = document.querySelectorAll('canvas');
                if (canvases.length === 0) return false;
                return Array.from(canvases).every(c => {{
                    const chart = Chart.getChart(c);
                    return chart && !chart._animating;
                }});
            }}, {{ timeout: 15000 }}).catch(() => {{}});

            // Extra wait for animations to settle
            await new Promise(r => setTimeout(r, 1500));

            const chartIds = {chart_ids_json};
            const outputPaths = {output_paths_json};
            const results = [];

            for (let i = 0; i < chartIds.length; i++) {{
                const chartId = chartIds[i];
                const outPath = outputPaths[i];

                const el = await page.$('#chart-' + chartId);
                if (!el) {{
                    results.push({{ id: chartId, ok: false, error: 'element not found' }});
                    continue;
                }}

                // Hide the share bar before screenshot
                await page.evaluate((cid) => {{
                    const fig = document.getElementById('chart-' + cid);
                    if (fig) {{
                        const bar = fig.querySelector('.chart-share-bar');
                        if (bar) bar.style.display = 'none';
                    }}
                }}, chartId);

                try {{
                    await el.screenshot({{
                        path: outPath,
                        type: 'png',
                        omitBackground: false
                    }});
                    results.push({{ id: chartId, ok: true }});
                }} catch (err) {{
                    results.push({{ id: chartId, ok: false, error: err.message }});
                }}

                // Restore share bar
                await page.evaluate((cid) => {{
                    const fig = document.getElementById('chart-' + cid);
                    if (fig) {{
                        const bar = fig.querySelector('.chart-share-bar');
                        if (bar) bar.style.display = '';
                    }}
                }}, chartId);
            }}

            console.log(JSON.stringify(results));
            await browser.close();
        }})();
    """)

    try:
        result = subprocess.run(
            ["node", "-e", node_script],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print(f"  [ERROR] Puppeteer failed: {result.stderr[:300]}")
            return []

        results = json.loads(result.stdout.strip().split("\n")[-1])
        return results

    except subprocess.TimeoutExpired:
        print(f"  [ERROR] Puppeteer timed out for {slug}")
        return []
    except (json.JSONDecodeError, IndexError) as e:
        print(f"  [ERROR] Could not parse Puppeteer output: {e}")
        return []


def main():
    all_charts = get_all_charts()
    total_charts = sum(len(v) for v in all_charts.values())
    print(f"Generating chart images for {total_charts} charts across {len(all_charts)} articles\n")

    # Check Puppeteer is available
    try:
        subprocess.run(["node", "-e", "require('puppeteer')"],
                       capture_output=True, check=True, timeout=10)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: Puppeteer not found. Install it with: npm install -g puppeteer")
        print("  or: npx puppeteer install")
        sys.exit(1)

    print("Starting local server...")
    httpd = start_local_server()

    success = 0
    failed = 0
    skipped = 0

    for slug, chart_list in all_charts.items():
        print(f"\n[{slug}] {len(chart_list)} charts")

        # Generate share pages for each chart
        for chart in chart_list:
            generate_chart_share_page(
                slug, chart["id"], chart["title"],
                chart["desc"], chart["source"]
            )

        # Screenshot all charts in one Puppeteer session per article
        results = screenshot_charts_for_article(slug, chart_list)

        for r in results:
            if r.get("ok"):
                print(f"  ✓ {r['id']}")
                success += 1
            else:
                print(f"  ✗ {r['id']}: {r.get('error', 'unknown')}")
                failed += 1

        if not results:
            skipped += len(chart_list)

    httpd.shutdown()

    print(f"\n{'='*50}")
    print(f"Done: {success} captured, {failed} failed, {skipped} skipped")
    print(f"Share pages generated for all charts")

    if failed > 0 or skipped > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
