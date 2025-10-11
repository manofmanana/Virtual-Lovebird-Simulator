from playwright.sync_api import sync_playwright
import json, time
URL = 'http://127.0.0.1:8000/index.html'
OUT = 'build/web/pygbag_multi_clicks_console.json'
TERMPATH = 'build/web/pygbag_multi_clicks_terminal.txt'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(viewport={'width':1024,'height':768})
    page = ctx.new_page()
    console_messages = []
    page.on('console', lambda msg: console_messages.append((msg.type, msg.text)))
    page.goto(URL, wait_until='networkidle', timeout=60000)
    clicks = [
        ('flappy', 824, 80),
        ('feed', 212, 260),
        ('tickle', 880, 320),
    ]
    for name,x,y in clicks:
        page.mouse.click(x,y)
        time.sleep(1.2)
        # capture terminal innerText snapshot after each
        txt = page.evaluate("() => (document.getElementById('terminal') ? document.getElementById('terminal').innerText : '')")
        with open(f'build/web/pygbag_multi_{name}_terminal.txt', 'w') as f:
            f.write(txt)
    with open(OUT, 'w') as f:
        json.dump(console_messages, f, indent=2)
    with open(TERMPATH, 'w') as f:
        f.write('\n--- Combined Terminal ---\n')
        for name,x,y in clicks:
            try:
                with open(f'build/web/pygbag_multi_{name}_terminal.txt','r') as t:
                    f.write(f'\n== {name} ==\n')
                    f.write(t.read())
            except Exception:
                pass
    print('Saved console and terminal snapshots')
    browser.close()
