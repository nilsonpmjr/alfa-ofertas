import requests
from typing import List, Dict
from bs4 import BeautifulSoup
from src.config import Config
import random
import time

class AmazonScraper:
    BASE_URL = "https://www.amazon.com.br/s"

    def search(self, query: str) -> List[Dict]:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Linux"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
        
        params = {"k": query}
        
        try:
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(self.BASE_URL, params=params, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            deals = []
            
            # Amazon search results
            items = soup.find_all('div', {'data-component-type': 's-search-result'})
            
            for item in items:
                try:
                    title_tag = item.find('span', class_='a-text-normal')
                    link_tag = item.find('a', class_='a-link-normal')
                    price_whole = item.find('span', class_='a-price-whole')
                    price_fraction = item.find('span', class_='a-price-fraction')
                    
                    if not title_tag or not link_tag or not price_whole:
                        continue

                    title = title_tag.text.strip()
                    link = "https://www.amazon.com.br" + link_tag['href']
                    
                    # Price formatting: 1.234,56 -> 1234.56
                    price_str = price_whole.text.replace('.', '').replace(',', '')
                    if price_fraction:
                        price_str += f".{price_fraction.text}"
                    price = float(price_str)
                    
                    # Check for "Limited Time Deal" or "Save X%"
                    # This is hard to parse reliably, so we might just look for strikethrough price
                    original_price_tag = item.find('span', class_='a-text-price')
                    original_price = price
                    discount = 0
                    
                    if original_price_tag:
                        off_text = original_price_tag.find('span', class_='a-offscreen')
                        if off_text:
                            op_str = off_text.text.replace('R$', '').strip().replace('.', '').replace(',', '.')
                            try:
                                original_price = float(op_str)
                                if original_price > price:
                                    discount = int(((original_price - price) / original_price) * 100)
                            except:
                                pass
                    
                    if discount >= Config.MIN_DISCOUNT:
                        deals.append({
                            "source": "Amazon",
                            "id": item['data-asin'],
                            "title": title,
                            "price": price,
                            "original_price": original_price,
                            "discount": discount,
                            "link": self._append_affiliate_tag(link),
                            "image": item.find('img', class_='s-image')['src'] if item.find('img', class_='s-image') else "",
                        })
                        
                except Exception as e:
                    continue
                    
            return deals

        except Exception as e:
            print(f"Error searching Amazon for {query}: {e}")
            if 'response' in locals():
                print(f"Status: {response.status_code}")
                # print(f"Response snippet: {response.text[:500]}")
            return []

    def _append_affiliate_tag(self, url: str) -> str:
        if not url:
            return ""
        if "?" in url:
            return f"{url}&tag={Config.AMAZON_TAG}"
        else:
            return f"{url}?tag={Config.AMAZON_TAG}"
