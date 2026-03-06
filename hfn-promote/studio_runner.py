"""Article Studio — Background task runner using threading + subprocess."""
import sys, threading, subprocess, json, re as _re
from datetime import datetime
from pathlib import Path
import db

_PYTHON = sys.executable  # Always use the running interpreter, not bare "python"
from config import HFN_SOURCE_DIR, HFN_SITE_OUTPUT, HFN_CONTENT_DIR, HFN_AUDIO_DIR, HFN_ARTICLE_IMAGES

BUILD_SYSTEM = HFN_SOURCE_DIR
SCRIPTS_DIR = HFN_SOURCE_DIR.parent / "scripts"

# Ensure subprocess PATH includes Homebrew (launchd has minimal PATH)
import os as _os
_SUBPROCESS_ENV = _os.environ.copy()
_homebrew_paths = "/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin"
_SUBPROCESS_ENV["PATH"] = _homebrew_paths + ":" + _SUBPROCESS_ENV.get("PATH", "/usr/bin:/bin")


def start_task(task_id, task_type, draft_id):
    """Spawn a background thread to run the given task."""
    runners = {
        "save_to_disk": _run_save_to_disk,
        "generate_image": _run_generate_image,
        "generate_audio": _run_generate_audio,
        "build": _run_build,
        "deploy": _run_deploy,
        "publish": _run_publish,
    }
    runner = runners.get(task_type)
    if not runner:
        db.update_studio_task(task_id, status="error", error=f"Unknown task type: {task_type}")
        return
    t = threading.Thread(target=_wrap, args=(runner, task_id, draft_id), daemon=True)
    t.start()


def _wrap(runner, task_id, draft_id):
    """Wrapper that catches exceptions and updates task status."""
    try:
        db.update_studio_task(task_id, status="running", progress="Starting...")
        runner(task_id, draft_id)
        db.update_studio_task(task_id, status="done",
                              completed_at=datetime.now().isoformat())
    except Exception as e:
        db.update_studio_task(task_id, status="error", error=str(e)[:500],
                              completed_at=datetime.now().isoformat())


def _update_library(new_books):
    """Append genuinely new books to library_data.py. Returns count added."""
    lib_path = HFN_SOURCE_DIR / "library_data.py"
    if not lib_path.exists() or not new_books:
        return 0

    text = lib_path.read_text(encoding="utf-8")

    # Build set of existing titles (case-insensitive)
    existing = set()
    for m in _re.finditer(r'"title":\s*"([^"]+)"', text):
        existing.add(m.group(1).lower())

    year = datetime.now().year
    entries = []
    for b in new_books:
        title = (b.get("title") or "").strip()
        if not title or title.lower() in existing:
            continue
        author = (b.get("author") or "Unknown").strip()
        themes = b.get("themes", ["world"])
        # Validate theme keys
        valid_themes = {"ancient", "medieval", "modern", "world", "geopolitics",
                        "economics", "politics", "religion", "science", "biology",
                        "philosophy", "fiction"}
        themes = [t for t in themes if t in valid_themes] or ["world"]
        entry = f'    {{"title": "{title}", "author": "{author}", "year": {year}, "source": "kindle", "themes": {json.dumps(themes)}}},'
        entries.append(entry)
        existing.add(title.lower())

    if not entries:
        return 0

    # Insert before the closing ] of the BOOKS list
    close_idx = text.rfind("\n]\n")
    if close_idx == -1:
        close_idx = text.rfind("\n]")
    if close_idx == -1:
        return 0

    insert_block = "\n" + "\n".join(entries) + "\n"
    updated = text[:close_idx] + insert_block + text[close_idx:]
    lib_path.write_text(updated, encoding="utf-8")
    return len(entries)


