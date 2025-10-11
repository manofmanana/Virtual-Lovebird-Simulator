from playwright.sync_api import sync_playwright
import json
import time

URL = "http://127.0.0.1:8000/index.html"
OUT_TEXT = "build/web/pygbag_terminal_innerText.txt"
OUT_HTML = "build/web/pygbag_terminal_innerHTML.txt"
CONSOLE_LOG = "build/web/pygbag_terminal_console.json"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(viewport={"width":1024, "height":768})
    page = ctx.new_page()
    console_messages = []
    page.on('console', lambda msg: console_messages.append((msg.type, msg.text)))
    page.goto(URL, wait_until='networkidle', timeout=60000)
    # click flappy button region
    page.mouse.click(824,80)
    time.sleep(1.5)
    term_text = page.evaluate("() => (document.getElementById('terminal') ? document.getElementById('terminal').innerText : '')")
    term_html = page.evaluate("() => (document.getElementById('terminal') ? document.getElementById('terminal').innerHTML : '')")
    with open(OUT_TEXT, 'w') as f:
        f.write(term_text)
    with open(OUT_HTML, 'w') as f:
        f.write(term_html)
    with open(CONSOLE_LOG, 'w') as f:
        json.dump(console_messages, f, indent=2)
    print('Saved terminal text/html and console log')
    browser.close()
