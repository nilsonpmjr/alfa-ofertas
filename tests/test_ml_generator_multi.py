"""
Comprehensive test of ML Link Generator with multiple product URLs
Tests different product categories to ensure robustness.
"""
from src.services.ml_link_generator import get_ml_affiliate_link
import time

# Test URLs from different categories
test_products = [
    {
        "category": "Electronics - iPhone",
        "url": "https://www.mercadolivre.com.br/apple-iphone-16-256-gb-preto-distribuidor-autorizado/p/MLB1040287796"
    },
    {
        "category": "Tools - Power Drill",
        "url": "https://www.mercadolivre.com.br/furadeira-e-parafusadeira-impacto-brushless-dewalt-dcd709-amarelo-e-preto-127v/p/MLB18825888"
    },
    {
        "category": "Auto - Car Jack",
        "url": "https://www.mercadolivre.com.br/macaco-hidraulico-automotivo-jacare-2-toneladas-com-maleta/p/MLB19396671"
    }
]

print("🧪 ML Link Generator - Multi-Product Test")
print("=" * 70)
print(f"Testing {len(test_products)} products across different categories\n")

results = []

for i, product in enumerate(test_products, 1):
    print(f"\n[{i}/{len(test_products)}] Testing: {product['category']}")
    print(f"URL: {product['url'][:60]}...")
    
    start_time = time.time()
    affiliate_link = get_ml_affiliate_link(product['url'])
    elapsed = time.time() - start_time
    
    success = affiliate_link != product['url'] and 'mercadolivre.com/sec/' in affiliate_link
    
    results.append({
        "category": product['category'],
        "success": success,
        "link": affiliate_link,
        "time": elapsed
    })
    
    if success:
        print(f"✅ SUCCESS ({elapsed:.1f}s)")
        print(f"   Generated: {affiliate_link}")
    else:
        print(f"❌ FAILED ({elapsed:.1f}s)")
        print(f"   Returned: {affiliate_link}")
    
    # Small delay between tests to avoid rate limiting
    if i < len(test_products):
        print("   Waiting 5 seconds before next test...")
        time.sleep(5)

# Summary
print("\n" + "=" * 70)
print("📊 TEST SUMMARY")
print("=" * 70)

success_count = sum(1 for r in results if r['success'])
avg_time = sum(r['time'] for r in results) / len(results)

print(f"Total Tests: {len(results)}")
print(f"Successful: {success_count}")
print(f"Failed: {len(results) - success_count}")
print(f"Success Rate: {(success_count/len(results)*100):.1f}%")
print(f"Average Time: {avg_time:.1f}s")
print("\nDetailed Results:")
for r in results:
    status = "✅" if r['success'] else "❌"
    print(f"  {status} {r['category']}: {r['link'][:50]}... ({r['time']:.1f}s)")

print("=" * 70)

if success_count == len(results):
    print("\n🎉 ALL TESTS PASSED! Service is ready for integration.")
else:
    print(f"\n⚠️ {len(results) - success_count} test(s) failed. Review errors above.")
