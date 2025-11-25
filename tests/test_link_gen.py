from src.services.ml_affiliate import get_ml_link

test_url = "https://www.mercadolivre.com.br/ofertas"
print(f"Testing Link Generation for: {test_url}")

link = get_ml_link(test_url)
print(f"Result: {link}")
