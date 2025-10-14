#!/usr/bin/env python3
"""Test pygbag game WITHOUT debug mode to avoid local repo redirect."""
from playwright.sync_api import sync_playwright
import time
import json

URL = "http://127.0.0.1:8000/"  # NO #debug flag!
OUT_DIR = "build/web"

console_events = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width":1280, "height":720})
    page = context.new_page()

    def on_console(msg):
        try:
            console_events.append({"type": msg.type, "text": msg.text})
        except Exception:
            pass

    page.on("console", on_console)

    print(f"Loading game at {URL} (without debug mode)...")
    page.goto(URL, wait_until="load")
    time.sleep(3)

    print("Clicking for user gesture...")
    page.mouse.click(640, 360)
    time.sleep(1)

    print("Waiting for game to load (up to 90 seconds)...")
    
    def get_terminal():
        try:
            return page.evaluate("() => document.getElementById('terminal') ? document.getElementById('terminal').innerText : ''")
        except:
            return ""

    last_len = 0
    for i in range(180):  # 90 seconds
        time.sleep(0.5)
        term = get_terminal()
        term_len = len(term)
        
        if term_len != last_len:
            print(f"  [{i*0.5:.1f}s] Terminal: {term_len} chars")
            last_len = term_len
            
            # Check for success indicators
            if "Starting Mango" in term or "MangoTamagotchi" in term:
                print("  ✅ GAME STARTED!")
                break
            
            # Check for errors
            if "Traceback" in term or "ModuleNotFoundError" in term:
                print("  ❌ ERROR DETECTED!")
                break
                
    time.sleep(2)
    final_term = get_terminal()
    
    # Save artifacts
    page.screenshot(path=f"{OUT_DIR}/test_no_debug_screenshot.png", full_page=True)
    
    with open(f"{OUT_DIR}/test_no_debug_terminal.txt", "w") as f:
        f.write(final_term)
    
    with open(f"{OUT_DIR}/test_no_debug_console.json", "w") as f:
        json.dump(console_events, f, indent=2)
    
    print(f"\n{'='*60}")
    print("FINAL TERMINAL OUTPUT:")
    print(f"{'='*60}")
    print(final_term[-2000:] if len(final_term) > 2000 else final_term)
    print(f"{'='*60}")
    
    # Check for errors
    has_traceback = "Traceback" in final_term
    has_module_error = "ModuleNotFoundError" in final_term
    has_game_start = "Starting Mango" in final_term or "pygbag launcher" in final_term
    
    print(f"\nRESULTS:")
    print(f"  Terminal length: {len(final_term)} chars")
    print(f"  Has errors: {'❌ YES' if has_traceback or has_module_error else '✅ NO'}")
    print(f"  Game started: {'✅ YES' if has_game_start else '❌ NO'}")
    
    browser.close()
