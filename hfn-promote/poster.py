"""HFN Promote — Poster. Playwright browser automation for X and LinkedIn.

X: Uses your real Chrome profile (persistent context) — the only approach X accepts.
   Chrome close/reopen is batched: one bounce per posting cycle, not per post.
LinkedIn: Uses LinkedIn's Voyager REST API with saved session cookies.
          Falls back to Playwright browser automation if API image upload fails.

Login: python3 poster.py linkedin  (X uses your Chrome profile — no login needed)
"""
import json, time, subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import requests
import db
from config import SESSIONS_DIR, MAX_X_PER_DAY, MAX_LI_PER_DAY

LI_SESSION = SESSIONS_DIR / "linkedin_session.json"
CHROME_PROFILE = Path.home() / "Library/Application Support/Google/Chrome"

def _load_cookies(path):
    return json.loads(path.read_text()) if path.exists() else []

def _save_cookies(page, path):
    path.write_text(json.dumps(page.context.cookies(), indent=2))


def login_interactive(platform):
    """One-time interactive login to save session cookies (LinkedIn only).
    X uses your Chrome profile directly — no separate login needed."""
    if platform == "x":
        print("\n  X uses your Chrome profile — no login step needed.")
        print("  Just make sure you're logged into x.com in Chrome.\n")
        return
    url = "https://www.linkedin.com/login"
    session_path = LI_SESSION
    print(f"\n  Opening {platform} login page...")
    print("  Log in manually, then press Enter here.\n")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        cookies = _load_cookies(session_path)
        if cookies:
            ctx.add_cookies(cookies)
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded")
        input("  Press Enter after logging in... ")
        _save_cookies(page, session_path)
        print(f"  ✓ Session saved to {session_path.name}")
        ctx.close()
        browser.close()


# ── X / Twitter ──

def _close_chrome():
    """Close Chrome and wait for it to release profile lock. Returns True if Chrome was running."""
    try:
        result = subprocess.run(["pgrep", "-x", "Google Chrome"], capture_output=True)
        if result.returncode != 0:
            return False  # Not running
        print("  Pausing Chrome for X posts...")
        subprocess.run(["osascript", "-e", 'tell application "Google Chrome" to quit'], timeout=10)
        for _ in range(15):
            time.sleep(1)
            if subprocess.run(["pgrep", "-x", "Google Chrome"], capture_output=True).returncode != 0:
                return True
        print("  [!] Chrome didn't close in time")
        return False
    except Exception:
        return False


def _reopen_chrome():
    """Reopen Chrome."""
    print("  Resuming Chrome...")
    subprocess.Popen(["open", "-a", "Google Chrome"])


def _post_to_x_single(page, text, image_path):
    """Post a single tweet using an already-open Playwright page. Returns True on success."""
    try:
        page.goto("https://x.com/compose/post", wait_until="domcontentloaded")
        time.sleep(3)

        # Dismiss overlays
        for dismiss_sel in ['[data-testid="twc-cc-mask"]', '[data-testid="sheetDialog"] button',
                            '[aria-label="Close"]', '[data-testid="app-bar-close"]']:
            try:
                el = page.locator(dismiss_sel).first
                if el.is_visible(timeout=1000):
                    el.click(force=True)
                    time.sleep(1)
            except:
                pass

        if "login" in page.url.lower():
            print("  [!] Not logged in to X — log in via Chrome and retry")
            try: page.screenshot(path=str(SESSIONS_DIR / "x_debug.png"))
            except: pass
            return False

        editor = page.get_by_test_id("primaryColumn").get_by_test_id("tweetTextarea_0")
        editor.wait_for(timeout=10000)
        editor.click(force=True)
        time.sleep(0.5)

        for ch in text:
            page.keyboard.press(ch) if len(ch) == 1 and ch.isalnum() else page.keyboard.type(ch, delay=10)
            time.sleep(0.01)
        time.sleep(2)

        try:
            page.wait_for_function("""() => {
                const btn = document.querySelector('[data-testid="tweetButtonInline"]');
                return btn && !btn.disabled;
            }""", timeout=10000)
        except:
            editor.click(force=True)
            time.sleep(0.5)
            page.evaluate(f"""() => {{
                const dt = new DataTransfer();
                dt.setData('text/plain', {json.dumps(text)});
                const el = document.querySelector('[data-testid="tweetTextarea_0"]');
                el.dispatchEvent(new ClipboardEvent('paste', {{clipboardData: dt, bubbles: true}}));
            }}""")
            time.sleep(2)
        time.sleep(1)

        if image_path and Path(image_path).exists():
            page.locator('input[data-testid="fileInput"]').set_input_files(image_path)
            time.sleep(3)

        page.locator('[data-testid="tweetButtonInline"]').click()
        time.sleep(3)
        return True
    except Exception as ex:
        try: page.screenshot(path=str(SESSIONS_DIR / "x_debug.png"))
        except: pass
        print(f"  [!] X error: {ex}")
        return False


