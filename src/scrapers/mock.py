from typing import List, Dict
import random
from src.config import Config

class MockScraper:
    def search(self, query: str) -> List[Dict]:
        # Simulate finding 2-3 deals per query
        deals = []
        for i in range(random.randint(2, 4)):
            price = random.uniform(50.0, 500.0)
            discount = random.randint(20, 50)
            original_price = price / (1 - discount/100)
            
            deals.append({
                "source": "MockStore",
                "id": f"mock-{random.randint(1000, 9999)}",
                "title": f"[MOCK] {query.title()} - Modelo {random.choice(['Pro', 'Ultra', 'Max'])}",
                "price": round(price, 2),
                "original_price": round(original_price, 2),
                "discount": discount,
                "link": f"https://example.com/deal?q={query}&id={i}",
                "image": "https://via.placeholder.com/300",
            })
        return deals
