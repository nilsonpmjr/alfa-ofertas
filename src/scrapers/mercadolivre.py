import requests
from typing import List, Dict, Optional
from src.config import Config

class MercadoLivreScraper:
    BASE_URL = "https://api.mercadolibre.com/sites/MLB/search"

    def search(self, query: str) -> List[Dict]:
        # Format query for URL: "jogo de chaves" -> "jogo-de-chaves"
        # formatted_query = query.replace(" ", "-")
        # url = f"https://lista.mercadolivre.com.br/{formatted_query}_Orden_price_asc"
        url = "https://www.mercadolivre.com.br/jm/search"
        
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
        
        params = {"as_word": query}

        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            deals = []
            # ML search results usually have this class
            items = soup.find_all('li', class_='ui-search-layout__item')
            
            if not items:
                 # Try alternative layout
                 items = soup.find_all('div', class_='ui-search-result__wrapper')

            for item in items:
                try:
                    title_tag = item.find('h2', class_='ui-search-item__title')
                    link_tag = item.find('a', class_='ui-search-link')
                    price_tag = item.find('span', class_='andes-money-amount__fraction')
                    
                    if not title_tag or not link_tag or not price_tag:
                        continue

                    title = title_tag.text.strip()
                    link = link_tag['href']
                    price = float(price_tag.text.replace('.', '').replace(',', '.'))
                    
                    # Try to find original price for discount calc
                    # This is tricky in HTML, often in a separate 's-item__discount' or similar
                    # For now, we'll just grab the current price and assume 0 discount if not found
                    discount = 0
                    original_price = price
                    
                    # Look for discount tag
                    discount_tag = item.find('span', class_='ui-search-price__discount')
                    if discount_tag:
                        # "20% OFF"
                        discount_text = discount_tag.text.strip().replace('% OFF', '')
                        try:
                            discount = int(discount_text)
                            original_price = price / (1 - discount/100)
                        except:
                            pass

                    if discount >= Config.MIN_DISCOUNT:
                        deals.append({
                            "source": "Mercado Livre",
                            "id": link.split('MLB-')[1].split('-')[0] if 'MLB-' in link else link,
                            "title": title,
                            "price": price,
                            "original_price": round(original_price, 2),
                            "discount": discount,
                            "link": self._append_affiliate_tag(link),
                            "image": "", # Image extraction is complex, skipping for now
                        })
                except Exception as e:
                    continue
            
            return deals

        except Exception as e:
            print(f"Error searching Mercado Livre for {query}: {e}")
            return []

    def _append_affiliate_tag(self, url: str) -> str:
        if not url:
            return ""
        # Basic appending, ML structure might vary but usually query params work
        if "?" in url:
            return f"{url}&p={Config.MERCADO_LIVRE_ID}"
        else:
            return f"{url}?p={Config.MERCADO_LIVRE_ID}"
