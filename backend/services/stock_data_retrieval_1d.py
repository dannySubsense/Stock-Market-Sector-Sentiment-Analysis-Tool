"""
1D Stock Data Retrieval Service - API Comparison and Data Quality Analysis
Tests both FMP and Polygon APIs for 1D sector performance calculation data needs
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

from mcp.fmp_client import get_fmp_client
from mcp.polygon_client import get_polygon_client
from services.sector_performance_1d import StockData1D

logger = logging.getLogger(__name__)


@dataclass
class APITestResult:
    """Result from API data retrieval test"""

    api_name: str
    symbol: str
    success: bool
    response_time_ms: float
    data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    data_quality_score: float
    validation_issues: List[str]


@dataclass
class APIComparison:
    """Comparison result between APIs for a symbol"""

    symbol: str
    fmp_result: APITestResult
    polygon_result: APITestResult
    data_consistency_score: float
    recommended_api: str
    recommendation_reason: str


class StockDataRetrieval1D:
    """
    1D Stock Data Retrieval Service
    Tests and compares FMP vs Polygon APIs for 1D calculation data
    """

    # Test stocks as specified in Step 2
    TEST_STOCKS = ["SOUN", "BBAI", "PATH", "OCUL", "SMCI"]

    # Data validation thresholds
    MIN_PRICE = 0.01
    MAX_PRICE = 1000.0
    MAX_DAILY_CHANGE_PERCENT = 50.0
    MIN_VOLUME = 0

    def __init__(self):
        self.fmp_client = get_fmp_client()
        self.polygon_client = get_polygon_client()

    async def test_api_data_retrieval(
        self, symbols: List[str] = None
    ) -> Dict[str, Any]:
        """
        Test both APIs with specified stocks and compare results

        Args:
            symbols: List of symbols to test (defaults to TEST_STOCKS)

        Returns:
            Comprehensive comparison and recommendation
        """
        if symbols is None:
            symbols = self.TEST_STOCKS

        logger.info(f"Testing API data retrieval for {len(symbols)} stocks: {symbols}")

        # Test both APIs for all symbols
        comparisons = []
        fmp_performance = []
        polygon_performance = []

        for symbol in symbols:
            logger.info(f"Testing APIs for {symbol}")

            # Test FMP
            fmp_result = await self._test_fmp_api(symbol)
            fmp_performance.append(fmp_result.response_time_ms)

            # Test Polygon
            polygon_result = await self._test_polygon_api(symbol)
            polygon_performance.append(polygon_result.response_time_ms)

            # Compare results
            comparison = self._compare_api_results(symbol, fmp_result, polygon_result)
            comparisons.append(comparison)

            # Rate limiting between symbols
            await asyncio.sleep(0.5)

        # Generate overall recommendation
        overall_recommendation = self._generate_overall_recommendation(
            comparisons, fmp_performance, polygon_performance
        )

        return {
            "test_summary": {
                "symbols_tested": symbols,
                "test_timestamp": datetime.utcnow().isoformat(),
                "total_symbols": len(symbols),
                "successful_tests": sum(
                    1
                    for c in comparisons
                    if c.fmp_result.success and c.polygon_result.success
                ),
            },
            "individual_comparisons": [
                self._comparison_to_dict(c) for c in comparisons
            ],
            "performance_analysis": {
                "fmp": {
                    "avg_response_time_ms": (
                        sum(fmp_performance) / len(fmp_performance)
                        if fmp_performance
                        else 0
                    ),
                    "max_response_time_ms": (
                        max(fmp_performance) if fmp_performance else 0
                    ),
                    "success_rate": sum(1 for c in comparisons if c.fmp_result.success)
                    / len(comparisons)
                    * 100,
                },
                "polygon": {
                    "avg_response_time_ms": (
                        sum(polygon_performance) / len(polygon_performance)
                        if polygon_performance
                        else 0
                    ),
                    "max_response_time_ms": (
                        max(polygon_performance) if polygon_performance else 0
                    ),
                    "success_rate": sum(
                        1 for c in comparisons if c.polygon_result.success
                    )
                    / len(comparisons)
                    * 100,
                },
            },
            "overall_recommendation": overall_recommendation,
        }

    async def _test_fmp_api(self, symbol: str) -> APITestResult:
        """Test FMP API for a single symbol"""
        start_time = time.time()

        try:
            result = await self.fmp_client.get_quote(symbol)
            response_time = (time.time() - start_time) * 1000

            if result["status"] == "success" and result["quote"]:
                quote_data = result["quote"]

                # Validate data quality
                quality_score, validation_issues = self._validate_quote_data(
                    quote_data, "FMP"
                )

                return APITestResult(
                    api_name="FMP",
                    symbol=symbol,
                    success=True,
                    response_time_ms=response_time,
                    data=quote_data,
                    error_message=None,
                    data_quality_score=quality_score,
                    validation_issues=validation_issues,
                )
            else:
                return APITestResult(
                    api_name="FMP",
                    symbol=symbol,
                    success=False,
                    response_time_ms=response_time,
                    data=None,
                    error_message=result.get("message", "Unknown error"),
                    data_quality_score=0.0,
                    validation_issues=["API call failed"],
                )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return APITestResult(
                api_name="FMP",
                symbol=symbol,
                success=False,
                response_time_ms=response_time,
                data=None,
                error_message=str(e),
                data_quality_score=0.0,
                validation_issues=[f"Exception: {str(e)}"],
            )

    async def _test_polygon_api(self, symbol: str) -> APITestResult:
        """Test Polygon API for a single symbol"""
        start_time = time.time()

        try:
            result = await self.polygon_client.get_quote_with_volume_avg(symbol)
            response_time = (time.time() - start_time) * 1000

            if result["status"] == "success" and result["quote"]:
                quote_data = result["quote"]

                # Validate data quality
                quality_score, validation_issues = self._validate_quote_data(
                    quote_data, "Polygon"
                )

                return APITestResult(
                    api_name="Polygon",
                    symbol=symbol,
                    success=True,
                    response_time_ms=response_time,
                    data=quote_data,
                    error_message=None,
                    data_quality_score=quality_score,
                    validation_issues=validation_issues,
                )
            else:
                return APITestResult(
                    api_name="Polygon",
                    symbol=symbol,
                    success=False,
                    response_time_ms=response_time,
                    data=None,
                    error_message=result.get("message", "Unknown error"),
                    data_quality_score=0.0,
                    validation_issues=["API call failed"],
                )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return APITestResult(
                api_name="Polygon",
                symbol=symbol,
                success=False,
                response_time_ms=response_time,
                data=None,
                error_message=str(e),
                data_quality_score=0.0,
                validation_issues=[f"Exception: {str(e)}"],
            )

    def _validate_quote_data(
        self, quote_data: Dict[str, Any], api_name: str
    ) -> Tuple[float, List[str]]:
        """
        Validate quote data for 1D calculation requirements

        Returns:
            Tuple of (quality_score, validation_issues)
        """
        issues = []
        score = 1.0

        # Required fields for 1D calculation
        required_fields = {
            "price": "Current price",
            "previousClose": "Previous close price",
            "volume": "Current volume",
        }

        # Check required fields
        for field, description in required_fields.items():
            if field not in quote_data or quote_data[field] is None:
                issues.append(f"Missing {description} ({field})")
                score -= 0.3
            else:
                value = quote_data[field]

                # Validate price fields
                if field in ["price", "previousClose"]:
                    if not isinstance(value, (int, float)) or value <= 0:
                        issues.append(f"Invalid {description}: {value}")
                        score -= 0.2
                    elif value < self.MIN_PRICE or value > self.MAX_PRICE:
                        issues.append(
                            f"{description} outside reasonable range: ${value}"
                        )
                        score -= 0.1

                # Validate volume
                elif field == "volume":
                    if not isinstance(value, (int, float)) or value < 0:
                        issues.append(f"Invalid volume: {value}")
                        score -= 0.2

        # Check for average volume (beneficial but not required)
        if "avgVolume" not in quote_data or quote_data["avgVolume"] is None:
            issues.append("Missing average volume (will use volume ratio = 1.0)")
            score -= 0.1

        # Validate price change reasonableness
        if (
            "price" in quote_data
            and "previousClose" in quote_data
            and quote_data["price"] is not None
            and quote_data["previousClose"] is not None
            and quote_data["previousClose"] > 0
        ):

            price_change_percent = abs(
                (quote_data["price"] - quote_data["previousClose"])
                / quote_data["previousClose"]
                * 100
            )
            if price_change_percent > self.MAX_DAILY_CHANGE_PERCENT:
                issues.append(
                    f"Extreme price change: {price_change_percent:.1f}% (>{self.MAX_DAILY_CHANGE_PERCENT}%)"
                )
                score -= 0.1

        # API-specific validations
        if api_name == "FMP":
            # FMP should have market cap data
            if "marketCap" not in quote_data:
                issues.append("Missing market cap data (FMP specific)")
                score -= 0.05

        elif api_name == "Polygon":
            # Polygon should have bid/ask data
            if "bid" not in quote_data or "ask" not in quote_data:
                issues.append("Missing bid/ask data (Polygon specific)")
                score -= 0.05

        return max(0.0, score), issues

    def _compare_api_results(
        self, symbol: str, fmp_result: APITestResult, polygon_result: APITestResult
    ) -> APIComparison:
        """Compare FMP and Polygon results for a symbol"""

        # Calculate data consistency if both APIs succeeded
        consistency_score = 0.0
        if fmp_result.success and polygon_result.success:
            consistency_score = self._calculate_data_consistency(
                fmp_result.data, polygon_result.data
            )

        # Determine recommendation
        recommended_api, reason = self._determine_api_recommendation(
            fmp_result, polygon_result, consistency_score
        )

        return APIComparison(
            symbol=symbol,
            fmp_result=fmp_result,
            polygon_result=polygon_result,
            data_consistency_score=consistency_score,
            recommended_api=recommended_api,
            recommendation_reason=reason,
        )

    def _calculate_data_consistency(
        self, fmp_data: Dict[str, Any], polygon_data: Dict[str, Any]
    ) -> float:
        """Calculate consistency score between FMP and Polygon data"""
        score = 1.0

        # Compare prices (should be very close)
        if (
            "price" in fmp_data
            and "price" in polygon_data
            and fmp_data["price"] is not None
            and polygon_data["price"] is not None
        ):

            price_diff_percent = (
                abs(fmp_data["price"] - polygon_data["price"]) / fmp_data["price"] * 100
            )
            if price_diff_percent > 2.0:  # More than 2% difference is concerning
                score -= 0.3
            elif (
                price_diff_percent > 0.5
            ):  # More than 0.5% difference is moderate concern
                score -= 0.1

        # Compare volumes (can vary more but should be in same ballpark)
        if (
            "volume" in fmp_data
            and "volume" in polygon_data
            and fmp_data["volume"] is not None
            and polygon_data["volume"] is not None
            and fmp_data["volume"] > 0
        ):

            volume_diff_percent = (
                abs(fmp_data["volume"] - polygon_data["volume"])
                / fmp_data["volume"]
                * 100
            )
            if (
                volume_diff_percent > 20.0
            ):  # More than 20% difference is concerning for volume
                score -= 0.2

        return max(0.0, score)

    def _determine_api_recommendation(
        self,
        fmp_result: APITestResult,
        polygon_result: APITestResult,
        consistency_score: float,
    ) -> Tuple[str, str]:
        """Determine which API to recommend for this symbol"""

        # If only one succeeded, recommend that one
        if fmp_result.success and not polygon_result.success:
            return (
                "FMP",
                f"Only FMP succeeded (Polygon error: {polygon_result.error_message})",
            )
        elif polygon_result.success and not fmp_result.success:
            return (
                "Polygon",
                f"Only Polygon succeeded (FMP error: {fmp_result.error_message})",
            )
        elif not fmp_result.success and not polygon_result.success:
            return "Neither", "Both APIs failed"

        # Both succeeded - compare quality and performance
        reasons = []
        fmp_score = 0
        polygon_score = 0

        # Data quality comparison
        if fmp_result.data_quality_score > polygon_result.data_quality_score:
            fmp_score += 2
            reasons.append(
                f"FMP higher data quality ({fmp_result.data_quality_score:.2f} vs {polygon_result.data_quality_score:.2f})"
            )
        elif polygon_result.data_quality_score > fmp_result.data_quality_score:
            polygon_score += 2
            reasons.append(
                f"Polygon higher data quality ({polygon_result.data_quality_score:.2f} vs {fmp_result.data_quality_score:.2f})"
            )

        # Response time comparison (lower is better)
        if (
            fmp_result.response_time_ms < polygon_result.response_time_ms * 0.8
        ):  # 20% faster threshold
            fmp_score += 1
            reasons.append(
                f"FMP faster response ({fmp_result.response_time_ms:.0f}ms vs {polygon_result.response_time_ms:.0f}ms)"
            )
        elif polygon_result.response_time_ms < fmp_result.response_time_ms * 0.8:
            polygon_score += 1
            reasons.append(
                f"Polygon faster response ({polygon_result.response_time_ms:.0f}ms vs {fmp_result.response_time_ms:.0f}ms)"
            )

        # Validation issues comparison
        if len(fmp_result.validation_issues) < len(polygon_result.validation_issues):
            fmp_score += 1
            reasons.append(
                f"FMP fewer validation issues ({len(fmp_result.validation_issues)} vs {len(polygon_result.validation_issues)})"
            )
        elif len(polygon_result.validation_issues) < len(fmp_result.validation_issues):
            polygon_score += 1
            reasons.append(
                f"Polygon fewer validation issues ({len(polygon_result.validation_issues)} vs {len(fmp_result.validation_issues)})"
            )

        # Determine winner
        if fmp_score > polygon_score:
            return "FMP", "; ".join(reasons)
        elif polygon_score > fmp_score:
            return "Polygon", "; ".join(reasons)
        else:
            return (
                "Tie",
                f"Both APIs performed equally well (consistency: {consistency_score:.2f})",
            )

    def _generate_overall_recommendation(
        self,
        comparisons: List[APIComparison],
        fmp_performance: List[float],
        polygon_performance: List[float],
    ) -> Dict[str, Any]:
        """Generate overall API recommendation based on all test results"""

        # Count recommendations
        fmp_wins = sum(1 for c in comparisons if c.recommended_api == "FMP")
        polygon_wins = sum(1 for c in comparisons if c.recommended_api == "Polygon")
        ties = sum(1 for c in comparisons if c.recommended_api == "Tie")
        failures = sum(1 for c in comparisons if c.recommended_api == "Neither")

        # Calculate average metrics
        fmp_avg_quality = sum(
            c.fmp_result.data_quality_score for c in comparisons if c.fmp_result.success
        ) / max(1, sum(1 for c in comparisons if c.fmp_result.success))
        polygon_avg_quality = sum(
            c.polygon_result.data_quality_score
            for c in comparisons
            if c.polygon_result.success
        ) / max(1, sum(1 for c in comparisons if c.polygon_result.success))

        avg_consistency = sum(
            c.data_consistency_score
            for c in comparisons
            if c.data_consistency_score > 0
        ) / max(1, sum(1 for c in comparisons if c.data_consistency_score > 0))

        # Determine overall recommendation
        if fmp_wins > polygon_wins:
            recommended_api = "FMP"
            confidence = fmp_wins / len(comparisons) * 100
        elif polygon_wins > fmp_wins:
            recommended_api = "Polygon"
            confidence = polygon_wins / len(comparisons) * 100
        else:
            recommended_api = (
                "FMP"  # Default to FMP on tie (based on existing codebase usage)
            )
            confidence = 50.0

        return {
            "recommended_primary_api": recommended_api,
            "confidence_percentage": confidence,
            "symbol_results": {
                "fmp_wins": fmp_wins,
                "polygon_wins": polygon_wins,
                "ties": ties,
                "failures": failures,
            },
            "quality_metrics": {
                "fmp_avg_data_quality": fmp_avg_quality,
                "polygon_avg_data_quality": polygon_avg_quality,
                "avg_data_consistency": avg_consistency,
            },
            "recommendation_reasoning": self._build_recommendation_reasoning(
                fmp_wins,
                polygon_wins,
                ties,
                failures,
                fmp_avg_quality,
                polygon_avg_quality,
                avg_consistency,
            ),
        }

    def _build_recommendation_reasoning(
        self,
        fmp_wins: int,
        polygon_wins: int,
        ties: int,
        failures: int,
        fmp_quality: float,
        polygon_quality: float,
        consistency: float,
    ) -> str:
        """Build human-readable recommendation reasoning"""
        total_tests = fmp_wins + polygon_wins + ties + failures

        reasoning = []

        if fmp_wins > polygon_wins:
            reasoning.append(
                f"FMP performed better in {fmp_wins}/{total_tests} tests ({fmp_wins/total_tests*100:.0f}%)"
            )
        elif polygon_wins > fmp_wins:
            reasoning.append(
                f"Polygon performed better in {polygon_wins}/{total_tests} tests ({polygon_wins/total_tests*100:.0f}%)"
            )
        else:
            reasoning.append(f"Both APIs tied in performance ({fmp_wins} wins each)")

        reasoning.append(f"FMP average data quality: {fmp_quality:.2f}")
        reasoning.append(f"Polygon average data quality: {polygon_quality:.2f}")

        if consistency > 0:
            reasoning.append(f"Data consistency between APIs: {consistency:.2f}")

        if failures > 0:
            reasoning.append(f"Warning: {failures} symbols failed on both APIs")

        return "; ".join(reasoning)

    def _comparison_to_dict(self, comparison: APIComparison) -> Dict[str, Any]:
        """Convert APIComparison to dictionary for JSON serialization"""
        return {
            "symbol": comparison.symbol,
            "fmp_result": {
                "success": comparison.fmp_result.success,
                "response_time_ms": comparison.fmp_result.response_time_ms,
                "data_quality_score": comparison.fmp_result.data_quality_score,
                "validation_issues": comparison.fmp_result.validation_issues,
                "error_message": comparison.fmp_result.error_message,
                "data_preview": (
                    self._extract_data_preview(comparison.fmp_result.data)
                    if comparison.fmp_result.data
                    else None
                ),
            },
            "polygon_result": {
                "success": comparison.polygon_result.success,
                "response_time_ms": comparison.polygon_result.response_time_ms,
                "data_quality_score": comparison.polygon_result.data_quality_score,
                "validation_issues": comparison.polygon_result.validation_issues,
                "error_message": comparison.polygon_result.error_message,
                "data_preview": (
                    self._extract_data_preview(comparison.polygon_result.data)
                    if comparison.polygon_result.data
                    else None
                ),
            },
            "data_consistency_score": comparison.data_consistency_score,
            "recommended_api": comparison.recommended_api,
            "recommendation_reason": comparison.recommendation_reason,
        }

    def _extract_data_preview(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key fields for data preview"""
        if not data:
            return {}

        preview_fields = [
            "price",
            "previousClose",
            "volume",
            "avgVolume",
            "marketCap",
            "timestamp",
        ]
        return {field: data.get(field) for field in preview_fields if field in data}

    async def get_1d_stock_data(
        self, symbol: str, preferred_api: str = "auto"
    ) -> Optional[StockData1D]:
        """
        Get validated stock data for 1D calculation

        Args:
            symbol: Stock symbol
            preferred_api: "fmp", "polygon", or "auto" for automatic selection

        Returns:
            StockData1D object or None if data unavailable
        """
        try:
            quote_data = None

            if preferred_api == "auto":
                # Try FMP first, fallback to Polygon
                fmp_result = await self._test_fmp_api(symbol)
                if fmp_result.success and fmp_result.data_quality_score >= 0.7:
                    quote_data = fmp_result.data
                else:
                    polygon_result = await self._test_polygon_api(symbol)
                    if (
                        polygon_result.success
                        and polygon_result.data_quality_score >= 0.7
                    ):
                        quote_data = polygon_result.data

            elif preferred_api == "fmp":
                fmp_result = await self._test_fmp_api(symbol)
                if fmp_result.success:
                    quote_data = fmp_result.data

            elif preferred_api == "polygon":
                polygon_result = await self._test_polygon_api(symbol)
                if polygon_result.success:
                    quote_data = polygon_result.data

            if quote_data:
                return self._convert_to_stock_data_1d(symbol, quote_data)

            return None

        except Exception as e:
            logger.error(f"Error getting 1D stock data for {symbol}: {e}")
            return None

    def _convert_to_stock_data_1d(
        self, symbol: str, quote_data: Dict[str, Any]
    ) -> StockData1D:
        """Convert API quote data to StockData1D format"""
        return StockData1D(
            symbol=symbol.upper(),
            current_price=float(quote_data.get("price", 0)),
            previous_close=float(quote_data.get("previousClose", 0)),
            current_volume=int(quote_data.get("volume", 0)),
            avg_20_day_volume=int(
                quote_data.get("avgVolume", quote_data.get("volume", 0))
            ),
            sector="",  # Will be populated from universe data
        )