def _run_save_to_disk(task_id, draft_id):
    """Write draft markdown to essays/ with YAML frontmatter."""

    draft = db.get_draft(draft_id)
    if not draft:
        raise ValueError("Draft not found")

    db.update_studio_task(task_id, progress="Writing file...")

    # Extract sources from the markdown's embedded YAML frontmatter (if any)
    raw_md = draft.get("markdown") or ""
    sources_lines = []
    body_md = raw_md

    new_books = []

    fm_match = _re.match(r'^\s*---\n([\s\S]*?)\n---\s*\n?', raw_md)
    if fm_match:
        fm_block = fm_match.group(1)
        body_md = raw_md[fm_match.end():]
        # Extract sources list
        src_match = _re.search(r'sources:\s*\n((?:\s+-\s+.*\n?)*)', fm_block)
        if src_match:
            for line in src_match.group(1).split('\n'):
                m = _re.match(r'^\s+-\s+["\']?([^"\'\n]+?)["\']?\s*$', line)
                if m:
                    sources_lines.append(f'  - "{m.group(1).strip()}"')

        # Extract new_books list (YAML block of dicts with title/author/themes)
        nb_match = _re.search(r'new_books:\s*\n((?:\s+[-\w].*\n?)*)', fm_block)
        if nb_match:
            current = {}
            for line in nb_match.group(1).split('\n'):
                line = line.strip()
                if not line:
                    continue
                if line.startswith('- title:'):
                    if current.get("title"):
                        new_books.append(current)
                    current = {"title": line.split(':', 1)[1].strip().strip('"').strip("'")}
                elif line.startswith('author:'):
                    current["author"] = line.split(':', 1)[1].strip().strip('"').strip("'")
                elif line.startswith('themes:'):
                    # Parse inline YAML list: ["economics", "politics"]
                    themes_str = line.split(':', 1)[1].strip()
                    themes_match = _re.findall(r'"([^"]+)"|\'([^\']+)\'', themes_str)
                    current["themes"] = [t[0] or t[1] for t in themes_match]
            if current.get("title"):
                new_books.append(current)

    # Build frontmatter from DB fields + extracted sources (new_books stripped)
    fm_lines = ["---"]
    fm_lines.append(f"title: \"{draft['title']}\"")
    if draft.get("section"):
        fm_lines.append(f"section: \"{draft['section']}\"")
    if draft.get("excerpt"):
        fm_lines.append(f"excerpt: \"{draft['excerpt']}\"")
    if draft.get("share_summary"):
        fm_lines.append(f"share_summary: \"{draft['share_summary']}\"")
    if sources_lines:
        fm_lines.append("sources:")
        fm_lines.extend(sources_lines)
    fm_lines.append("---")
    fm_lines.append("")

    content = "\n".join(fm_lines) + body_md

    out_path = HFN_CONTENT_DIR / f"{draft['slug']}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")

    # Write chart definitions to chart_defs.py if present
    chart_defs = (draft.get("chart_defs") or "").strip()
    if chart_defs:
        _write_chart_defs(task_id, draft["slug"], chart_defs)

    # Update library with new books from the AI
    if new_books:
        added = _update_library(new_books)
        if added > 0:
            # Clear caches so next article sees updated library
            import app as _app
            _app._library_books_cache = None
            _app._library_catalog_cache = None
            db.update_studio_task(task_id, progress=f"Saved to {out_path.name} — added {added} new book{'s' if added != 1 else ''} to library")
        else:
            db.update_studio_task(task_id, progress=f"Saved to {out_path.name}")
    else:
        db.update_studio_task(task_id, progress=f"Saved to {out_path.name}")
    db.update_draft(draft_id, stage="draft")

    # Update series article status if this draft is part of a series
    if draft.get("series_article_id"):
        db.update_series_article(draft["series_article_id"], status="drafted")


def _write_chart_defs(task_id, slug, chart_defs):
    """Append chart definitions for a slug into chart_defs.py (idempotent)."""
    import re

    chart_file = BUILD_SYSTEM / "chart_defs.py"
    if not chart_file.exists():
        db.update_studio_task(task_id, progress="chart_defs.py not found — skipping")
        return

    existing = chart_file.read_text(encoding="utf-8")

    # Skip if charts for this slug already exist
    marker = f"charts['{slug}']"
    if marker in existing:
        db.update_studio_task(task_id, progress=f"Charts for {slug} already in chart_defs.py — skipped")
        return

    # Strip comment header lines (# === ...) from AI output
    lines = chart_defs.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#') and not cleaned:
            continue  # skip leading comment lines
        cleaned.append(line)
    chart_code = '\n'.join(cleaned).strip()

    # Replace whatever slug the AI used with the draft's actual slug
    chart_code = re.sub(r"charts\['[^']+'\]", f"charts['{slug}']", chart_code)

    # If the AI didn't wrap in charts['slug'] = [...], add the wrapper
    if not re.search(r"charts\[", chart_code):
        # Ensure the bare dicts are wrapped in a list
        if not chart_code.startswith('['):
            chart_code = f"[\n    {chart_code}\n    ]"
        chart_code = f"charts['{slug}'] = {chart_code}"

    # Build the block to insert
    block = f"\n    # ─── STUDIO: {slug} ───\n    {chart_code}\n"

    # Insert before "return charts" line
    insert_point = existing.rfind("    return charts")
    if insert_point == -1:
        db.update_studio_task(task_id, progress="Could not find 'return charts' in chart_defs.py — skipping")
        return

    updated = existing[:insert_point] + block + "\n" + existing[insert_point:]
    chart_file.write_text(updated, encoding="utf-8")
    db.update_studio_task(task_id, progress=f"Chart defs appended to chart_defs.py")