def post_to_x(text, image_path=None):
    """Post a single tweet. Closes Chrome, posts, reopens. For single manual posts."""
    if db.posts_today("x") >= MAX_X_PER_DAY:
        print(f"  [!] X daily limit reached ({MAX_X_PER_DAY})")
        return False

    chrome_was_running = _close_chrome()
    try:
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                str(CHROME_PROFILE / "Default"),
                headless=True, channel="chrome",
                viewport={"width": 1280, "height": 900},
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = ctx.new_page()
            ok = _post_to_x_single(page, text, image_path)
            ctx.close()
            return ok
    finally:
        if chrome_was_running:
            _reopen_chrome()


def post_x_batch(posts_with_text):
    """Post multiple tweets in one Chrome session. One close/reopen cycle.
    posts_with_text: list of (post_dict, text_str) tuples.
    Returns list of (post_dict, success_bool)."""
    if not posts_with_text:
        return []

    chrome_was_running = _close_chrome()
    results = []
    try:
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                str(CHROME_PROFILE / "Default"),
                headless=True, channel="chrome",
                viewport={"width": 1280, "height": 900},
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = ctx.new_page()
            for post, text in posts_with_text:
                ok = _post_to_x_single(page, text, post.get("image_path"))
                results.append((post, ok))
                if ok:
                    time.sleep(2)  # Brief pause between posts
                else:
                    # If login failed, skip remaining
                    if "login" in (page.url or "").lower():
                        for remaining_post, _ in posts_with_text[len(results):]:
                            results.append((remaining_post, False))
                        break
            ctx.close()
    except Exception as ex:
        print(f"  [!] X batch error: {ex}")
        # Mark remaining as failed
        for post, text in posts_with_text[len(results):]:
            results.append((post, False))
    finally:
        if chrome_was_running:
            _reopen_chrome()

    return results


# ── LinkedIn ──

def _li_api_session():
    """Build a requests.Session from saved Playwright LinkedIn cookies.
    Returns (session, error_msg). Session is None on failure."""
    cookies = _load_cookies(LI_SESSION)
    if not cookies:
        return None, "No LinkedIn session. Run: python3 poster.py linkedin"

    li_at = None
    jsessionid = None
    for c in cookies:
        if c["name"] == "li_at":
            li_at = c["value"]
        elif c["name"] == "JSESSIONID":
            jsessionid = c["value"].strip('"')

    if not li_at or not jsessionid:
        return None, "LinkedIn session cookies missing li_at or JSESSIONID. Run: python3 poster.py linkedin"

    s = requests.Session()
    s.cookies.set("li_at", li_at, domain=".www.linkedin.com")
    s.cookies.set("JSESSIONID", f'"{jsessionid}"', domain=".www.linkedin.com")
    s.headers.update({
        "csrf-token": jsessionid,
        "x-restli-protocol-version": "2.0.0",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "accept": "application/vnd.linkedin.normalized+json+2.1",
    })
    return s, None


