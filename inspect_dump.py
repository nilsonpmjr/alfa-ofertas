from bs4 import BeautifulSoup

with open("ml_dump.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all cards
cards = soup.find_all('div', class_='andes-card')
print(f"Found {len(cards)} cards.")

for i, card in enumerate(cards[:5]):
    print(f"\n--- Card {i} ---")
    # Print text content to see if it's a product
    print(f"Text: {card.get_text(strip=True)[:100]}...")
    
    # Try to find title class
    # Usually p or h3
    title = card.find('p', class_='promotion-item__title')
    if title:
        print(f"Title (p.promotion-item__title): {title.text}")
    else:
        # Look for any text element
        print("No promotion-item__title found. Classes in card:")
        for tag in card.find_all(True):
            if tag.get('class'):
                print(f"  {tag.name}.{'.'.join(tag.get('class'))}")
