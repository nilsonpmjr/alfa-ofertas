"""
ML Affiliate Link Generator - Recommendations Approach
Uses the "Produtos selecionados para você" section in Affiliate Central
"""
import json
import time
import os
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


def get_ml_affiliate_link(product_url: str, timeout: int = 30) -> str:
    """
    Generate ML affiliate link by searching in Affiliate Central recommendations.
    
    Args:
        product_url: Full ML product URL
        timeout: Max seconds to wait for link generation
        
    Returns:
        Affiliate link or None if generation fails
    """
    # Extract product ID from URL
    product_id = extract_product_id(product_url)
    if not product_id:
        print(f"   ⚠️ Could not extract product ID from {product_url}")
        return None
    
    # Load authentication cookies
    cookie_file = "ml_auth.json"
    if not os.path.exists(cookie_file):
        cookie_file = os.path.join("src", cookie_file)
    
    if not os.path.exists(cookie_file):
        print(f"   ⚠️ ML auth cookies not found: {cookie_file}")
        return None
    
    with open(cookie_file, "r") as f:
        cookies = json.load(f)
    
    captured_link = None
    
    def handle_response(response):
        """Intercept createLink API response to capture affiliate link"""
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
            except Exception as e:
                pass
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--use-gl=egl", "--enable-gpu"],
                timeout=30000
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            )
            context.add_cookies(cookies)
            
            page = context.new_page()
            page.on("response", handle_response)
            
            # Navigate to Affiliate Central Hub
            page.goto("https://www.mercadolivre.com.br/afiliados/hub#menu-lateral", timeout=60000)
            page.wait_for_load_state('domcontentloaded')
            time.sleep(5)
            
            # Look for the product in recommendations section
            print(f"   🔍 Searching for product {product_id} in recommendations...")
            
            # Search for product card containing this product ID
            found_and_clicked = page.evaluate(f'''() => {{
                // Find the recommendations container
                const container = document.querySelector('div#recommendations_card');
                if (!container) return "recommendations_card not found";
                
                // Find all product cards
                const cards = container.querySelectorAll('div.poly-card');
                
                // Search for card with matching product ID in href
                for (const card of cards) {{
                    const link = card.querySelector('a.poly-component__title');
                    if (link && link.href && link.href.includes('{product_id}')) {{
                        // Found the matching product card!
                        // Now click the "Compartilhar" button
                        const compartilharBtn = card.querySelector('button');
                        if (compartilharBtn && compartilharBtn.textContent.includes('Compartilhar')) {{
                            compartilharBtn.scrollIntoView({{ block: 'center' }});
                            compartilharBtn.click();
                            return "clicked_compartilhar";
                        }}
                        return "button_not_found";
                    }}
                }}
                
                return "product_not_found";
            }}''')
            
            if found_and_clicked == "clicked_compartilhar":
                print(f"   ✅ Found product and clicked Compartilhar")
                
                # Wait for modal/popup and click "Copiar link"
                time.sleep(3)
                
                copy_result = page.evaluate('''() => {
                    // Look for "Copiar" or "Copiar link" button
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const copyBtn = buttons.find(btn => 
                        btn.textContent.toLowerCase().includes('copiar')
                    );
                    
                    if (copyBtn) {
                        copyBtn.click();
                        return "clicked_copiar";
                    }
                    return "copiar_not_found";
                }''')
                
                print(f"   {copy_result}")
                time.sleep(5)
                
            else:
                print(f"   ⚠️ {found_and_clicked}")
            
            browser.close()
            
            if captured_link:
                print(f"   ✅ Generated: {captured_link}")
                return captured_link
            else:
                print(f"   ⚠️ No affiliate link captured for {product_id}")
                return None
                
    except Exception as e:
        print(f"   ❌ Error generating affiliate link: {e}")
        return None


def extract_product_id(url: str) -> str:
    """Extract MLB product ID from URL"""
    match = re.search(r'(MLB-?\d+)', url)
    if match:
        return match.group(1).replace('-', '')
    return None
