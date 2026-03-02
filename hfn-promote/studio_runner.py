"""Article Studio — Background task runner using threading + subprocess."""
import threading, subprocess, json
from datetime import datetime
from pathlib import Path
import db
from config import HFN_SOURCE_DIR, HFN_SITE_OUTPUT, HFN_CONTENT_DIR, HFN_AUDIO_DIR, HFN_ARTICLE_IMAGES

BUILD_SYSTEM = HFN_SOURCE_DIR
SCRIPTS_DIR = HFN_SOURCE_DIR.parent / "scripts"


def start_task(task_id, task_type, draft_id):
    """Spawn a background thread to run the given task."""
    runners = {
        "save_to_disk": _run_save_to_disk,
        "generate_image": _run_generate_image,
        "generate_audio": _run_generate_audio,
        "build": _run_build,
        "deploy": _run_deploy,
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


def _run_save_to_disk(task_id, draft_id):
    """Write draft markdown to essays/ with YAML frontmatter."""
    draft = db.get_draft(draft_id)
    if not draft:
        raise ValueError("Draft not found")

    db.update_studio_task(task_id, progress="Writing file...")

    # Build frontmatter
    fm_lines = ["---"]
    fm_lines.append(f"title: \"{draft['title']}\"")
    if draft.get("section"):
        fm_lines.append(f"section: \"{draft['section']}\"")
    if draft.get("excerpt"):
        fm_lines.append(f"excerpt: \"{draft['excerpt']}\"")
    if draft.get("share_summary"):
        fm_lines.append(f"share_summary: \"{draft['share_summary']}\"")
    fm_lines.append("---")
    fm_lines.append("")

    content = "\n".join(fm_lines) + (draft.get("markdown") or "")

    out_path = HFN_CONTENT_DIR / f"{draft['slug']}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")

    db.update_studio_task(task_id, progress=f"Saved to {out_path.name}")
    db.update_draft(draft_id, stage="draft")


def _run_generate_image(task_id, draft_id):
    """Run the hero image generation script."""
    draft = db.get_draft(draft_id)
    if not draft:
        raise ValueError("Draft not found")

    db.update_studio_task(task_id, progress="Generating hero image...")

    script = BUILD_SYSTEM / "generate_chart_images.py"
    if not script.exists():
        # Fallback — try generate_icons or a generic image gen
        raise FileNotFoundError(f"Image generation script not found: {script}")

    # Ensure output dir exists
    img_dir = HFN_ARTICLE_IMAGES / draft["slug"]
    img_dir.mkdir(parents=True, exist_ok=True)

    # Run image generation — this is a placeholder call
    # The actual command depends on the HFN build system's image generation pipeline
    proc = subprocess.run(
        ["python", str(script), "--slug", draft["slug"]],
        cwd=str(BUILD_SYSTEM),
        capture_output=True, text=True, timeout=300
    )

    if proc.returncode != 0:
        err = proc.stderr[:300] if proc.stderr else "Unknown error"
        raise RuntimeError(f"Image generation failed: {err}")

    # Check if hero image was created
    hero = img_dir / "hero.png"
    if hero.exists():
        db.update_draft(draft_id, has_hero_image=1, stage="images")
        db.update_studio_task(task_id, progress="Hero image generated")
    else:
        db.update_studio_task(task_id, progress="Script ran but hero.png not found")


def _run_generate_audio(task_id, draft_id):
    """Run audio narration generation."""
    draft = db.get_draft(draft_id)
    if not draft:
        raise ValueError("Draft not found")

    db.update_studio_task(task_id, progress="Generating audio narration...")

    script = BUILD_SYSTEM / "generate_audio.py"
    if not script.exists():
        raise FileNotFoundError(f"Audio script not found: {script}")

    proc = subprocess.run(
        ["python", str(script), "--slug", draft["slug"]],
        cwd=str(BUILD_SYSTEM),
        capture_output=True, text=True, timeout=600
    )

    if proc.returncode != 0:
        err = proc.stderr[:300] if proc.stderr else "Unknown error"
        raise RuntimeError(f"Audio generation failed: {err}")

    # Check if audio file was created
    audio_path = HFN_AUDIO_DIR / f"{draft['slug']}.mp3"
    if audio_path.exists():
        db.update_draft(draft_id, has_audio=1, stage="audio")
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
        ["python", str(BUILD_SYSTEM / "build.py")],
        cwd=str(BUILD_SYSTEM),
        capture_output=True, text=True, timeout=300
    )

    if proc.returncode != 0:
        err = proc.stderr[:300] if proc.stderr else "Unknown error"
        raise RuntimeError(f"Build failed: {err}")

    db.update_draft(draft_id, stage="review")
    db.update_studio_task(task_id, progress="Build complete — preview ready")


def _run_deploy(task_id, draft_id):
    """Deploy the site to production via deploy.sh."""
    draft = db.get_draft(draft_id)
    if not draft:
        raise ValueError("Draft not found")

    db.update_studio_task(task_id, progress="Deploying to production...")

    deploy_script = SCRIPTS_DIR / "deploy.sh"
    if not deploy_script.exists():
        raise FileNotFoundError(f"Deploy script not found: {deploy_script}")

    proc = subprocess.run(
        ["bash", str(deploy_script), f"feat: publish {draft['title'][:50]}"],
        cwd=str(BUILD_SYSTEM.parent),
        capture_output=True, text=True, timeout=300
    )

    if proc.returncode != 0:
        err = proc.stderr[:300] if proc.stderr else "Unknown error"
        raise RuntimeError(f"Deploy failed: {err}")

    db.update_draft(draft_id, stage="deployed")
    db.update_studio_task(task_id, progress="Deployed to production")
