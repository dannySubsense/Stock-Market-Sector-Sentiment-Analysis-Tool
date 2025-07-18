"""
Stock Universe Builder - Slice 1A Implementation
Builds and maintains the 1,500 small-cap stock universe
Market Cap Focus: $10M - $2B (micro-cap to small-cap)
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import asyncio
import logging
from datetime import datetime, timedelta

from core.database import SessionLocal
from models.stock_universe import StockUniverse
from models.stock_data import StockData
from mcp.polygon_client import get_polygon_client
from mcp.fmp_client import get_fmp_client
from config.volatility_weights import get_static_weights, get_weight_for_sector

logger = logging.getLogger(__name__)

# Sector classification mapping from SDD (volatility multipliers now from config)
SECTOR_MAPPING = {
    "technology": {
        "keywords": [
            "software",
            "technology",
            "ai",
            "artificial intelligence",
            "computer",
            "internet",
            "semiconductor",
        ],
        "gap_frequency": "high",
    },
    "healthcare": {
        "keywords": [
            "healthcare",
            "biotech",
            "pharmaceutical",
            "medical",
            "drug",
            "therapeutics",
            "clinical",
        ],
        "gap_frequency": "extreme",
    },
    "energy": {
        "keywords": [
            "energy",
            "oil",
            "gas",
            "solar",
            "renewable",
            "mining",
            "coal",
            "petroleum",
        ],
        "gap_frequency": "moderate",
    },
    "financial": {
        "keywords": [
            "bank",
            "financial",
            "insurance",
            "credit",
            "lending",
            "fintech",
            "payment",
        ],
        "gap_frequency": "moderate",
    },
    "consumer_discretionary": {
        "keywords": [
            "retail",
            "consumer",
            "restaurant",
            "entertainment",
            "gaming",
            "media",
            "clothing",
        ],
        "gap_frequency": "high",
    },
    "industrials": {
        "keywords": [
            "industrial",
            "manufacturing",
            "aerospace",
            "defense",
            "transportation",
            "logistics",
        ],
        "gap_frequency": "low",
    },
    "materials": {
        "keywords": [
            "materials",
            "steel",
            "copper",
            "aluminum",
            "chemicals",
            "construction",
        ],
        "gap_frequency": "low",
    },
    "utilities": {
        "keywords": [
            "utilities",
            "electric",
            "water",
            "gas",
            "power",
            "energy infrastructure",
        ],
        "gap_frequency": "very_low",
    },
}


class UniverseBuilder:
    """
    Builds and maintains the 1,500 small-cap stock universe
    Selection Criteria from SDD:
    - Market Cap: $10M - $2B
    - Min Daily Volume: 1M+ shares
    - Min Price: $2.00
    - Exchange: NASDAQ/NYSE
    """

    def __init__(self):
        self.polygon_client = get_polygon_client()
        self.fmp_client = get_fmp_client()
        self.target_universe_size = 1500

        # Universe selection criteria - Optimized for sector sentiment analysis
        self.market_cap_min = 10_000_000  # $10M
        self.market_cap_max = 2_000_000_000  # $2B
        self.min_daily_volume = 100_000  # 100K shares (liquidity optimized)
        self.min_price = None  # No minimum price for sentiment analysis
        self.max_price = None  # No maximum price for sentiment analysis
        self.valid_exchanges = ["NASDAQ", "NYSE"]  # Remove NYSEARCA (ETFs)

    def get_fmp_screening_criteria(self) -> Dict[str, Any]:
        """
        Get FMP API screening criteria for sector sentiment analysis
        
        Returns:
            Dict: FMP API parameters for stock screening
        """
        criteria = {
            "marketCapMoreThan": str(self.market_cap_min),
            "marketCapLowerThan": str(self.market_cap_max),
            "volumeMoreThan": str(self.min_daily_volume),
            "exchange": ",".join(self.valid_exchanges),
            "isActivelyTrading": "true",
            "limit": "10000",  # Get complete universe
        }
        
        # Add price filters only if specified
        if self.min_price is not None:
            criteria["priceMoreThan"] = str(self.min_price)
        if self.max_price is not None:
            criteria["priceLowerThan"] = str(self.max_price)
            
        return criteria

    async def get_fmp_universe(self) -> Dict[str, Any]:
        """
        Get complete universe using FMP screener
        
        Returns:
            Dict: Universe data from FMP
        """
        criteria = self.get_fmp_screening_criteria()
        return await self.fmp_client.get_stock_screener(criteria)

    async def build_daily_universe(self) -> Dict[str, Any]:
        """Build the complete daily universe from scratch"""
        try:
            logger.info("Starting daily universe build...")

            # Step 1: Get all available stocks from multiple sources
            all_stocks = await self._get_all_available_stocks()
            logger.info(f"Retrieved {len(all_stocks)} total stocks")

            # Step 2: Apply filtering criteria
            filtered_stocks = await self._apply_universe_filters(all_stocks)
            logger.info(f"After filtering: {len(filtered_stocks)} qualifying stocks")

            # Step 3: Classify stocks into sectors
            classified_stocks = await self._classify_stocks_by_sector(filtered_stocks)
            logger.info(f"Classified {len(classified_stocks)} stocks into sectors")

            # Step 4: Optimize universe size (target 1,500 stocks)
            final_universe = await self._optimize_universe_size(classified_stocks)
            logger.info(f"Final universe size: {len(final_universe)} stocks")

            # Step 5: Update database
            update_result = await self._update_stock_universe_table(final_universe)

            return {
                "status": "success",
                "universe_size": len(final_universe),
                "sectors": self._get_sector_breakdown(final_universe),
                "update_result": update_result,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to build universe: {e}")
            return {"status": "error", "message": str(e), "universe_size": 0}

    async def _get_all_available_stocks(self) -> List[Dict[str, Any]]:
        """Get stocks from both Polygon and FMP"""
        stocks = []

        try:
            # Get from FMP (more comprehensive list)
            fmp_result = await self.fmp_client.get_stock_list()
            print(f"FMP API Response: {fmp_result}")
            if fmp_result["status"] == "success":
                print(f"FMP Stocks Count: {len(fmp_result['stocks'])}")
                print(f"FMP First 3 Stocks: {fmp_result['stocks'][:3]}")
                stocks.extend(fmp_result["stocks"])
                logger.info(f"Retrieved {len(fmp_result['stocks'])} stocks from FMP")

            # Get from Polygon (for validation and additional data)
            polygon_result = await self.polygon_client.get_tickers(
                market="stocks", limit=5000
            )
            if polygon_result["status"] == "success":
                # Merge with FMP data (deduplicate by symbol)
                existing_symbols = {stock.get("symbol", "") for stock in stocks}
                for ticker in polygon_result["tickers"]:
                    symbol = ticker.get("ticker", "")
                    if symbol and symbol not in existing_symbols:
                        # Convert Polygon format to match FMP format
                        stock_data = {
                            "symbol": symbol,
                            "name": ticker.get("name", ""),
                            "exchange": ticker.get("primary_exchange", ""),
                            "type": ticker.get("type", ""),
                            "market": ticker.get("market", ""),
                        }
                        stocks.append(stock_data)

                logger.info(
                    f"Added {len(polygon_result['tickers'])} additional stocks from Polygon"
                )

        except Exception as e:
            logger.error(f"Error getting stocks: {e}")

        return stocks

    async def _apply_universe_filters(
        self, stocks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply SDD filtering criteria to stocks"""
        filtered_stocks = []

        for stock in stocks:
            try:
                symbol = stock.get("symbol", "").upper()
                if not symbol:
                    continue

                # Get detailed quote data for filtering
                quote_data = await self._get_stock_quote_data(symbol)
                if not quote_data:
                    continue

                # Extract filtering criteria
                market_cap = quote_data.get("marketCap", 0)
                price = quote_data.get("price", 0)
                volume = quote_data.get("volume", 0)
                avg_volume = quote_data.get(
                    "avgVolume", volume
                )  # Use current volume if avg not available
                exchange = stock.get("exchange", "").upper()

                # Apply filters
                if self._passes_universe_filters(
                    market_cap, price, avg_volume, exchange
                ):
                    stock_info = {
                        "symbol": symbol,
                        "company_name": stock.get("name", ""),
                        "exchange": exchange,
                        "market_cap": market_cap,
                        "current_price": price,
                        "avg_daily_volume": avg_volume,
                        "volume": volume,
                    }
                    filtered_stocks.append(stock_info)

                # Rate limiting to avoid API overload
                if len(filtered_stocks) % 50 == 0:
                    await asyncio.sleep(1)

            except Exception as e:
                logger.warning(
                    f"Error processing stock {stock.get('symbol', 'unknown')}: {e}"
                )
                continue

        return filtered_stocks

    def _passes_universe_filters(
        self, market_cap: float, price: float, volume: float, exchange: str
    ) -> bool:
        """Check if stock passes all universe filtering criteria"""
        return (
            self.market_cap_min <= market_cap <= self.market_cap_max
            and price >= self.min_price
            and price <= self.max_price
            and volume >= self.min_daily_volume
            and exchange in self.valid_exchanges
        )

    async def _get_stock_quote_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get quote data for filtering"""
        try:
            # Try FMP first (has market cap data)
            fmp_result = await self.fmp_client.get_quote(symbol)
            if fmp_result["status"] == "success" and fmp_result["quote"]:
                quote = fmp_result["quote"]
                return {
                    "price": quote.get("price", 0),
                    "marketCap": quote.get("marketCap", 0),
                    "volume": quote.get("volume", 0),
                    "avgVolume": quote.get("avgVolume", 0),
                }
        except Exception as e:
            logger.warning(f"Error getting quote for {symbol}: {e}")

        return None

    async def _classify_stocks_by_sector(
        self, stocks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Classify stocks into 8 sectors based on business description"""
        classified_stocks = []

        for stock in stocks:
            try:
                symbol = stock["symbol"]

                # Get company profile for sector classification
                sector = await self._determine_stock_sector(symbol)

                stock_info = stock.copy()
                stock_info["sector"] = sector
                stock_info["volatility_multiplier"] = SECTOR_MAPPING[sector][
                    "volatility_multiplier"
                ]
                stock_info["gap_frequency"] = SECTOR_MAPPING[sector]["gap_frequency"]

                classified_stocks.append(stock_info)

                # Rate limiting
                if len(classified_stocks) % 30 == 0:
                    await asyncio.sleep(1)

            except Exception as e:
                logger.warning(
                    f"Error classifying stock {stock.get('symbol', 'unknown')}: {e}"
                )
                continue

        return classified_stocks

    async def _determine_stock_sector(self, symbol: str) -> str:
        """Determine sector for a stock based on company profile"""
        try:
            # Get company profile
            profile_result = await self.fmp_client.get_company_profile(symbol)
            if profile_result["status"] == "success" and profile_result["profile"]:
                profile = profile_result["profile"]

                # Check sector from profile first
                profile_sector = profile.get("sector", "").lower()
                industry = profile.get("industry", "").lower()
                description = profile.get("description", "").lower()

                # Map to our 8 sectors
                combined_text = f"{profile_sector} {industry} {description}"

                for sector, config in SECTOR_MAPPING.items():
                    for keyword in config["keywords"]:
                        if keyword.lower() in combined_text:
                            return sector

                # Default classification based on profile sector
                if "technology" in profile_sector or "software" in profile_sector:
                    return "technology"
                elif "health" in profile_sector or "biotech" in profile_sector:
                    return "healthcare"
                elif "energy" in profile_sector:
                    return "energy"
                elif "financial" in profile_sector:
                    return "financial"
                elif "consumer" in profile_sector:
                    return "consumer_discretionary"
                elif "industrial" in profile_sector:
                    return "industrials"
                elif "materials" in profile_sector:
                    return "materials"
                else:
                    return "utilities"  # Default fallback

        except Exception as e:
            logger.warning(f"Error determining sector for {symbol}: {e}")

        # Default fallback
        return "technology"

    async def _optimize_universe_size(
        self, stocks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Optimize universe to target size with sector balance"""
        if len(stocks) <= self.target_universe_size:
            return stocks

        # Group by sector
        sector_groups = {}
        for stock in stocks:
            sector = stock["sector"]
            if sector not in sector_groups:
                sector_groups[sector] = []
            sector_groups[sector].append(stock)

        # Target stocks per sector (roughly balanced)
        target_per_sector = self.target_universe_size // len(SECTOR_MAPPING)

        final_universe = []
        for sector, sector_stocks in sector_groups.items():
            # Sort by market cap (prefer larger for liquidity)
            sorted_stocks = sorted(
                sector_stocks, key=lambda x: x["market_cap"], reverse=True
            )

            # Take top stocks for this sector
            sector_allocation = min(target_per_sector, len(sorted_stocks))
            final_universe.extend(sorted_stocks[:sector_allocation])

        # If we're under target, fill with remaining best stocks
        if len(final_universe) < self.target_universe_size:
            remaining_slots = self.target_universe_size - len(final_universe)
            used_symbols = {stock["symbol"] for stock in final_universe}

            # Get remaining stocks sorted by market cap
            remaining_stocks = [s for s in stocks if s["symbol"] not in used_symbols]
            remaining_stocks.sort(key=lambda x: x["market_cap"], reverse=True)

            final_universe.extend(remaining_stocks[:remaining_slots])

        return final_universe[: self.target_universe_size]

    async def _update_stock_universe_table(
        self, universe_stocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update the StockUniverse table with new data"""
        try:
            with SessionLocal() as db:
                # Mark all existing stocks as inactive first
                db.query(StockUniverse).update({"is_active": False})

                updated_count = 0
                created_count = 0

                for stock_data in universe_stocks:
                    # Check if stock exists
                    existing_stock = (
                        db.query(StockUniverse)
                        .filter(StockUniverse.symbol == stock_data["symbol"])
                        .first()
                    )

                    if existing_stock:
                        # Update existing stock
                        existing_stock.company_name = stock_data["company_name"]
                        existing_stock.exchange = stock_data["exchange"]
                        existing_stock.market_cap = stock_data["market_cap"]
                        existing_stock.avg_daily_volume = stock_data["avg_daily_volume"]
                        existing_stock.current_price = stock_data["current_price"]
                        existing_stock.sector = stock_data["sector"]
                        existing_stock.volatility_multiplier = stock_data[
                            "volatility_multiplier"
                        ]
                        existing_stock.gap_frequency = stock_data["gap_frequency"]
                        existing_stock.is_active = True
                        existing_stock.last_updated = datetime.utcnow()
                        updated_count += 1
                    else:
                        # Create new stock
                        new_stock = StockUniverse(
                            symbol=stock_data["symbol"],
                            company_name=stock_data["company_name"],
                            exchange=stock_data["exchange"],
                            market_cap=stock_data["market_cap"],
                            avg_daily_volume=stock_data["avg_daily_volume"],
                            current_price=stock_data["current_price"],
                            sector=stock_data["sector"],
                            volatility_multiplier=stock_data["volatility_multiplier"],
                            gap_frequency=stock_data["gap_frequency"],
                            is_active=True,
                            last_updated=datetime.utcnow(),
                        )
                        db.add(new_stock)
                        created_count += 1

                # Commit all changes
                db.commit()

                # Get inactive count
                inactive_count = (
                    db.query(StockUniverse)
                    .filter(StockUniverse.is_active == False)
                    .count()
                )

                return {
                    "status": "success",
                    "updated": updated_count,
                    "created": created_count,
                    "inactive": inactive_count,
                    "total_active": len(universe_stocks),
                }

        except Exception as e:
            logger.error(f"Failed to update stock universe table: {e}")
            return {"status": "error", "message": str(e)}

    def _get_sector_breakdown(self, stocks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get count of stocks per sector"""
        sector_counts = {}
        for stock in stocks:
            sector = stock["sector"]
            sector_counts[sector] = sector_counts.get(sector, 0) + 1
        return sector_counts

    async def refresh_universe_data(self) -> Dict[str, Any]:
        """Refresh existing universe with updated market data"""
        try:
            logger.info("Refreshing universe data...")

            with SessionLocal() as db:
                # Get all active stocks
                active_stocks = (
                    db.query(StockUniverse)
                    .filter(StockUniverse.is_active == True)
                    .all()
                )

                updated_count = 0
                for stock in active_stocks:
                    try:
                        # Get fresh quote data
                        quote_data = await self._get_stock_quote_data(stock.symbol)

                        if quote_data:
                            # Update stock data
                            stock.market_cap = quote_data.get(
                                "marketCap", stock.market_cap
                            )
                            stock.current_price = quote_data.get(
                                "price", stock.current_price
                            )
                            stock.avg_daily_volume = quote_data.get(
                                "avgVolume", stock.avg_daily_volume
                            )
                            stock.last_updated = datetime.utcnow()
                            updated_count += 1

                            # Check if still meets criteria
                            if not self._passes_universe_filters(
                                stock.market_cap,
                                stock.current_price,
                                stock.avg_daily_volume,
                                stock.exchange,
                            ):
                                stock.is_active = False
                                logger.info(
                                    f"Deactivated {stock.symbol} - no longer meets criteria"
                                )

                        # Rate limiting
                        if updated_count % 50 == 0:
                            await asyncio.sleep(1)

                    except Exception as e:
                        logger.warning(f"Error updating {stock.symbol}: {e}")
                        continue

                db.commit()

                return {
                    "status": "success",
                    "updated_count": updated_count,
                    "total_stocks": len(active_stocks),
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logger.error(f"Failed to refresh universe data: {e}")
            return {"status": "error", "message": str(e)}


# Global instance
_universe_builder: Optional[UniverseBuilder] = None


def get_universe_builder() -> UniverseBuilder:
    """Get global universe builder instance"""
    global _universe_builder
    if _universe_builder is None:
        _universe_builder = UniverseBuilder()
    return _universe_builder