def _run_generate_image(task_id, draft_id):
    """Generate hero image using Gemini API directly."""
    import os

    draft = db.get_draft(draft_id)
    if not draft:
        raise ValueError("Draft not found")

    db.update_studio_task(task_id, progress="Generating hero image...")

    # Build the image prompt
    user_prompt = (draft.get("image_prompt") or "").strip()
    title = draft.get("title", "Untitled")
    if not user_prompt:
        # Auto-generate a prompt from the article title
        user_prompt = (
            f"Editorial illustration for an article titled '{title}'. "
            "Style: flat geometric editorial illustration, mid-century modern poster aesthetic. "
            "The illustration must fill the ENTIRE frame edge-to-edge with NO empty space, NO margins, NO borders, NO background padding. "
            "Warm muted editorial palette (terracotta, navy, sand, teal, grey, ochre). "
            "No text, no writing, no photorealism, no detailed faces, no people. "
            "Landscape orientation, wide panoramic format, 16:9 aspect ratio."
        )
        db.update_studio_task(task_id, progress="Auto-generated image prompt from title...")

    # Ensure we have the HFN style prefix
    if "flat geometric" not in user_prompt.lower() and "editorial illustration" not in user_prompt.lower():
        user_prompt = (
            "Flat geometric editorial illustration in a mid-century modern poster style. "
            "The illustration must fill the ENTIRE frame edge-to-edge with NO empty space, NO margins, NO borders. "
            "Warm muted editorial palette (terracotta, navy, sand, teal, grey, ochre). "
            "No text, no writing, no photorealism, no detailed faces, no people. "
            "Landscape orientation, wide panoramic format, 16:9 aspect ratio. "
        ) + user_prompt

    # Always add edge-to-edge instruction
    if "edge-to-edge" not in user_prompt.lower() and "fill the entire" not in user_prompt.lower():
        user_prompt += " The illustration must fill the ENTIRE frame edge-to-edge. No empty space, no margins, no background padding."

    # Always ensure landscape orientation is requested
    if "landscape" not in user_prompt.lower() and "16:9" not in user_prompt:
        user_prompt += " Landscape orientation, wide format, 16:9 aspect ratio."

    # Check API key — try env first, then fall back to .zshrc extraction
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Try loading from shell config as fallback
        zshrc = Path.home() / ".zshrc"
        if zshrc.exists():
            import re as _re
            for line in zshrc.read_text().splitlines():
                m = _re.match(r'export\s+GEMINI_API_KEY=["\']?([^"\']+)', line)
                if m:
                    api_key = m.group(1)
                    break
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment or ~/.zshrc")

    db.update_studio_task(task_id, progress="Calling Gemini image generation...")

    # Run image generation via subprocess with system python3 (has google-generativeai)
    img_dir = HFN_ARTICLE_IMAGES / draft["slug"]
    img_dir.mkdir(parents=True, exist_ok=True)
    hero = img_dir / "hero.png"

    # Use json to safely pass prompt/api_key/output path
    import json as _json
    args_json = _json.dumps({"prompt": user_prompt, "api_key": api_key, "output": str(hero)})

    gen_script = """
import sys, json, warnings, pathlib, io
warnings.filterwarnings("ignore", category=FutureWarning)
args = json.loads(sys.argv[1])
import google.generativeai as genai
genai.configure(api_key=args["api_key"])
model = genai.GenerativeModel("gemini-2.5-flash-image")
response = model.generate_content(
    "Generate an image: " + args["prompt"],
    generation_config={"response_modalities": ["IMAGE"]},
)
for part in (response.candidates[0].content.parts if response.candidates else []):
    if hasattr(part, "inline_data") and part.inline_data:
        raw_bytes = part.inline_data.data
        # Crop-to-fit 1200x675 (HFN hero image standard) — never stretch
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(raw_bytes))
            target_w, target_h = 1200, 675
            target_ratio = target_w / target_h
            src_ratio = img.width / img.height
            if src_ratio > target_ratio:
                # Source is wider — fit height, crop width
                new_h = target_h
                new_w = int(img.width * target_h / img.height)
            else:
                # Source is taller — fit width, crop height
                new_w = target_w
                new_h = int(img.height * target_w / img.width)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            left = (new_w - target_w) // 2
            top = (new_h - target_h) // 2
            img = img.crop((left, top, left + target_w, top + target_h))
            img.save(args["output"], "PNG", optimize=True)
        except ImportError:
            # No Pillow — save raw and warn
            pathlib.Path(args["output"]).write_bytes(raw_bytes)
            print("OK_NO_RESIZE")
            sys.exit(0)
        print("OK")
        sys.exit(0)
print("NO_IMAGE")
sys.exit(1)
"""

    proc = subprocess.run(
        ["/opt/homebrew/bin/python3", "-c", gen_script, args_json],
        capture_output=True, text=True, timeout=120
    )

    if proc.returncode != 0:
        err = (proc.stderr.strip() or proc.stdout.strip() or "Unknown error")[:1000]
        raise RuntimeError(f"Gemini image generation failed: {err}")

    if not hero.exists():
        raise RuntimeError(f"Image generation succeeded but {hero} not found")

    db.update_draft(draft_id, has_hero_image=1, stage="images")
    db.update_studio_task(task_id, progress="Hero image generated")


