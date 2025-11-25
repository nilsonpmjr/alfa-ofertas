import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Affiliate IDs (Placeholders until user provides them)
    AMAZON_TAG = os.getenv("AMAZON_TAG", "tag-placeholder")
    MERCADO_LIVRE_ID = os.getenv("MERCADO_LIVRE_ID", "ml-placeholder")
    SHOPEE_ID = os.getenv("SHOPEE_ID", "shopee-placeholder")

    # WhatsApp / Facebook
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "")
    FACEBOOK_GROUP_ID = os.getenv("FACEBOOK_GROUP_ID", "")
    
    # Filtering Rules
    MIN_DISCOUNT = 15  # User requested to widen the cut (was 25)
    MIN_RATING = 4.0   # User requested min 4.0 stars
    MAX_DAILY_DEALS = 15 # User requested max 15 deals per day
    
    # Search Keywords (Alfa Ofertas Niche)
    KEYWORDS = [
        # --- Category A: Tools & Hardware (Primary) ---
        "Jogo de ferramentas", "Kit ferramentas completo", "Maleta de ferramentas", "Caixa de ferramentas", "Ferramentas manuais",
        "Parafusadeira e Furadeira", "Parafusadeira de impacto", "Martelete rompedor", "Esmerilhadeira angular",
        "Serra tico tico", "Serra circular", "Lixadeira orbital", "Nível a laser", "Trena a laser", "Medidor de distância",
        
        # --- Category B: Automotive & Garage ---
        "Aspirador automotivo portátil", "Compressor de ar portátil", "Mini compressor pneu", "Auxiliar de partida", "Jump starter",
        "Carregador de bateria carro", "Macaco hidráulico garrafa", "Macaco jacaré", "Chave de roda cruz",
        "Kit limpeza automotiva", "Cera automotiva", "Lavadora de alta pressão", "Organizador de garagem", "Painel de ferramentas",
        
        # --- Category C: Tactical, Outdoor & EDC ---
        "Canivete tático", "Canivete dobrável", "Faca tática", "Faca sobrevivência", 
        "Lanterna tática", "Mochila tática", "Mochila militar", "Bornal de perna", "Pochete tática", "Luva tática",
        "Pederneira", "Filtro de água portátil", "Kit primeiros socorros tático", "Isqueiro plasma", "Maçarico portátil",
        
        # --- Category D: Rugged Tech & Utility ---
        "Power bank robusto", "Carregador portátil alta capacidade", "Smartwatch robusto", "Caixa de som bluetooth resistente",
        "Cabos reforçados", "Suporte celular moto metálico", "Suporte celular carro robusto",
        
        # --- Category E: Lifestyle & BBQ ---
        "Kit churrasco inox", "Faca do chef", "Faca churrasco artesanal", "Tábua de carne rústica",
        "Garrafa térmica", "Copo térmico", "Cooler", "Caixa térmica"
    ]
    
    # Negative Keywords (Exclude results containing these)
    NEGATIVE_KEYWORDS = [
        "infantil", "brinquedo", "feminino", "decoração", "capinha", "usado", "kids", "boneco"
    ]
    
    # Brand Filtering (Quality Gate)
    # Tier 1: Pro/High Demand
    # Tier 2: Prosumer/Reliable
    # Others: Auto/Tech/Lifestyle
    PREFERRED_BRANDS = [
        "Bosch", "Makita", "DeWalt", "Stanley", "Vonder", "Worx", "Black+Decker",
        "Anker", "Baseus", "JBL", "WAP", "Karcher", "Vonixx", "3M", "Coleman"
    ]
    
    # Feature Flags
    ENABLE_COUPONS = False  # Paused per Phase 1 directive

    # Search Settings
    # ...

def job():
    # ... (ML part is fine)

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
