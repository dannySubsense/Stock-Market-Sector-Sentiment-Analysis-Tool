"""
Sector Data Service

Database service for sector calculations with in-database filtering.
Applies gap, volume, and price filters directly in SQL queries for efficiency.
"""

from typing import Dict, List
import logging
import sqlalchemy
from core.database import SessionLocal
from .sector_filters import SectorFilters

logger = logging.getLogger(__name__)


class SectorDataService:
    """Database service for sector calculations"""

    def __init__(self):
        pass

    async def get_filtered_sector_data(
        self, sector: str, filters: SectorFilters
    ) -> List[Dict]:
        """Get sector data with filters applied directly in database"""
        try:
            with SessionLocal() as db:
                query = self._build_filtered_query(sector, filters)
                result = db.execute(sqlalchemy.text(query))

                # Convert to list of dictionaries
                stocks = []
                for row in result.fetchall():
                    stock_data = {
                        "symbol": row[0],
                        "changes_percentage": float(row[1]) if row[1] else 0.0,
                        "volume": int(row[2]) if row[2] else 0,
                        "current_price": float(row[3]) if row[3] else 0.0,
                    }
                    stocks.append(stock_data)

                logger.info(f"Retrieved {len(stocks)} stocks for sector {sector}")
                return stocks

        except Exception as e:
            logger.error(f"Error retrieving filtered sector data for {sector}: {e}")
            return []

    def _build_filtered_query(self, sector: str, filters: SectorFilters) -> str:
        """Build SQL query with filters applied"""
        params = filters.to_sql_params()

        # Select only the latest row per symbol using window function over recorded_at/fmp_timestamp
        query = f"""
        WITH latest AS (
            SELECT
                sp.symbol,
                -- Derive changes_percentage from price/previous_close if missing or null
                COALESCE(
                  NULLIF(sp.changes_percentage, NULL),
                  CASE WHEN sp.previous_close IS NOT NULL AND sp.previous_close > 0
                       THEN ((sp.price - sp.previous_close) / sp.previous_close) * 100
                       ELSE NULL
                  END
                ) AS changes_percentage,
                sp.volume,
                sp.price,
                ROW_NUMBER() OVER (
                    PARTITION BY sp.symbol
                    ORDER BY sp.fmp_timestamp DESC, sp.recorded_at DESC
                ) AS rn
            FROM stock_prices_1d sp
            JOIN stock_universe su ON sp.symbol = su.symbol
            WHERE su.sector = '{sector}'
              AND su.is_active = true
        )
        SELECT symbol, changes_percentage, volume, price
        FROM latest l
        WHERE l.rn = 1
          AND l.changes_percentage IS NOT NULL
          AND l.changes_percentage >= {params['min_gap']}
          AND l.changes_percentage <= {params['max_gap']}
          AND l.volume >= {params['min_volume']}
        """

        # Add optional volume max filter
        if params.get("max_volume"):
            query += f" AND l.volume <= {params['max_volume']}"

        # Add price filters
        query += f" AND l.price >= {params['min_price']}"

        if params.get("max_price"):
            query += f" AND l.price <= {params['max_price']}"

        # Order by changes_percentage for consistent results
        query += " ORDER BY l.changes_percentage DESC"

        return query
