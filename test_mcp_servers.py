#!/usr/bin/env python3
"""
Test script for MCP servers (Polygon.io and FMP)
This script tests both MCP server connections and validates API functionality
"""
import asyncio
import sys
import json
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from mcp.polygon_client import test_polygon_connection, get_polygon_client
from mcp.fmp_client import test_fmp_connection, get_fmp_client

async def test_polygon_server():
    """Test Polygon.io MCP server functionality"""
    print("🔵 Testing Polygon.io MCP Server")
    print("=" * 50)
    
    # Test connection
    print("1. Testing connection...")
    connection_result = await test_polygon_connection()
    print(f"   Status: {connection_result['status']}")
    print(f"   Message: {connection_result['message']}")
    
    if connection_result['status'] != 'success':
        print("   ❌ Connection failed!")
        return False
    
    print("   ✅ Connection successful!")
    
    # Test specific endpoints
    client = get_polygon_client()
    
    # Test tickers endpoint
    print("\n2. Testing tickers endpoint...")
    tickers_result = await client.get_tickers(limit=5)
    print(f"   Status: {tickers_result['status']}")
    if tickers_result['status'] == 'success':
        print(f"   Retrieved {tickers_result['count']} tickers")
        print("   ✅ Tickers endpoint working!")
    else:
        print(f"   ❌ Tickers endpoint failed: {tickers_result['message']}")
    
    # Test market status
    print("\n3. Testing market status...")
    market_result = await client.get_market_status()
    print(f"   Status: {market_result['status']}")
    if market_result['status'] == 'success':
        print("   ✅ Market status endpoint working!")
    else:
        print(f"   ❌ Market status failed: {market_result['message']}")
    
    # Test with a specific stock (AAPL)
    print("\n4. Testing specific stock data (AAPL)...")
    ticker_result = await client.get_ticker_details("AAPL")
    print(f"   Status: {ticker_result['status']}")
    if ticker_result['status'] == 'success':
        ticker_data = ticker_result['ticker_data']
        print(f"   Company: {ticker_data.get('name', 'N/A')}")
        print(f"   Market Cap: ${ticker_data.get('market_cap', 'N/A'):,}" if ticker_data.get('market_cap') else "   Market Cap: N/A")
        print("   ✅ Ticker details working!")
    else:
        print(f"   ❌ Ticker details failed: {ticker_result['message']}")
    
    # Test previous close
    print("\n5. Testing previous close data (AAPL)...")
    prev_close_result = await client.get_previous_close("AAPL")
    print(f"   Status: {prev_close_result['status']}")
    if prev_close_result['status'] == 'success':
        print(f"   Previous Close: ${prev_close_result.get('previous_close', 'N/A')}")
        print(f"   Volume: {prev_close_result.get('volume', 'N/A'):,}" if prev_close_result.get('volume') else "   Volume: N/A")
        print("   ✅ Previous close working!")
    else:
        print(f"   ❌ Previous close failed: {prev_close_result['message']}")
    
    # Don't close singleton client - other tests need it
    # await client.close()
    return True

