from playwright.sync_api import sync_playwright
from typing import List, Dict
import time
import random
import re
from src.config import Config

class PlaywrightScraper:
    def scrape_ml_offers(self) -> List[Dict]:
        deals = []
        url = "https://www.mercadolivre.com.br/ofertas?container_id=MLB779362-1&promotion_type=lightning#filter_applied=promotion_type&filter_position=2&is_recommended_domain=false&origin=scut"
        
        with sync_playwright() as p:
            print("   🕷️ Launching browser for scraping...")
            browser = p.chromium.launch(
                headless=True,
                args=["--use-gl=egl", "--enable-gpu"],
                timeout=30000
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720}
            )
            page = context.new_page()
            
            try:
                print(f"   🕷️ Navigating to: {url[:50]}...")
                page.goto(url, timeout=60000)
                print("   🕷️ Page loaded, waiting for DOM...")
                page.wait_for_load_state('domcontentloaded')
                
                # Scroll to load items
                for _ in range(3):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                
                # Use 'andes-card' as the main container for offers
                items = page.query_selector_all('div.andes-card')
                print(f"Found {len(items)} potential offers on ML")

                for item in items:
                    try:
                        # Selectors for "Ofertas" page (Poly components)
                        title_el = item.query_selector('a.poly-component__title')
                        price_el = item.query_selector('div.poly-price__current span.andes-money-amount__fraction')
                        link_el = item.query_selector('a.poly-component__title')
                        
                        if not title_el or not price_el:
                            continue
                            
                        title = title_el.inner_text().strip()
                        link = link_el.get_attribute('href')
                        price = float(price_el.inner_text().replace('.', '').replace(',', '.'))
                        
                        # Discount
                        discount = 0
                        original_price = price
                        
                        discount_el = item.query_selector('span.poly-price__disc_label')
                        if discount_el:
                            d_text = discount_el.inner_text().replace('% OFF', '').strip()
                            try:
                                discount = int(d_text)
                                original_price = price / (1 - discount/100)
                            except:
                                pass
                        
                        # Image
                        image = ""
                        img_el = item.query_selector('img.poly-component__picture')
                        if img_el:
                            image = img_el.get_attribute('data-src') or img_el.get_attribute('src')

                        # Rating (Quality Check)
                        rating = 0.0
                        rating_el = item.query_selector('span.poly-reviews__rating')
                        if rating_el:
                            try:
                                rating = float(rating_el.inner_text().strip())
                            except:
                                pass
                        
                        if rating > 0 and rating < Config.MIN_RATING:
                            # print(f"Skipping {title[:20]}... (Rating {rating} < {Config.MIN_RATING})")
                            continue

                        # Seller Reputation (Basic Check)
                        # We prefer "Loja oficial" or "MercadoLíder"
                        seller = ""
                        seller_el = item.query_selector('span.poly-component__seller')
                        if seller_el:
                            seller = seller_el.inner_text().strip()
                        
                        # If it's a new seller (no rating, no seller info), be cautious.
                        # But for now, we rely on the rating filter. 
                        # If rating is 0 (no reviews), we might want to skip if strict.
                        # User said "Filter out new sellers". 0 rating usually means new.
                        if rating == 0:
                             # print(f"Skipping {title[:20]}... (No rating/New seller)")
                             continue

                        # Extract ID robustly
                        # Link format: .../p/MLB12345 or .../MLB-12345...
                        item_id = link
                        mlb_match = re.search(r'(MLB-?\d+)', link)
                        if mlb_match:
                            item_id = mlb_match.group(1).replace('-', '') # Normalize to MLB12345
                        
                        if discount >= Config.MIN_DISCOUNT:
                            deals.append({
                                "source": "Mercado Livre",
                                "id": item_id,
                                "title": title,
                                "price": price,
                                "original_price": round(original_price, 2),
                                "discount": discount,
                                "rating": rating,
                                "seller": seller,
                                "link": self._append_affiliate_tag(link, "ML"),
                                "image": image,
                            })
                    except Exception as e:
                        # print(f"Error parsing ML offer: {e}")
                        continue

            except Exception as e:
                print(f"Error scraping ML Offers: {e}")
            
            browser.close()
            
        return deals

    def search(self, query: str) -> List[Dict]:
        deals = []
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720}
            )
            page = context.new_page()

            # --- 1. Mercado Livre Search ---
            try:
                # Format query: "jogo de chaves" -> "jogo-de-chaves"
                formatted_query = query.replace(" ", "-")
                ml_url = f"https://lista.mercadolivre.com.br/{formatted_query}_Orden_price_asc"
                print(f"Searching ML for {query}: {ml_url}")
                
                page.goto(ml_url, timeout=60000)
                page.wait_for_load_state('domcontentloaded')
                
                # ML Search Results Selectors
                # Usually 'li.ui-search-layout__item' or 'div.ui-search-result__wrapper'
                items = page.query_selector_all('li.ui-search-layout__item')
                if not items:
                    items = page.query_selector_all('div.ui-search-result__wrapper')
                
                print(f"Found {len(items)} items on ML Search")
                
                for item in items:
                    try:
                        title_el = item.query_selector('h2.ui-search-item__title')
                        link_el = item.query_selector('a.ui-search-link')
                        price_el = item.query_selector('span.andes-money-amount__fraction')
                        
                        if not title_el or not link_el or not price_el:
                            continue

                        title = title_el.inner_text().strip()
                        link = link_el.get_attribute('href')
                        price = float(price_el.inner_text().replace('.', '').replace(',', '.'))
                        
                        # Discount
                        discount = 0
                        original_price = price
                        
                        discount_el = item.query_selector('span.ui-search-price__discount')
                        if discount_el:
                            d_text = discount_el.inner_text().replace('% OFF', '').strip()
                            try:
                                discount = int(d_text)
                                original_price = price / (1 - discount/100)
                            except:
                                pass
                        
                        # Rating
                        rating = 0.0
                        # ML search sometimes doesn't show rating clearly, or uses different classes
                        # Try to find star icon or aria-label
                        
                        # Image
                        image = ""
                        img_el = item.query_selector('img.ui-search-result-image__element')
                        if img_el:
                            image = img_el.get_attribute('src')

                        # ID Extraction
                        item_id = link
                        mlb_match = re.search(r'(MLB-?\d+)', link)
                        if mlb_match:
                            item_id = mlb_match.group(1).replace('-', '')

                        # Quality Control Protocols (Phase 4)
                        
                        # Protocol 2: Noise Canceller (Negative Keywords)
                        if any(neg.lower() in title.lower() for neg in Config.NEGATIVE_KEYWORDS):
                            # print(f"   Skipped (Negative Keyword): {title[:30]}...")
                            continue

                        # Protocol 1: Quality Gate (Brand Filtering)
                        # Only apply if searching for Tools (Category A)
                        # We can infer this if the query is in the Tools list
                        is_tool_search = query in Config.KEYWORDS[:15] # First 15 are tools
                        
                        if is_tool_search:
                            # Check if title contains any preferred brand
                            has_preferred_brand = any(brand.lower() in title.lower() for brand in Config.PREFERRED_BRANDS)
                            if not has_preferred_brand:
                                # print(f"   Skipped (Brand Mismatch): {title[:30]}...")
                                continue
                        
                        if discount >= Config.MIN_DISCOUNT:
                            deals.append({
                                "source": "Mercado Livre",
                                "id": item_id,
                                "title": title,
                                "price": price,
                                "original_price": round(original_price, 2),
                                "discount": discount,
                                "rating": rating, 
                                "link": link, # Original link, will be converted later
                                "image": image,
                            })
                        else:
                             # print(f"   Skipped (Low Discount {discount}%): {title[:20]}...")
                             pass
                    except Exception as e:
                        continue

            except Exception as e:
                print(f"Error searching ML: {e}")

            # --- 2. Amazon Search ---
            try:
                print(f"Scraping Amazon for {query}...")
                page.goto(f"https://www.amazon.com.br/s?k={query}", timeout=60000)
                page.wait_for_load_state('domcontentloaded')
                time.sleep(2)
                
                items = page.query_selector_all('div[data-component-type="s-search-result"]')
                print(f"Found {len(items)} items on Amazon")
                
                for item in items:
                    try:
                        # Title: Try multiple selectors
                        title_el = item.query_selector('h2 a span')
                        if not title_el: title_el = item.query_selector('span.a-text-normal')
                        
                        # Link
                        link_el = item.query_selector('h2 a')
                        if not link_el: link_el = item.query_selector('a.a-link-normal.s-no-outline')
                        
                        # Price
                        price_whole = item.query_selector('span.a-price-whole')
                        
                        if not title_el or not link_el or not price_whole:
                            # print("Amazon: Missing core element")
                            continue
                            
                        title = title_el.inner_text().strip()
                        link = "https://www.amazon.com.br" + link_el.get_attribute('href')
                        price_str = price_whole.inner_text().replace('.', '').replace(',', '')
                        price = float(price_str)
                        
                        # Discount
                        discount = 0
                        original_price = price
                        
                        # Look for "List Price" or "Typical Price"
                        op_el = item.query_selector('span.a-text-price span.a-offscreen')
                        if op_el:
                             op_str = op_el.inner_text().replace('R$', '').strip().replace('.', '').replace(',', '.')
                             try:
                                 original_price = float(op_str)
                                 if original_price > price:
                                     discount = int(((original_price - price) / original_price) * 100)
                             except:
                                 pass

                        # Rating
                        rating = 0.0
                        rating_el = item.query_selector('span.a-icon-alt')
                        if rating_el:
                            r_text = rating_el.inner_text().split(' ')[0].replace(',', '.')
                            try:
                                rating = float(r_text)
                            except:
                                pass
                        
                        if rating > 0 and rating < Config.MIN_RATING:
                            continue
                        
                        # Skip if no rating (New seller/product)
                        if rating == 0:
                            continue

                        if discount >= Config.MIN_DISCOUNT:
                            deals.append({
                                "source": "Amazon",
                                "id": item.get_attribute('data-asin'),
                                "title": title,
                                "price": price,
                                "original_price": round(original_price, 2),
                                "discount": discount,
                                "rating": rating,
                                "link": self._append_affiliate_tag(link, "AMZ"),
                                "image": item.query_selector('img.s-image').get_attribute('src') if item.query_selector('img.s-image') else "",
                            })
                    except Exception as e:
                        continue

            except Exception as e:
                print(f"Error scraping Amazon: {e}")

            browser.close()
        
        return deals

    def _append_affiliate_tag(self, url: str, source: str) -> str:
        if not url: return ""
        if source == "AMZ":
            tag = Config.AMAZON_TAG
            return f"{url}&tag={tag}" if "?" in url else f"{url}?tag={tag}"
        elif source == "ML":
            tag = Config.MERCADO_LIVRE_ID
            return f"{url}&p={tag}" if "?" in url else f"{url}?p={tag}"
        return url
