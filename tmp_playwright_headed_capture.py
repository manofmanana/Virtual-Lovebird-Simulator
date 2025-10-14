from playwright.sync_api import sync_playwright
import time
import json

URL = "http://127.0.0.1:8000/index.html"
OUT_DIR = "build/web"
TERMINAL_OUT = f"{OUT_DIR}/pygbag_headed_terminal.txt"
CONSOLE_OUT = f"{OUT_DIR}/pygbag_headed_console.json"
SCREENSHOT_OUT = f"{OUT_DIR}/pygbag_headed_screenshot.png"

console_events = []

with sync_playwright() as p:
    # Launch headed so user can watch the browser
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width":1280, "height":720})
    page = context.new_page()

    def on_console(msg):
        try:
            # capture more info when available
            entry = {"type": msg.type, "text": msg.text}
            try:
                entry["location"] = msg.location
            except Exception:
                pass
            console_events.append(entry)
        except Exception:
            console_events.append({"type": "error", "text": "<console capture failed>"})

    page.on("console", on_console)

    print("navigating to page...", URL)
    page.goto(URL, wait_until="load")

    # click center of canvas to satisfy user gesture (autoplay/audio)
    print("clicking canvas center to satisfy user gesture")
    try:
        page.mouse.click(640, 360)
    except Exception as e:
        print("initial click failed:", e)
    time.sleep(0.5)

    # click near the expected Flappy button (right-side top area)
    print("clicking flappy button area")
    try:
        page.mouse.click(1080, 60)
    except Exception as e:
        print("flappy click failed:", e)

    # wait for runtime to react and possibly log - longer so user can observe
    timeout = 30.0
    poll_interval = 0.5
    elapsed = 0.0

    def get_terminal_text():
        try:
            return page.evaluate("() => (document.getElementById('terminal') ? document.getElementById('terminal').innerText : document.body.innerText)")
        except Exception as e:
            return f"<evaluate-failed: {e}>"

    last_text = get_terminal_text() or ""
    print("initial terminal len:", len(last_text))

    polled = last_text
    while elapsed < timeout:
        time.sleep(poll_interval)
        elapsed += poll_interval
        polled = get_terminal_text() or ""
        # print progress while waiting so user knows it's polling
        print(f"poll elapsed={elapsed:.1f}s terminal_len={len(polled)}")
        if polled and polled != last_text:
            print("terminal changed (len now)", len(polled))
            break

    # extra small wait for late logs
    time.sleep(0.6)

    # save artifacts
    print("saving screenshot to", SCREENSHOT_OUT)
    try:
        page.screenshot(path=SCREENSHOT_OUT, full_page=True)
    except Exception as e:
        print("screenshot failed:", e)

    print("writing terminal dump to", TERMINAL_OUT)
    try:
        with open(TERMINAL_OUT, "w", encoding="utf-8") as f:
            f.write(polled or "")
    except Exception as e:
        print("write terminal failed:", e)

    print("writing console events to", CONSOLE_OUT)
    try:
        with open(CONSOLE_OUT, "w", encoding="utf-8") as f:
            json.dump(console_events, f, indent=2)
    except Exception as e:
        print("write console failed:", e)

    print("keeping browser open for user to inspect (press Ctrl+C here to continue)")
    try:
        # keep the script alive so user can interact with the browser
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("closing browser after user interrupt")

    browser.close()
    print("done")
