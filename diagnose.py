#!/usr/bin/env python3
"""
Open the game and capture ACTUAL terminal output from the browser.
This will show us what Python is actually doing (or not doing).
"""
from playwright.sync_api import sync_playwright
import time
import json

URL = "http://127.0.0.1:8000/"  # NO DEBUG!

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Watch it load!
    context = browser.new_context(viewport={"width":1280, "height":720})
    page = context.new_page()
    
    console_msgs = []
    def log_console(msg):
        console_msgs.append(f"[{msg.type}] {msg.text}")
    page.on("console", log_console)
    
    print("Loading game at", URL)
    page.goto(URL)
    
    print("Waiting 15 seconds for Python to load...")
    for i in range(30):
        time.sleep(0.5)
        try:
            # Get terminal content
            term = page.evaluate("() => document.getElementById('terminal') ? document.getElementById('terminal').innerText : ''")
            if term and len(term) > 100:
                print(f"  [{i*0.5:.1f}s] Terminal has {len(term)} chars")
                if "pygame" in term.lower() or "mango" in term.lower():
                    print(f"  ✅ Found pygame/mango in terminal!")
                    break
        except:
            pass
    
    time.sleep(2)
    
    # Get final terminal
    terminal = page.evaluate("() => document.getElementById('terminal') ? document.getElementById('terminal').innerText : 'NO TERMINAL FOUND'")
    
    print("\n" + "="*80)
    print("TERMINAL OUTPUT:")
    print("="*80)
    print(terminal)
    print("="*80)
    
    print("\n" + "="*80)
    print("CONSOLE MESSAGES (last 30):")
    print("="*80)
    for msg in console_msgs[-30:]:
        print(msg)
    print("="*80)
    
    # Check what's visible
    try:
        canvas = page.locator("canvas").first
        if canvas:
            print("\n✅ Canvas element exists")
    except:
        print("\n❌ No canvas found")
    
    print("\nKeeping browser open for 10 seconds so you can inspect...")
    time.sleep(10)
    
    browser.close()
    
    print("\n" + "="*80)
    print("DIAGNOSIS:")
    print("="*80)
    
    if "ModuleNotFoundError" in terminal:
        print("❌ Python module import failed")
    elif "Traceback" in terminal:
        print("❌ Python error occurred")
    elif "Starting Mango" in terminal or "pygbag launcher" in terminal:
        print("✅ Game started successfully!")
    elif len(terminal) < 100:
        print("❌ Python never started - loader issue")
    else:
        print("⚠️  Python loaded but may have failed silently")
