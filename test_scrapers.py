from src.scrapers.mercadolivre import MercadoLivreScraper
from src.scrapers.amazon import AmazonScraper
from src.scrapers.mock import MockScraper
from src.scrapers.playwright_scraper import PlaywrightScraper
from src.config import Config

def test_scrapers():
    # Test Playwright (Real Data)
    print(f"\nTesting Playwright Scraper for: {Config.KEYWORDS[0]}...")
    pw_scraper = PlaywrightScraper()
    pw_deals = pw_scraper.search(Config.KEYWORDS[0])
    print(f"Found {len(pw_deals)} Playwright deals.")
    for deal in pw_deals[:3]:
        print(f"[{deal['discount']}% OFF] {deal['title']} - R$ {deal['price']}")
        print(f"Link: {deal['link']}")

    # Test Mock
    # print(f"\nTesting Mock Scraper for: {Config.KEYWORDS[0]}...")
    # mock_scraper = MockScraper()
    # ...



if __name__ == "__main__":
    test_scrapers()
