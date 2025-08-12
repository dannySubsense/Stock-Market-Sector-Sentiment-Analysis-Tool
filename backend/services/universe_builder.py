"""
Stock Universe Builder - Slice 1A Implementation
Builds and maintains the 1,500 small-cap stock universe
Market Cap Focus: $10M - $2B (micro-cap to small-cap)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from core.database import SessionLocal
from mcp.fmp_client import get_fmp_client
from mcp.polygon_client import get_polygon_client
from models.stock_universe import StockUniverse
from services.sector_mapper import FMPSectorMapper
from config.volatility_weights import get_weight_for_sector
from services.sector_normalizer import (
    normalize_sector_name,
    log_sector_normalization_warning,
)

logger = logging.getLogger(__name__)

# Expected stock criteria from SDD (Real-World Tested & Optimized)
# BENCHMARKS (July 21, 2025):
#   25K volume threshold = 3,073 stocks ✅ OPTIMAL (exceeds >2k target)
#   100K volume threshold = 1,790 stocks
#   250K volume threshold = 1,066 stocks
#   500K volume threshold = 682 stocks
#   1M volume threshold = 373 stocks (original SDD - too restrictive)
MIN_MARKET_CAP = 10_000_000  # $10M minimum
MAX_MARKET_CAP = 2_000_000_000  # $2B maximum
MIN_VOLUME = 25_000  # 25K shares daily volume (real-world optimized from 1M)
MIN_PRICE = 0.50  # $0.50 minimum price (real-world optimized from $1.00)
ALLOWED_EXCHANGES = ["NASDAQ", "NYSE"]

# Small cap sector definitions for intelligent classification
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
            "tech",
            "data",
            "cloud",
            "saas",
        ]
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
            "pharma",
            "biotechnology",
        ]
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
            "power",
            "drilling",
        ]
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
            "finance",
            "capital",
        ]
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
            "leisure",
            "travel",
        ]
    },
    "industrials": {
        "keywords": [
            "industrial",
            "manufacturing",
            "construction",
            "aerospace",
            "defense",
            "logistics",
            "transportation",
        ]
    },
    "materials": {
        "keywords": [
            "materials",
            "chemicals",
            "metals",
            "steel",
            "aluminum",
            "copper",
            "mining",
            "forestry",
        ]
    },
    "utilities": {
        "keywords": [
            "utilities",
            "electric",
            "water",
            "waste",
            "infrastructure",
            "pipeline",
            "transmission",
        ]
    },
}


class UniverseBuilder:
    """
    Builds and maintains the small-cap stock universe for sector sentiment analysis
    Uses FMP screener to identify qualifying stocks based on SDD criteria
    """

    def __init__(self):
        self.fmp_client = get_fmp_client()
        self.polygon_client = get_polygon_client()
        self.sector_mapper = FMPSectorMapper()

        # Universe filtering criteria
        self.market_cap_min = MIN_MARKET_CAP
        self.market_cap_max = MAX_MARKET_CAP
        self.min_daily_volume = MIN_VOLUME
        self.min_price = MIN_PRICE
        self.max_price = None  # No upper price limit
        self.valid_exchanges = ALLOWED_EXCHANGES

    def get_fmp_screening_criteria(self) -> Dict[str, Any]:
        """
        Get the screening criteria for FMP based on SDD requirements
        Small-cap focus: $10M - $2B market cap, 1M+ volume, $2+ price
        """
        return {
            "marketCapMoreThan": MIN_MARKET_CAP,  # Fixed: camelCase
            "marketCapLowerThan": MAX_MARKET_CAP,  # Fixed: camelCase
            "volumeMoreThan": MIN_VOLUME,  # Fixed: camelCase
            "priceMoreThan": MIN_PRICE,  # Fixed: camelCase
            "exchange": "NASDAQ,NYSE",  # Only major exchanges
            "limit": 5000,  # Tested sweet spot to capture >2k stocks
        }

    async def get_fmp_universe(self) -> Dict[str, Any]:
        """
        Get complete universe using FMP screener with sector mapping

        Returns:
            Dict: Universe data from FMP with mapped sectors
        """
        try:
            # Get raw data from FMP
            criteria = self.get_fmp_screening_criteria()
            fmp_result = await self.fmp_client.get_stock_screener(criteria)

            if fmp_result.get("status") != "success":
                return fmp_result

            # Map sectors for each stock
            mapped_stocks = []
            for stock in fmp_result.get("stocks", []):
                # Get original FMP sector
                original_fmp_sector = stock.get("sector", "")

                # Map to internal sector name
                mapped_sector = self.sector_mapper.map_fmp_sector(original_fmp_sector)

                # Add sector mapping to stock data
                mapped_stock = {
                    **stock,  # Preserve all original FMP data
                    "sector": mapped_sector,  # Our internal sector
                    "original_fmp_sector": original_fmp_sector,  # Preserve original
                }
                mapped_stocks.append(mapped_stock)

            # Return updated result
            return {
                **fmp_result,
                "stocks": mapped_stocks,
                "universe_size": len(mapped_stocks),
            }

        except Exception as e:
            logger.error(f"Failed to get FMP universe with sector mapping: {e}")
            return {
                "status": "error",
                "message": str(e),
                "stocks": [],
                "universe_size": 0,
            }

    async def build_daily_universe(self) -> Dict[str, Any]:
        """Build the complete daily universe from scratch using FMP screener"""
        try:
            logger.info("Starting daily universe build with FMP screener...")

            # Step 1: Get qualified stocks using FMP screener (efficient approach)
            universe_result = await self.get_fmp_universe()
            if universe_result.get("status") != "success":
                return universe_result

            qualified_stocks = universe_result.get("stocks", [])
            logger.info(
                f"FMP screener returned {len(qualified_stocks)} qualified stocks"
            )

            # Step 2: Transform FMP data to our database format
            transformed_stocks = []
            for stock in qualified_stocks:
                # Basic validation - stocks from screener should already meet criteria
                if self._validate_stock_data(stock):
                    # Transform FMP field names to our database field names
                    transformed_stock = self._transform_fmp_to_database_format(stock)
                    transformed_stocks.append(transformed_stock)

            logger.info(
                f"After validation and transformation: {len(transformed_stocks)} stocks"
            )

            # Step 3: Process universe (no artificial size limits)
            final_universe = await self._optimize_universe_size(transformed_stocks)
            logger.info(f"Final universe size: {len(final_universe)} stocks")

            # Step 4: Update database
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

    def _transform_fmp_to_database_format(
        self, fmp_stock: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform FMP field names to our database field names
        FMP uses: companyName, price, volume, marketCap, exchange
        We need: company_name, current_price, avg_daily_volume, market_cap, exchange
        """
        # Get mapped sector (already normalized by FMPSectorMapper)
        raw_sector = fmp_stock.get("sector", "unknown_sector")

        # Apply pure normalization function for additional safety
        sector = normalize_sector_name(raw_sector)
        log_sector_normalization_warning(raw_sector, sector)

        # Get volatility multiplier for sector
        volatility_multiplier = get_weight_for_sector(sector)

        return {
            "symbol": fmp_stock.get("symbol", ""),
            "company_name": fmp_stock.get(
                "companyName", ""
            ),  # FMP: companyName -> company_name
            "exchange": fmp_stock.get("exchange", ""),
            "market_cap": fmp_stock.get("marketCap", 0),
            "avg_daily_volume": fmp_stock.get(
                "volume", 0
            ),  # FMP: volume -> avg_daily_volume (current volume as proxy)
            "current_price": fmp_stock.get("price", 0.0),  # FMP: price -> current_price
            "sector": sector,  # Guaranteed to be lowercase and standardized
            "original_fmp_sector": fmp_stock.get("original_fmp_sector", ""),
            "volatility_multiplier": volatility_multiplier,
            "gap_frequency": "medium",  # Default value - we don't have this from FMP
        }

    def _validate_stock_data(self, stock: Dict[str, Any]) -> bool:
        """Basic validation for stock data from screener"""
        try:
            # Check required fields exist
            required_fields = ["symbol", "sector", "marketCap", "price", "volume"]
            for field in required_fields:
                if field not in stock or stock[field] is None:
                    return False

            # Basic sanity checks
            return (
                isinstance(stock["symbol"], str)
                and len(stock["symbol"]) > 0
                and isinstance(stock["marketCap"], (int, float))
                and stock["marketCap"] > 0
                and isinstance(stock["price"], (int, float))
                and stock["price"] > 0
            )
        except Exception:
            return False

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
        # Handle None values for price filters
        min_price = self.min_price if self.min_price is not None else 0.0
        max_price = self.max_price if self.max_price is not None else float("inf")

        return (
            self.market_cap_min <= market_cap <= self.market_cap_max
            and price >= min_price
            and price <= max_price
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
        """
        Process universe stocks - NO ARTIFICIAL SIZE LIMITS
        Universe size is market-driven based on screening criteria only
        """
        # NO TRUNCATION - Accept all stocks meeting criteria
        logger.info(
            f"Universe contains {len(stocks)} stocks meeting screening criteria"
        )

        # Group by sector for reporting/validation only
        sector_groups: Dict[str, List[Dict[str, Any]]] = {}
        for stock in stocks:
            sector = stock["sector"]
            if sector not in sector_groups:
                sector_groups[sector] = []
            sector_groups[sector].append(stock)

        # Log sector distribution for validation
        for sector, sector_stocks in sector_groups.items():
            logger.info(f"Sector {sector}: {len(sector_stocks)} stocks")

        # Return ALL qualified stocks - no artificial limits
        return stocks

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
                        existing_stock.is_active = True  # type: ignore
                        existing_stock.last_updated = datetime.utcnow()  # type: ignore
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
                            is_active=True,  # type: ignore
                            last_updated=datetime.utcnow(),  # type: ignore
                        )
                        db.add(new_stock)
                        created_count += 1

                # Commit all changes
                db.commit()

                # Get inactive count
                inactive_count = (
                    db.query(StockUniverse)
                    .filter(StockUniverse.is_active.is_(False))
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
        sector_counts: Dict[str, int] = {}
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
                    .filter(StockUniverse.is_active.is_(True))
                    .all()
                )

                updated_count = 0
                for stock in active_stocks:
                    try:
                        # Get fresh quote data - access the actual string value
                        quote_data = await self._get_stock_quote_data(str(stock.symbol))

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
                            stock.last_updated = datetime.utcnow()  # type: ignore
                            updated_count += 1

                            # Check if still meets criteria - access actual values
                            market_cap_val = (
                                float(stock.market_cap) if stock.market_cap else 0.0
                            )
                            price_val = (
                                float(stock.current_price)
                                if stock.current_price
                                else 0.0
                            )
                            volume_val = (
                                float(stock.avg_daily_volume)
                                if stock.avg_daily_volume
                                else 0.0
                            )
                            exchange_val = str(stock.exchange) if stock.exchange else ""  # type: ignore

                            if not self._passes_universe_filters(
                                market_cap_val,
                                price_val,
                                volume_val,
                                exchange_val,
                            ):
                                stock.is_active = False  # type: ignore
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
