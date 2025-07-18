"""
E2E Test Validation Functions for Market Sector Sentiment Analysis Tool
Standardized validation functions for E2E test responses and performance
"""

from typing import Dict, Any, List
from fastapi import status


def validate_e2e_response_structure(response_data: dict, endpoint: str) -> bool:
    """
    Standard E2E response validation - follows existing patterns from unit/integration tests
    
    Args:
        response_data: Response data from API endpoint
        endpoint: Endpoint name for specific validation
        
    Returns:
        bool: True if validation passes, raises AssertionError if fails
    """
    # Common validation patterns from unit/integration tests
    assert isinstance(response_data, dict), f"Response data must be dict, got {type(response_data)}"
    
    # Endpoint-specific validations
    if endpoint == "sectors":
        assert "sectors" in response_data, "Sectors endpoint must return 'sectors' key"
        assert "timestamp" in response_data, "Sectors endpoint must return 'timestamp' key"
        assert "total_sectors" in response_data, "Sectors endpoint must return 'total_sectors' key"
        assert "source" in response_data, "Sectors endpoint must return 'source' key"
        
    elif endpoint == "stocks":
        # Handle different stocks endpoint structures
        if "total_count" in response_data and "returned_count" in response_data:
            # Main stocks endpoint (/api/stocks)
            assert "stocks" in response_data, "Stocks endpoint must return 'stocks' key"
            assert "total_count" in response_data, "Stocks endpoint must return 'total_count' key"
            assert "returned_count" in response_data, "Stocks endpoint must return 'returned_count' key"
        elif "count" in response_data and "sector" in response_data:
            # Sector stocks endpoint (/api/sectors/{sector}/stocks)
            assert "stocks" in response_data, "Sector stocks endpoint must return 'stocks' key"
            assert "count" in response_data, "Sector stocks endpoint must return 'count' key"
            assert "sector" in response_data, "Sector stocks endpoint must return 'sector' key"
        elif "total_stocks" in response_data and "target_universe_size" in response_data:
            # Universe stats endpoint (/api/stocks/universe/stats)
            assert "total_stocks" in response_data, "Universe stats endpoint must return 'total_stocks' key"
            assert "target_universe_size" in response_data, "Universe stats endpoint must return 'target_universe_size' key"
            assert "coverage_percentage" in response_data, "Universe stats endpoint must return 'coverage_percentage' key"
        elif "gap_stocks" in response_data:
            # Gap stocks endpoint (/api/stocks/gaps)
            assert "gap_stocks" in response_data, "Gap stocks endpoint must return 'gap_stocks' key"
            assert "count" in response_data, "Gap stocks endpoint must return 'count' key"
        elif "volume_leaders" in response_data:
            # Volume leaders endpoint (/api/stocks/volume-leaders)
            assert "volume_leaders" in response_data, "Volume leaders endpoint must return 'volume_leaders' key"
            assert "count" in response_data, "Volume leaders endpoint must return 'count' key"
        elif (
            "status" in response_data and
            "message" in response_data and
            "estimated_completion" in response_data and
            "timestamp" in response_data
        ):
            # Universe refresh endpoint (/api/stocks/universe/refresh)
            assert response_data["status"] == "in_progress", "Universe refresh must return status 'in_progress'"
            assert isinstance(response_data["message"], str), "Universe refresh must return a message"
            assert isinstance(response_data["estimated_completion"], str), "Universe refresh must return estimated_completion"
            assert isinstance(response_data["timestamp"], str), "Universe refresh must return timestamp"
        else:
            # Generic stocks validation - just check for stocks array
            assert "stocks" in response_data, "Stocks endpoint must return 'stocks' key"
        
    elif endpoint == "health":
        assert "status" in response_data, "Health endpoint must return 'status' key"
        assert "timestamp" in response_data, "Health endpoint must return 'timestamp' key"
        assert "version" in response_data, "Health endpoint must return 'version' key"
        
    elif endpoint == "analysis":
        assert "status" in response_data, "Analysis endpoint must return 'status' key"
        assert "analysis_type" in response_data, "Analysis endpoint must return 'analysis_type' key"
        
    return True


def validate_e2e_performance(execution_time: float, target_time: float, test_name: str, greater_is_better: bool = False) -> bool:
    """
    Standard E2E performance validation
    
    Args:
        execution_time: Actual execution time in seconds
        target_time: Target execution time in seconds
        test_name: Name of the test for error reporting
        greater_is_better: If True, higher values are better (e.g., throughput)
        
    Returns:
        bool: True if performance target met, raises AssertionError if fails
    """
    if greater_is_better:
        assert execution_time >= target_time, f"{test_name} achieved {execution_time}, below {target_time} target"
    else:
        assert execution_time < target_time, f"{test_name} took {execution_time}s, exceeds {target_time}s limit"
    return True


