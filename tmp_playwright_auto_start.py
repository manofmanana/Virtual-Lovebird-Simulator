from playwright.sync_api import sync_playwright
import time, json

OUT_SCREEN = 'build/web/auto_start_screenshot.png'
OUT_CONS = 'build/web/auto_start_console.json'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    console_msgs = []
    page.on('console', lambda msg: console_msgs.append({'type': msg.type, 'text': msg.text}))
    page.on('pageerror', lambda err: console_msgs.append({'type': 'pageerror', 'text': str(err)}))

    url = 'http://127.0.0.1:8000/#debug'
    print('Navigating to', url)
    page.goto(url, wait_until='networkidle')

    # Wait for overlay button then click it
    try:
        page.wait_for_selector('#start_overlay_btn', timeout=5000)
        page.click('#start_overlay_btn')
        print('Clicked start overlay')
    except Exception as e:
        print('No overlay button found or click failed:', e)

    # Give the app some time to initialize
    time.sleep(4)

    # Save screenshot and console log
    page.screenshot(path=OUT_SCREEN)
    with open(OUT_CONS, 'w', encoding='utf-8') as f:
        json.dump(console_msgs, f, indent=2)

    print('Saved', OUT_SCREEN, 'and', OUT_CONS)
    browser.close()