def _deep_get(d, *keys):
    """Safely traverse nested dicts."""
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _li_upload_image(session, image_path, max_retries=3):
    """Register + upload an image via LinkedIn Voyager API with retries.
    Returns (media_urn, error_msg). media_urn is None on failure."""
    img = Path(image_path)
    file_size = img.stat().st_size
    suffix = img.suffix.lower()
    content_type = "image/png" if suffix == ".png" else "image/jpeg"

    last_err = None
    for attempt in range(max_retries):
        if attempt > 0:
            time.sleep(2 * attempt)
            print(f"  Retrying image upload (attempt {attempt + 1}/{max_retries})...")

        try:
            register_url = "https://www.linkedin.com/voyager/api/voyagerMediaUploadMetadata?action=upload"
            register_body = {
                "mediaUploadType": "IMAGE_SHARING",
                "fileSize": file_size,
                "filename": img.name,
            }
            resp = session.post(register_url, json=register_body)
            if resp.status_code in (401, 403):
                return None, "LinkedIn session expired. Run: python3 poster.py linkedin"
            if resp.status_code != 200:
                last_err = f"Register HTTP {resp.status_code}: {resp.text[:300]}"
                print(f"  [!] {last_err}")
                continue

            raw = resp.json()
            data = raw.get("data", raw)
            value = data.get("value", data)

            upload_url = (
                value.get("singleUploadUrl")
                or value.get("uploadUrl")
                or _deep_get(value, "uploadMechanism",
                             "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest",
                             "uploadUrl")
            )
            media_urn = (
                value.get("urn")
                or value.get("mediaArtifact")
            )

            if not upload_url or not media_urn:
                last_err = f"Couldn't parse register response: {json.dumps(raw)[:400]}"
                print(f"  [!] {last_err}")
                continue

            with open(img, "rb") as f:
                put_resp = session.put(upload_url, data=f, headers={
                    "Content-Type": content_type,
                    "accept": "*/*",
                })
            if put_resp.status_code not in (200, 201):
                last_err = f"Upload PUT HTTP {put_resp.status_code}: {put_resp.text[:300]}"
                print(f"  [!] {last_err}")
                continue

            print(f"  ✓ Image uploaded via API ({media_urn[:50]}...)")
            return media_urn, None

        except Exception as ex:
            last_err = str(ex)
            print(f"  [!] Upload attempt {attempt + 1} error: {ex}")

    return None, f"Image upload failed after {max_retries} attempts. Last error: {last_err}"


