-- Add weighted sentiment score column to 3D sector table
ALTER TABLE IF EXISTS sector_sentiment_3d
ADD COLUMN IF NOT EXISTS weighted_sentiment_score FLOAT;

-- Optional: future index if needed for analytics (not required now)
-- CREATE INDEX IF NOT EXISTS idx_sector_sentiment_3d_weighted ON sector_sentiment_3d(weighted_sentiment_score);

