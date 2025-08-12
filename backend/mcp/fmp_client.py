"""
Financial Modeling Prep (FMP) MCP Client Integration
Handles connections to the FMP MCP server for financial data
"""

import asyncio
import httpx
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta
import logging

from core.config import get_settings

logger = logging.getLogger(__name__)


class FMPMCPClient:
    """Client for interacting with FMP MCP server"""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = None
        self.base_url = "https://financialmodelingprep.com/api"
        self.mcp_endpoint = None  # Will be set when MCP server is running

        # Get API key from settings
        if self.settings.credentials and self.settings.credentials.api_keys.get("fmp"):
            self.api_key = self.settings.credentials.api_keys["fmp"].key

        # HTTP client
        self.client = httpx.AsyncClient(timeout=30.0)

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to FMP API"""
        try:
            if not self.api_key:
                return {"status": "error", "message": "No FMP API key configured"}

            # Test with a simple endpoint
            url = f"{self.base_url}/v3/stock/list"
            params = {"apikey": self.api_key}

            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "message": "Connection successful",
                    "sample_data": data[:1] if isinstance(data, list) else [data],
                }
            else:
                return {
                    "status": "error",
                    "message": f"API returned status {response.status_code}",
                    "response": response.text,
                }

        except Exception as e:
            logger.error(f"FMP API test failed: {e}")
            return {"status": "error", "message": f"Connection failed: {str(e)}"}

    async def get_stock_list(self) -> Dict[str, Any]:
        """Get list of all stocks from FMP"""
        import asyncio

        try:
            if not self.api_key:
                raise ValueError("No FMP API key configured")

            url = f"{self.base_url}/v3/stock/list"
            params = {"apikey": self.api_key}

            # Retry logic for rate limiting
            for attempt in range(3):
                try:
                    response = await self.client.get(url, params=params)

                    if response.status_code == 429:
                        print(
                            f"FMP Rate limit hit, attempt {attempt + 1}/3. Waiting 5 seconds..."
                        )
                        if attempt < 2:  # Don't wait on last attempt
                            await asyncio.sleep(5)
                        continue

                    response.raise_for_status()

                    data = response.json()
                    return {
                        "status": "success",
                        "stocks": data if isinstance(data, list) else [],
                        "count": len(data) if isinstance(data, list) else 0,
                    }
                except Exception as e:
                    if attempt == 2:  # Last attempt
                        raise e
                    print(f"FMP attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(10)

            # If we get here, all attempts failed
            raise Exception("All FMP API attempts failed")

        except Exception as e:
            logger.error(f"Failed to get stock list: {e}")
            return {"status": "error", "message": str(e), "stocks": []}

    async def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile for a specific symbol"""
        try:
            if not self.api_key:
                raise ValueError("No FMP API key configured")

            url = f"{self.base_url}/v3/profile/{symbol.upper()}"
            params = {"apikey": self.api_key}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                "status": "success",
                "symbol": symbol.upper(),
                "profile": data[0] if isinstance(data, list) and data else data,
            }

        except Exception as e:
            logger.error(f"Failed to get company profile for {symbol}: {e}")
            return {"status": "error", "message": str(e), "profile": {}}

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get current quote for a stock (DEPRECATED: Do not use in production)"""
        # WARNING: This method is deprecated and should not be used in production pipelines.
        # Use get_batch_quotes for all production data retrieval.
        try:
            if not self.api_key:
                raise ValueError("No FMP API key configured")

            url = f"{self.base_url}/v3/quote/{symbol.upper()}"
            params = {"apikey": self.api_key}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                "status": "success",
                "symbol": symbol.upper(),
                "quote": data[0] if isinstance(data, list) and data else data,
            }

        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return {"status": "error", "message": str(e), "quote": {}}

    async def get_historical_prices(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get historical price data for a stock"""
        try:
            if not self.api_key:
                raise ValueError("No FMP API key configured")

            url = f"{self.base_url}/v3/historical-price-full/{symbol.upper()}"
            params = {"apikey": self.api_key}

            if from_date:
                params["from"] = from_date
            if to_date:
                params["to"] = to_date

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                "status": "success",
                "symbol": symbol.upper(),
                "historical": (
                    data.get("historical", []) if isinstance(data, dict) else []
                ),
                "count": (
                    len(data.get("historical", [])) if isinstance(data, dict) else 0
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get historical prices for {symbol}: {e}")
            return {"status": "error", "message": str(e), "historical": []}

    async def get_sector_performance(self) -> Dict[str, Any]:
        """Get sector performance data"""
        try:
            if not self.api_key:
                raise ValueError("No FMP API key configured")

            url = f"{self.base_url}/v3/sector-performance"
            params = {"apikey": self.api_key}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                "status": "success",
                "sectors": data if isinstance(data, list) else [],
                "count": len(data) if isinstance(data, list) else 0,
            }

        except Exception as e:
            logger.error(f"Failed to get sector performance: {e}")
            return {"status": "error", "message": str(e), "sectors": []}

    async def get_market_cap(self, symbol: str) -> Dict[str, Any]:
        """Get market cap data for a stock"""
        try:
            if not self.api_key:
                raise ValueError("No FMP API key configured")

            url = f"{self.base_url}/v3/market-capitalization/{symbol.upper()}"
            params = {"apikey": self.api_key}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                "status": "success",
                "symbol": symbol.upper(),
                "market_cap_data": data[0] if isinstance(data, list) and data else data,
            }

        except Exception as e:
            logger.error(f"Failed to get market cap for {symbol}: {e}")
            return {"status": "error", "message": str(e), "market_cap_data": {}}

    async def get_stock_screener(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic stock screener - accepts any criteria

        Args:
            criteria: Dictionary of screening criteria (marketCapMoreThan, volumeMoreThan, etc.)

        Returns:
            Dict with status, stocks, and metadata
        """
        try:
            if not self.api_key:
                raise ValueError("No FMP API key configured")

            url = f"{self.base_url}/v3/stock-screener"

            # Build parameters from criteria
            params = {"apikey": self.api_key}
            params.update(criteria)

            # Ensure limit is set for complete results
            if "limit" not in params:
                params["limit"] = "10000"

            logger.info("Calling FMP stock screener for complete universe")
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Log universe size for monitoring
            universe_size = len(data) if isinstance(data, list) else 0
            logger.info(f"FMP Screener returned {universe_size} stocks")

            return {
                "status": "success",
                "stocks": data if isinstance(data, list) else [],
                "count": universe_size,
                "criteria_applied": criteria,
                "raw_response": data,
                "processing_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"FMP stock screener failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "stocks": [],
                "count": 0,
                "criteria_applied": criteria,
                "processing_timestamp": datetime.utcnow().isoformat(),
            }

    async def get_gainers_losers(self, list_type: str = "gainers") -> Dict[str, Any]:
        """Get gainers or losers"""
        try:
            if not self.api_key:
                raise ValueError("No FMP API key configured")

            if list_type not in ["gainers", "losers"]:
                raise ValueError("list_type must be 'gainers' or 'losers'")

            url = f"{self.base_url}/v3/{list_type}"
            params = {"apikey": self.api_key}

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                "status": "success",
                "type": list_type,
                "stocks": data if isinstance(data, list) else [],
                "count": len(data) if isinstance(data, list) else 0,
            }

        except Exception as e:
            logger.error(f"Failed to get {list_type}: {e}")
            return {"status": "error", "message": str(e), "stocks": []}

    async def get_batch_quotes(
        self, symbols: List[str], batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get quotes for multiple symbols using FMP batch quote capability

        Args:
            symbols: List of stock symbols
            batch_size: Number of symbols per batch call (max recommended: 100)

        Returns:
            List of quote dictionaries with price, volume, and market data
        """
        try:
            if not self.api_key:
                raise ValueError("No FMP API key configured")

            if not symbols:
                return []

            all_quotes = []

            # Process symbols in batches
            for i in range(0, len(symbols), batch_size):
                batch_symbols = symbols[i : i + batch_size]
                symbols_str = ",".join(batch_symbols)

                url = f"{self.base_url}/v3/quote/{symbols_str}"
                params = {"apikey": self.api_key}

                logger.info(
                    f"FMP batch quote: {len(batch_symbols)} symbols (batch {i//batch_size + 1})"
                )

                # Retry logic for rate limiting
                for attempt in range(3):
                    try:
                        response = await self.client.get(url, params=params)

                        if response.status_code == 429:
                            logger.warning(
                                f"FMP rate limit hit, attempt {attempt + 1}/3. Waiting..."
                            )
                            if attempt < 2:
                                await asyncio.sleep(5)
                            continue

                        response.raise_for_status()
                        batch_data = response.json()

                        if isinstance(batch_data, list):
                            all_quotes.extend(batch_data)
                        elif isinstance(batch_data, dict):
                            all_quotes.append(batch_data)

                        break  # Success, exit retry loop

                    except Exception as e:
                        if attempt == 2:  # Last attempt
                            logger.error(
                                f"FMP batch quote failed for symbols {batch_symbols}: {e}"
                            )
                            # Continue with next batch instead of failing completely
                            break
                        await asyncio.sleep(5)

                # Small delay between batches to respect rate limits
                if i + batch_size < len(symbols):
                    await asyncio.sleep(0.1)  # 100ms delay between batches

            logger.info(
                f"FMP batch quotes completed: {len(all_quotes)} quotes for {len(symbols)} symbols"
            )
            return all_quotes

        except Exception as e:
            logger.error(f"FMP batch quotes failed: {e}")
            return []

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global client instance
_fmp_client: Optional[FMPMCPClient] = None


def get_fmp_client() -> FMPMCPClient:
    """Get global FMP MCP client instance"""
    global _fmp_client
    if _fmp_client is None:
        _fmp_client = FMPMCPClient()
    return _fmp_client


async def test_fmp_connection() -> Dict[str, Any]:
    """Test FMP connection"""
    client = get_fmp_client()
    return await client.test_connection()
