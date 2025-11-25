import time
import json
import os
from playwright.sync_api import sync_playwright

def test_affiliate_central_share():
    cookies = []
    cookie_file = "ml_auth.json"
    if not os.path.exists(cookie_file) and os.path.exists(os.path.join("src", "ml_auth.json")):
        cookie_file = os.path.join("src", "ml_auth.json")
        
    if os.path.exists(cookie_file):
        with open(cookie_file, "r") as f:
            cookies = json.load(f)
    else:
        print("⚠️ No cookies found. Script will likely fail.")

    with sync_playwright() as p:
        # Enable GPU and use force click
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
        
        url = "https://www.mercadolivre.com.br/afiliados/hub#menu-lateral"
        print(f"Navigating to {url}...")
        page.goto(url, timeout=60000)
        page.wait_for_load_state('domcontentloaded')
        
        # Fixed wait for SPA rendering
        print("Waiting 15 seconds for SPA to render...")
        time.sleep(15)
        
        # Find ALL Compartilhar buttons and use JavaScript directly
        print("Searching for 'Compartilhar' buttons...")
        
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
                // Wait a tiny bit for scroll
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
            print(f"✅ Found and clicked Compartilhar button via JavaScript (Total: {result['buttonCount']})")
            print(f"   Button text: {result['buttonText']}")
            
            # Wait for modal to open
            print("Waiting for modal... (5 seconds)")
            time.sleep(5)
            
            # Dump modal content
            with open("share_modal.html", "w") as f:
                f.write(page.content())
                
            # Check for link input value (DOM property)
            link_input = page.query_selector('input.andes-form-control__field')
            if link_input:
                val = link_input.input_value()
                print(f"✅ Found Link Input Value: '{val}'")
            else:
                print("⚠️ Link input selector not found.")

            # Look for "Copiar link" - use pure JavaScript to click
            print("Looking for 'Copiar link' button...")
            
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
                print(f"✅ Clicked 'Copiar link' via JavaScript: {copy_result['buttonText']}")
                time.sleep(2)  # Wait for link to populate
                
                # Check if input was populated
                if link_input:
                    val = link_input.input_value()
                    print(f"Input value after JS click: '{val}'")
                    
                    if val and "mercadolivre" in val.lower():
                        print(f"🎉 SUCCESS! Captured Affiliate Link: {val}")
                    elif not val:
                        # Try reading clipboard via paste
                        print("Input empty. Attempting clipboard paste...")
                        try:
                            link_input.click()
                            link_input.fill("")
                            page.keyboard.press("Control+V")
                            time.sleep(0.5)
                            val = link_input.input_value()
                            print(f"Input value after paste: '{val}'")
                            
                            if val and "mercadolivre" in val.lower():
                                print(f"🎉 SUCCESS via Paste! Affiliate Link: {val}")
                            else:
                                print(f"⚠️ Paste result: '{val}'")
                        except Exception as e:
                            print(f"Paste failed: {e}")
                    else:
                        print(f"⚠️ Input has unexpected value: {val}")
            else:
                print("❌ 'Copiar link' button not found via JavaScript.")
                
        else:
            print(f"❌ Failed to find/click Compartilhar button. Result: {result}")
        
        page.screenshot(path="final_state_debug.png")
        browser.close()

if __name__ == "__main__":
    test_affiliate_central_share()