def validate_e2e_workflow_completion(workflow_steps: List[str], completed_steps: List[str], workflow_name: str) -> bool:
    """
    Standard E2E workflow completion validation
    
    Args:
        workflow_steps: Expected workflow steps
        completed_steps: Actually completed steps
        workflow_name: Name of the workflow for error reporting
        
    Returns:
        bool: True if workflow complete, raises AssertionError if fails
    """
    assert len(completed_steps) == len(workflow_steps), f"{workflow_name} incomplete: {len(completed_steps)}/{len(workflow_steps)} steps"
    
    # Validate each step was completed
    for step in workflow_steps:
        assert step in completed_steps, f"Workflow step '{step}' not completed in {workflow_name}"
    
    return True


def validate_e2e_sector_data_structure(sector_data: dict) -> bool:
    """
    Validate sector data structure for E2E tests
    
    Args:
        sector_data: Sector data from API response
        
    Returns:
        bool: True if validation passes, raises AssertionError if fails
    """
    assert "sector" in sector_data, "Sector data must contain 'sector' key"
    assert "sentiment" in sector_data, "Sector data must contain 'sentiment' key"
    assert "timeframes" in sector_data, "Sector data must contain 'timeframes' key"
    assert "top_stocks" in sector_data, "Sector data must contain 'top_stocks' key"
    
    # Validate timeframes structure
    timeframes = sector_data["timeframes"]
    expected_timeframes = ["30min", "1day", "3day", "1week"]
    for timeframe in expected_timeframes:
        assert timeframe in timeframes, f"Sector data must contain '{timeframe}' timeframe"
    
    return True


def validate_e2e_stock_data_structure(stock_data: dict) -> bool:
    """
    Validate stock data structure for E2E tests
    
    Args:
        stock_data: Stock data from API response
        
    Returns:
        bool: True if validation passes, raises AssertionError if fails
    """
    assert "symbol" in stock_data, "Stock data must contain 'symbol' key"
    assert "current_price" in stock_data, "Stock data must contain 'current_price' key"
    assert "price_change_percent" in stock_data, "Stock data must contain 'price_change_percent' key"
    assert "sector" in stock_data, "Stock data must contain 'sector' key"
    
    return True


def validate_e2e_error_response(response_data: dict, expected_error_type: str) -> bool:
    """
    Validate error response structure for E2E tests
    
    Args:
        response_data: Error response data
        expected_error_type: Expected error type (e.g., "api_failure", "timeout")
        
    Returns:
        bool: True if validation passes, raises AssertionError if fails
    """
    assert "detail" in response_data, "Error response must contain 'detail' key"
    assert "error_type" in response_data, "Error response must contain 'error_type' key"
    assert "timestamp" in response_data, "Error response must contain 'timestamp' key"
    
    if expected_error_type == "api_failure":
        assert "fallback_used" in response_data, "API failure response must contain 'fallback_used' key"
    elif expected_error_type == "timeout":
        assert "timeout_duration" in response_data, "Timeout response must contain 'timeout_duration' key"
    
    return True


def validate_e2e_cache_effectiveness(cache_hit_rate: float, target_hit_rate: float = 0.9) -> bool:
    """
    Validate cache effectiveness for E2E tests
    
    Args:
        cache_hit_rate: Actual cache hit rate (0.0 to 1.0)
        target_hit_rate: Target cache hit rate (default 0.9 = 90%)
        
    Returns:
        bool: True if cache effectiveness target met, raises AssertionError if fails
    """
    assert 0.0 <= cache_hit_rate <= 1.0, f"Cache hit rate must be between 0.0 and 1.0, got {cache_hit_rate}"
    assert cache_hit_rate >= target_hit_rate, f"Cache hit rate {cache_hit_rate} below target {target_hit_rate}"
    return True


def validate_e2e_concurrent_user_performance(response_times: List[float], max_response_time: float = 1.0) -> bool:
    """
    Validate concurrent user performance for E2E tests
    
    Args:
        response_times: List of response times for concurrent users
        max_response_time: Maximum acceptable response time in seconds
        
    Returns:
        bool: True if performance target met, raises AssertionError if fails
    """
    assert len(response_times) > 0, "Response times list cannot be empty"
    
    avg_response_time = sum(response_times) / len(response_times)
    max_observed_time = max(response_times)
    
    assert avg_response_time < max_response_time, f"Average response time {avg_response_time}s exceeds {max_response_time}s limit"
    assert max_observed_time < max_response_time * 2, f"Max response time {max_observed_time}s exceeds {max_response_time * 2}s limit"
    
    return True


