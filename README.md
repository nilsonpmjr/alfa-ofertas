# Alfa Ofertas Bot 🐺

**Alfa Ofertas** is a sales finder bot that monitors **Mercado Livre** and **Amazon Brazil** for high-quality deals in specific niches (Tools, Automotive, Tech).

## Features
*   **Real-time Scraping**: Monitors offers 24/7.
*   **Strict Filtering**:
    *   Min Discount: 15%
    *   Min Rating: 4.0 Stars
    *   Niche: Tools, Auto, Tech, Tactical, DIY
*   **Deduplication**: Uses SQLite to ensure the same deal is never sent twice in one day.
*   **Local Dashboard**: Web interface to view live deals (`http://localhost:3000`).

## 🚀 Deployment Guide (VM/VPS)

Follow these steps to run the bot on a fresh Linux VM (Ubuntu/Debian).

### 1. Clone the Repository
```bash
git clone https://github.com/nilsonpmjr/alfa-ofertas.git
cd alfa-ofertas
```

### 2. System Dependencies
Install Python and browser dependencies:
```bash
sudo apt update && sudo apt install -y python3-venv python3-pip
```

### 3. Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Install Playwright Browsers
Required for the scraper to work:
```bash
playwright install chromium
playwright install-deps
```

### 5. Configuration (.env)
**Important:** The `.env` file is NOT in the repository for security. You must create it manually.

Create a file named `.env`:
```bash
nano .env
```

Paste the following content (adjust as needed):
```ini
# WhatsApp Configuration (Optional for now)
WHATSAPP_TOKEN=your_token_here
WHATSAPP_PHONE_ID=your_phone_id_here
MY_VERIFY_TOKEN=your_verify_token

# Facebook Configuration (Optional)
FACEBOOK_PAGE_ID=your_page_id
FACEBOOK_ACCESS_TOKEN=your_fb_token
FACEBOOK_GROUP_ID=your_group_id

# Affiliate Tags (Optional)
AMAZON_TAG=alfa00-20
MERCADO_LIVRE_ID=123456
```

### 6. Run the Bot
```bash
# Run in background (using nohup or systemd is recommended for production)
python3 src/main.py
```

The dashboard will be available at `http://YOUR_VM_IP:3000`.