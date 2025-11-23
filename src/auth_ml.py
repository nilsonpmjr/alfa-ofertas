#!/usr/bin/env python3
"""
Mercado Livre Authentication Script
Opens a browser for manual login and saves session cookies for affiliate link generation.
"""
from playwright.sync_api import sync_playwright
import json
import os

COOKIES_FILE = os.path.join(os.path.dirname(__file__), '..', 'ml_auth.json')
ML_AFFILIATE_URL = "https://afiliados.mercadolivre.com.br/"

def capture_ml_session():
    """Opens browser for ML login and saves cookies."""
    print("🔐 Mercado Livre Authentication Script")
    print("=" * 50)
    print("\nThis script will:")
    print("1. Open a Chrome window")
    print("2. Navigate to ML Affiliate Portal")
    print("3. Wait for you to log in")
    print("4. Save your session cookies\n")
    
    input("Press ENTER to start...")
    
    with sync_playwright() as p:
        # Launch browser in NON-headless mode so user can see
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        page = context.new_page()
        
        # Navigate to ML affiliate portal
        print(f"\n📱 Opening {ML_AFFILIATE_URL}")
        page.goto(ML_AFFILIATE_URL, timeout=60000)
        
        print("\n⏳ Please LOG IN to your Mercado Livre Affiliate account in the browser window.")
        print("   Once you're logged in and see your dashboard, come back here.\n")
        
        input("Press ENTER once you've successfully logged in...")
        
        # Get cookies
        cookies = context.cookies()
        
        # Save to file
        with open(COOKIES_FILE, 'w') as f:
            json.dump(cookies, f, indent=2)
        
        print(f"\n✅ Session saved to: {COOKIES_FILE}")
        print("   The bot can now generate affiliate links automatically!\n")
        
        browser.close()

if __name__ == "__main__":
    try:
        capture_ml_session()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user.")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