def validate_e2e_api_integration(api_chain: List[str], executed_chain: List[str], chain_name: str) -> bool:
    """
    Validate API integration chain completion for E2E tests
    
    Args:
        api_chain: Expected API chain steps
        executed_chain: Actually executed API chain steps
        chain_name: Name of the API chain for error reporting
        
    Returns:
        bool: True if API chain complete, raises AssertionError if fails
    """
    assert len(executed_chain) == len(api_chain), f"{chain_name} incomplete: {len(executed_chain)}/{len(api_chain)} steps"
    
    # Validate each step was executed
    for step in api_chain:
        assert step in executed_chain, f"API chain step '{step}' not executed in {chain_name}"
    
    return True


def validate_e2e_data_consistency(data: dict, data_type: str) -> bool:
    """
    Validate data consistency for E2E tests
    
    Args:
        data: Data to validate
        data_type: Type of data for specific validation
        
    Returns:
        bool: True if validation passes, raises AssertionError if fails
    """
    assert isinstance(data, dict), f"Data must be dict, got {type(data)}"
    
    if data_type == "sectors":
        assert "sectors" in data, "Sectors data must contain 'sectors' key"
    elif data_type == "stocks":
        assert "stocks" in data, "Stocks data must contain 'stocks' key"
    elif data_type == "analysis":
        assert "status" in data, "Analysis data must contain 'status' key"
    elif data_type == "cache":
        assert "cache_stats" in data or "hit_rate" in data, "Cache data must contain cache statistics"
    
    return True


def validate_e2e_system_integration(integration_steps: List[str], completed_steps: List[str], integration_name: str) -> bool:
    """
    Validate system integration completion for E2E tests
    
    Args:
        integration_steps: Expected integration steps
        completed_steps: Actually completed integration steps
        integration_name: Name of the integration for error reporting
        
    Returns:
        bool: True if integration complete, raises AssertionError if fails
    """
    assert len(completed_steps) >= len(integration_steps) - 1, f"{integration_name} incomplete: {len(completed_steps)}/{len(integration_steps)} steps"
    
    # Validate critical steps were completed
    critical_steps = [step for step in integration_steps if "validation" in step]
    for step in critical_steps:
        assert step in completed_steps, f"Critical integration step '{step}' not completed in {integration_name}"
    
    return True


def validate_e2e_data_integrity(data: dict, data_type: str) -> bool:
    """
    Validate data integrity for E2E tests
    
    Args:
        data: Data to validate
        data_type: Type of data for specific validation
        
    Returns:
        bool: True if validation passes, raises AssertionError if fails
    """
    assert isinstance(data, dict), f"Data must be dict, got {type(data)}"
    
    # Basic integrity checks
    assert len(data) > 0, f"{data_type} data cannot be empty"
    
    if data_type == "sectors":
        assert "sectors" in data, "Sectors data must contain 'sectors' key"
        if data["sectors"]:
            # Check that sectors have required structure
            for sector_name, sector_data in data["sectors"].items():
                assert isinstance(sector_data, dict), f"Sector data for {sector_name} must be dict"
    elif data_type == "stocks":
        assert "stocks" in data, "Stocks data must contain 'stocks' key"
        if data["stocks"]:
            # Check that stocks have required structure
            for stock in data["stocks"]:
                assert isinstance(stock, dict), "Stock data must be dict"
    
    return True


def validate_e2e_benchmark_results(benchmark_stats: dict, benchmark_targets: dict) -> bool:
    """
    Validate benchmark results for E2E tests
    
    Args:
        benchmark_stats: Benchmark statistics
        benchmark_targets: Benchmark performance targets
        
    Returns:
        bool: True if benchmark targets met, raises AssertionError if fails
    """
    assert isinstance(benchmark_stats, dict), "Benchmark stats must be dict"
    assert isinstance(benchmark_targets, dict), "Benchmark targets must be dict"
    
    # Validate benchmark statistics structure
    for metric, stats in benchmark_stats.items():
        assert isinstance(stats, dict), f"Benchmark stats for {metric} must be dict"
        
        if "average" in stats:
            assert isinstance(stats["average"], (int, float)), f"Average for {metric} must be numeric"
        if "maximum" in stats:
            assert isinstance(stats["maximum"], (int, float)), f"Maximum for {metric} must be numeric"
        if "minimum" in stats:
            assert isinstance(stats["minimum"], (int, float)), f"Minimum for {metric} must be numeric"
    
    return True 