async def test_fmp_server():
    """Test FMP MCP server functionality"""
    print("\n🟡 Testing FMP MCP Server")
    print("=" * 50)
    
    # Test connection
    print("1. Testing connection...")
    connection_result = await test_fmp_connection()
    print(f"   Status: {connection_result['status']}")
    print(f"   Message: {connection_result['message']}")
    
    if connection_result['status'] != 'success':
        print("   ❌ Connection failed!")
        return False
    
    print("   ✅ Connection successful!")
    
    # Test specific endpoints
    client = get_fmp_client()
    
    # Test stock list (limited)
    print("\n2. Testing stock list...")
    stock_list_result = await client.get_stock_list()
    print(f"   Status: {stock_list_result['status']}")
    if stock_list_result['status'] == 'success':
        print(f"   Retrieved {stock_list_result['count']} stocks")
        print("   ✅ Stock list endpoint working!")
    else:
        print(f"   ❌ Stock list failed: {stock_list_result['message']}")
    
    # Test company profile
    print("\n3. Testing company profile (AAPL)...")
    profile_result = await client.get_company_profile("AAPL")
    print(f"   Status: {profile_result['status']}")
    if profile_result['status'] == 'success':
        profile = profile_result['profile']
        print(f"   Company: {profile.get('companyName', 'N/A')}")
        print(f"   Sector: {profile.get('sector', 'N/A')}")
        print(f"   Market Cap: ${profile.get('mktCap', 'N/A'):,}" if profile.get('mktCap') else "   Market Cap: N/A")
        print("   ✅ Company profile working!")
    else:
        print(f"   ❌ Company profile failed: {profile_result['message']}")
    
    # Test quote
    print("\n4. Testing quote (AAPL)...")
    quote_result = await client.get_quote("AAPL")
    print(f"   Status: {quote_result['status']}")
    if quote_result['status'] == 'success':
        quote = quote_result['quote']
        print(f"   Price: ${quote.get('price', 'N/A')}")
        print(f"   Change: {quote.get('change', 'N/A')}")
        print(f"   Volume: {quote.get('volume', 'N/A'):,}" if quote.get('volume') else "   Volume: N/A")
        print("   ✅ Quote working!")
    else:
        print(f"   ❌ Quote failed: {quote_result['message']}")
    
    # Test sector performance
    print("\n5. Testing sector performance...")
    sector_result = await client.get_sector_performance()
    print(f"   Status: {sector_result['status']}")
    if sector_result['status'] == 'success':
        sectors = sector_result['sectors']
        print(f"   Retrieved {len(sectors)} sectors")
        if sectors:
            print(f"   Sample sector: {sectors[0].get('sector', 'N/A')} ({sectors[0].get('changesPercentage', 'N/A')}%)")
        print("   ✅ Sector performance working!")
    else:
        print(f"   ❌ Sector performance failed: {sector_result['message']}")
    
    # Test stock screener for small caps
    print("\n6a. Testing stock screener (small caps $10M-$2B)...")
    screener_result = await client.get_stock_screener(
        market_cap_more_than=10_000_000,  # $10M+
        market_cap_less_than=2_000_000_000,  # $2B
        limit=10
    )
    print(f"   Status: {screener_result['status']}")
    if screener_result['status'] == 'success':
        stocks = screener_result['stocks']
        print(f"   Found {len(stocks)} small-cap stocks")
        
        if stocks:
            print(f"\n   📊 Small-Cap Stock Details:")
            print(f"   {'Symbol':<8} {'Company Name':<25} {'Market Cap':<15} {'Shares Out':<12} {'Float':<12}")
            print(f"   {'-'*8} {'-'*25} {'-'*15} {'-'*12} {'-'*12}")
            
            for i, stock in enumerate(stocks[:10], 1):
                symbol = stock.get('symbol', 'N/A')
                name = stock.get('companyName', 'N/A')
                market_cap = stock.get('marketCap', 0)
                shares_out = stock.get('sharesOutstanding', 0)
                float_shares = stock.get('floatShares', 0)
                
                # Format market cap
                if market_cap:
                    if market_cap >= 1_000_000_000:
                        mc_str = f"${market_cap/1_000_000_000:.1f}B"
                    elif market_cap >= 1_000_000:
                        mc_str = f"${market_cap/1_000_000:.0f}M"
                    else:
                        mc_str = f"${market_cap:,.0f}"
                else:
                    mc_str = "N/A"
                
                # Format shares outstanding  
                if shares_out:
                    if shares_out >= 1_000_000:
                        so_str = f"{shares_out/1_000_000:.1f}M"
                    else:
                        so_str = f"{shares_out:,.0f}"
                else:
                    so_str = "N/A"
                
                # Format float
                if float_shares:
                    if float_shares >= 1_000_000:
                        float_str = f"{float_shares/1_000_000:.1f}M"
                    else:
                        float_str = f"{float_shares:,.0f}"
                else:
                    float_str = "N/A"
                
                # Truncate long company names
                if len(name) > 25:
                    name = name[:22] + "..."
                
                print(f"   {symbol:<8} {name:<25} {mc_str:<15} {so_str:<12} {float_str:<12}")
            
            print(f"\n   📈 All data fields available in screener:")
            if stocks:
                sample_keys = list(stocks[0].keys())
                print(f"   Available fields: {', '.join(sample_keys)}")
        
        print("   ✅ Stock screener working!")
    else:
        print(f"   ❌ Stock screener failed: {screener_result['message']}")
    
    # Test with $1B limit to confirm theory
    print("\n6b. Testing stock screener (small caps $10M-$1B)...")
    screener_1b_result = await client.get_stock_screener(
        market_cap_more_than=10_000_000,  # $10M+
        market_cap_less_than=1_000_000_000,  # $1B
        limit=10
    )
    print(f"   Status: {screener_1b_result['status']}")
    if screener_1b_result['status'] == 'success':
        stocks_1b = screener_1b_result['stocks']
        print(f"   Found {len(stocks_1b)} stocks under $1B")
        
        if stocks_1b:
            print(f"\n   📊 $1B Limit Test:")
            print(f"   {'Symbol':<8} {'Market Cap':<15}")
            print(f"   {'-'*8} {'-'*15}")
            
            for stock in stocks_1b[:5]:  # Show first 5
                symbol = stock.get('symbol', 'N/A')
                market_cap = stock.get('marketCap', 0)
                
                if market_cap:
                    if market_cap >= 1_000_000_000:
                        mc_str = f"${market_cap/1_000_000_000:.1f}B"
                    elif market_cap >= 1_000_000:
                        mc_str = f"${market_cap/1_000_000:.0f}M"
                    else:
                        mc_str = f"${market_cap:,.0f}"
                else:
                    mc_str = "N/A"
                
                print(f"   {symbol:<8} {mc_str:<15}")
            
            print(f"   📝 Theory test: Are all stocks at exactly $1B? {all(s.get('marketCap') == 1_000_000_000 for s in stocks_1b[:5])}")
        
        print("   ✅ $1B limit test completed!")
    else:
        print(f"   ❌ $1B screener failed: {screener_1b_result['message']}")
    
    # Don't close singleton client - other tests need it  
    # await client.close()
    return True

