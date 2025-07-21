"""
Polygon.io MCP Client Integration
Handles connections to the Polygon.io MCP server for market data
"""

import asyncio
import httpx
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta
import logging

from core.config import get_settings

logger = logging.getLogger(__name__)


class PolygonMCPClient:
    """Client for interacting with Polygon.io MCP server"""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = None
        self.base_url = "https://api.polygon.io"
        self.mcp_endpoint = None  # Will be set when MCP server is running

        # Get API key from settings
        if self.settings.credentials and self.settings.credentials.api_keys.get(
            "polygon"
        ):
            self.api_key = self.settings.credentials.api_keys["polygon"].key

        # HTTP client
        self.client = httpx.AsyncClient(timeout=30.0)

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Polygon.io API"""
        try:
            if not self.api_key:
                return {"status": "error", "message": "No Polygon API key configured"}

            # Test with a simple endpoint
            url = f"{self.base_url}/v3/reference/tickers"
            params = {
                "apikey": self.api_key,
                "market": "stocks",
                "active": "true",
                "limit": 1,
            }

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "message": "Connection successful",
                    "api_calls_remaining": response.headers.get(
                        "X-RateLimit-Remaining", "unknown"
                    ),
                    "sample_data": data.get("results", [])[:1],
                }
            else:
                return {
                    "status": "error",
                    "message": f"API returned status {response.status_code}",
                    "response": response.text,
                }

        except Exception as e:
            logger.error(f"Polygon API test failed: {e}")
            return {"status": "error", "message": f"Connection failed: {str(e)}"}

    async def get_tickers(
        self, market: str = "stocks", active: bool = True, limit: int = 1000
    ) -> Dict[str, Any]:
        """Get list of tickers from Polygon.io"""
        try:
            if not self.api_key:
                raise ValueError("No Polygon API key configured")

            url = f"{self.base_url}/v3/reference/tickers"
            params = {
                "apikey": self.api_key,
                "market": market,
                "active": str(active).lower(),
                "limit": limit,
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                "status": "success",
                "tickers": data.get("results", []),
                "count": len(data.get("results", [])),
                "next_url": data.get("next_url"),
                "request_id": data.get("request_id"),
            }

        except Exception as e:
            logger.error(f"Failed to get tickers: {e}")
            return {"status": "error", "message": str(e), "tickers": []}

    async def get_ticker_details(self, symbol: str) -> Dict[str, Any]:
        """Get detailed information for a specific ticker"""
        try:
            if not self.api_key:
                raise ValueError("No Polygon API key configured")

            url = f"{self.base_url}/v3/reference/tickers/{symbol.upper()}"
            params = {"apikey": self.api_key}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                "status": "success",
                "ticker_data": data.get("results", {}),
                "request_id": data.get("request_id"),
            }

        except Exception as e:
            logger.error(f"Failed to get ticker details for {symbol}: {e}")
            return {"status": "error", "message": str(e), "ticker_data": {}}

    async def get_daily_bars(
        self, symbol: str, from_date: str, to_date: str
    ) -> Dict[str, Any]:
        """Get daily price bars for a stock"""
        try:
            if not self.api_key:
                raise ValueError("No Polygon API key configured")

            url = f"{self.base_url}/v2/aggs/ticker/{symbol.upper()}/range/1/day/{from_date}/{to_date}"
            params = {"apikey": self.api_key}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                "status": "success",
                "symbol": symbol.upper(),
                "bars": data.get("results", []),
                "count": data.get("resultsCount", 0),
                "request_id": data.get("request_id"),
            }

        except Exception as e:
            logger.error(f"Failed to get daily bars for {symbol}: {e}")
            return {"status": "error", "message": str(e), "bars": []}

    async def get_previous_close(self, symbol: str) -> Dict[str, Any]:
        """Get previous close data for a stock"""
        try:
            if not self.api_key:
                raise ValueError("No Polygon API key configured")

            url = f"{self.base_url}/v2/aggs/ticker/{symbol.upper()}/prev"
            params = {"apikey": self.api_key}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            if results:
                result = results[0]
                return {
                    "status": "success",
                    "symbol": symbol.upper(),
                    "previous_close": result.get("c"),
                    "open": result.get("o"),
                    "high": result.get("h"),
                    "low": result.get("l"),
                    "volume": result.get("v"),
                    "timestamp": result.get("t"),
                }
            else:
                return {
                    "status": "error",
                    "message": "No previous close data found",
                    "symbol": symbol.upper(),
                }

        except Exception as e:
            logger.error(f"Failed to get previous close for {symbol}: {e}")
            return {"status": "error", "message": str(e), "symbol": symbol.upper()}

    async def get_real_time_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time quote data for 1D calculations
        Provides current price, previous close, and volume data
        """
        try:
            if not self.api_key:
                raise ValueError("No Polygon API key configured")

            # Use snapshot endpoint for real-time data
            url = f"{self.base_url}/v2/snapshot/locale/us/markets/stocks/tickers/{symbol.upper()}"
            params = {"apikey": self.api_key}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            ticker_data = data.get("ticker", {})

            if ticker_data:
                # Extract price data
                day_data = ticker_data.get("day", {})
                prev_day_data = ticker_data.get("prevDay", {})
                last_quote = ticker_data.get("lastQuote", {})
                last_trade = ticker_data.get("lastTrade", {})

                # Get current price (from last trade or last quote)
                current_price = (
                    last_trade.get("p") or last_quote.get("p") or day_data.get("c")
                )

                return {
                    "status": "success",
                    "symbol": symbol.upper(),
                    "quote": {
                        # Current price data
                        "price": current_price,
                        "open": day_data.get("o"),
                        "high": day_data.get("h"),
                        "low": day_data.get("l"),
                        "close": day_data.get("c"),
                        # Previous close for 1D calculation
                        "previousClose": prev_day_data.get("c"),
                        # Volume data for volume weighting
                        "volume": day_data.get("v"),
                        "avgVolume": prev_day_data.get(
                            "v"
                        ),  # Previous day volume as approximation
                        # Additional metadata
                        "timestamp": last_trade.get("t") or last_quote.get("t"),
                        "exchange": last_trade.get("x"),
                        "bid": last_quote.get("b"),
                        "ask": last_quote.get("a"),
                        "bidSize": last_quote.get("s"),
                        "askSize": last_quote.get("S"),
                    },
                }
            else:
                return {
                    "status": "error",
                    "message": "No real-time quote data found",
                    "symbol": symbol.upper(),
                }

        except Exception as e:
            logger.error(f"Failed to get real-time quote for {symbol}: {e}")
            return {"status": "error", "message": str(e), "symbol": symbol.upper()}

    async def get_quote_with_volume_avg(
        self, symbol: str, days_for_avg: int = 20
    ) -> Dict[str, Any]:
        """
        Get quote data with calculated average volume for 1D calculations
        Combines real-time quote with historical volume average
        """
        try:
            # Get real-time quote
            quote_result = await self.get_real_time_quote(symbol)
            if quote_result["status"] != "success":
                return quote_result

            # Get historical bars for volume average calculation
            to_date = datetime.now().strftime("%Y-%m-%d")
            from_date = (datetime.now() - timedelta(days=days_for_avg + 5)).strftime(
                "%Y-%m-%d"
            )

            bars_result = await self.get_daily_bars(symbol, from_date, to_date)

            quote_data = quote_result["quote"]

            # Calculate average volume if historical data available
            if bars_result["status"] == "success" and bars_result["bars"]:
                volumes = [
                    bar.get("v", 0)
                    for bar in bars_result["bars"]
                    if bar.get("v", 0) > 0
                ]
                if len(volumes) >= 5:  # Minimum 5 days of data
                    avg_volume = sum(volumes[-days_for_avg:]) // len(
                        volumes[-days_for_avg:]
                    )
                    quote_data["avgVolume"] = avg_volume
                    quote_data["volumeDataDays"] = len(volumes)

            return {"status": "success", "symbol": symbol.upper(), "quote": quote_data}

        except Exception as e:
            logger.error(f"Failed to get quote with volume average for {symbol}: {e}")
            return {"status": "error", "message": str(e), "symbol": symbol.upper()}

    async def get_market_status(self) -> Dict[str, Any]:
        """Get current market status"""
        try:
            if not self.api_key:
                raise ValueError("No Polygon API key configured")

            url = f"{self.base_url}/v1/marketstatus/now"
            params = {"apikey": self.api_key}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                "status": "success",
                "market_data": data,
                "request_id": data.get("request_id"),
            }

        except Exception as e:
            logger.error(f"Failed to get market status: {e}")
            return {"status": "error", "message": str(e), "market_data": {}}

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global client instance
_polygon_client: Optional[PolygonMCPClient] = None


def get_polygon_client() -> PolygonMCPClient:
    """Get global Polygon MCP client instance"""
    global _polygon_client
    if _polygon_client is None:
        _polygon_client = PolygonMCPClient()
    return _polygon_client


async def test_polygon_connection() -> Dict[str, Any]:
    """Test Polygon.io connection"""
    client = get_polygon_client()
    return await client.test_connection()
