"""
Coupon Engine - Finds items eligible for discount coupons
"""
from playwright.sync_api import sync_playwright
from typing import List, Dict
import time
import re
from src.config import Config

class CouponScraper:
    """Scrapes Mercado Livre for items with active coupons."""
    
    def scrape_ml_coupons(self) -> List[Dict]:
        """
        Scrape ML for items with available coupons.
        ML often has a dedicated coupons page or items with 'CUPOM' badges.
        """
        deals = []
        
        # ML Coupon pages to check
        coupon_urls = [
            "https://www.mercadolivre.com.br/ofertas?container_id=MLB779362-1&promotion_type=coupon",
            "https://www.mercadolivre.com.br/cupons"
        ]
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 720}
            )
            page = context.new_page()
            
            for url in coupon_urls:
                try:
                    print(f"Scraping ML Coupons: {url}")
                    page.goto(url, timeout=60000)
                    page.wait_for_load_state('domcontentloaded')
                    
                    # Scroll to load items
                    for _ in range(3):
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(1)
                    
                    # Try different selectors for coupon items
                    items = page.query_selector_all('div.andes-card')
                    if not items:
                        items = page.query_selector_all('li.ui-search-layout__item')
                    
                    print(f"Found {len(items)} potential coupon items")
                    
                    for item in items:
                        try:
                            # Extract coupon info
                            coupon_badge = item.query_selector('span.poly-component__coupon, span[class*="coupon"], span[class*="cupom"]')
                            
                            # Basic info
                            title_el = item.query_selector('a.poly-component__title, h2.ui-search-item__title')
                            price_el = item.query_selector('span.andes-money-amount__fraction')
                            link_el = item.query_selector('a.poly-component__title, a.ui-search-link')
                            
                            if not title_el or not price_el or not link_el:
                                continue
                            
                            title = title_el.inner_text().strip()
                            link = link_el.get_attribute('href')
                            price = float(price_el.inner_text().replace('.', '').replace(',', '.'))
                            
                            # Coupon discount
                            coupon_text = ""
                            coupon_discount = 0
                            if coupon_badge:
                                coupon_text = coupon_badge.inner_text().strip()
                                # Extract percentage if present (e.g., "10% OFF")
                                match = re.search(r'(\d+)%', coupon_text)
                                if match:
                                    coupon_discount = int(match.group(1))
                            
                            # Original price / discount
                            discount = 0
                            original_price = price
                            discount_el = item.query_selector('span.poly-price__disc_label, span.ui-search-price__discount')
                            if discount_el:
                                d_text = discount_el.inner_text().replace('% OFF', '').strip()
                                try:
                                    discount = int(d_text)
                                    original_price = price / (1 - discount/100)
                                except:
                                    pass
                            
                            # Rating
                            rating = 0.0
                            rating_el = item.query_selector('span.poly-reviews__rating, span.ui-search-reviews__rating-number')
                            if rating_el:
                                try:
                                    rating = float(rating_el.inner_text().strip())
                                except:
                                    pass
                            
                            # Skip if rating too low
                            if rating > 0 and rating < Config.MIN_RATING:
                                continue
                            if rating == 0:  # New seller
                                continue
                            
                            # Image
                            image = ""
                            img_el = item.query_selector('img.poly-component__picture, img.ui-search-result-image__element')
                            if img_el:
                                image = img_el.get_attribute('data-src') or img_el.get_attribute('src')
                            
                            # Seller
                            seller = ""
                            seller_el = item.query_selector('span.poly-component__seller, span.ui-search-item__group__element')
                            if seller_el:
                                seller = seller_el.inner_text().strip()
                            
                            # Extract ID
                            item_id = link
                            mlb_match = re.search(r'(MLB-?\d+)', link)
                            if mlb_match:
                                item_id = mlb_match.group(1).replace('-', '')
                            
                            # Calculate effective discount (base discount + coupon)
                            effective_discount = discount + coupon_discount
                            
                            # Only add if meets minimum discount criteria
                            if effective_discount >= Config.MIN_DISCOUNT:
                                # Generate affiliate link
                                from src.services.ml_affiliate import get_ml_link
                                affiliate_link = get_ml_link(link)
                                
                                deals.append({
                                    "source": "Mercado Livre Cupom",
                                    "id": item_id,
                                    "title": title,
                                    "price": price,
                                    "original_price": round(original_price, 2),
                                    "discount": effective_discount,
                                    "coupon": coupon_text,
                                    "rating": rating,
                                    "seller": seller,
                                    "link": affiliate_link,
                                    "image": image,
                                })
                        except Exception as e:
                            continue
                    
                except Exception as e:
                    print(f"Error scraping ML coupons from {url}: {e}")
                    continue
            
            browser.close()
        
        return deals
