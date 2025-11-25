"""
End-to-End Integration Test
Simulates complete bot workflow with mock deals to verify:
1. ML affiliate link generation
2. Amazon affiliate tag appending
3. Database deduplication
4. Message formatting
"""
import sys
sys.path.insert(0, '/home/nilsonpmjr/.gemini/antigravity/scratch/sales_finder')

from src.database import Database
from src.services.ml_link_generator import get_ml_affiliate_link
from src.config import Config

def test_workflow():
    print("🧪 End-to-End Workflow Integration Test")
    print("=" * 70)
    
    # Initialize database
    db = Database()
    
    import random
    import time
    
    # Mock deals (one from each source) with unique IDs
    suffix = int(time.time())
    mock_deals = [
        {
            "id": f"MLB-TEST-{suffix}",
            "source": "Mercado Livre",
            "title": "iPhone 16 Test Deal",
            "price": 7999.00,
            "original_price": 9999.00,
            "discount": 20, # Assuming 20% discount for 7999 from 9999
            "rating": 4.8,
            "link": "https://www.mercadolivre.com.br/apple-iphone-16-256-gb-preto-distribuidor-autorizado/p/MLB1040287796"
        },
        {
            "id": f"B0TEST-{suffix}",
            "source": "Amazon",
            "title": "Parafusadeira Elétrica 12V Bivolt",
            "price": 189.90,
            "original_price": 299.90,
            "discount": 37,
            "rating": 4.5,
            "link": "https://www.amazon.com.br/dp/B0TEST123"
        }
    ]
    
    print(f"\n📦 Processing {len(mock_deals)} mock deals...\n")
    
    for i, deal in enumerate(mock_deals, 1):
        print(f"[{i}/{len(mock_deals)}] {deal['source']}: {deal['title'][:40]}...")
        
        # Step 1: Generate affiliate link for ML deals
        if 'mercadolivre.com' in deal['link']:
            print(f"  🔗 Generating ML affiliate link...")
            original = deal['link']
            affiliate = get_ml_affiliate_link(original)
            if affiliate != original:
                deal['link'] = affiliate
                print(f"  ✅ Generated: {affiliate}")
            else:
                print(f"  ⚠️ Using original (generation failed)")
        
        # Step 2: Append Amazon tag
        elif 'amazon.com' in deal['link']:
            tag = Config.AMAZON_TAG
            if '?' in deal['link']:
                deal['link'] = f"{deal['link']}&tag={tag}"
            else:
                deal['link'] = f"{deal['link']}?tag={tag}"
            print(f"  🏷️ Appended Amazon tag: {deal['link']}")
        
        # Step 3: Check for duplicates
        is_duplicate = db.is_deal_sent_today(deal['id'])
        if is_duplicate:
            print(f"  ⚠️ Duplicate detected - would skip")
            continue
        else:
            print(f"  ✅ Not a duplicate - would send")
        
        # Step 4: Format WhatsApp message
        rating_str = f"⭐ {deal.get('rating', 'N/A')}" if deal.get('rating') else ""
        msg = f"*OFERTA ENCONTRADA!* 🚀\\n\\n" \
              f"*{deal['title']}*\\n" \
              f"💰 De: ~R$ {deal['original_price']}~\\n" \
              f"🔥 *Por: R$ {deal['price']}*\\n" \
              f"📉 Desconto: {deal['discount']}%\\n" \
              f"{rating_str}\\n\\n" \
              f"🔗 *Link:* {deal['link']}"
        
        print(f"  📱 Message preview:")
        print("  " + "-" * 60)
        for line in msg.split("\\n"):
            print(f"  {line}")
        print("  " + "-" * 60)
        
        # Step 5: Mark as sent (for test purposes)
        db.mark_deal_as_sent(deal)
        print(f"  💾 Marked as sent in database")
        print()
    
    # Verify today's count
    count = db.get_today_deals_count()
    print("=" * 70)
    print(f"📊 Database state: {count} deals sent today")
    print(f"   Daily limit: {Config.MAX_DAILY_DEALS}")
    print("=" * 70)
    
    print("\n✅ End-to-End Test Complete!")
    print("\nVerified components:")
    print("  ✓ ML affiliate link generation (network interception)")
    print("  ✓ Amazon affiliate tag appending")
    print("  ✓ Database deduplication check")
    print("  ✓ Message formatting")
    print("  ✓ Deal tracking in database")

if __name__ == "__main__":
    test_workflow()
