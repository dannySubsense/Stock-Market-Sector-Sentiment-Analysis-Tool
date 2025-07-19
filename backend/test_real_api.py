#!/usr/bin/env python3
"""
Test Real API Endpoints
Tests the actual FastAPI application endpoints with real data
"""
import asyncio
import httpx
import json

async def test_real_api_endpoints():
    """Test the actual production API endpoints"""
    print("🌐 TESTING REAL FASTAPI APPLICATION")
    print("=" * 60)
    print("🎯 Target: http://localhost:8000")
    print("🎯 Testing: Actual production API endpoints")
    print("=" * 60)
    print()
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # ===== TEST 1: Health Check =====
        print("🏥 TEST 1: Health Check")
        print("-" * 40)
        
        try:
            response = await client.get(f"{base_url}/api/health")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Health: {data.get('status', 'unknown')}")
                print(f"   📊 Database: {data.get('database', 'unknown')}")
                print(f"   🔄 Redis: {data.get('redis', 'unknown')}")
            else:
                print(f"   ❌ Health check failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
        
        print()
        
        # ===== TEST 2: Universe Stats (Real Small-Cap Data) =====
        print("📊 TEST 2: Universe Stats (Real Small-Cap Data)")
        print("-" * 40)
        
        try:
            response = await client.get(f"{base_url}/api/stocks/universe/stats")
            if response.status_code == 200:
                data = response.json()
                total_stocks = data.get('total_stocks', 0)
                target = data.get('target_universe_size', 1500)
                coverage = data.get('coverage_percentage', 0)
                
                print(f"   📈 Total Stocks: {total_stocks}")
                print(f"   🎯 Target: {target}")
                print(f"   📊 Coverage: {coverage:.1f}%")
                
                # Show sector breakdown
                sectors = data.get('sector_breakdown', {})
                print(f"   🏭 Sectors Found: {len(sectors)}")
                for sector, count in sectors.items():
                    print(f"      • {sector}: {count} stocks")
                
                # Show market cap breakdown
                market_cap = data.get('market_cap_breakdown', {})
                print(f"   💰 Market Cap Breakdown:")
                print(f"      • Micro-cap (<$300M): {market_cap.get('micro_cap', 0)}")
                print(f"      • Small-cap ($300M-$2B): {market_cap.get('small_cap', 0)}")
                
                # Validate SDD alignment
                print(f"   🔍 SDD Alignment Check:")
                if total_stocks >= 1200:
                    print(f"      ✅ Universe size meets SDD target (1,200+)")
                else:
                    print(f"      ⚠️  Universe size below SDD target: {total_stocks}/1,200")
                
                if len(sectors) >= 8:
                    print(f"      ✅ Sufficient sector diversity ({len(sectors)} sectors)")
                else:
                    print(f"      ⚠️  Limited sector diversity: {len(sectors)} sectors")
                    
            else:
                print(f"   ❌ Universe stats failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Universe stats error: {e}")
        
        print()
        
        # ===== TEST 3: Get Some Actual Stocks =====
        print("📋 TEST 3: Sample Small-Cap Stocks")
        print("-" * 40)
        
        try:
            response = await client.get(f"{base_url}/api/stocks?limit=10")
            if response.status_code == 200:
                data = response.json()
                stocks = data.get('stocks', [])
                
                print(f"   📊 Retrieved: {len(stocks)} sample stocks")
                
                for i, stock in enumerate(stocks[:5], 1):
                    symbol = stock.get('symbol', 'N/A')
                    name = stock.get('company_name', 'N/A')[:30]
                    sector = stock.get('sector', 'N/A')
                    market_cap = stock.get('market_cap', 0)
                    
                    print(f"   {i}. {symbol:6s} | {name:30s}")
                    print(f"      💰 ${market_cap:,}" if isinstance(market_cap, (int, float)) else f"      💰 {market_cap}")
                    print(f"      🏭 {sector}")
                    
                    # Validate small-cap
                    if isinstance(market_cap, (int, float)):
                        if 10_000_000 <= market_cap <= 2_000_000_000:
                            print(f"      ✅ Small-cap validated")
                        else:
                            print(f"      ❌ Outside small-cap range")
                    print()
                    
            else:
                print(f"   ❌ Stocks endpoint failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ Stocks endpoint error: {e}")
        
        print()
        
        # ===== TEST 4: Sectors Endpoint =====
        print("🎨 TEST 4: Sector Sentiment Data")
        print("-" * 40)
        
        try:
            response = await client.get(f"{base_url}/api/sectors")
            if response.status_code == 200:
                data = response.json()
                sectors = data.get('sectors', {})
                
                print(f"   📊 Found: {len(sectors)} sectors with sentiment data")
                print(f"   🗂️  Source: {data.get('source', 'unknown')}")
                
                for sector_name, sector_data in list(sectors.items())[:5]:
                    sentiment_score = sector_data.get('sentiment_score', 0)
                    color = sector_data.get('color_classification', 'unknown')
                    stock_count = sector_data.get('stock_count', 0)
                    
                    print(f"   🎯 {sector_name}:")
                    print(f"      Sentiment: {sentiment_score:.2f} ({color})")
                    print(f"      Stocks: {stock_count}")
                    
            else:
                print(f"   ❌ Sectors endpoint failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Sectors endpoint error: {e}")
        
        print()
        
        # ===== TEST 5: Universe Refresh (Optional) =====
        print("🔄 TEST 5: Universe Refresh Capability")
        print("-" * 40)
        
        try:
            response = await client.post(f"{base_url}/api/stocks/universe/refresh")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Refresh triggered: {data.get('status', 'unknown')}")
                print(f"   ⏱️  ETA: {data.get('estimated_completion', 'unknown')}")
            else:
                print(f"   ❌ Universe refresh failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ Universe refresh error: {e}")
    
    print()
    print("🏁 REAL API TESTING COMPLETE")
    print("📋 Summary: Testing actual production FastAPI endpoints")
    print("🎯 Focus: Small-cap universe and sector sentiment data")

if __name__ == "__main__":
    print("⚠️  MAKE SURE FastAPI server is running on localhost:8000")
    print("   Start with: python main.py")
    print()
    asyncio.run(test_real_api_endpoints()) 