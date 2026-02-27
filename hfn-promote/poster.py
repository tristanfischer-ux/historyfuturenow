"""HFN Promote — Poster. Playwright browser automation for X and LinkedIn.

X: Uses your real Chrome profile (already logged in).
LinkedIn: Uses LinkedIn's Voyager REST API with saved session cookies.

IMPORTANT: Chrome must be fully closed before posting to X,
because Chrome locks its profile directory while running.
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
    """One-time interactive login to save session cookies."""
    url = "https://x.com/login" if platform == "x" else "https://www.linkedin.com/login"
    session = SESSIONS_DIR / f"{platform}_session.json"
    print(f"\n  Opening {platform} login page...")
    print("  Log in manually, then press Enter here.\n")
    with sync_playwright() as p:
        if platform == "x":
            ctx = p.chromium.launch_persistent_context(
                str(CHROME_PROFILE / "Default"),
                headless=False,
                channel="chrome",
                viewport={"width": 1280, "height": 900},
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = ctx.new_page()
        else:
            browser = p.chromium.launch(headless=False)
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            cookies = _load_cookies(session)
            if cookies: ctx.add_cookies(cookies)
            page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded")
        input("  Press Enter after logging in... ")
        if platform != "x":
            _save_cookies(page, session)
        print(f"  ✓ Session saved")
        ctx.close()
        if platform != "x":
            browser.close()


def post_to_x(text, image_path=None):
    """Post to X using real Chrome profile."""
    if db.posts_today("x") >= MAX_X_PER_DAY:
        print(f"  [!] X daily limit reached ({MAX_X_PER_DAY})")
        return False

    # Check Chrome isn't running (it locks the profile)
    try:
        result = subprocess.run(["pgrep", "-x", "Google Chrome"], capture_output=True)
        if result.returncode == 0:
            print("  [!] Chrome is running. Close Chrome first, or X posting will fail.")
            print("      (Chrome locks its profile while running)")
            return False
    except Exception:
        pass

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(CHROME_PROFILE / "Default"),
            headless=True,
            channel="chrome",
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.new_page()
        try:
            page.goto("https://x.com/compose/post", wait_until="domcontentloaded")
            time.sleep(3)

            # Dismiss any overlay/cookie consent/notification layers
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
                print("  [!] Not logged in to X. Run: python3 poster.py x")
                page.screenshot(path=str(SESSIONS_DIR / "x_debug.png"))
                return False

            editor = page.get_by_test_id("primaryColumn").get_by_test_id("tweetTextarea_0")
            editor.wait_for(timeout=10000)
            editor.click(force=True)
            time.sleep(0.5)
            # Type character by character with press events to trigger React state updates
            for ch in text:
                page.keyboard.press(ch) if len(ch) == 1 and ch.isalnum() else page.keyboard.type(ch, delay=10)
                time.sleep(0.01)
            time.sleep(2)

            # Wait for post button to become enabled (means text was registered)
            post_btn = page.locator('[data-testid="tweetButtonInline"]')
            try:
                page.wait_for_function("""() => {
                    const btn = document.querySelector('[data-testid="tweetButtonInline"]');
                    return btn && !btn.disabled;
                }""", timeout=10000)
            except:
                # Fallback: try clicking editor and using clipboard
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
            page.screenshot(path=str(SESSIONS_DIR / "x_debug.png"))
            print(f"  [!] X error: {ex}")
            return False
        finally:
            ctx.close()


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


def _li_upload_image(session, image_path):
    """Register + upload an image via LinkedIn Voyager API.
    Returns (media_urn, error_msg). media_urn is None on failure."""
    img = Path(image_path)
    file_size = img.stat().st_size
    suffix = img.suffix.lower()
    content_type = "image/png" if suffix == ".png" else "image/jpeg"

    # Step 1: Register the upload
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
        return None, f"Image register failed (HTTP {resp.status_code}): {resp.text[:200]}"

    data = resp.json().get("data", resp.json())
    upload_url = data.get("value", data).get("singleUploadUrl") or data.get("value", data).get("uploadUrl")
    media_urn = data.get("value", data).get("urn") or data.get("value", data).get("mediaArtifact")

    if not upload_url or not media_urn:
        return None, f"Unexpected register response: {json.dumps(data)[:300]}"

    # Step 2: Upload the binary
    with open(img, "rb") as f:
        put_resp = session.put(upload_url, data=f, headers={
            "Content-Type": content_type,
            "accept": "*/*",
        })
    if put_resp.status_code not in (200, 201):
        return None, f"Image upload failed (HTTP {put_resp.status_code}): {put_resp.text[:200]}"

    return media_urn, None


def post_to_linkedin(text, image_path=None):
    """Post to LinkedIn using the Voyager REST API with saved session cookies."""
    if db.posts_today("linkedin") >= MAX_LI_PER_DAY:
        print(f"  [!] LinkedIn daily limit reached ({MAX_LI_PER_DAY})")
        return False

    session, err = _li_api_session()
    if not session:
        print(f"  [!] {err}")
        return False

    # Upload image if provided
    media_urn = None
    if image_path and Path(image_path).exists():
        media_urn, img_err = _li_upload_image(session, image_path)
        if img_err:
            print(f"  [!] Image upload failed, posting without image: {img_err}")
            media_urn = None

    # Build post payload (note: endpoint is lowercase 'contentcreation')
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
        print(f"  [!] LinkedIn post failed (HTTP {resp.status_code}): {resp.text[:300]}")
        return False
    except Exception as ex:
        print(f"  [!] LinkedIn error: {ex}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        login_interactive(sys.argv[1])
    else:
        print("Usage: python3 poster.py [x|linkedin]")
        print("  Saves login session for automated posting")
