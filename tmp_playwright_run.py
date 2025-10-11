from playwright.sync_api import sync_playwright
import json
import time

URL = "http://127.0.0.1:8000/index.html"
SCREENSHOT = "build/web/pygbag_headed_run.png"
CONSOLE_LOG = "build/web/pygbag_headed_console.json"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1024, "height": 768})
        page = context.new_page()

        console_messages = []

        def on_console(msg):
            try:
                loc = msg.location
            except Exception:
                loc = None
            console_messages.append({
                "type": msg.type,
                "text": msg.text,
                "location": loc
            })

        page.on("console", on_console)

        print(f"Navigating to {URL} ...")
        page.goto(URL, wait_until="networkidle", timeout=60000)

        # try to click center of the visible canvas
        try:
            box = page.eval_on_selector("canvas", "c => { const r=c.getBoundingClientRect(); return {x:r.left, y:r.top, w:r.width, h:r.height}; }")
            cx = box["x"] + box["w"] / 2
            cy = box["y"] + box["h"] / 2
            print(f"Clicking canvas at {cx},{cy}")
            page.mouse.click(cx, cy)
        except Exception as e:
            print("Could not click canvas:", e)

        # wait a little for game to run
        time.sleep(2)

        print("Taking screenshot...")
        page.screenshot(path=SCREENSHOT)

        print(f"Writing console log to {CONSOLE_LOG} ...")
        with open(CONSOLE_LOG, "w") as f:
            json.dump(console_messages, f, indent=2)

        print("Browser launched in headed mode. Inspect the page in the opened window.")
        print("When you're done, return to this terminal and press Enter to close the browser.")
        try:
            # Wait for user to press Enter so the browser stays open for interactive inspection
            input()
        except KeyboardInterrupt:
            # allow Ctrl-C to also close
            pass

        print("Closing browser...")
        browser.close()


if __name__ == "__main__":
    main()
