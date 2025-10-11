from playwright.sync_api import sync_playwright
import json
import time

URL = "http://127.0.0.1:8000/index.html"
SCREENSHOT = "build/web/pygbag_flappy_dom.png"
CONSOLE_LOG = "build/web/pygbag_flappy_dom_console.json"
DOM_TEXT = "build/web/pygbag_flappy_dom.txt"


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

        # click roughly where the Flappy button is drawn
        page.mouse.click(824, 80)

        time.sleep(2.0)

        page.screenshot(path=SCREENSHOT)

        # capture document body text
        body_text = page.evaluate("() => document.body.innerText")
        with open(DOM_TEXT, "w") as f:
            f.write(body_text)

        with open(CONSOLE_LOG, "w") as f:
            json.dump(console_messages, f, indent=2)

        print("Saved screenshot, console log, and dom text")

        browser.close()

if __name__ == "__main__":
    main()
