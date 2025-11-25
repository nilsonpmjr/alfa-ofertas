from playwright.sync_api import sync_playwright
import time

def debug_ml_offers():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        url = "https://www.mercadolivre.com.br/ofertas?container_id=MLB779362-1&promotion_type=lightning#filter_applied=promotion_type&filter_position=2&is_recommended_domain=false&origin=scut"
        print(f"Navigating to {url}...")
        page.goto(url, timeout=60000)
        page.wait_for_load_state('domcontentloaded')
        time.sleep(5) # Wait for dynamic content
        
        print(f"Title: {page.title()}")
        page.screenshot(path="ml_offers_debug.png")
        
        # Dump HTML to file for inspection
        with open("ml_dump.html", "w", encoding="utf-8") as f:
            f.write(page.content())
            
        print("Saved HTML to ml_dump.html")
            
        browser.close()

if __name__ == "__main__":
    debug_ml_offers()
