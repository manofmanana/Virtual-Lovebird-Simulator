from playwright.sync_api import sync_playwright
import time
import json

URL = "http://127.0.0.1:8000/index.html"
OUT_DIR = "build/web"
TERMINAL_OUT = f"{OUT_DIR}/pygbag_polled_terminal.txt"
CONSOLE_OUT = f"{OUT_DIR}/pygbag_polled_console.json"
SCREENSHOT_OUT = f"{OUT_DIR}/pygbag_polled_screenshot.png"

console_events = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width":1280, "height":720})
    page = context.new_page()

    def on_console(msg):
        try:
            console_events.append({"type": msg.type, "text": msg.text})
        except Exception:
            console_events.append({"type": "error", "text": "<console capture failed>"})

    page.on("console", on_console)

    print("navigating to page...", URL)
    page.goto(URL)

    # click center of canvas to satisfy user gesture (autoplay/audio)
    print("clicking canvas center to satisfy user gesture")
    page.mouse.click(640, 360)
    time.sleep(0.6)

    # click near the expected Flappy button (right-side top area)
    # This may need small adjustments depending on scaling; picked a conservative spot.
    print("clicking flappy button area")
    page.mouse.click(1080, 60)

    # wait for some time for runtime to react and possibly log
    timeout = 12.0
    poll_interval = 0.35
    elapsed = 0.0

    last_text = page.evaluate("() => document.getElementById('terminal') ? document.getElementById('terminal').innerText : document.body.innerText")
    print("initial terminal length:", len(last_text or ""))

    polled = last_text
    while elapsed < timeout:
        time.sleep(poll_interval)
        elapsed += poll_interval
        try:
            polled = page.evaluate("() => document.getElementById('terminal') ? document.getElementById('terminal').innerText : document.body.innerText")
        except Exception as e:
            print("page evaluate failed (target closed?)", e)
            break
        if polled and polled != last_text:
            print("terminal changed (len now)", len(polled))
            break

    # give a moment for any late logs
    time.sleep(0.4)

    # save artifacts
    print("saving screenshot to", SCREENSHOT_OUT)
    page.screenshot(path=SCREENSHOT_OUT, full_page=True)

    print("writing terminal dump to", TERMINAL_OUT)
    with open(TERMINAL_OUT, "w", encoding="utf-8") as f:
        f.write(polled or "")

    print("writing console events to", CONSOLE_OUT)
    with open(CONSOLE_OUT, "w", encoding="utf-8") as f:
        json.dump(console_events, f, indent=2)

    print("done — leaving browser open for inspection")
    # keep the browser open for manual inspection
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("exiting")
        browser.close()
