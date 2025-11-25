"""
Test Coupon Scraper Integration
Verifies that the coupon scraper finds deals and that the main workflow would generate affiliate links for them.
"""
from src.scrapers.coupon_scraper import CouponScraper
from src.services.ml_link_generator import get_ml_affiliate_link
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_coupon_integration():
    print("🚀 Starting Coupon Scraper Integration Test...")
    
    scraper = CouponScraper()
    
    # Run the scraper (this might take a minute)
    print("🕵️ Scraping coupons (this may take a while)...")
    deals = scraper.scrape_ml_coupons()
    
    print(f"✅ Found {len(deals)} deals.")
    
    if not deals:
        print("⚠️ No deals found. Check scraper logic or website changes.")
        return

    # Take the first deal and simulate processing
    deal = deals[0]
    print(f"\n📝 Testing processing for deal: {deal['title']}")
    print(f"   Original Link: {deal['link']}")
    
    # Verify it's a raw link (not already affiliated)
    if "mercadolivre.com/sec/" in deal['link']:
        print("⚠️ Warning: Link looks like it's already affiliated!")
    
    # Simulate main.py processing
    print("🔗 Generating Affiliate Link...")
    # We use the real generator here. Since it uses a fresh browser, it will take ~15s.
    # For this test, we might want to mock it or just run it for one item to be sure.
    
    try:
        affiliate_link = get_ml_affiliate_link(deal['link'])
        print(f"✅ Generated Affiliate Link: {affiliate_link}")
        
        if "mercadolivre.com/sec/" in affiliate_link:
            print("🎉 SUCCESS: Affiliate link generated correctly!")
        else:
            print("❌ FAILURE: Generated link does not look like an affiliate link.")
            
    except Exception as e:
        print(f"❌ Error generating link: {e}")

if __name__ == "__main__":
    test_coupon_integration()
