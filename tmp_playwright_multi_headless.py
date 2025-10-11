from playwright.sync_api import sync_playwright
import time
import json

URL = "http://127.0.0.1:8000/index.html"
OUT_DIR = "build/web"
TERMINAL_OUT = f"{OUT_DIR}/pygbag_multi_headless_terminal.txt"
CONSOLE_OUT = f"{OUT_DIR}/pygbag_multi_headless_console.json"
SCREENSHOT_OUT = f"{OUT_DIR}/pygbag_multi_headless_screenshot.png"

console_events = []
terminal_snapshots = {}

clicks = [
    ("flappy", 1080, 60),
    ("feed", 212, 260),
    ("tickle", 880, 320),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width":1280, "height":720})
    page = context.new_page()

    def on_console(msg):
        try:
            console_events.append({"type": msg.type, "text": msg.text})
        except Exception:
            console_events.append({"type": "error", "text": "<console capture failed>"})

    page.on("console", on_console)

    print("navigating to page...", URL)
    page.goto(URL, wait_until="load")

    # initial canvas click
    try:
        page.mouse.click(640, 360)
    except Exception as e:
        print("initial click failed:", e)
    time.sleep(0.5)

    def get_terminal_text():
        try:
            return page.evaluate("() => (document.getElementById('terminal') ? document.getElementById('terminal').innerText : document.body.innerText)")
        except Exception as e:
            return f"<evaluate-failed: {e}>"

    last = get_terminal_text() or ""

    for name, x, y in clicks:
        print(f"clicking {name} at {x},{y}")
        try:
            page.mouse.click(x, y)
        except Exception as e:
            print(f"click {name} failed:", e)
        # wait and poll for terminal change
        timeout = 10.0
        poll = 0.25
        elapsed = 0.0
        snapshot = last
        while elapsed < timeout:
            time.sleep(poll)
            elapsed += poll
            t = get_terminal_text() or ""
            if t and t != last:
                print(f"terminal changed after clicking {name} (len {len(t)})")
                snapshot = t
                last = t
                break
        terminal_snapshots[name] = snapshot
        # small pause before next click
        time.sleep(0.6)

    # screenshot
    try:
        page.screenshot(path=SCREENSHOT_OUT, full_page=True)
    except Exception as e:
        print("screenshot failed:", e)

    # write terminal combined file
    try:
        with open(TERMINAL_OUT, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join([f'== {k} ==\n{v}' for k,v in terminal_snapshots.items()]))
    except Exception as e:
        print('write terminal failed:', e)

    try:
        with open(CONSOLE_OUT, 'w', encoding='utf-8') as f:
            json.dump(console_events, f, indent=2)
    except Exception as e:
        print('write console failed:', e)

    browser.close()
    print('done')