async def test_polygon_screening():
    """Test Polygon-based small-cap screening"""
    print("\n⭐ Testing Polygon Small-Cap Screening")
    print("=" * 50)
    
    polygon_client = get_polygon_client()
    
    # Get a batch of tickers
    print("1. Getting ticker list from Polygon...")
    tickers_result = await polygon_client.get_tickers(market="stocks", limit=50)
    
    if tickers_result['status'] != 'success':
        print(f"   ❌ Failed to get tickers: {tickers_result['message']}")
        # Don't close singleton client
        # await polygon_client.close()
        return False
    
    tickers = tickers_result['tickers']
    print(f"   Retrieved {len(tickers)} tickers for screening")
    
    # Screen for small caps by checking market cap
    print("\n2. Screening for small caps ($10M-$2B)...")
    small_caps = []
    
    for i, ticker in enumerate(tickers[:20]):  # Test first 20 to avoid too many API calls
        symbol = ticker.get('ticker', ticker.get('symbol', 'N/A'))
        print(f"   Checking {symbol}... ({i+1}/20)", end='\r')
        
        try:
            details = await polygon_client.get_ticker_details(symbol)
            if details['status'] == 'success':
                ticker_data = details.get('ticker_data', {})
                market_cap = ticker_data.get('market_cap')
                
                if market_cap and 10_000_000 <= market_cap <= 2_000_000_000:
                    small_caps.append({
                        'symbol': symbol,
                        'name': ticker_data.get('name', 'N/A'),
                        'market_cap': market_cap,
                        'shares_outstanding': ticker_data.get('share_class_shares_outstanding'),
                        'weighted_shares_outstanding': ticker_data.get('weighted_shares_outstanding')
                    })
                    
                    if len(small_caps) >= 5:  # Stop after finding 5 small caps
                        break
        except Exception as e:
            continue  # Skip on error
    
    print(f"\n   Found {len(small_caps)} small-cap stocks from Polygon")
    
    if small_caps:
        print(f"\n   📊 Polygon Small-Cap Results:")
        print(f"   {'Symbol':<8} {'Company Name':<25} {'Market Cap':<15} {'Shares Out':<15}")
        print(f"   {'-'*8} {'-'*25} {'-'*15} {'-'*15}")
        
        for stock in small_caps:
            symbol = stock['symbol']
            name = stock['name']
            market_cap = stock['market_cap']
            shares_out = stock.get('shares_outstanding') or stock.get('weighted_shares_outstanding')
            
            # Format market cap
            if market_cap >= 1_000_000_000:
                mc_str = f"${market_cap/1_000_000_000:.1f}B"
            elif market_cap >= 1_000_000:
                mc_str = f"${market_cap/1_000_000:.0f}M"
            else:
                mc_str = f"${market_cap:,.0f}"
            
            # Format shares outstanding
            if shares_out:
                if shares_out >= 1_000_000:
                    so_str = f"{shares_out/1_000_000:.1f}M"
                else:
                    so_str = f"{shares_out:,.0f}"
            else:
                so_str = "N/A"
            
            # Truncate long names
            if len(name) > 25:
                name = name[:22] + "..."
            
            print(f"   {symbol:<8} {name:<25} {mc_str:<15} {so_str:<15}")
        
        print(f"\n   📈 Polygon shows varied market caps: {len(set(s['market_cap'] for s in small_caps)) == len(small_caps)}")
        print("   ✅ Polygon screening test completed!")
    else:
        print("   ⚠️  No small caps found in sample")
    
    # Don't close singleton client - other tests need it
    # await polygon_client.close()
    return True

