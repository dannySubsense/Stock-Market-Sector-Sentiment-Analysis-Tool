"""
E2E Test Helper Functions for Market Sector Sentiment Analysis Tool
Common utilities and helper functions for E2E test implementation
"""

import time
import asyncio
from typing import Dict, Any, List, Optional
from httpx import AsyncClient, Response
from fastapi import status


async def measure_response_time(
    async_client: AsyncClient,
    endpoint: str,
    method: str = "GET",
    json_data: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> float:
    """
    Measure response time for an API endpoint

    Args:
        async_client: Async HTTP client
        endpoint: API endpoint to measure
        method: HTTP method (GET, POST, etc.)
        json_data: JSON data for POST requests
        **kwargs: Additional arguments for the request

    Returns:
        float: Response time in seconds
    """
    start_time = time.time()

    if method.upper() == "POST":
        if json_data:
            response = await async_client.post(endpoint, json=json_data, **kwargs)
        else:
            response = await async_client.post(endpoint, **kwargs)
    else:
        response = await async_client.get(endpoint, **kwargs)

    end_time = time.time()

    return end_time - start_time


async def retry_request(
    async_client: AsyncClient,
    endpoint: str,
    max_retries: int = 3,
    delay: float = 1.0,
    **kwargs,
) -> Response:
    """
    Retry a request with exponential backoff

    Args:
        async_client: Async HTTP client
        endpoint: API endpoint to request
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        **kwargs: Additional arguments for the request

    Returns:
        Response: HTTP response from the endpoint

    Raises:
        Exception: If all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            response = await async_client.get(endpoint, **kwargs)
            if response.status_code < 500:  # Don't retry on client errors
                return response
        except Exception as e:
            last_exception = e

        if attempt < max_retries:
            await asyncio.sleep(delay * (2**attempt))  # Exponential backoff

    raise last_exception or Exception(
        f"Request to {endpoint} failed after {max_retries} retries"
    )


async def wait_for_analysis_completion(
    async_client: AsyncClient, timeout: int = 300
) -> Dict[str, Any]:
    """
    Wait for analysis to complete and return status

    Args:
        async_client: Async HTTP client
        timeout: Maximum time to wait in seconds

    Returns:
        Dict[str, Any]: Analysis status response

    Raises:
        TimeoutError: If analysis doesn't complete within timeout
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = await async_client.get("/api/analysis/status")
            if response.status_code == 200:
                status_data = response.json()
                if status_data.get("status") == "completed":
                    return status_data
                elif status_data.get("status") == "error":
                    raise Exception(
                        f"Analysis failed: {status_data.get('error', 'Unknown error')}"
                    )
        except Exception as e:
            # Continue waiting on temporary errors
            pass

        await asyncio.sleep(5)  # Check every 5 seconds

    raise TimeoutError(f"Analysis did not complete within {timeout} seconds")


async def simulate_concurrent_users(
    async_client: AsyncClient, endpoint: str, num_users: int = 10, **kwargs
) -> List[float]:
    """
    Simulate concurrent users accessing an endpoint

    Args:
        async_client: Async HTTP client
        endpoint: API endpoint to access
        num_users: Number of concurrent users to simulate
        **kwargs: Additional arguments for the request

    Returns:
        List[float]: List of response times for each user
    """

    async def single_user_request():
        return await measure_response_time(async_client, endpoint, **kwargs)

    # Create concurrent tasks for all users
    tasks = [single_user_request() for _ in range(num_users)]

    # Execute all requests concurrently
    response_times = await asyncio.gather(*tasks)

    return response_times


def extract_sector_names(sectors_data: Dict[str, Any]) -> List[str]:
    """
    Extract sector names from sectors response data

    Args:
        sectors_data: Response data from sectors endpoint

    Returns:
        List[str]: List of sector names
    """
    if "sectors" in sectors_data and isinstance(sectors_data["sectors"], dict):
        return list(sectors_data["sectors"].keys())
    return []


def extract_stock_symbols(stocks_data: Dict[str, Any]) -> List[str]:
    """
    Extract stock symbols from stocks response data

    Args:
        stocks_data: Response data from stocks endpoint

    Returns:
        List[str]: List of stock symbols
    """
    symbols = []
    if "stocks" in stocks_data and isinstance(stocks_data["stocks"], list):
        for stock in stocks_data["stocks"]:
            if isinstance(stock, dict) and "symbol" in stock:
                symbols.append(stock["symbol"])
    return symbols


async def validate_sector_workflow_steps(
    async_client: AsyncClient, workflow_steps: List[str]
) -> List[str]:
    """
    Validate sector dashboard workflow steps

    Args:
        async_client: Async HTTP client
        workflow_steps: Expected workflow steps

    Returns:
        List[str]: List of completed workflow steps
    """
    completed_steps = []

    # Step 1: User opens dashboard (get sectors)
    try:
        response = await async_client.get("/api/sectors")
        if response.status_code == 200:
            completed_steps.append("user_opens_dashboard")
            completed_steps.append("system_loads_sector_grid")
    except Exception:
        pass

    # Step 2: User clicks on sector (get sector details)
    if "user_opens_dashboard" in completed_steps:
        try:
            response = await async_client.get("/api/sectors/technology")
            if response.status_code == 200:
                completed_steps.append("user_clicks_on_sector")
                completed_steps.append("system_shows_sector_details")
        except Exception:
            pass

    # Step 3: User views top stocks (get sector stocks)
    if "user_clicks_on_sector" in completed_steps:
        try:
            response = await async_client.get("/api/sectors/technology/stocks")
            if response.status_code == 200:
                completed_steps.append("user_views_top_stocks")
        except Exception:
            pass

    # Step 4: User triggers refresh (analysis endpoint)
    try:
        response = await async_client.post(
            "/api/analysis/on-demand", json={"analysis_type": "full"}
        )
        if response.status_code == 200:
            completed_steps.append("user_triggers_refresh")
            completed_steps.append("system_completes_analysis")
    except Exception:
        pass

    # Step 5: User sees updated data (get sectors again)
    if "user_triggers_refresh" in completed_steps:
        try:
            response = await async_client.get("/api/sectors")
            if response.status_code == 200:
                completed_steps.append("user_sees_updated_data")
        except Exception:
            pass

    return completed_steps


async def validate_stock_universe_workflow_steps(
    async_client: AsyncClient, workflow_steps: List[str]
) -> List[str]:
    """
    Validate stock universe workflow steps

    Args:
        async_client: Async HTTP client
        workflow_steps: Expected workflow steps

    Returns:
        List[str]: List of completed workflow steps
    """
    completed_steps = []

    # Step 1: User accesses stock universe (get universe stats)
    try:
        response = await async_client.get("/api/stocks/universe/stats")
        if response.status_code == 200:
            completed_steps.append("user_accesses_stock_universe")
            completed_steps.append("system_shows_universe_stats")
    except Exception:
        pass

    # Step 2: User filters by sector (get stocks with sector filter)
    try:
        response = await async_client.get("/api/stocks?sector=technology")
        if response.status_code == 200:
            completed_steps.append("user_filters_by_sector")
    except Exception:
        pass

    # Step 3: User views individual stock (get stock details)
    try:
        response = await async_client.get("/api/stocks/SOUN")
        if response.status_code == 200:
            completed_steps.append("user_views_individual_stock")
    except Exception:
        pass

    # Step 4: User checks gap stocks (get gap stocks)
    try:
        response = await async_client.get("/api/stocks/gaps")
        if response.status_code in [200, 404]:  # Accept both success and not found
            completed_steps.append("user_checks_gap_stocks")
    except Exception:
        pass

    # Step 5: User refreshes universe (refresh endpoint)
    try:
        response = await async_client.post("/api/stocks/universe/refresh")
        if response.status_code == 200:
            completed_steps.append("user_refreshes_universe")
            completed_steps.append("system_updates_universe")
    except Exception:
        pass

    # Step 6: User sees updated data (get stocks again)
    if "user_refreshes_universe" in completed_steps:
        try:
            response = await async_client.get("/api/stocks")
            if response.status_code == 200:
                completed_steps.append("user_sees_updated_data")
        except Exception:
            pass

    return completed_steps


def calculate_cache_hit_rate(cache_stats: Dict[str, Any]) -> float:
    """
    Calculate cache hit rate from cache statistics

    Args:
        cache_stats: Cache statistics response

    Returns:
        float: Cache hit rate (0.0 to 1.0)
    """
    if not cache_stats:
        return 0.0

    hits = cache_stats.get("hits", 0)
    misses = cache_stats.get("misses", 0)
    total = hits + misses

    if total == 0:
        return 0.0

    return hits / total


def format_performance_report(
    test_name: str,
    execution_time: float,
    target_time: float,
    additional_metrics: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Format performance report for E2E tests

    Args:
        test_name: Name of the test
        execution_time: Actual execution time
        target_time: Target execution time
        additional_metrics: Additional performance metrics

    Returns:
        str: Formatted performance report
    """
    report = f"""
E2E Performance Report: {test_name}
=====================================
Execution Time: {execution_time:.3f}s
Target Time: {target_time:.3f}s
Performance: {'✅ PASS' if execution_time < target_time else '❌ FAIL'}
"""

    if additional_metrics:
        report += "\nAdditional Metrics:\n"
        for metric, value in additional_metrics.items():
            report += f"  {metric}: {value}\n"

    return report


async def validate_api_endpoint_chain(
    expected_chain: List[str], executed_chain: List[str], chain_name: str
) -> bool:
    """
    Validate API endpoint chain execution

    Args:
        expected_chain: Expected API chain steps
        executed_chain: Actually executed API chain steps
        chain_name: Name of the API chain

    Returns:
        bool: True if chain validation passes
    """
    assert len(executed_chain) == len(
        expected_chain
    ), f"{chain_name} incomplete: {len(executed_chain)}/{len(expected_chain)} steps"

    for step in expected_chain:
        assert (
            step in executed_chain
        ), f"API chain step '{step}' not executed in {chain_name}"

    return True


async def validate_data_flow_integrity(
    expected_flow: List[str], validated_flows: List[str], flow_name: str
) -> bool:
    """
    Validate data flow integrity

    Args:
        expected_flow: Expected data flow steps
        validated_flows: Actually validated data flow steps
        flow_name: Name of the data flow

    Returns:
        bool: True if flow validation passes
    """
    assert len(validated_flows) == len(
        expected_flow
    ), f"{flow_name} incomplete: {len(validated_flows)}/{len(expected_flow)} steps"

    for step in expected_flow:
        assert (
            step in validated_flows
        ), f"Data flow step '{step}' not validated in {flow_name}"

    return True


async def validate_system_health(
    health_checks: List[str], integration_name: str
) -> bool:
    """
    Validate system health checks

    Args:
        health_checks: List of completed health checks
        integration_name: Name of the integration

    Returns:
        bool: True if health validation passes
    """
    expected_checks = [
        "basic_health_check",
        "performance_validation",
        "stability_validation",
    ]

    for check in expected_checks:
        assert (
            check in health_checks
        ), f"Health check '{check}' not completed in {integration_name}"

    return True


async def validate_data_pipeline_integrity(
    pipeline_steps: List[str], integration_name: str
) -> bool:
    """
    Validate data pipeline integrity

    Args:
        pipeline_steps: List of completed pipeline steps
        integration_name: Name of the integration

    Returns:
        bool: True if pipeline validation passes
    """
    expected_steps = [
        "data_source_validation",
        "data_storage_validation",
        "data_retrieval_validation",
    ]

    for step in expected_steps:
        assert (
            step in pipeline_steps
        ), f"Pipeline step '{step}' not completed in {integration_name}"

    return True


def run_performance_benchmark(
    async_client: AsyncClient, endpoint: str, iterations: int = 10
) -> Dict[str, float]:
    """
    Run performance benchmark for an endpoint

    Args:
        async_client: Async HTTP client
        endpoint: API endpoint to benchmark
        iterations: Number of benchmark iterations

    Returns:
        Dict[str, float]: Benchmark statistics
    """
    response_times = []

    for _ in range(iterations):
        start_time = time.time()
        response = async_client.get(endpoint)
        end_time = time.time()
        response_times.append(end_time - start_time)

    if response_times:
        return {
            "average": sum(response_times) / len(response_times),
            "maximum": max(response_times),
            "minimum": min(response_times),
            "total": sum(response_times),
        }

    return {"average": 0.0, "maximum": 0.0, "minimum": 0.0, "total": 0.0}


def calculate_performance_statistics(response_times: List[float]) -> Dict[str, float]:
    """
    Calculate performance statistics from response times

    Args:
        response_times: List of response times

    Returns:
        Dict[str, float]: Performance statistics
    """
    if not response_times:
        return {"average": 0.0, "maximum": 0.0, "minimum": 0.0, "total": 0.0}

    return {
        "average": sum(response_times) / len(response_times),
        "maximum": max(response_times),
        "minimum": min(response_times),
        "total": sum(response_times),
        "count": len(response_times),
    }


def format_benchmark_report(
    benchmark_name: str,
    total_execution_time: float,
    performance_stats: Dict[str, Any],
    benchmark_targets: Dict[str, float],
) -> str:
    """
    Format benchmark report for E2E tests

    Args:
        benchmark_name: Name of the benchmark
        total_execution_time: Total execution time
        performance_stats: Performance statistics
        benchmark_targets: Benchmark targets

    Returns:
        str: Formatted benchmark report
    """
    report = f"""
E2E Benchmark Report: {benchmark_name}
=====================================
Total Execution Time: {total_execution_time:.3f}s
"""

    if performance_stats:
        report += "\nPerformance Statistics:\n"
        for metric, stats in performance_stats.items():
            if isinstance(stats, dict):
                report += f"  {metric}:\n"
                for stat_name, value in stats.items():
                    if isinstance(value, (int, float)):
                        report += f"    {stat_name}: {value:.3f}s\n"
                    else:
                        report += f"    {stat_name}: {value}\n"
            else:
                report += f"  {metric}: {stats}\n"

    if benchmark_targets:
        report += "\nBenchmark Targets:\n"
        for target, value in benchmark_targets.items():
            report += f"  {target}: {value:.3f}s\n"

    return report


def format_integration_report(
    integration_name: str,
    total_execution_time: float,
    target_time: float,
    performance_metrics: Dict[str, Any],
    completed_steps: List[str],
) -> str:
    """
    Format integration report for E2E tests

    Args:
        integration_name: Name of the integration
        total_execution_time: Total execution time
        target_time: Target execution time
        performance_metrics: Performance metrics
        completed_steps: List of completed steps

    Returns:
        str: Formatted integration report
    """
    report = f"""
E2E Integration Report: {integration_name}
==========================================
Total Execution Time: {total_execution_time:.3f}s
Target Time: {target_time:.3f}s
Performance: {'✅ PASS' if total_execution_time < target_time else '❌ FAIL'}
Completed Steps: {len(completed_steps)}
"""

    if completed_steps:
        report += "\nCompleted Steps:\n"
        for step in completed_steps:
            report += f"  ✅ {step}\n"

    if performance_metrics:
        report += "\nPerformance Metrics:\n"
        for metric, value in performance_metrics.items():
            report += f"  {metric}: {value:.3f}s\n"

    return report
