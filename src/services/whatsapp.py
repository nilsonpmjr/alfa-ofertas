import requests
import json
from src.config import Config

class WhatsAppService:
    API_URL = "https://graph.facebook.com/v17.0"

    def __init__(self):
        self.token = Config.WHATSAPP_TOKEN
        self.phone_id = Config.WHATSAPP_PHONE_ID
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def send_message(self, to: str, message: str):
        url = f"{self.API_URL}/{self.phone_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            print(f"Message sent to {to}")
            return response.json()
        except Exception as e:
            print(f"Error sending WhatsApp message: {e}")
            if 'response' in locals():
                print(f"Response: {response.text}")
            return None

    def send_template(self, to: str, template_name: str, language_code: str = "pt_BR"):
        url = f"{self.API_URL}/{self.phone_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code}
            }
        }
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error sending Template: {e}")
            return None
