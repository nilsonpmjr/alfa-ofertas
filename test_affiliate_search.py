#!/usr/bin/env python3
"""
Test script for ML Affiliate Link Generation via Product Search
This tests the approach of:
1. Navigate to Affiliate Central
2. Search for specific product
3. Click "Compartilhar" on that product
4. Extract affiliate link
"""
import time
import json
import os
from playwright.sync_api import sync_playwright


def test_search_based_affiliate_link(product_url: str):
    """
    Test generating affiliate link by searching for product first.
    
    Args:
        product_url: Full ML product URL like https://www.mercadolivre.com.br/...
    """
    # Extract product ID from URL (MLB1234567890)
    import re
    match = re.search(r'MLB-?(\d+)', product_url)
    if not match:
        print(f"❌ Could not extract product ID from: {product_url}")
        return None
    
    product_id = f"MLB{match.group(1)}"
    print(f"🔍 Product ID: {product_id}")
    print(f"📦 Product URL: {product_url}")
    
    # Load cookies
    cookie_file = "ml_auth.json"
    if not os.path.exists(cookie_file):
        cookie_file = os.path.join("src", cookie_file)
    
    if not os.path.exists(cookie_file):
        print(f"❌ Cookie file not found: {cookie_file}")
        return None
    
    with open(cookie_file, "r") as f:
        cookies = json.load(f)
    
    print(f"✅ Loaded {len(cookies)} cookies")
    
    captured_link = None
    
    def handle_response(response):
        """Intercept createLink API response"""
        nonlocal captured_link
        
        url = response.url
        
        if 'createLink' in url and response.status == 200:
            try:
                body = response.text()
                data = json.loads(body)
                
                if isinstance(data, dict) and 'urls' in data:
                    urls_data = data['urls']
                    if isinstance(urls_data, list) and len(urls_data) > 0:
                        first_item = urls_data[0]
                        if isinstance(first_item, dict) and 'short_url' in first_item:
                            captured_link = first_item['short_url']
                            print(f"✅ API Response captured: {captured_link}")
            except Exception as e:
                print(f"⚠️ Error parsing response: {e}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,  # Run visible for debugging
                args=["--use-gl=egl", "--enable-gpu"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            )
            context.add_cookies(cookies)
            
            page = context.new_page()
            page.on("response", handle_response)
            
            # Navigate to Affiliate Central
            print("\n📱 Navigating to Affiliate Central...")
            page.goto("https://www.mercadolivre.com.br/afiliados/hub#menu-lateral", timeout=60000)
            page.wait_for_load_state('domcontentloaded')
            time.sleep(8)  # Wait for SPA
            
            print("📸 Taking screenshot: affiliate_search_1_dashboard.png")
            page.screenshot(path="affiliate_search_1_dashboard.png")
            
            # Try to search for the product
            print(f"\n🔍 Searching for product {product_id}...")
            
            # Look for search input or filter
            search_result = page.evaluate(f'''() => {{
                // Try to find search/filter input
                const inputs = Array.from(document.querySelectorAll('input'));
                const searchInput = inputs.find(input => 
                    input.placeholder && (
                        input.placeholder.toLowerCase().includes('buscar') ||
                        input.placeholder.toLowerCase().includes('pesquisar') ||
                        input.placeholder.toLowerCase().includes('search')
                    )
                );
                
                if (searchInput) {{
                    searchInput.value = "{product_id}";
                    searchInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    searchInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return "Found search input";
                }}
                return "No search input found";
            }}''')
            
            print(f"   {search_result}")
            time.sleep(3)
            
            print("📸 Taking screenshot: affiliate_search_2_after_search.png")
            page.screenshot(path="affiliate_search_2_after_search.png")
            
            # Find "Compartilhar" buttons and click the right one
            print("\n🎯 Looking for 'Compartilhar' button for our product...")
            
            result = page.evaluate(f'''() => {{
                const buttons = Array.from(document.querySelectorAll('button'));
                const shareButtons = buttons.filter(btn => 
                    btn.textContent.includes('Compartilhar') && btn.offsetParent !== null
                );
                
                console.log(`Found ${{shareButtons.length}} Compartilhar buttons`);
                
                // Click the first visible one (should be our searched product)
                if (shareButtons.length > 0) {{
                    shareButtons[0].scrollIntoView({{ block: 'center' }});
                    setTimeout(() => shareButtons[0].click(), 500);
                    return shareButtons.length;
                }}
                return 0;
            }}''')
            
            print(f"   Found {result} 'Compartilhar' buttons")
            
            if result > 0:
                print("⏳ Waiting for modal...")
                time.sleep(5)
                
                print("📸 Taking screenshot: affiliate_search_3_modal.png")
                page.screenshot(path="affiliate_search_3_modal.png")
                
                # Click "Copiar link"
                print("\n🔗 Clicking 'Copiar link'...")
                page.evaluate('''() => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const copyBtn = buttons.find(btn => btn.textContent.includes('Copiar link'));
                    if (copyBtn) {
                        copyBtn.click();
                        return true;
                    }
                    return false;
                }''')
                
                time.sleep(3)
                
                print("📸 Taking screenshot: affiliate_search_4_final.png")
                page.screenshot(path="affiliate_search_4_final.png")
            
            print("\n⏸️ Pausing for 10 seconds to review browser state...")
            time.sleep(10)
            
            browser.close()
            
            if captured_link:
                print(f"\n✅ SUCCESS! Generated affiliate link: {captured_link}")
                return captured_link
            else:
                print("\n⚠️ No affiliate link captured")
                return None
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Test with a real product URL
    test_url = "https://produto.mercadolivre.com.br/MLB-1234567890-test-product"
    
    print("="*60)
    print("ML Affiliate Link Generator - Search-Based Approach Test")
    print("="*60)
    print("\nThis will:")
    print("1. Open Affiliate Central in visible browser")
    print("2. Search for the product")
    print("3. Click Compartilhar on that product")
    print("4. Extract the affiliate link")
    print("5. Take screenshots at each step")
    print("\n" + "="*60 + "\n")
    
    link = test_search_based_affiliate_link(test_url)
    
    print("\n" + "="*60)
    if link:
        print(f"✅ Test PASSED - Link: {link}")
    else:
        print("❌ Test FAILED - Check screenshots")
    print("="*60)
