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
        if self.settings.credentials and self.settings.credentials.api_keys.get("polygon"):
            self.api_key = self.settings.credentials.api_keys["polygon"].key
        
        # HTTP client
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Polygon.io API"""
        try:
            if not self.api_key:
                return {
                    "status": "error",
                    "message": "No Polygon API key configured"
                }
            
            # Test with a simple endpoint
            url = f"{self.base_url}/v3/reference/tickers"
            params = {
                "apikey": self.api_key,
                "market": "stocks",
                "active": "true",
                "limit": 1
            }
            
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "message": "Connection successful",
                    "api_calls_remaining": response.headers.get("X-RateLimit-Remaining", "unknown"),
                    "sample_data": data.get("results", [])[:1]
                }
            else:
                return {
                    "status": "error",
                    "message": f"API returned status {response.status_code}",
                    "response": response.text
                }
                
        except Exception as e:
            logger.error(f"Polygon API test failed: {e}")
            return {
                "status": "error",
                "message": f"Connection failed: {str(e)}"
            }
    
    async def get_tickers(self, market: str = "stocks", active: bool = True, limit: int = 1000) -> Dict[str, Any]:
        """Get list of tickers from Polygon.io"""
        try:
            if not self.api_key:
                raise ValueError("No Polygon API key configured")
            
            url = f"{self.base_url}/v3/reference/tickers"
            params = {
                "apikey": self.api_key,
                "market": market,
                "active": str(active).lower(),
                "limit": limit
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return {
                "status": "success",
                "tickers": data.get("results", []),
                "count": len(data.get("results", [])),
                "next_url": data.get("next_url"),
                "request_id": data.get("request_id")
            }
            
        except Exception as e:
            logger.error(f"Failed to get tickers: {e}")
            return {
                "status": "error",
                "message": str(e),
                "tickers": []
            }
    
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
                "request_id": data.get("request_id")
            }
            
        except Exception as e:
            logger.error(f"Failed to get ticker details for {symbol}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "ticker_data": {}
            }
    
    async def get_daily_bars(self, symbol: str, from_date: str, to_date: str) -> Dict[str, Any]:
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
                "request_id": data.get("request_id")
            }
            
        except Exception as e:
            logger.error(f"Failed to get daily bars for {symbol}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "bars": []
            }
    
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
                    "timestamp": result.get("t")
                }
            else:
                return {
                    "status": "error",
                    "message": "No previous close data found",
                    "symbol": symbol.upper()
                }
                
        except Exception as e:
            logger.error(f"Failed to get previous close for {symbol}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "symbol": symbol.upper()
            }
    
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
                "request_id": data.get("request_id")
            }
            
        except Exception as e:
            logger.error(f"Failed to get market status: {e}")
            return {
                "status": "error",
                "message": str(e),
                "market_data": {}
            }
    
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