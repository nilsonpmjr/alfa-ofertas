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
    
    # Niche Keywords: Tools, Auto, Tech, Tactical, DIY
    KEYWORDS = [
        # Power & Hand Tools
        "furadeira impacto", "parafusadeira bateria", "jogo chaves", "serra circular", "esmerilhadeira",
        "multimetro digital", "trena laser", "caixa ferramentas",
        
        # Automotive
        "aspirador automotivo", "compressor ar portatil", "macaco hidraulico", "carregador bateria carro",
        "kit reparo pneu", "dashcam",
        
        # Men's Tech Gadgets
        "smartwatch", "fone bluetooth cancelamento ruido", "power bank", "drone camera",
        "caixa som bluetooth potente",
        
        # Tactical/Outdoor
        "canivete tatico", "lanterna tatica", "mochila militar", "botas taticas", "barraca camping",
        
        # DIY Hardware
        "fita led", "tomada inteligente", "interruptor inteligente", "kit arduino"
    ]