def _run_generate_audio(task_id, draft_id):
    """Run audio narration generation."""
    import os

    draft = db.get_draft(draft_id)
    if not draft:
        raise ValueError("Draft not found")

    # Audio script reads from essays/{slug}.md — save to disk first if needed
    essay_path = HFN_CONTENT_DIR / f"{draft['slug']}.md"
    if not essay_path.exists():
        db.update_studio_task(task_id, progress="Saving to disk first...")
        _run_save_to_disk(task_id, draft_id)

    db.update_studio_task(task_id, progress="Generating audio narration...")

    script = BUILD_SYSTEM / "generate_audio.py"
    if not script.exists():
        raise FileNotFoundError(f"Audio script not found: {script}")

    # Get GEMINI_API_KEY for the subprocess environment
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        zshrc = Path.home() / ".zshrc"
        if zshrc.exists():
            import re as _re
            for line in zshrc.read_text().splitlines():
                m = _re.match(r'export\s+GEMINI_API_KEY=["\']?([^"\']+)', line)
                if m:
                    api_key = m.group(1)
                    break
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment or ~/.zshrc")

    # Build env with the API key + proper PATH (launchd has minimal PATH)
    env = _SUBPROCESS_ENV.copy()
    env["GEMINI_API_KEY"] = api_key

    # Use system python3 (has required packages: yaml, requests, etc.)
    proc = subprocess.run(
        ["/opt/homebrew/bin/python3", str(script), "--article", draft["slug"]],
        cwd=str(BUILD_SYSTEM),
        env=env,
        capture_output=True, text=True, timeout=600
    )

    if proc.returncode != 0:
        err = (proc.stderr[:500] if proc.stderr else proc.stdout[:500]) or "Unknown error"
        raise RuntimeError(f"Audio generation failed: {err}")

    # Check if audio file was created
    audio_path = HFN_AUDIO_DIR / f"{draft['slug']}.mp3"
    if audio_path.exists():
        db.update_draft(draft_id, has_audio=1)
        db.update_studio_task(task_id, progress="Audio generated")
    else:
        db.update_studio_task(task_id, progress="Script ran but MP3 not found")


def _run_build(task_id, draft_id):
    """Run the site build to generate preview HTML."""
    draft = db.get_draft(draft_id)
    if not draft:
        raise ValueError("Draft not found")

    db.update_studio_task(task_id, progress="Adding to review slugs...")

    # Add slug to review_slugs.json so build.py includes it
    review_file = BUILD_SYSTEM / "review_slugs.json"
    slugs = set()
    if review_file.exists():
        try:
            slugs = set(json.loads(review_file.read_text()))
        except (json.JSONDecodeError, TypeError):
            pass
    slugs.add(draft["slug"])
    review_file.write_text(json.dumps(sorted(slugs), indent=2))

    db.update_studio_task(task_id, progress="Building site...")

    proc = subprocess.run(
        ["/opt/homebrew/bin/python3", str(BUILD_SYSTEM / "build.py")],
        cwd=str(BUILD_SYSTEM),
        capture_output=True, text=True, timeout=300
    )

    if proc.returncode != 0:
        err = proc.stderr[:300] if proc.stderr else "Unknown error"
        raise RuntimeError(f"Build failed: {err}")

    db.update_draft(draft_id, stage="review")
    db.update_studio_task(task_id, progress="Build complete — ready for deploy")


