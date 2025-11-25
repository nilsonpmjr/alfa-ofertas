import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, render_template
import threading
import time
import schedule
from src.config import Config
from src.scrapers.playwright_scraper import PlaywrightScraper
from src.scrapers.coupon_scraper import CouponScraper
from src.services.whatsapp import WhatsAppService
from src.services.ml_link_generator import get_ml_affiliate_link

app = Flask(__name__)
whatsapp = WhatsAppService()
scraper = PlaywrightScraper()
coupon_scraper = CouponScraper()

from src.database import Database

app = Flask(__name__)
whatsapp = WhatsAppService()
scraper = PlaywrightScraper()
db = Database()

# In-memory list for dashboard (still transient, but filtered by DB)
# Load recent deals from DB on startup
all_deals = db.get_recent_deals()
print(f"Loaded {len(all_deals)} deals from database.")

def job():
    # Check daily limit via DB
    daily_count = db.get_today_deals_count()
    if daily_count >= Config.MAX_DAILY_DEALS:
        print(f"Daily limit reached ({daily_count}/{Config.MAX_DAILY_DEALS}). Skipping job.")
        return

    print("Running scheduled job...")
    
    # 1. Scrape Mercado Livre Offers (Once)
    print("Fetching Mercado Livre Lightning Deals...")
    ml_deals = scraper.scrape_ml_offers()
    
    # Filter ML deals by keywords and negative keywords
    filtered_ml_deals = []
    for deal in ml_deals:
        title_lower = deal['title'].lower()
        
        # Check negative keywords first
        if any(neg in title_lower for neg in Config.NEGATIVE_KEYWORDS):
            # print(f"Skipped ML deal (Negative keyword): {deal['title']}")
            continue

        # Check if any keyword is in the title (case insensitive)
        if any(keyword.lower() in title_lower for keyword in Config.KEYWORDS):
            filtered_ml_deals.append(deal)
        else:
            # print(f"Skipped ML deal (No keyword match): {deal['title']}")
            pass
            
    print(f"Found {len(ml_deals)} total ML deals, {len(filtered_ml_deals)} matched keywords.")
    
    # Process ML Deals
    process_deals(filtered_ml_deals)

    # 1.5 Scrape Mercado Livre Coupons (New Engine)
    print("Fetching Mercado Livre Coupon Deals...")
    coupon_deals = coupon_scraper.scrape_ml_coupons()
    print(f"Found {len(coupon_deals)} coupon deals.")
    process_deals(coupon_deals)

    # 2. Scrape Amazon (Per Keyword)
    # Randomize keywords
    import random
    selected_keywords = random.sample(Config.KEYWORDS, min(3, len(Config.KEYWORDS)))
    
    for keyword in selected_keywords:
        # Check limit again inside loop
        if db.get_today_deals_count() >= Config.MAX_DAILY_DEALS:
            break
            
        print(f"Searching Amazon for {keyword}...")
        deals = scraper.search(keyword) 
        process_deals(deals)

def process_deals(deals):
    for deal in deals:
        if db.get_today_deals_count() >= Config.MAX_DAILY_DEALS:
            return

        # Check negative keywords (Double check for Amazon/Scraped items)
        if any(neg in deal['title'].lower() for neg in Config.NEGATIVE_KEYWORDS):
            # print(f"Skipped deal (Negative keyword): {deal['title']}")
            continue

        # Generate ML affiliate link if this is a Mercado Livre deal
        if 'mercadolivre.com' in deal.get('link', ''):
            print(f"🔗 Generating ML affiliate link for: {deal['title'][:30]}...")
            original_link = deal['link']
            affiliate_link = get_ml_affiliate_link(original_link)
            if affiliate_link != original_link:
                deal['link'] = affiliate_link
                print(f"   ✅ Generated: {affiliate_link}")
            else:
                print(f"   ⚠️ Using original link (generation failed)")
        
        # Check DB for duplicates
        print(f"Processing Deal ID: {deal['id']} | Title: {deal['title'][:20]}...")
        if not db.is_deal_sent_today(deal['id']):
            # Add to global list for dashboard
            all_deals.insert(0, deal)
            if len(all_deals) > 100:
                all_deals.pop()

            # Format message
            rating_str = f"⭐ {deal.get('rating', 'N/A')}" if deal.get('rating') else ""
            
            msg = f"*OFERTA ENCONTRADA!* 🚀\n\n" \
                  f"*{deal['title']}*\n" \
                  f"💰 De: ~R$ {deal['original_price']}~\n" \
                  f"🔥 *Por: R$ {deal['price']}*\n" \
                  f"📉 Desconto: {deal['discount']}%\n" \
                  f"{rating_str}\n\n" \
                  f"🔗 *Link:* {deal['link']}"
            
            print(f"Would send to WhatsApp: \n{msg}\n")
            
            # Send to WhatsApp Service (Node.js)
            try:
                import requests
                response = requests.post('http://localhost:3001/send-deal', json={'deal': deal})
                if response.status_code == 200:
                    print("✅ Sent to WhatsApp Service!")
                else:
                    print(f"❌ WhatsApp Service Error: {response.text}")
            except Exception as e:
                print(f"❌ Could not connect to WhatsApp Service: {e}")
            
            # Mark as sent in DB (Pass full deal object now)
            db.mark_deal_as_sent(deal)
            
            count = db.get_today_deals_count()
            print(f"Deals sent today: {count}/{Config.MAX_DAILY_DEALS}")
        else:
            # print(f"Duplicate deal skipped: {deal['title']}")
            pass

def run_scheduler():
    schedule.every(1).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/deals')
def get_deals():
    return jsonify(all_deals)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode and token:
            if mode == 'subscribe' and token == "MY_VERIFY_TOKEN":
                return challenge, 200
            else:
                return "Forbidden", 403
    
    elif request.method == 'POST':
        data = request.json
        print(f"Received webhook: {data}")
        return "OK", 200

if __name__ == "__main__":
    # Start scheduler
    t = threading.Thread(target=run_scheduler)
    t.daemon = True
    t.start()
    
    # Start Flask server
    print("Starting server on port 3000...")
    app.run(port=3000, host='0.0.0.0')
