#!/usr/bin/env python3
"""
Debug FMP API parameters and responses
Check if parameters are being sent correctly and responses are actually different
"""
import asyncio
import httpx
import json
from typing import Dict, Any

async def debug_fmp_api():
    print("🐛 FMP API PARAMETER DEBUG")
    print("=" * 50)
    
    # Get API key
    from core.config import get_settings
    settings = get_settings()
    
    if not settings.credentials or not settings.credentials.api_keys.get("fmp"):
        print("❌ No FMP API key configured")
        return
    
    api_key = settings.credentials.api_keys["fmp"].key
    base_url = "https://financialmodelingprep.com/api/v3/stock-screener"
    
    # Test different parameter sets
    test_cases = [
        {
            "name": "Original ($1-$100)",
            "params": {
                "marketCapMoreThan": "10000000",
                "marketCapLowerThan": "2000000000",
                "exchange": "NASDAQ,NYSE",
                "volumeMoreThan": "1000000",
                "priceMoreThan": "1.00",
                "priceLowerThan": "100.00",
                "isActivelyTrading": "true",
                "apikey": api_key
            }
        },
        {
            "name": "Tight Price ($1-$5)",
            "params": {
                "marketCapMoreThan": "10000000",
                "marketCapLowerThan": "2000000000",
                "exchange": "NASDAQ,NYSE",
                "volumeMoreThan": "1000000",
                "priceMoreThan": "1.00",
                "priceLowerThan": "5.00",  # VERY RESTRICTIVE
                "isActivelyTrading": "true",
                "apikey": api_key
            }
        },
        {
            "name": "No Filters (Just Exchange)",
            "params": {
                "exchange": "NASDAQ,NYSE",
                "isActivelyTrading": "true",
                "apikey": api_key
            }
        }
    ]
    
    results = []
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i, test_case in enumerate(test_cases, 1):
            print(f"🧪 Test {i}: {test_case['name']}")
            
            # Print actual URL and parameters being sent
            params = test_case['params']
            print(f"   URL: {base_url}")
            print(f"   Parameters sent:")
            for key, value in params.items():
                if key != 'apikey':  # Don't print API key
                    print(f"     {key} = {value}")
                else:
                    print(f"     {key} = [HIDDEN]")
            
            try:
                # Make the request
                print(f"   Making request...")
                response = await client.get(base_url, params=params)
                
                print(f"   HTTP Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else 0
                    print(f"   ✅ Success: {count} stocks returned")
                    
                    # Check if we got actual stock data
                    if count > 0 and isinstance(data, list):
                        # Sample first stock
                        sample = data[0]
                        symbol = sample.get('symbol', 'N/A')
                        price = sample.get('price', 0)
                        market_cap = sample.get('marketCap', 0)
                        
                        print(f"   Sample: {symbol} @ ${price:.2f}, Cap: ${market_cap:,.0f}")
                        
                        # For tight price test, verify prices are actually restricted
                        if "Tight Price" in test_case['name']:
                            prices = [s.get('price', 0) for s in data[:10] if s.get('price', 0) > 0]
                            if prices:
                                min_p, max_p = min(prices), max(prices)
                                print(f"   Price range check: ${min_p:.2f} - ${max_p:.2f}")
                                if max_p > 5.0:
                                    print(f"   🚨 PROBLEM: Max price ${max_p:.2f} > $5.00!")
                                else:
                                    print(f"   ✅ Price filter working correctly")
                    
                    results.append({
                        "name": test_case['name'],
                        "count": count,
                        "status": "success"
                    })
                
                elif response.status_code == 429:
                    print(f"   ⚠️  Rate limited (429)")
                    results.append({
                        "name": test_case['name'],
                        "count": 0,
                        "status": "rate_limited"
                    })
                
                else:
                    print(f"   ❌ HTTP Error: {response.status_code}")
                    print(f"   Response: {response.text[:200]}...")
                    results.append({
                        "name": test_case['name'],
                        "count": 0,
                        "status": "error"
                    })
            
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                results.append({
                    "name": test_case['name'],
                    "count": 0,
                    "status": "exception"
                })
            
            print()
    
    # Summary analysis
    print("=" * 50)
    print("📊 RESULTS SUMMARY:")
    for result in results:
        status_emoji = "✅" if result['status'] == 'success' else "❌"
        print(f"   {status_emoji} {result['name']}: {result['count']} stocks ({result['status']})")
    
    print()
    print("🔍 ANALYSIS:")
    
    # Check if counts are suspiciously similar
    success_counts = [r['count'] for r in results if r['status'] == 'success']
    if len(success_counts) >= 2:
        if all(count == success_counts[0] for count in success_counts):
            print("🚨 SUSPICIOUS: All successful tests returned same count!")
            print("   Possible causes:")
            print("   • FMP API ignoring parameters")
            print("   • Hidden result limits")
            print("   • Caching issues")
            print("   • Free tier restrictions")
        else:
            print("✅ GOOD: Different filters produced different counts")
            print("   This suggests filters are working correctly")
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(debug_fmp_api()) 