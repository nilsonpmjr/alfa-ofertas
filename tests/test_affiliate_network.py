import time
import json
import os
from playwright.sync_api import sync_playwright

def test_affiliate_central_with_interception():
    """
    Test affiliate link generation via Affiliate Central with network interception.
    Captures the affiliate link directly from API responses.
    """
    cookies = []
    cookie_file = "ml_auth.json"
    if not os.path.exists(cookie_file) and os.path.exists(os.path.join("src", "ml_auth.json")):
        cookie_file = os.path.join("src", "ml_auth.json")
        
    if os.path.exists(cookie_file):
        with open(cookie_file, "r") as f:
            cookies = json.load(f)
    else:
        print("⚠️ No cookies found. Script will likely fail.")
        return None

    captured_link = None
    
    def handle_response(response):
        """Intercept API responses to find the affiliate link"""
        nonlocal captured_link
        
        url = response.url
        
        # Specifically target the createLink API endpoint
        if 'createLink' in url or 'affiliate' in url.lower():
            try:
                if response.status == 200:
                    print(f"📡 Intercepted createLink API: {url[:80]}...")
                    body = response.text()
                    
                    # Parse JSON response
                    try:
                        data = json.loads(body)
                        print(f"📋 API Response structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                        
                        # Log the full response for debugging
                        print(f"📄 Full API Response: {json.dumps(data, indent=2)[:500]}...")
                        
                        # Check if 'urls' field exists
                        if isinstance(data, dict) and 'urls' in data:
                            urls_data = data['urls']
                            print(f"📌 Found 'urls' field type: {type(urls_data)}")
                            
                            # Extract the first affiliate link if urls is a list
                            if isinstance(urls_data, list) and len(urls_data) > 0:
                                first_url_item = urls_data[0]
                                if isinstance(first_url_item, dict):
                                    # Look for common link field names - short_url is the most likely
                                    for key in ['short_url', 'long_url', 'affiliate_link', 'url', 'link', 'shortUrl', 'deeplink', 'affiliateUrl']:
                                        if key in first_url_item:
                                            captured_link = first_url_item[key]
                                            print(f"🎉 CAPTURED AFFILIATE LINK from urls[0].{key}: {captured_link}")
                                            break
                                elif isinstance(first_url_item, str):
                                    captured_link = first_url_item
                                    print(f"🎉 CAPTURED AFFILIATE LINK from urls[0]: {captured_link}")
                            elif isinstance(urls_data, dict):
                                # If urls is a dict, try to extract any URL value
                                for key, value in urls_data.items():
                                    if isinstance(value, str) and 'mercadolivre.com' in value:
                                        captured_link = value
                                        print(f"🎉 CAPTURED AFFILIATE LINK from urls.{key}: {captured_link}")
                                        break
                        
                        # Fallback: generic extraction
                        if not captured_link:
                            link = extract_link_from_json(data)
                            if link and 'mercadolivre.com' in link and 'bookmarks' not in link:
                                captured_link = link
                                print(f"🎉 CAPTURED AFFILIATE LINK (fallback): {link}")
                    except json.JSONDecodeError:
                        # Try regex as fallback
                        import re
                        urls = re.findall(r'https?://[^\s<>"]+', body)
                        ml_urls = [u for u in urls if 'mercadolivre.com' in u and 'bookmarks' not in u and 'sec' not in u]
                        if ml_urls:
                            captured_link = ml_urls[0]
                            print(f"🎉 CAPTURED LINK (regex): {captured_link}")
            except Exception as e:
                print(f"⚠️ Error processing response: {e}")

    def extract_link_from_json(data, depth=0):
        """Recursively search for affiliate link in JSON data"""
        if depth > 5:  # Prevent infinite recursion
            return None
            
        if isinstance(data, dict):
            # Check common field names
            for key in ['link', 'url', 'affiliate_link', 'share_link', 'shortUrl', 'deeplink']:
                if key in data and isinstance(data[key], str) and 'mercadolivre.com' in data[key]:
                    return data[key]
            # Recursively search all values
            for value in data.values():
                result = extract_link_from_json(value, depth + 1)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = extract_link_from_json(item, depth + 1)
                if result:
                    return result
        return None

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--use-gl=egl", "--enable-gpu", "--ignore-gpu-blocklist"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        if cookies:
            context.add_cookies(cookies)
            
        page = context.new_page()
        
        # Set up network interception
        page.on("response", handle_response)
        
        url = "https://www.mercadolivre.com.br/afiliados/hub#menu-lateral"
        print(f"🌐 Navigating to {url}...")
        page.goto(url, timeout=60000)
        page.wait_for_load_state('domcontentloaded')
        
        print("⏳ Waiting 15 seconds for SPA to render...")
        time.sleep(15)
        
        print("🔍 Searching for 'Compartilhar' buttons...")
        
        # Use JavaScript to find and click the first visible button
        result = page.evaluate('''() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const shareButtons = buttons.filter(btn => {
                const text = btn.textContent || '';
                return text.includes('Compartilhar') && btn.offsetParent !== null;
            });
            
            if (shareButtons.length > 0) {
                const firstBtn = shareButtons[0];
                firstBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
                setTimeout(() => {
                    firstBtn.click();
                }, 500);
                return {
                    success: true,
                    buttonCount: shareButtons.length,
                    buttonText: firstBtn.textContent
                };
            }
            
            return { success: false, buttonCount: 0 };
        }''')
        
        if result['success']:
            print(f"✅ Found and clicked Compartilhar button (Total: {result['buttonCount']})")
            
            # Wait for modal and network requests
            print("⏳ Waiting for modal and network requests (5 seconds)...")
            time.sleep(5)
            
            # Click "Copiar link" to trigger the link generation
            print("🔍 Looking for 'Copiar link' button...")
            
            copy_result = page.evaluate('''() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const copyButton = buttons.find(btn => {
                    const text = btn.textContent || '';
                    return text.includes('Copiar link');
                });
                
                if (copyButton) {
                    copyButton.click();
                    return { success: true, buttonText: copyButton.textContent };
                }
                return { success: false };
            }''')
            
            if copy_result['success']:
                print(f"✅ Clicked 'Copiar link' via JavaScript")
                
                # Wait for any network requests triggered by the click
                print("⏳ Waiting for network requests (3 seconds)...")
                time.sleep(3)
                
                if captured_link:
                    print(f"\n{'='*60}")
                    print(f"🎉 SUCCESS! Captured Affiliate Link:")
                    print(f"{'='*60}")
                    print(f"{captured_link}")
                    print(f"{'='*60}\n")
                else:
                    print("⚠️ No affiliate link captured from network requests.")
                    print("   The link might be generated client-side or use a different mechanism.")
            else:
                print("❌ 'Copiar link' button not found.")
        else:
            print(f"❌ Failed to find/click Compartilhar button.")
        
        page.screenshot(path="network_interception_debug.png")
        browser.close()
        
        return captured_link

if __name__ == "__main__":
    link = test_affiliate_central_with_interception()
    if link:
        print(f"\n✅ Final Result: {link}")
    else:
        print("\n❌ No affiliate link was captured.")
