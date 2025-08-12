-- Views to separate read concerns for daily prices
-- 1) stock_prices_daily_latest: latest row per symbol (quote-like)
-- 2) stock_prices_daily_ohlc: rows with OHLC close_price present (historical bars)

-- Latest-per-symbol view using window function (prioritizes fmp_timestamp then recorded_at)
CREATE OR REPLACE VIEW stock_prices_daily_latest AS
WITH ranked AS (
  SELECT
    sp.*,
    ROW_NUMBER() OVER (
      PARTITION BY sp.symbol
      ORDER BY sp.fmp_timestamp DESC, sp.recorded_at DESC
    ) AS rn
  FROM stock_prices_1d sp
)
SELECT
  symbol,
  name,
  price,
  changes_percentage,
  change,
  day_low,
  day_high,
  year_high,
  year_low,
  market_cap,
  price_avg_50,
  price_avg_200,
  exchange,
  volume,
  avg_volume,
  open_price,
  previous_close,
  eps,
  pe,
  earnings_announcement,
  shares_outstanding,
  fmp_timestamp,
  recorded_at
FROM ranked
WHERE rn = 1;

-- OHLC-only historical rows
CREATE OR REPLACE VIEW stock_prices_daily_ohlc AS
SELECT
  symbol,
  open_price,
  day_high   AS high_price,
  day_low    AS low_price,
  price      AS close_price,
  volume,
  fmp_timestamp,
  recorded_at
FROM stock_prices_1d
WHERE price IS NOT NULL;


