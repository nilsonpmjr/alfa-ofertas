"""
Mercado Livre Affiliate Link Generator Service
Generates affiliate links via Affiliate Central Link Builder (UI Automation).
"""
import time
import json
import os
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


class MLLinkGenerator:
    """Generate ML affiliate links via robust UI automation using Link Builder."""
    
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
    
    def generate_link(self, product_url: str, product_title: str = None) -> str:
        """
        Generate affiliate link for a product URL using Link Builder.
        
        Args:
            product_url: The original Mercado Livre product URL
            product_title: Optional title (unused in Link Builder but kept for interface)
            
        Returns:
            The generated affiliate link, or None if generation fails.
        """
        if not self.cookies:
            print("⚠️ No cookies found. Cannot generate affiliate link.")
            return None
        
        print(f"🔗 Generating ML Affiliate Link via Link Builder for: {product_url[:40]}...")
        
        captured_link = None
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        "--use-gl=egl", 
                        "--enable-gpu"
                    ],
                    timeout=60000
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080},
                    locale='pt-BR',
                    timezone_id='America/Sao_Paulo',
                    permissions=['geolocation'],
                    geolocation={'latitude': -23.5505, 'longitude': -46.6333},
                )
                context.add_cookies(self.cookies)
                context.set_default_timeout(60000)
                
                page = context.new_page()
                
                # Inject anti-detection scripts
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['pt-BR', 'pt', 'en-US', 'en']
                    });
                    
                    window.chrome = {
                        runtime: {}
                    };
                """)
                
                # Navigate to Link Builder
                print("   📱 Navigating to Link Builder...")
                page.goto("https://www.mercadolivre.com.br/afiliados/linkbuilder#hub", timeout=60000)
                page.wait_for_load_state('domcontentloaded')
                time.sleep(5)
                
                # Paste URL into textarea#url-0
                print("   📝 Typing URL...")
                try:
                    page.click('textarea#url-0')
                    page.fill('textarea#url-0', '') # Clear
                    page.type('textarea#url-0', product_url, delay=10) # Type fast but real
                    page.press('textarea#url-0', 'Enter')
                except Exception as e:
                    print(f"   ⚠️ Error typing URL: {e}")
                    # Fallback: try setting value directly
                    page.evaluate(f'''() => {{
                        const ta = document.querySelector('textarea#url-0');
                        if (ta) {{
                            ta.value = "{product_url}";
                            ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            ta.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                    }}''')
                
                time.sleep(2)
                
                # Ensure input events trigger validation
                page.evaluate('''() => {
                    const textarea = document.querySelector('textarea#url-0');
                    if (textarea) {
                        textarea.dispatchEvent(new Event('input', { bubbles: true }));
                        textarea.dispatchEvent(new Event('change', { bubbles: true }));
                        textarea.dispatchEvent(new Event('blur', { bubbles: true }));
                    }
                }''')
                
                # Click "Gerar" button
                print("   🔘 Clicking 'Gerar'...")
                button_clicked = False
                for _ in range(5):
                    try:
                        # Check if enabled
                        is_disabled = page.evaluate('''() => {
                            const btn = Array.from(document.querySelectorAll('button.button_generate-links')).find(b => b.textContent.trim() === 'Gerar');
                            return btn ? btn.disabled : true;
                        }''')
                        
                        if not is_disabled:
                            page.evaluate('''() => {
                                const btn = Array.from(document.querySelectorAll('button.button_generate-links')).find(b => b.textContent.trim() === 'Gerar');
                                if (btn) btn.click();
                            }''')
                            button_clicked = True
                            break
                        else:
                            time.sleep(1)
                    except:
                        time.sleep(1)
                
                if not button_clicked:
                    print("   ⚠️ 'Gerar' button not enabled or found.")
                    # Try clicking anyway if found
                    page.evaluate('''() => {
                        const btn = Array.from(document.querySelectorAll('button.button_generate-links')).find(b => b.textContent.trim() === 'Gerar');
                        if (btn) btn.click();
                    }''')
                
                time.sleep(5) # Wait for generation
                
                # Extract link
                print("   🔍 Extracting link...")
                captured_link = page.evaluate('''() => {
                    // 1. Check inputs/textareas
                    const inputs = Array.from(document.querySelectorAll('input, textarea'));
                    const linkInput = inputs.find(i => i.value && i.value.includes('mercadolivre.com/sec/'));
                    if (linkInput) return linkInput.value;
                    
                    // 2. Check text content
                    const allElements = Array.from(document.querySelectorAll('div, span, p'));
                    const linkEl = allElements.find(el => el.textContent && el.textContent.includes('https://mercadolivre.com/sec/'));
                    if (linkEl) {
                        const match = linkEl.textContent.match(/(https?:\/\/mercadolivre\.com\/sec\/[^\s]+)/);
                        if (match) return match[1];
                    }
                    return null;
                }''')
                
                if not captured_link:
                    # Fallback: Click "Link completo"
                    print("   🔄 Clicking 'Link completo' fallback...")
                    page.evaluate('''() => {
                        const labels = Array.from(document.querySelectorAll('label'));
                        const linkCompleto = labels.find(l => l.textContent.includes('Link completo'));
                        if (linkCompleto) linkCompleto.click();
                    }''')
                    time.sleep(2)
                    
                    captured_link = page.evaluate('''() => {
                        const inputs = Array.from(document.querySelectorAll('input, textarea'));
                        const linkInput = inputs.find(i => i.value && i.value.includes('mercadolivre.com/sec/'));
                        return linkInput ? linkInput.value : null;
                    }''')
                
                browser.close()
                
                if captured_link:
                    # Clean up link (sometimes it has extra text)
                    match = re.search(r'(https?://mercadolivre\.com/sec/[^\s]+)', captured_link)
                    if match:
                        captured_link = match.group(1)
                    
                    print(f"   ✅ Generated: {captured_link}")
                    return captured_link
                else:
                    print("   ❌ Failed to capture link.")
                    return None
                    
        except Exception as e:
            print(f"   ❌ Error generating affiliate link: {str(e)[:100]}")
            return None


# Singleton instance
_generator = None

def get_ml_affiliate_link(product_url: str, product_title: str = None) -> str:
    """
    Get affiliate link for a Mercado Livre product.
    
    Args:
        product_url: Original ML product URL
        product_title: Optional title
        
    Returns:
        Affiliate link or None if generation fails
    """
    global _generator
    if _generator is None:
        _generator = MLLinkGenerator()
    return _generator.generate_link(product_url, product_title)
