"""
Mercado Livre Affiliate Link Generator Service
Generates affiliate links via Affiliate Central by intercepting the createLink API.
"""
import time
import json
import os
from playwright.sync_api import sync_playwright


class MLLinkGenerator:
    """Generate ML affiliate links via Affiliate Central API interception."""
    
    def __init__(self, cookie_file="ml_auth.json"):
        """Initialize the generator with authentication cookies."""
        self.cookies = []
        
        # Try to load cookies
        if not os.path.exists(cookie_file) and os.path.exists(os.path.join("src", cookie_file)):
            cookie_file = os.path.join("src", cookie_file)
            
        if os.path.exists(cookie_file):
            with open(cookie_file, "r") as f:
                self.cookies = json.load(f)
        else:
            print(f"⚠️ Warning: Cookie file {cookie_file} not found.")
    
    def generate_link(self, product_url: str) -> str:
        """
        Generate affiliate link for a product URL.
        
        Args:
            product_url: The original Mercado Livre product URL
            
        Returns:
            The generated affiliate link, or the original URL if generation fails
        """
        if not self.cookies:
            print("⚠️ No cookies found. Returning original URL.")
            return product_url
        
        print(f"🔗 Generating ML Affiliate Link for: {product_url[:60]}...")
        
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
                                print(f"✅ Generated: {captured_link}")
                except:
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
                context.add_cookies(self.cookies)
                context.set_default_timeout(30000)
                
                page = context.new_page()
                page.on("response", handle_response)
                
                # Navigate to Affiliate Central
                page.goto("https://www.mercadolivre.com.br/afiliados/hub", timeout=30000)
                page.wait_for_load_state('domcontentloaded', timeout=15000)
                time.sleep(3)
                
                # Make direct API call with the product URL and extract link
                print(f"   📡 Calling createLink API...")
                result = page.evaluate(f'''async () => {{
                    try {{
                        const response = await fetch('/affiliate-program/api/v2/affiliates/createLink', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                url: "{product_url}",
                                channel: "whatsapp"
                            }})
                        }});
                        const data = await response.json();
                        if (data && data.urls && data.urls.length > 0 && data.urls[0].short_url) {{
                            return data.urls[0].short_url;
                        }}
                        return null;
                    }} catch (e) {{
                        return null;
                    }}
                }}''')
                
                browser.close()
                
                if result and isinstance(result, str) and 'mercadolivre.com/sec/' in result:
                    print(f"✅ Generated: {result}")
                    return result
                else:
                    print("⚠️ Failed to generate link. Returning original URL.")
                    return product_url
                    
        except Exception as e:
            print(f"❌ Link generation error (timeout or failure): {str(e)[:100]}")
            return product_url


# Singleton instance
_generator = None

def get_ml_affiliate_link(product_url: str) -> str:
    """
    Get affiliate link for a Mercado Livre product.
    
    Args:
        product_url: Original ML product URL
        
    Returns:
        Affiliate link or original URL if generation fails
    """
    global _generator
    if _generator is None:
        _generator = MLLinkGenerator()
    return _generator.generate_link(product_url)