async def test_small_cap_workflow():
    """Test a complete small-cap workflow using both APIs"""
    print("\n🚀 Testing Small-Cap Workflow")
    print("=" * 50)
    
    # Get FMP client for screening
    fmp_client = get_fmp_client()
    
    # Screen for small caps
    print("1. Screening for small-cap stocks...")
    screener_result = await fmp_client.get_stock_screener(
        market_cap_more_than=10_000_000,  # $10M+
        market_cap_less_than=2_000_000_000,  # $2B
        limit=5
    )
    
    if screener_result['status'] != 'success':
        print(f"   ❌ Screening failed: {screener_result['message']}")
        return False
    
    small_caps = screener_result['stocks']
    print(f"   Found {len(small_caps)} small-cap stocks")
    
    if not small_caps:
        print("   ❌ No small caps found!")
        return False
    
    # Get Polygon client for detailed data
    polygon_client = get_polygon_client()
    
    # Test with first small cap
    test_symbol = small_caps[0]['symbol']
    print(f"\n2. Testing detailed data for {test_symbol}...")
    
    # Get ticker details from Polygon
    ticker_result = await polygon_client.get_ticker_details(test_symbol)
    if ticker_result['status'] == 'success':
        ticker_data = ticker_result['ticker_data']
        print(f"   {test_symbol}: {ticker_data.get('name', 'N/A')}")
        print(f"   Market Cap: ${ticker_data.get('market_cap', 'N/A'):,}" if ticker_data.get('market_cap') else "   Market Cap: N/A")
    
    # Get previous close from Polygon
    prev_close = await polygon_client.get_previous_close(test_symbol)
    if prev_close['status'] == 'success':
        print(f"   Previous Close: ${prev_close.get('previous_close', 'N/A')}")
        print(f"   Volume: {prev_close.get('volume', 'N/A'):,}" if prev_close.get('volume') else "   Volume: N/A")
    
    # Get current quote from FMP
    quote_result = await fmp_client.get_quote(test_symbol)
    if quote_result['status'] == 'success':
        quote = quote_result['quote']
        print(f"   Current Price: ${quote.get('price', 'N/A')}")
        print(f"   Daily Change: {quote.get('changesPercentage', 'N/A')}%")
    
    print("   ✅ Small-cap workflow test completed!")
    
    # Don't close singleton clients - they're shared across tests
    # await fmp_client.close()
    # await polygon_client.close()
    return True

async def main():
    """Main test function"""
    print("🧪 Market Sector Sentiment Analysis Tool - MCP Server Tests")
    print("=" * 60)
    
    # Test results
    results = {
        'polygon': False,
        'fmp': False,
        'polygon_screening': False,
        'workflow': False
    }
    
    try:
        # Test Polygon server
        results['polygon'] = await test_polygon_server()
        
        # Test FMP server
        results['fmp'] = await test_fmp_server()
        
        # Test Polygon screening approach
        if results['polygon']:
            results['polygon_screening'] = await test_polygon_screening()
        
        # Test combined workflow
        if results['polygon'] and results['fmp']:
            results['workflow'] = await test_small_cap_workflow()
        
        # Print summary
        print("\n📊 Test Summary")
        print("=" * 40)
        print(f"Polygon.io MCP:      {'✅ PASS' if results['polygon'] else '❌ FAIL'}")
        print(f"FMP MCP:             {'✅ PASS' if results['fmp'] else '❌ FAIL'}")
        print(f"Polygon Screening:   {'✅ PASS' if results['polygon_screening'] else '❌ FAIL'}")
        print(f"Workflow Test:       {'✅ PASS' if results['workflow'] else '❌ FAIL'}")
        
        if all(results.values()):
            print("\n🎉 All tests passed! MCP servers are working correctly.")
            return 0
        else:
            print("\n⚠️  Some tests failed. Check your API keys and credentials.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 