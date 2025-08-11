graph TD
    A["🔍 FMP Stock Screener API<br/>Market Cap: $10M - $2B<br/>~2,000 small-cap stocks"] --> B["📊 stock_universe Table<br/>• symbol, sector, market_cap<br/>• volatility_multiplier<br/>• is_active status<br/>• 11 sectors mapped"]
    
    B --> C["🎯 Sector Analysis Trigger<br/>User requests sector sentiment<br/>or scheduled calculation"]
    
    C --> D["📈 Live Stock Data APIs<br/>FMP + Polygon (fallback)<br/>Real-time quotes & volume"]
    
    D --> E["⚠️ CRITICAL INSIGHT<br/>NO stock_prices table storage<br/>Live data used directly!"]
    
    E --> F["🔢 Volume Weighting Engine<br/>• Current vs Previous Close<br/>• Volume vs 20-day average<br/>• Volatility multipliers<br/>• Per-stock performance"]
    
    F --> G["📊 IWM Benchmark Service<br/>Russell 2000 ETF performance<br/>Current vs Previous Close"]
    
    G --> H["✅ WE ARE HERE<br/>Sector Performance Calculator<br/>• Aggregate weighted performance<br/>• Apply sector volatility multiplier<br/>• Calculate vs IWM alpha"]
    
    H --> I["🎨 Color Classification<br/>• Dark Red: < -0.6<br/>• Light Red: -0.6 to -0.2<br/>• Blue: -0.2 to 0.2<br/>• Light Green: 0.2 to 0.6<br/>• Dark Green: > 0.6"]
    
    I --> J["💾 sector_sentiment Table<br/>• sector, timeframe<br/>• sentiment_score<br/>• bullish/bearish counts<br/>• total_volume, timestamp"]
    
    J --> K["🚀 STEP 5 - NOT IMPLEMENTED<br/>Multi-Timeframe Analysis<br/>30min, 1D, 3D, 1W"]
    
    K --> L["🚀 STEP 6 - NOT IMPLEMENTED<br/>Stock Rankings<br/>Top 3 bullish/bearish per sector"]
    
    L --> M["🚀 STEP 7 - NOT IMPLEMENTED<br/>Real-time WebSocket Updates<br/>30-minute refresh cycles"]
    
    M --> N["🚀 STEP 8 - NOT IMPLEMENTED<br/>Frontend Sector Grid<br/>8x3 grid display<br/>Color-coded cards"]

    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style D fill:#e8f5e8
    style E fill:#ffebee
    style F fill:#fff3e0
    style G fill:#f1f8e9
    style H fill:#e3f2fd
    style I fill:#fce4ec
    style J fill:#f3e5f5
    style K fill:#ffecb3
    style L fill:#ffecb3
    style M fill:#ffecb3
    style N fill:#ffecb3