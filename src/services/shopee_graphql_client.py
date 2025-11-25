#!/usr/bin/env python3
"""
Shopee GraphQL API Client
Handles authentication and API calls to Shopee affiliate GraphQL endpoint.
"""

import json
import hashlib
import hmac
import time
import requests
from typing import Dict, List, Optional

class ShopeeGraphQLClient:
    """Client for Shopee Affiliate GraphQL API"""
    
    def __init__(self, app_id: str, secret: str):
        """
        Initialize Shopee GraphQL client.
        
        Args:
            app_id: Your Shopee AppID
            secret: Your Shopee Secret/Password
        """
        self.app_id = app_id
        self.secret = secret
        self.endpoint = "https://open-api.affiliate.shopee.com.br/graphql"
    
    def _generate_signature(self, timestamp: int) -> str:
        """
        Generate SHA256 signature for authentication.
        
        Args:
            timestamp: Unix timestamp
            
        Returns:
            Hexadecimal signature string
        """
        # Message is timestamp + app_id (based on typical HMAC-SHA256 patterns)
        message = f"{timestamp}{self.app_id}"
        signature = hmac.new(
            self.secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_auth_header(self) -> str:
        """
        Generate authorization header.
        
        Returns:
            Authorization header value
        """
        timestamp = int(time.time())
        signature = self._generate_signature(timestamp)
        
        return f"SHA256 Credential={self.app_id}, Signature={signature}, Timestamp={timestamp}"
    
    def execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Execute a GraphQL query.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            
        Returns:
            API response as dictionary
        """
        headers = {
            'Authorization': self._get_auth_header(),
            'Content-Type': 'application/json'
        }
        
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Response: {e.response.text}")
            return {}
    
    def get_shopee_offers(self, keyword: str = "", sort_type: int = 1, 
                         page: int = 1, limit: int = 20) -> List[Dict]:
        """
        Get Shopee offers/deals.
        
        Args:
            keyword: Search keyword (optional)
            sort_type: 1 = Latest DESC, 2 = Highest Commission DESC
            page: Page number
            limit: Results per page
            
        Returns:
            List of offers
        """
        query = """
        query($keyword: String, $sortType: Int, $page: Int, $limit: Int) {
          shopeeOfferV2(keyword: $keyword, sortType: $sortType, page: $page, limit: $limit) {
            nodes {
              commissionRate
              imageUrl
              offerLink
              originalLink
              offerName
              offerType
              categoryId
              collectionId
              periodStartTime
              periodEndTime
            }
            pageInfo {
              page
              limit
              hasNextPage
            }
          }
        }
        """
        
        variables = {
            'keyword': keyword,
            'sortType': sort_type,
            'page': page,
            'limit': limit
        }
        
        result = self.execute_query(query, variables)
        
        if 'data' in result and 'shopeeOfferV2' in result['data']:
            return result['data']['shopeeOfferV2']['nodes']
        elif 'errors' in result:
            print(f"❌ GraphQL errors: {result['errors']}")
        
        return []
    
    def generate_short_link(self, original_url: str, sub_ids: Optional[List[str]] = None) -> Optional[str]:
        """
        Generate Shopee affiliate short link.
        
        Args:
            original_url: Original product URL
            sub_ids: Optional tracking sub IDs (up to 5)
            
        Returns:
            Short link URL or None
        """
        if sub_ids is None:
            sub_ids = []
        
        # Ensure max 5 sub IDs
        sub_ids = sub_ids[:5]
        
        query = """
        mutation($originUrl: String!, $subIds: [String]) {
          generateShortLink(input: {originUrl: $originUrl, subIds: $subIds}) {
            shortLink
          }
        }
        """
        
        variables = {
            'originUrl': original_url,
            'subIds': sub_ids
        }
        
        result = self.execute_query(query, variables)
        
        if 'data' in result and 'generateShortLink' in result['data']:
            return result['data']['generateShortLink']['shortLink']
        elif 'errors' in result:
            print(f"❌ GraphQL errors: {result['errors']}")
        
        return None


def main():
    """Test the Shopee GraphQL client."""
    print("🛍️ Shopee GraphQL API Test\n")
    
    # Get credentials
    app_id = input("Enter your AppID: ").strip()
    secret = input("Enter your Secret: ").strip()
    
    if not app_id or not secret:
        print("❌ AppID and Secret are required")
        return
    
    # Create client
    client = ShopeeGraphQLClient(app_id, secret)
    
    # Test: Get offers
    print("\n📦 Fetching Shopee offers...")
    offers = client.get_shopee_offers(limit=5)
    
    print(f"\n✅ Found {len(offers)} offers:\n")
    
    for i, offer in enumerate(offers, 1):
        print(f"{i}. {offer['offerName']}")
        print(f"   💰 Commission: {offer['commissionRate']}%")
        print(f"   🔗 Link: {offer['offerLink'][:60]}...")
        print()
    
    # Test: Generate short link
    if offers:
        test_offer = offers[0]
        print(f"\n🔗 Testing short link generation for: {test_offer['offerName'][:50]}")
        short_link = client.generate_short_link(test_offer['originalLink'])
        
        if short_link:
            print(f"✅ Generated short link: {short_link}")
        else:
            print("❌ Failed to generate short link")
    
    # Save results
    with open('shopee_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(offers, f, indent=2, ensure_ascii=False)
    print("\n💾 Results saved to shopee_test_results.json")


if __name__ == "__main__":
    main()
