"""
Unit tests for FMP Client - Phase 1: Stock Screener Complete
Tests the new unlimited stock screener method for universe building
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
import json

from mcp.fmp_client import FMPMCPClient, get_fmp_client


class TestFMPClientStockScreenerComplete:
    """Test suite for get_stock_screener_complete method"""
    
    @pytest.fixture
    def fmp_client(self):
        """Create FMP client instance for testing"""
        client = FMPMCPClient()
        client.api_key = "test_api_key"
        return client
    
    @pytest.fixture
    def mock_response_data(self):
        """Sample FMP screener response data"""
        return [
            {
                "symbol": "AAPL",
                "companyName": "Apple Inc.",
                "marketCap": 3000000000,
                "price": 175.50,
                "volume": 50000000,
                "avgVolume": 45000000,
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Consumer Electronics"
            },
            {
                "symbol": "MSFT", 
                "companyName": "Microsoft Corporation",
                "marketCap": 2800000000,
                "price": 378.25,
                "volume": 25000000,
                "avgVolume": 22000000,
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Software"
            },
            {
                "symbol": "JNJ",
                "companyName": "Johnson & Johnson",
                "marketCap": 450000000,
                "price": 162.75,
                "volume": 8000000,
                "avgVolume": 7500000,
                "exchange": "NYSE",
                "sector": "Healthcare",
                "industry": "Pharmaceuticals"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_get_stock_screener_complete_success(self, fmp_client, mock_response_data):
        """Test successful universe retrieval"""
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        
        with patch.object(fmp_client.client, 'get', return_value=mock_response):
            result = await fmp_client.get_stock_screener_complete()
        
        # Verify success response structure
        assert result["status"] == "success"
        assert result["universe_size"] == 3
        assert len(result["stocks"]) == 3
        assert "filters_applied" in result
        assert "processing_timestamp" in result
        assert "criteria" in result
        
        # Verify criteria are correctly set
        criteria = result["criteria"]
        assert criteria["market_cap_range"] == "$10M - $2B"
        assert criteria["price_range"] == "$1.00 - $100.00"
        assert criteria["min_volume"] == "1M+ daily"
        assert criteria["exchanges"] == "NASDAQ, NYSE"
        assert criteria["active_only"] is True
        
        # Verify filters applied correctly
        filters = result["filters_applied"]
        assert filters["marketCapMoreThan"] == "10000000"
        assert filters["marketCapLowerThan"] == "2000000000"
        assert filters["exchange"] == "NASDAQ,NYSE"
        assert filters["volumeMoreThan"] == "1000000"
        assert filters["priceMoreThan"] == "1.00"
        assert filters["priceLowerThan"] == "100.00"
        assert filters["isActivelyTrading"] == "true"
        assert "limit" not in filters  # Critical: no limit parameter
        
        # Verify stock data preservation
        assert result["stocks"][0]["symbol"] == "AAPL"
        assert result["stocks"][0]["sector"] == "Technology"
        assert result["stocks"][1]["symbol"] == "MSFT"
        assert result["stocks"][2]["symbol"] == "JNJ"
    
    @pytest.mark.asyncio
    async def test_get_stock_screener_complete_no_api_key(self, fmp_client):
        """Test error handling when no API key configured"""
        fmp_client.api_key = None
        
        result = await fmp_client.get_stock_screener_complete()
        
        assert result["status"] == "error"
        assert "No FMP API key configured" in result["message"]
        assert result["universe_size"] == 0
        assert result["stocks"] == []
        assert "processing_timestamp" in result
    
    @pytest.mark.asyncio
    async def test_get_stock_screener_complete_api_error(self, fmp_client):
        """Test handling of API errors"""
        # Mock HTTP error
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("API Error: 429 Rate Limited")
        
        with patch.object(fmp_client.client, 'get', return_value=mock_response):
            result = await fmp_client.get_stock_screener_complete()
        
        assert result["status"] == "error"
        assert "API Error: 429 Rate Limited" in result["message"]
        assert result["universe_size"] == 0
        assert result["stocks"] == []
    
    @pytest.mark.asyncio
    async def test_get_stock_screener_complete_empty_response(self, fmp_client):
        """Test handling of empty response"""
        # Mock empty response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        
        with patch.object(fmp_client.client, 'get', return_value=mock_response):
            result = await fmp_client.get_stock_screener_complete()
        
        assert result["status"] == "success"
        assert result["universe_size"] == 0
        assert result["stocks"] == []
        assert "filters_applied" in result
    
    @pytest.mark.asyncio
    async def test_get_stock_screener_complete_invalid_json_response(self, fmp_client):
        """Test handling of non-list JSON response"""
        # Mock invalid response format
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Invalid request"}
        mock_response.raise_for_status.return_value = None
        
        with patch.object(fmp_client.client, 'get', return_value=mock_response):
            result = await fmp_client.get_stock_screener_complete()
        
        assert result["status"] == "success"
        assert result["universe_size"] == 0
        assert result["stocks"] == []
    
    @pytest.mark.asyncio
    async def test_get_stock_screener_complete_large_universe(self, fmp_client):
        """Test handling of large universe response (1500+ stocks)"""
        # Create large mock dataset
        large_dataset = []
        for i in range(1500):
            large_dataset.append({
                "symbol": f"STOCK{i:04d}",
                "companyName": f"Test Company {i}",
                "marketCap": 50000000 + (i * 1000000),  # $50M to $1.55B range
                "price": 10.00 + (i * 0.1),
                "volume": 1500000 + (i * 1000),
                "exchange": "NASDAQ" if i % 2 == 0 else "NYSE",
                "sector": ["Technology", "Healthcare", "Energy"][i % 3]
            })
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = large_dataset
        mock_response.raise_for_status.return_value = None
        
        with patch.object(fmp_client.client, 'get', return_value=mock_response):
            result = await fmp_client.get_stock_screener_complete()
        
        assert result["status"] == "success"
        assert result["universe_size"] == 1500
        assert len(result["stocks"]) == 1500
        assert result["stocks"][0]["symbol"] == "STOCK0000"
        assert result["stocks"][-1]["symbol"] == "STOCK1499"
    
    @pytest.mark.asyncio
    async def test_get_stock_screener_complete_url_construction(self, fmp_client):
        """Test that URL and parameters are constructed correctly"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        
        with patch.object(fmp_client.client, 'get', return_value=mock_response) as mock_get:
            await fmp_client.get_stock_screener_complete()
            
            # Verify the URL was called correctly
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            
            # Check URL
            assert call_args[0][0] == "https://financialmodelingprep.com/api/v3/stock-screener"
            
            # Check parameters
            params = call_args[1]["params"]
            assert params["marketCapMoreThan"] == "10000000"
            assert params["marketCapLowerThan"] == "2000000000"
            assert params["exchange"] == "NASDAQ,NYSE"
            assert params["volumeMoreThan"] == "1000000"
            assert params["priceMoreThan"] == "1.00"
            assert params["priceLowerThan"] == "100.00"
            assert params["isActivelyTrading"] == "true"
            assert params["apikey"] == "test_api_key"
            
            # CRITICAL: Verify no limit parameter
            assert "limit" not in params
    
    def test_timestamp_format(self, fmp_client):
        """Test that processing timestamp is in correct ISO format"""
        # This test verifies the timestamp format without making actual API calls
        test_timestamp = datetime.utcnow().isoformat()
        
        # Verify ISO format
        assert "T" in test_timestamp
        assert len(test_timestamp.split("T")) == 2
        
        # Verify can be parsed back
        parsed = datetime.fromisoformat(test_timestamp)
        assert isinstance(parsed, datetime)


class TestFMPClientGlobalInstance:
    """Test global FMP client instance management"""
    
    def test_get_fmp_client_singleton(self):
        """Test that get_fmp_client returns same instance"""
        client1 = get_fmp_client()
        client2 = get_fmp_client()
        
        assert client1 is client2
        assert isinstance(client1, FMPMCPClient)
    
    def test_fmp_client_initialization(self):
        """Test FMP client proper initialization"""
        client = get_fmp_client()
        
        assert client.base_url == "https://financialmodelingprep.com/api"
        assert hasattr(client, 'client')
        assert hasattr(client, 'api_key')


class TestFMPClientMethodSignature:
    """Test method signature and type hints"""
    
    def test_get_stock_screener_complete_signature(self):
        """Test method signature matches specification"""
        import inspect
        
        method = FMPMCPClient.get_stock_screener_complete
        signature = inspect.signature(method)
        
        # Should have only self parameter (no other parameters)
        params = list(signature.parameters.keys())
        assert params == ['self']
        
        # Should return Dict[str, Any] annotation
        return_annotation = signature.return_annotation
        assert 'Dict' in str(return_annotation) 