def _run_deploy(task_id, draft_id):
    """Save to disk, build, then deploy to review via deploy.sh."""
    draft = db.get_draft(draft_id)
    if not draft:
        raise ValueError("Draft not found")

    # Step 1: Save to disk (ensures essays/{slug}.md exists)
    db.update_studio_task(task_id, progress="Saving to disk...")
    _run_save_to_disk(task_id, draft_id)

    # Step 2: Build (adds to review_slugs, runs build.py)
    db.update_studio_task(task_id, progress="Building site...")
    _run_build(task_id, draft_id)

    # Step 3: Git pull to avoid rejection (remote may have new commits)
    db.update_studio_task(task_id, progress="Syncing with remote...")
    root_dir = str(BUILD_SYSTEM.parent)
    pull = subprocess.run(
        ["git", "pull", "--rebase", "--autostash"],
        cwd=root_dir, env=_SUBPROCESS_ENV,
        capture_output=True, text=True, timeout=120
    )
    if pull.returncode != 0:
        err = pull.stderr[:300] if pull.stderr else "pull failed"
        raise RuntimeError(f"Git pull failed: {err}")

    # Step 4: Deploy (skip-build since we already built)
    db.update_studio_task(task_id, progress="Deploying to review...")

    deploy_script = SCRIPTS_DIR / "deploy.sh"
    if not deploy_script.exists():
        raise FileNotFoundError(f"Deploy script not found: {deploy_script}")

    proc = subprocess.run(
        ["bash", str(deploy_script), "--skip-build",
         f"feat: deploy {draft['title'][:50]} to review"],
        cwd=root_dir, env=_SUBPROCESS_ENV,
        capture_output=True, text=True, timeout=600
    )

    if proc.returncode != 0:
        err = (proc.stderr[:300] if proc.stderr else proc.stdout[:300]) or "Unknown error"
        raise RuntimeError(f"Deploy failed: {err}")

    db.update_draft(draft_id, stage="in_review")
    db.update_studio_task(task_id, progress="Deployed to review — awaiting approval")


def _run_publish(task_id, draft_id):
    """Publish article to the public website."""
    draft = db.get_draft(draft_id)
    if not draft:
        raise ValueError("Draft not found")

    slug = draft["slug"]
    db.update_studio_task(task_id, progress="Moving article to public site...")

    # Remove from review_slugs.json
    review_file = BUILD_SYSTEM / "review_slugs.json"
    if review_file.exists():
        try:
            slugs = set(json.loads(review_file.read_text()))
            slugs.discard(slug)
            review_file.write_text(json.dumps(sorted(slugs), indent=2))
        except (json.JSONDecodeError, TypeError):
            pass

    # Add to released_slugs.json
    released_file = BUILD_SYSTEM / "released_slugs.json"
    released = set()
    if released_file.exists():
        try:
            released = set(json.loads(released_file.read_text()))
        except (json.JSONDecodeError, TypeError):
            pass
    released.add(slug)
    released_file.write_text(json.dumps(sorted(released), indent=2))

    # Rebuild site
    db.update_studio_task(task_id, progress="Rebuilding site...")
    proc = subprocess.run(
        ["/opt/homebrew/bin/python3", str(BUILD_SYSTEM / "build.py")],
        cwd=str(BUILD_SYSTEM),
        capture_output=True, text=True, timeout=300
    )
    if proc.returncode != 0:
        err = proc.stderr[:300] if proc.stderr else "Unknown error"
        raise RuntimeError(f"Build failed: {err}")

    # Deploy to Vercel
    db.update_studio_task(task_id, progress="Deploying to website...")
    deploy_script = SCRIPTS_DIR / "deploy.sh"
    if not deploy_script.exists():
        raise FileNotFoundError(f"Deploy script not found: {deploy_script}")

    proc = subprocess.run(
        ["bash", str(deploy_script), "--skip-build",
         f"feat: publish {draft['title'][:50]}"],
        cwd=str(BUILD_SYSTEM.parent),
        capture_output=True, text=True, timeout=300
    )
    if proc.returncode != 0:
        err = proc.stderr[:300] if proc.stderr else "Unknown error"
        raise RuntimeError(f"Deploy failed: {err}")

    db.update_draft(draft_id, stage="published")
    db.update_studio_task(task_id, progress="Published to website")
