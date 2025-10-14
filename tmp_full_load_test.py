#!/usr/bin/env python3
"""
Extended headless test that waits for pygame to fully load and game to initialize.
"""
from playwright.sync_api import sync_playwright
import time
import json

URL = "http://127.0.0.1:8000/#debug"
OUT_DIR = "build/web"
TERMINAL_OUT = f"{OUT_DIR}/pygbag_full_load_terminal.txt"
CONSOLE_OUT = f"{OUT_DIR}/pygbag_full_load_console.json"
SCREENSHOT_OUT = f"{OUT_DIR}/pygbag_full_load_screenshot.png"

console_events = []

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

    print("Navigating to page...", URL)
    page.goto(URL, wait_until="load")
    time.sleep(2)

    # Click to satisfy user gesture
    print("Clicking canvas center for user gesture...")
    try:
        page.mouse.click(640, 360)
        time.sleep(0.5)
    except Exception as e:
        print(f"Initial click failed: {e}")

    # Wait longer for pygame and game to load
    print("Waiting for game to fully load (60 seconds)...")
    def get_terminal_text():
        try:
            return page.evaluate("() => (document.getElementById('terminal') ? document.getElementById('terminal').innerText : '')")
        except Exception:
            return ""

    last_len = 0
    stable_count = 0
    for i in range(120):  # 60 seconds max (0.5s intervals)
        time.sleep(0.5)
        current_text = get_terminal_text()
        current_len = len(current_text)
        
        if current_len != last_len:
            print(f"  [{i*0.5:.1f}s] Terminal length: {current_len}")
            last_len = current_len
            stable_count = 0
        else:
            stable_count += 1
            # If terminal hasn't changed for 5 seconds, assume loaded
            if stable_count >= 10 and current_len > 100:
                print(f"  Terminal stable at {current_len} chars, assuming loaded")
                break

    # Get final state
    time.sleep(1)
    final_terminal = get_terminal_text()
    
    print(f"\nFinal terminal length: {len(final_terminal)}")
    print("\nSaving artifacts...")
    
    try:
        page.screenshot(path=SCREENSHOT_OUT, full_page=True)
        print(f"  Screenshot: {SCREENSHOT_OUT}")
    except Exception as e:
        print(f"  Screenshot failed: {e}")

    with open(TERMINAL_OUT, "w", encoding="utf-8") as f:
        f.write(final_terminal)
    print(f"  Terminal: {TERMINAL_OUT}")

    with open(CONSOLE_OUT, "w", encoding="utf-8") as f:
        json.dump(console_events, f, indent=2)
    print(f"  Console: {CONSOLE_OUT}")

    print("\nLast 20 lines of terminal:")
    lines = final_terminal.split('\n')
    for line in lines[-20:]:
        print(f"  {line}")

    browser.close()
    print("\nDone!")
