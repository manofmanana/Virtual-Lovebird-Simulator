from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    messages = []
    errors = []

    def on_console(msg):
        messages.append((msg.type, msg.text))
        print(f"CONSOLE {msg.type}: {msg.text}")

    def on_error(err):
        errors.append(str(err))
        print('PAGEERROR:', err)

    page.on('console', on_console)
    page.on('pageerror', on_error)

    url = 'http://127.0.0.1:8000/#debug'
    print('Opening', url)
    page.goto(url, wait_until='networkidle')
    time.sleep(3)
    page.screenshot(path='playwright_debug_screenshot.png')
    print('Saved screenshot to playwright_debug_screenshot.png')

    browser.close()
