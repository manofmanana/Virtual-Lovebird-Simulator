from playwright.sync_api import sync_playwright
import json
import time

URL = "http://127.0.0.1:8000/index.html"
SCREENSHOT = "build/web/pygbag_flappy_click.png"
CONSOLE_LOG = "build/web/pygbag_flappy_console.json"


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

        page.goto(URL, wait_until="networkidle", timeout=60000)

        # click roughly where the Flappy button is drawn in hub_ui.py (screen_w - 200, y=20)
        # our page viewport is 1024x768; click at x=824,y=80
        page.mouse.click(824, 80)

        # wait a short while for crash to reproduce
        time.sleep(1.5)

        page.screenshot(path=SCREENSHOT)

        with open(CONSOLE_LOG, "w") as f:
            json.dump(console_messages, f, indent=2)

        print("Saved screenshot and console log")

        browser.close()

if __name__ == "__main__":
    main()
