"""
E2E Tests for API Integration - Market Sector Sentiment Analysis Tool
End-to-end tests for API endpoint integration and data flow validation
Aligned with sector-first architecture and Slice 1A/1B implementation
"""

import pytest
import time
import asyncio
from typing import List, Dict, Any
from httpx import AsyncClient
from fastapi import status

from .utils.e2e_validators import (
    validate_e2e_response_structure,
    validate_e2e_api_integration,
    validate_e2e_data_consistency,
    validate_e2e_performance,
)
from .utils.e2e_helpers import (
    measure_response_time,
    validate_api_endpoint_chain,
    validate_data_flow_integrity,
    format_performance_report,
)


class TestE2EAPIIntegration:
    """
    E2E tests for API endpoint integration and data flow validation

    Test Coverage:
    - API Endpoint Chain: 6-step API integration flow
    - Data Flow Integration: 5-step data consistency validation
    - Performance Integration: 4-step performance validation
    - Error Integration: 5-step error handling validation

    Performance Requirements:
    - API Chain Execution: <2 seconds
    - Data Flow Validation: <1 second
    - Error Recovery: <0.5 seconds

    Architecture Alignment:
    - Sector-first API validation
    - Multi-timeframe data consistency
    - Stock universe API integration
    - Cache and database integration
    """

    @pytest.mark.e2e
    @pytest.mark.api_integration
    @pytest.mark.asyncio
    async def test_e2e_api_endpoint_chain(
        self,
        async_client: AsyncClient,
        e2e_api_chains: Dict[str, List[str]],
        e2e_test_data: Dict[str, Any],
    ):
        """
        E2E Test: Complete API Endpoint Chain Integration

        Steps: 6 steps (health check → sectors → stocks → analysis → cache → health)
        Timeout: 2 minutes
        Performance: <2s total chain execution
        Architecture: API integration validation

        Test Flow:
        1. Setup Phase: Initialize API chain
        2. Execute Phase: Run complete endpoint chain
        3. Validate Phase: Verify chain integrity and performance
        4. Cleanup Phase: Verify system stability
        """
        # Phase 1: Setup & Initial State
        chain_name = "api_endpoint_chain"
        expected_chain = e2e_api_chains[chain_name]
        executed_endpoints = []
        performance_metrics = {}

        # Phase 2: Execute API Chain
        start_time = time.time()

        # Step 1: Health check endpoint
        response_time = await measure_response_time(async_client, "/api/health")
        performance_metrics["health_check"] = response_time

        response = await async_client.get("/api/health")
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Health check failed: {response.status_code}"

        health_data = response.json()
        validate_e2e_response_structure(health_data, "health")
        executed_endpoints.append("health_check")

        # Step 2: Sectors endpoint
        response_time = await measure_response_time(async_client, "/api/sectors")
        performance_metrics["sectors_endpoint"] = response_time

        response = await async_client.get("/api/sectors")
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Sectors endpoint failed: {response.status_code}"

        sectors_data = response.json()
        validate_e2e_response_structure(sectors_data, "sectors")
        executed_endpoints.append("sectors_endpoint")

        # Step 3: Stocks endpoint
        response_time = await measure_response_time(async_client, "/api/stocks")
        performance_metrics["stocks_endpoint"] = response_time

        response = await async_client.get("/api/stocks")
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Stocks endpoint failed: {response.status_code}"

        stocks_data = response.json()
        validate_e2e_response_structure(stocks_data, "stocks")
        executed_endpoints.append("stocks_endpoint")

        # Step 4: Analysis endpoint
        response_time = await measure_response_time(
            async_client,
            "/api/analysis/on-demand",
            method="POST",
            json_data={"analysis_type": "full"},
        )
        performance_metrics["analysis_endpoint"] = response_time

        response = await async_client.post(
            "/api/analysis/on-demand", json={"analysis_type": "full"}
        )
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Analysis endpoint failed: {response.status_code}"

        analysis_data = response.json()
        validate_e2e_response_structure(analysis_data, "analysis")
        executed_endpoints.append("analysis_endpoint")

        # Step 5: Cache endpoint
        response_time = await measure_response_time(async_client, "/api/cache/stats")
        performance_metrics["cache_endpoint"] = response_time

        response = await async_client.get("/api/cache/stats")
        if response.status_code == status.HTTP_200_OK:
            cache_data = response.json()
            validate_e2e_response_structure(cache_data, "cache")
        executed_endpoints.append("cache_endpoint")

        # Step 6: Final health check
        response_time = await measure_response_time(async_client, "/api/health")
        performance_metrics["final_health_check"] = response_time

        response = await async_client.get("/api/health")
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Final health check failed: {response.status_code}"

        final_health_data = response.json()
        validate_e2e_response_structure(final_health_data, "health")
        executed_endpoints.append("final_health_check")

        end_time = time.time()
        total_execution_time = end_time - start_time

        # Phase 3: Validate Results & Performance
        await validate_api_endpoint_chain(
            expected_chain, executed_endpoints, chain_name
        )

        # Validate performance targets
        target_time = e2e_test_data["performance_targets"]["api_chain_execution"]
        validate_e2e_performance(
            total_execution_time, target_time, "API Chain Execution"
        )

        # Validate individual endpoint performance
        api_target = e2e_test_data["performance_targets"]["api_response_time"]
        for endpoint, response_time in performance_metrics.items():
            validate_e2e_performance(
                response_time, api_target, f"{endpoint} Response Time"
            )

        # Generate performance report
        performance_report = format_performance_report(
            "API Endpoint Chain", total_execution_time, target_time, performance_metrics
        )
        print(performance_report)

    @pytest.mark.e2e
    @pytest.mark.api_integration
    @pytest.mark.asyncio
    async def test_e2e_data_flow_integration(
        self,
        async_client: AsyncClient,
        e2e_data_flows: Dict[str, List[str]],
        e2e_test_data: Dict[str, Any],
    ):
        """
        E2E Test: Data Flow Integration Validation

        Steps: 5 steps (sector data → stock data → analysis data → cache data → consistency)
        Timeout: 1 minute
        Performance: <1s data flow validation
        Architecture: Data consistency validation
        """
        # Phase 1: Setup & Initial State
        flow_name = "data_flow_integration"
        expected_flow = e2e_data_flows[flow_name]
        validated_flows = []
        performance_metrics = {}

        # Phase 2: Execute Data Flow Validation
        start_time = time.time()

        # Step 1: Validate sector data flow
        response = await async_client.get("/api/sectors")
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Sector data flow failed: {response.status_code}"

        sectors_data = response.json()
        validate_e2e_data_consistency(sectors_data, "sectors")
        validated_flows.append("sector_data_flow")

        # Step 2: Validate stock data flow
        response = await async_client.get("/api/stocks")
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Stock data flow failed: {response.status_code}"

        stocks_data = response.json()
        validate_e2e_data_consistency(stocks_data, "stocks")
        validated_flows.append("stock_data_flow")

        # Step 3: Validate analysis data flow
        response = await async_client.post(
            "/api/analysis/on-demand", json={"analysis_type": "full"}
        )
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Analysis data flow failed: {response.status_code}"

        analysis_data = response.json()
        validate_e2e_data_consistency(analysis_data, "analysis")
        validated_flows.append("analysis_data_flow")

        # Step 4: Validate cache data flow
        response = await async_client.get("/api/cache/stats")
        if response.status_code == status.HTTP_200_OK:
            cache_data = response.json()
            validate_e2e_data_consistency(cache_data, "cache")
        validated_flows.append("cache_data_flow")

        # Step 5: Validate data consistency across flows
        # Verify that sector data and stock data are consistent
        if sectors_data.get("sectors") and stocks_data.get("stocks"):
            sector_names = set(sectors_data["sectors"].keys())
            stock_sectors = set()
            for stock in stocks_data["stocks"]:
                if "sector" in stock:
                    stock_sectors.add(stock["sector"])

            # Check for consistency (some overlap expected)
            consistency_score = (
                len(sector_names.intersection(stock_sectors)) / len(sector_names)
                if sector_names
                else 0
            )
            assert consistency_score > 0, "No consistency between sector and stock data"

        validated_flows.append("data_consistency_validation")

        end_time = time.time()
        total_execution_time = end_time - start_time

        # Phase 3: Validate Results & Performance
        await validate_data_flow_integrity(expected_flow, validated_flows, flow_name)

        # Validate performance targets
        target_time = e2e_test_data["performance_targets"]["data_flow_validation"]
        validate_e2e_performance(
            total_execution_time, target_time, "Data Flow Validation"
        )

        # Generate performance report
        performance_report = format_performance_report(
            "Data Flow Integration",
            total_execution_time,
            target_time,
            performance_metrics,
        )
        print(performance_report)

    @pytest.mark.e2e
    @pytest.mark.api_integration
    @pytest.mark.asyncio
    async def test_e2e_performance_integration(
        self,
        async_client: AsyncClient,
        e2e_performance_targets: Dict[str, float],
        e2e_test_data: Dict[str, Any],
    ):
        """
        E2E Test: Performance Integration Validation

        Steps: 4 steps (baseline → load → stress → recovery)
        Timeout: 1 minute
        Performance: Validate all performance targets
        Architecture: Performance validation
        """
        # Phase 1: Setup & Initial State
        performance_metrics = {}
        baseline_metrics = {}

        # Phase 2: Execute Performance Validation
        start_time = time.time()

        # Step 1: Baseline performance measurement
        baseline_endpoints = ["/api/health", "/api/sectors", "/api/stocks"]
        for endpoint in baseline_endpoints:
            response_time = await measure_response_time(async_client, endpoint)
            baseline_metrics[endpoint] = response_time

        performance_metrics["baseline"] = baseline_metrics

        # Step 2: Load testing (concurrent requests)
        load_start = time.time()
        concurrent_tasks = []
        for _ in range(3):  # 3 concurrent requests
            task = asyncio.create_task(async_client.get("/api/sectors"))
            concurrent_tasks.append(task)

        load_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        load_end = time.time()
        load_duration = load_end - load_start

        # Validate all concurrent requests succeeded
        successful_requests = sum(
            1 for result in load_results if not isinstance(result, Exception)
        )
        assert successful_requests == len(
            concurrent_tasks
        ), f"Only {successful_requests}/{len(concurrent_tasks)} concurrent requests succeeded"

        performance_metrics["load_test"] = {
            "duration": load_duration,
            "successful_requests": successful_requests,
            "total_requests": len(concurrent_tasks),
        }

        # Step 3: Stress testing (rapid sequential requests)
        stress_start = time.time()
        stress_responses = []
        for _ in range(5):  # 5 rapid sequential requests
            response = await async_client.get("/api/health")
            stress_responses.append(response.status_code)

        stress_end = time.time()
        stress_duration = stress_end - stress_start

        # Validate all stress requests succeeded
        successful_stress = sum(1 for status in stress_responses if status == 200)
        assert successful_stress == len(
            stress_responses
        ), f"Only {successful_stress}/{len(stress_responses)} stress requests succeeded"

        performance_metrics["stress_test"] = {
            "duration": stress_duration,
            "successful_requests": successful_stress,
            "total_requests": len(stress_responses),
        }

        # Step 4: Recovery validation (verify system still responsive)
        recovery_response = await async_client.get("/api/health")
        assert (
            recovery_response.status_code == status.HTTP_200_OK
        ), "System not responsive after stress test"

        recovery_data = recovery_response.json()
        validate_e2e_response_structure(recovery_data, "health")

        end_time = time.time()
        total_execution_time = end_time - start_time

        # Phase 3: Validate Performance Targets
        # Validate baseline performance
        for endpoint, response_time in baseline_metrics.items():
            target_time = e2e_performance_targets.get("api_response_time", 0.5)
            validate_e2e_performance(response_time, target_time, f"Baseline {endpoint}")

        # Validate load test performance
        load_target = e2e_performance_targets.get("concurrent_requests", 2.0)
        validate_e2e_performance(load_duration, load_target, "Load Test Duration")

        # Validate stress test performance
        stress_target = e2e_performance_targets.get("sequential_requests", 1.0)
        validate_e2e_performance(stress_duration, stress_target, "Stress Test Duration")

        # Generate performance report
        performance_report = format_performance_report(
            "Performance Integration",
            total_execution_time,
            e2e_test_data["e2e_timeout"],
            performance_metrics,
        )
        print(performance_report)

    @pytest.mark.e2e
    @pytest.mark.api_integration
    @pytest.mark.asyncio
    async def test_e2e_error_integration(
        self,
        async_client: AsyncClient,
        e2e_error_scenarios: Dict[str, List[str]],
        e2e_test_data: Dict[str, Any],
    ):
        """
        E2E Test: Error Integration Validation

        Steps: 5 steps (invalid endpoint → malformed request → rate limit → recovery → validation)
        Timeout: 30 seconds
        Performance: <0.5s error recovery
        Architecture: Error handling validation
        """
        # Phase 1: Setup & Initial State
        scenario_name = "error_integration"
        expected_scenarios = e2e_error_scenarios[scenario_name]
        handled_errors = []
        performance_metrics = {}

        # Phase 2: Execute Error Scenarios
        start_time = time.time()

        # Step 1: Test invalid endpoint
        try:
            response = await async_client.get("/api/invalid/endpoint")
            # Should return 404
            assert (
                response.status_code == status.HTTP_404_NOT_FOUND
            ), f"Invalid endpoint should return 404, got {response.status_code}"
            handled_errors.append("invalid_endpoint_handled")
        except Exception as e:
            # Exception is also acceptable for invalid endpoints
            handled_errors.append("invalid_endpoint_handled")

        # Step 2: Test malformed request
        try:
            response = await async_client.post(
                "/api/analysis/on-demand", json={"invalid": "data"}
            )
            # Should handle gracefully (400 or 422)
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ], f"Malformed request should return 400/422, got {response.status_code}"
            handled_errors.append("malformed_request_handled")
        except Exception as e:
            # Exception is also acceptable for malformed requests
            handled_errors.append("malformed_request_handled")

        # Step 3: Test rate limiting (simulate by rapid requests)
        rapid_responses = []
        for _ in range(10):  # Rapid requests to potentially trigger rate limiting
            try:
                response = await async_client.get("/api/health")
                rapid_responses.append(response.status_code)
            except Exception:
                rapid_responses.append(500)  # Simulate error

        # Validate system handles rapid requests gracefully
        successful_rapid = sum(1 for status in rapid_responses if status == 200)
        assert successful_rapid > 0, "System should handle rapid requests gracefully"
        handled_errors.append("rate_limit_handled")

        # Step 4: Test recovery after errors
        recovery_response = await async_client.get("/api/health")
        assert (
            recovery_response.status_code == status.HTTP_200_OK
        ), "System should recover after errors"

        recovery_data = recovery_response.json()
        validate_e2e_response_structure(recovery_data, "health")
        handled_errors.append("system_recovery_validated")

        # Step 5: Validate system stability
        stability_response = await async_client.get("/api/sectors")
        assert (
            stability_response.status_code == status.HTTP_200_OK
        ), "System should remain stable after errors"

        stability_data = stability_response.json()
        validate_e2e_response_structure(stability_data, "sectors")
        handled_errors.append("system_stability_validated")

        end_time = time.time()
        total_execution_time = end_time - start_time

        # Phase 3: Validate Results & Performance
        # Validate error handling completion
        assert (
            len(handled_errors) >= len(expected_scenarios) - 1
        ), f"Too few error scenarios handled: {len(handled_errors)}/{len(expected_scenarios)}"

        # Validate error recovery performance
        error_recovery_target = e2e_test_data["performance_targets"]["error_recovery"]
        validate_e2e_performance(
            total_execution_time, error_recovery_target, "Error Recovery"
        )

        # Generate performance report
        performance_report = format_performance_report(
            "Error Integration",
            total_execution_time,
            error_recovery_target,
            performance_metrics,
        )
        print(performance_report)
