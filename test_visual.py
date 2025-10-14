#!/usr/bin/env python3
"""
Simple test that opens the game in a regular (headed) browser.
This bypasses headless network issues and lets you actually SEE the game.
"""
from playwright.sync_api import sync_playwright
import time

URL = "http://127.0.0.1:8000/"

print(f"Opening {URL} in a real browser window...")
print("This will stay open for 30 seconds so you can see if the game loads.")
print("Look for:")
print("  - Should NOT be a blank teal screen")
print("  - Should see Mango the bird")
print("  - Should see UI buttons")
print("\nOpening browser...")

with sync_playwright() as p:
    # Launch with headed=False to see the actual browser
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width":1280, "height":720})
    page = context.new_page()
    
    page.goto(URL)
    print("✅ Page loaded")
    print("   Waiting 30 seconds... (watch the browser window!)")
    
    time.sleep(5)
    print("   [5s] Clicking canvas...")
    page.mouse.click(640, 360)
    
    time.sleep(25)
    
    print("\n" + "="*60)
    print("DONE - Closing browser")
    print("="*60)
    print("\nDid you see:")
    print("  [ ] Mango the lovebird?")
    print("  [ ] UI buttons (Feed, Play, Clean, etc)?")
    print("  [ ] Colorful background?")
    print("\nIf you saw a blank teal screen, there's still a loading issue.")
    
    browser.close()