def _li_post_playwright(text, image_path):
    """Fallback: post to LinkedIn via Playwright browser automation.
    Used when the Voyager REST API image upload fails."""
    cookies = _load_cookies(LI_SESSION)
    if not cookies:
        print("  [!] No LinkedIn cookies for Playwright fallback")
        return False

    print("  Trying Playwright fallback for LinkedIn post...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        try:
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
            time.sleep(3)

            if "login" in page.url.lower() or "checkpoint" in page.url.lower():
                print("  [!] LinkedIn session expired for Playwright. Run: python3 poster.py linkedin")
                try: page.screenshot(path=str(SESSIONS_DIR / "li_debug.png"))
                except: pass
                return False

            trigger = page.locator(
                'button.share-box-feed-entry__trigger, '
                'button.artdeco-button--tertiary[class*="share-box"], '
                '[data-test-id="share-box-feed-entry__trigger"]'
            ).first
            trigger.wait_for(timeout=10000)
            trigger.click()
            time.sleep(2)

            modal = page.locator(
                '.share-creation-state, '
                '[data-test-id="share-creation-state"], '
                '.share-box_actions'
            ).first
            modal.wait_for(timeout=10000)

            if image_path and Path(image_path).exists():
                media_btn = page.locator(
                    'button[aria-label*="media"], '
                    'button[aria-label*="image"], '
                    'button[aria-label*="photo"], '
                    'button[aria-label*="Add a photo"]'
                ).first
                try:
                    media_btn.wait_for(timeout=5000)
                    media_btn.click()
                    time.sleep(1)
                except:
                    pass

                file_input = page.locator('input[type="file"][accept*="image"]').first
                file_input.wait_for(timeout=5000)
                file_input.set_input_files(image_path)
                time.sleep(3)

                for done_sel in ['button[aria-label="Done"]', 'button[data-test-id="image-sharing-done-button"]',
                                 'button.share-media-actions__done-button']:
                    try:
                        done = page.locator(done_sel).first
                        if done.is_visible(timeout=2000):
                            done.click()
                            time.sleep(1)
                            break
                    except:
                        pass

            editor = page.locator(
                '.ql-editor[contenteditable="true"], '
                'div[role="textbox"][contenteditable="true"], '
                '[data-test-id="share-creation-text-area"] .ql-editor'
            ).first
            editor.wait_for(timeout=10000)
            editor.click()
            time.sleep(0.5)
            page.keyboard.type(text, delay=5)
            time.sleep(2)

            post_btn = page.locator(
                'button.share-actions__primary-action, '
                'button[data-test-id="share-actions__primary-action"], '
                'button[class*="share-actions__primary"]'
            ).first
            post_btn.wait_for(timeout=10000)
            post_btn.click()
            time.sleep(4)

            try: _save_cookies(page, LI_SESSION)
            except: pass

            print("  ✓ Posted via Playwright fallback")
            return True

        except Exception as ex:
            try: page.screenshot(path=str(SESSIONS_DIR / "li_debug.png"))
            except: pass
            print(f"  [!] LinkedIn Playwright error: {ex}")
            print(f"      Debug screenshot saved to {SESSIONS_DIR / 'li_debug.png'}")
            return False
        finally:
            ctx.close()
            browser.close()


def post_to_linkedin(text, image_path=None):
    """Post to LinkedIn. Tries Voyager REST API first, falls back to Playwright."""
    if db.posts_today("linkedin") >= MAX_LI_PER_DAY:
        print(f"  [!] LinkedIn daily limit reached ({MAX_LI_PER_DAY})")
        return False

    session, err = _li_api_session()
    if not session:
        print(f"  [!] {err}")
        return False

    media_urn = None
    if image_path:
        if not Path(image_path).exists():
            print(f"  [!] Image file not found: {image_path}")
            return False
        media_urn, img_err = _li_upload_image(session, image_path)
        if img_err:
            print(f"  [!] API image upload failed: {img_err}")
            print(f"  Falling back to Playwright...")
            return _li_post_playwright(text, image_path)

    share_url = "https://www.linkedin.com/voyager/api/contentcreation/normShares"
    payload = {
        "visibleToConnectionsOnly": False,
        "externalAudienceProviders": [],
        "commentaryV2": {"text": text, "attributes": []},
        "origin": "FEED",
        "allowedCommentersScope": "ALL",
        "postState": "PUBLISHED",
    }

    if media_urn:
        payload["mediaCategory"] = "IMAGE"
        payload["attachments"] = [{"id": media_urn}]

    try:
        resp = session.post(share_url, json=payload)
        if resp.status_code in (401, 403):
            print("  [!] LinkedIn session expired. Run: python3 poster.py linkedin")
            return False
        if resp.status_code in (200, 201):
            return True
        print(f"  [!] LinkedIn share failed (HTTP {resp.status_code}): {resp.text[:300]}")
        if image_path:
            print(f"  Falling back to Playwright...")
            return _li_post_playwright(text, image_path)
        return False
    except Exception as ex:
        print(f"  [!] LinkedIn error: {ex}")
        if image_path:
            return _li_post_playwright(text, image_path)
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        login_interactive(sys.argv[1])
    else:
        print("Usage: python3 poster.py linkedin")
        print("  Saves login session for automated posting")
        print("  X uses your Chrome profile — no login needed")
