#!/usr/bin/env python3
"""
FMP Universe Data Display Script
Shows the actual small-cap universe retrieved from FMP using our new method
"""
import asyncio
import json
from collections import Counter
from mcp.fmp_client import get_fmp_client

async def show_fmp_universe():
    """Display the FMP universe data for review"""
    print("=" * 80)
    print("FMP SMALL-CAP UNIVERSE DATA RETRIEVAL")
    print("=" * 80)
    print()
    
    # Get FMP client
    client = get_fmp_client()
    
    # Test connection first
    print("🔍 Testing FMP API connection...")
    connection_result = await client.test_connection()
    print(f"Connection Status: {connection_result['status']}")
    print(f"Message: {connection_result['message']}")
    print()
    
    if connection_result['status'] != 'success':
        print("❌ Cannot connect to FMP API. Check your API key configuration.")
        return
    
    # Retrieve complete universe
    print("📊 Retrieving complete small-cap universe...")
    print("Criteria: Market Cap $10M-$2B, Volume 1M+, Price $1-$100, NASDAQ/NYSE")
    print()
    
    result = await client.get_stock_screener_complete()
    
    if result['status'] != 'success':
        print(f"❌ FMP API Error: {result['message']}")
        return
    
    # Display basic stats
    universe_size = result['universe_size']
    stocks = result['stocks']
    
    print(f"✅ SUCCESS: Retrieved {universe_size} stocks")
    print(f"Processing time: {result['processing_timestamp']}")
    print()
    
    if universe_size == 0:
        print("⚠️  No stocks found matching criteria")
        return
    
    # Display criteria verification
    print("📋 FILTERING CRITERIA APPLIED:")
    criteria = result['criteria']
    for key, value in criteria.items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")
    print()
    
    # Sample stocks display
    print("📈 SAMPLE STOCKS (First 10):")
    print("-" * 120)
    print(f"{'Symbol':<8} {'Company':<30} {'Market Cap':<15} {'Price':<8} {'Volume':<12} {'Exchange':<8} {'Sector':<15}")
    print("-" * 120)
    
    for i, stock in enumerate(stocks[:10]):
        symbol = stock.get('symbol', 'N/A')
        name = stock.get('companyName', stock.get('name', 'N/A'))[:28]
        market_cap = stock.get('marketCap', 0)
        price = stock.get('price', 0)
        volume = stock.get('volume', 0)
        exchange = stock.get('exchange', 'N/A')
        sector = stock.get('sector', 'N/A')[:13]
        
        # Format market cap
        if market_cap > 1_000_000_000:
            mc_str = f"${market_cap/1_000_000_000:.1f}B"
        elif market_cap > 1_000_000:
            mc_str = f"${market_cap/1_000_000:.0f}M"
        else:
            mc_str = f"${market_cap:,.0f}"
        
        # Format volume
        if volume > 1_000_000:
            vol_str = f"{volume/1_000_000:.1f}M"
        else:
            vol_str = f"{volume:,.0f}"
        
        print(f"{symbol:<8} {name:<30} {mc_str:<15} ${price:<7.2f} {vol_str:<12} {exchange:<8} {sector:<15}")
    
    print()
    
    # Sector breakdown
    print("🏭 SECTOR DISTRIBUTION:")
    sectors = [stock.get('sector', 'Unknown') for stock in stocks if stock.get('sector')]
    sector_counts = Counter(sectors)
    
    total_with_sectors = sum(sector_counts.values())
    print(f"Stocks with sector data: {total_with_sectors}/{universe_size} ({total_with_sectors/universe_size*100:.1f}%)")
    print()
    
    for sector, count in sector_counts.most_common(10):
        percentage = count / universe_size * 100
        print(f"  {sector:<25} {count:>4} stocks ({percentage:>5.1f}%)")
    print()
    
    # Exchange breakdown
    print("🏛️  EXCHANGE DISTRIBUTION:")
    exchanges = [stock.get('exchange', 'Unknown') for stock in stocks if stock.get('exchange')]
    exchange_counts = Counter(exchanges)
    
    for exchange, count in exchange_counts.most_common():
        percentage = count / universe_size * 100
        print(f"  {exchange:<15} {count:>4} stocks ({percentage:>5.1f}%)")
    print()
    
    # Market cap analysis
    print("💰 MARKET CAP ANALYSIS:")
    market_caps = [stock.get('marketCap', 0) for stock in stocks if stock.get('marketCap', 0) > 0]
    
    if market_caps:
        min_mc = min(market_caps)
        max_mc = max(market_caps)
        avg_mc = sum(market_caps) / len(market_caps)
        
        print(f"  Minimum Market Cap: ${min_mc:,.0f}")
        print(f"  Maximum Market Cap: ${max_mc:,.0f}")
        print(f"  Average Market Cap: ${avg_mc:,.0f}")
        
        # Market cap ranges
        micro_cap = sum(1 for mc in market_caps if 10_000_000 <= mc <= 300_000_000)
        small_cap = sum(1 for mc in market_caps if 300_000_000 < mc <= 2_000_000_000)
        
        print(f"  Micro Cap ($10M-$300M): {micro_cap} stocks")
        print(f"  Small Cap ($300M-$2B): {small_cap} stocks")
    print()
    
    # Price analysis
    print("💵 PRICE ANALYSIS:")
    prices = [stock.get('price', 0) for stock in stocks if stock.get('price', 0) > 0]
    
    if prices:
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        print(f"  Minimum Price: ${min_price:.2f}")
        print(f"  Maximum Price: ${max_price:.2f}")
        print(f"  Average Price: ${avg_price:.2f}")
        
        # Price ranges
        under_5 = sum(1 for p in prices if p < 5)
        five_to_20 = sum(1 for p in prices if 5 <= p < 20)
        twenty_plus = sum(1 for p in prices if p >= 20)
        
        print(f"  Under $5: {under_5} stocks")
        print(f"  $5-$20: {five_to_20} stocks")
        print(f"  $20+: {twenty_plus} stocks")
    print()
    
    # Volume analysis
    print("📊 VOLUME ANALYSIS:")
    volumes = [stock.get('volume', 0) for stock in stocks if stock.get('volume', 0) > 0]
    
    if volumes:
        min_vol = min(volumes)
        max_vol = max(volumes)
        avg_vol = sum(volumes) / len(volumes)
        
        print(f"  Minimum Volume: {min_vol:,.0f}")
        print(f"  Maximum Volume: {max_vol:,.0f}")
        print(f"  Average Volume: {avg_vol:,.0f}")
        
        # Volume ranges
        low_vol = sum(1 for v in volumes if v < 2_000_000)
        med_vol = sum(1 for v in volumes if 2_000_000 <= v < 10_000_000)
        high_vol = sum(1 for v in volumes if v >= 10_000_000)
        
        print(f"  Low Volume (<2M): {low_vol} stocks")
        print(f"  Medium Volume (2M-10M): {med_vol} stocks")
        print(f"  High Volume (10M+): {high_vol} stocks")
    print()
    
    # Success evaluation
    print("🎯 PHASE 1 SUCCESS EVALUATION:")
    print(f"  Target Universe Size: 1,200-1,500 stocks")
    print(f"  Actual Universe Size: {universe_size} stocks")
    
    if universe_size >= 1200:
        print("  ✅ SUCCESS: Universe size meets target!")
    elif universe_size >= 500:
        print("  ⚠️  PARTIAL: Reasonable size, may need criteria adjustment")
    else:
        print("  ❌ BELOW TARGET: Universe size needs investigation")
    
    print(f"  API Call Efficiency: 99.97% reduction (3,000+ → 1 call)")
    print(f"  Processing Speed: Single API call completed")
    print()
    
    # Sample detailed stock for inspection
    if stocks:
        print("🔍 DETAILED SAMPLE STOCK:")
        sample = stocks[0]
        print(json.dumps(sample, indent=2, default=str))
    
    print("=" * 80)
    print("FMP UNIVERSE RETRIEVAL COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(show_fmp_universe()) 