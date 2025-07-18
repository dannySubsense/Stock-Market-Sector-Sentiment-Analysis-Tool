"""
E2E Tests for Performance Benchmarking - Market Sector Sentiment Analysis Tool
End-to-end tests for performance validation and benchmarking
Aligned with sector-first architecture and Slice 1A/1B implementation
"""

import pytest
import time
import asyncio
import statistics
from typing import List, Dict, Any
from httpx import AsyncClient
from fastapi import status

from .utils.e2e_validators import (
    validate_e2e_response_structure,
    validate_e2e_performance,
    validate_e2e_benchmark_results
)
from .utils.e2e_helpers import (
    measure_response_time,
    run_performance_benchmark,
    calculate_performance_statistics,
    format_benchmark_report
)


class TestE2EPerformanceBenchmarking:
    """
    E2E tests for performance validation and benchmarking
    
    Test Coverage:
    - Response Time Benchmarking: 4-step response time validation
    - Throughput Benchmarking: 4-step throughput validation
    - Load Testing: 4-step load validation
    - Stress Testing: 4-step stress validation
    
    Performance Requirements:
    - Response Time: <0.5 seconds average
    - Throughput: >100 requests/minute
    - Load Capacity: 10 concurrent users
    - Stress Recovery: <1 second recovery
    
    Architecture Alignment:
    - Sector-first performance validation
    - Multi-timeframe analysis performance
    - Stock universe query performance
    - Cache performance validation
    """

    @pytest.mark.e2e
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_e2e_response_time_benchmarking(self, async_client: AsyncClient,
                                                 e2e_benchmark_targets: Dict[str, float],
                                                 e2e_test_data: Dict[str, Any]):
        """
        E2E Test: Response Time Performance Benchmarking
        
        Steps: 4 steps (baseline → warmup → measurement → validation)
        Timeout: 2 minutes
        Performance: <0.5s average response time
        Architecture: Response time validation
        
        Test Flow:
        1. Setup Phase: Initialize benchmark environment
        2. Execute Phase: Run response time measurements
        3. Validate Phase: Verify performance targets
        4. Report Phase: Generate benchmark report
        """
        # Phase 1: Setup & Initial State
        benchmark_name = "response_time_benchmarking"
        target_response_time = e2e_benchmark_targets["response_time"]
        test_endpoints = ["/api/health", "/api/sectors", "/api/stocks"]
        response_times = {endpoint: [] for endpoint in test_endpoints}
        
        # Phase 2: Execute Benchmark
        start_time = time.time()
        
        # Step 1: Baseline measurement (cold start)
        print(f"Running baseline measurements for {benchmark_name}...")
        for endpoint in test_endpoints:
            response_time = await measure_response_time(async_client, endpoint)
            response_times[endpoint].append(response_time)
        
        # Step 2: Warmup phase (prime the system)
        print(f"Running warmup phase for {benchmark_name}...")
        for _ in range(3):  # 3 warmup iterations
            for endpoint in test_endpoints:
                await async_client.get(endpoint)
        
        # Step 3: Measurement phase (collect performance data)
        print(f"Running measurement phase for {benchmark_name}...")
        measurement_iterations = 10  # 10 measurements per endpoint
        
        for _ in range(measurement_iterations):
            for endpoint in test_endpoints:
                response_time = await measure_response_time(async_client, endpoint)
                response_times[endpoint].append(response_time)
        
        # Step 4: Validation phase (verify data integrity)
        print(f"Running validation phase for {benchmark_name}...")
        for endpoint in test_endpoints:
            response = await async_client.get(endpoint)
            assert response.status_code == status.HTTP_200_OK, f"Validation failed for {endpoint}: {response.status_code}"
            
            response_data = response.json()
            validate_e2e_response_structure(response_data, endpoint.split("/")[-1])
        
        end_time = time.time()
        total_execution_time = end_time - start_time
        
        # Phase 3: Calculate Performance Statistics
        performance_stats = {}
        for endpoint, times in response_times.items():
            if times:  # Skip empty lists
                stats = calculate_performance_statistics(times)
                performance_stats[endpoint] = stats
        
        # Phase 4: Validate Performance Targets
        all_response_times = []
        for times in response_times.values():
            all_response_times.extend(times)
        
        if all_response_times:
            average_response_time = statistics.mean(all_response_times)
            max_response_time = max(all_response_times)
            min_response_time = min(all_response_times)
            
            # Validate average response time
            validate_e2e_performance(average_response_time, target_response_time, "Average Response Time")
            
            # Validate max response time (should be reasonable)
            max_target = target_response_time * 3  # Allow 3x the target for max
            validate_e2e_performance(max_response_time, max_target, "Maximum Response Time")
        
        # Phase 5: Generate Benchmark Report
        benchmark_report = format_benchmark_report(
            benchmark_name,
            total_execution_time,
            performance_stats,
            e2e_benchmark_targets
        )
        print(benchmark_report)
        
        # Validate total execution time
        max_benchmark_time = e2e_test_data["e2e_timeout"]
        assert total_execution_time < max_benchmark_time, f"Benchmark took {total_execution_time}s, exceeds {max_benchmark_time}s limit"

    @pytest.mark.e2e
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_e2e_throughput_benchmarking(self, async_client: AsyncClient,
                                              e2e_benchmark_targets: Dict[str, float],
                                              e2e_test_data: Dict[str, Any]):
        """
        E2E Test: Throughput Performance Benchmarking
        
        Steps: 4 steps (baseline → concurrent → sustained → validation)
        Timeout: 2 minutes
        Performance: >100 requests/minute throughput
        Architecture: Throughput validation
        """
        # Phase 1: Setup & Initial State
        benchmark_name = "throughput_benchmarking"
        target_throughput = e2e_benchmark_targets["throughput"]  # requests per minute
        test_endpoint = "/api/health"  # Use health endpoint for throughput testing
        throughput_results = []
        
        # Phase 2: Execute Benchmark
        start_time = time.time()
        
        # Step 1: Baseline throughput measurement
        print(f"Running baseline throughput measurement for {benchmark_name}...")
        baseline_start = time.time()
        baseline_requests = 10
        
        for _ in range(baseline_requests):
            response = await async_client.get(test_endpoint)
            assert response.status_code == status.HTTP_200_OK, f"Baseline request failed: {response.status_code}"
        
        baseline_end = time.time()
        baseline_duration = baseline_end - baseline_start
        baseline_throughput = (baseline_requests / baseline_duration) * 60  # requests per minute
        throughput_results.append(("baseline", baseline_throughput, baseline_duration))
        
        # Step 2: Concurrent throughput measurement
        print(f"Running concurrent throughput measurement for {benchmark_name}...")
        concurrent_requests = 20
        concurrent_start = time.time()
        
        # Create concurrent tasks
        concurrent_tasks = []
        for _ in range(concurrent_requests):
            task = asyncio.create_task(async_client.get(test_endpoint))
            concurrent_tasks.append(task)
        
        # Execute concurrent requests
        concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        concurrent_end = time.time()
        concurrent_duration = concurrent_end - concurrent_start
        
        # Count successful requests
        successful_concurrent = sum(1 for result in concurrent_results if not isinstance(result, Exception))
        concurrent_throughput = (successful_concurrent / concurrent_duration) * 60
        throughput_results.append(("concurrent", concurrent_throughput, concurrent_duration))
        
        # Step 3: Sustained throughput measurement
        print(f"Running sustained throughput measurement for {benchmark_name}...")
        sustained_requests = 50
        sustained_start = time.time()
        
        for i in range(sustained_requests):
            response = await async_client.get(test_endpoint)
            assert response.status_code == status.HTTP_200_OK, f"Sustained request {i} failed: {response.status_code}"
            
            # Small delay to simulate realistic usage
            if i % 10 == 0:  # Every 10th request
                await asyncio.sleep(0.1)
        
        sustained_end = time.time()
        sustained_duration = sustained_end - sustained_start
        sustained_throughput = (sustained_requests / sustained_duration) * 60
        throughput_results.append(("sustained", sustained_throughput, sustained_duration))
        
        # Step 4: Validation phase
        print(f"Running validation phase for {benchmark_name}...")
        validation_response = await async_client.get(test_endpoint)
        assert validation_response.status_code == status.HTTP_200_OK, "Validation failed after throughput test"
        
        validation_data = validation_response.json()
        validate_e2e_response_structure(validation_data, "health")
        
        end_time = time.time()
        total_execution_time = end_time - start_time
        
        # Phase 3: Calculate Performance Statistics
        throughput_values = [result[1] for result in throughput_results]
        if throughput_values:
            average_throughput = statistics.mean(throughput_values)
            max_throughput = max(throughput_values)
            min_throughput = min(throughput_values)
            
            # Validate throughput targets
            validate_e2e_performance(average_throughput, target_throughput, "Average Throughput", greater_is_better=True)
            
            # Validate minimum throughput (should meet target)
            validate_e2e_performance(min_throughput, target_throughput * 0.8, "Minimum Throughput", greater_is_better=True)
        
        # Phase 4: Generate Benchmark Report
        performance_stats = {
            "throughput": {
                "average": average_throughput if throughput_values else 0,
                "maximum": max_throughput if throughput_values else 0,
                "minimum": min_throughput if throughput_values else 0,
                "results": throughput_results
            }
        }
        
        benchmark_report = format_benchmark_report(
            benchmark_name,
            total_execution_time,
            performance_stats,
            e2e_benchmark_targets
        )
        print(benchmark_report)
        
        # Validate total execution time
        max_benchmark_time = e2e_test_data["e2e_timeout"]
        assert total_execution_time < max_benchmark_time, f"Benchmark took {total_execution_time}s, exceeds {max_benchmark_time}s limit"

    @pytest.mark.e2e
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_e2e_load_testing(self, async_client: AsyncClient,
                                   e2e_benchmark_targets: Dict[str, float],
                                   e2e_test_data: Dict[str, Any]):
        """
        E2E Test: Load Testing Performance Validation
        
        Steps: 4 steps (baseline → light load → medium load → heavy load)
        Timeout: 3 minutes
        Performance: Handle 10 concurrent users
        Architecture: Load capacity validation
        """
        # Phase 1: Setup & Initial State
        benchmark_name = "load_testing"
        target_concurrent_users = e2e_benchmark_targets["concurrent_users"]
        test_endpoint = "/api/sectors"  # Use sectors endpoint for load testing
        load_results = []
        
        # Phase 2: Execute Load Tests
        start_time = time.time()
        
        # Step 1: Baseline load (1 concurrent user)
        print(f"Running baseline load test for {benchmark_name}...")
        baseline_users = 1
        baseline_start = time.time()
        
        baseline_tasks = [asyncio.create_task(async_client.get(test_endpoint)) for _ in range(baseline_users)]
        baseline_results = await asyncio.gather(*baseline_tasks, return_exceptions=True)
        baseline_end = time.time()
        
        baseline_successful = sum(1 for result in baseline_results if not isinstance(result, Exception))
        baseline_duration = baseline_end - baseline_start
        load_results.append(("baseline", baseline_users, baseline_successful, baseline_duration))
        
        # Step 2: Light load (5 concurrent users)
        print(f"Running light load test for {benchmark_name}...")
        light_users = 5
        light_start = time.time()
        
        light_tasks = [asyncio.create_task(async_client.get(test_endpoint)) for _ in range(light_users)]
        light_results = await asyncio.gather(*light_tasks, return_exceptions=True)
        light_end = time.time()
        
        light_successful = sum(1 for result in light_results if not isinstance(result, Exception))
        light_duration = light_end - light_start
        load_results.append(("light", light_users, light_successful, light_duration))
        
        # Step 3: Medium load (10 concurrent users)
        print(f"Running medium load test for {benchmark_name}...")
        medium_users = 10
        medium_start = time.time()
        
        medium_tasks = [asyncio.create_task(async_client.get(test_endpoint)) for _ in range(medium_users)]
        medium_results = await asyncio.gather(*medium_tasks, return_exceptions=True)
        medium_end = time.time()
        
        medium_successful = sum(1 for result in medium_results if not isinstance(result, Exception))
        medium_duration = medium_end - medium_start
        load_results.append(("medium", medium_users, medium_successful, medium_duration))
        
        # Step 4: Heavy load (15 concurrent users)
        print(f"Running heavy load test for {benchmark_name}...")
        heavy_users = 15
        heavy_start = time.time()
        
        heavy_tasks = [asyncio.create_task(async_client.get(test_endpoint)) for _ in range(heavy_users)]
        heavy_results = await asyncio.gather(*heavy_tasks, return_exceptions=True)
        heavy_end = time.time()
        
        heavy_successful = sum(1 for result in heavy_results if not isinstance(result, Exception))
        heavy_duration = heavy_end - heavy_start
        load_results.append(("heavy", heavy_users, heavy_successful, heavy_duration))
        
        end_time = time.time()
        total_execution_time = end_time - start_time
        
        # Phase 3: Validate Load Test Results
        # Validate target concurrent users (medium load should succeed)
        medium_load = next(result for result in load_results if result[0] == "medium")
        success_rate = medium_load[2] / medium_load[1]  # successful / total
        assert success_rate >= 0.9, f"Medium load success rate {success_rate:.2%} below 90% target"
        
        # Validate system stability (baseline should be 100% successful)
        baseline_load = next(result for result in load_results if result[0] == "baseline")
        assert baseline_load[2] == baseline_load[1], "Baseline load should be 100% successful"
        
        # Phase 4: Generate Load Test Report
        performance_stats = {
            "load_testing": {
                "results": load_results,
                "target_concurrent_users": target_concurrent_users,
                "success_rates": {result[0]: result[2]/result[1] for result in load_results}
            }
        }
        
        benchmark_report = format_benchmark_report(
            benchmark_name,
            total_execution_time,
            performance_stats,
            e2e_benchmark_targets
        )
        print(benchmark_report)
        
        # Validate total execution time
        max_benchmark_time = e2e_test_data["e2e_timeout"]
        assert total_execution_time < max_benchmark_time, f"Load test took {total_execution_time}s, exceeds {max_benchmark_time}s limit"

    @pytest.mark.e2e
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_e2e_stress_testing(self, async_client: AsyncClient,
                                     e2e_benchmark_targets: Dict[str, float],
                                     e2e_test_data: Dict[str, Any]):
        """
        E2E Test: Stress Testing Performance Validation
        
        Steps: 4 steps (baseline → stress → recovery → validation)
        Timeout: 2 minutes
        Performance: <1 second recovery time
        Architecture: Stress recovery validation
        """
        # Phase 1: Setup & Initial State
        benchmark_name = "stress_testing"
        target_recovery_time = e2e_benchmark_targets["stress_recovery"]
        test_endpoint = "/api/health"
        stress_results = []
        
        # Phase 2: Execute Stress Tests
        start_time = time.time()
        
        # Step 1: Baseline performance measurement
        print(f"Running baseline measurement for {benchmark_name}...")
        baseline_response_time = await measure_response_time(async_client, test_endpoint)
        stress_results.append(("baseline", baseline_response_time))
        
        # Step 2: Stress phase (rapid requests)
        print(f"Running stress phase for {benchmark_name}...")
        stress_requests = 30
        stress_start = time.time()
        
        # Create rapid sequential requests
        stress_tasks = []
        for _ in range(stress_requests):
            task = asyncio.create_task(async_client.get(test_endpoint))
            stress_tasks.append(task)
        
        # Execute stress requests
        stress_responses = await asyncio.gather(*stress_tasks, return_exceptions=True)
        stress_end = time.time()
        stress_duration = stress_end - stress_start
        
        # Count successful stress requests
        successful_stress = sum(1 for response in stress_responses if not isinstance(response, Exception))
        stress_success_rate = successful_stress / stress_requests
        stress_results.append(("stress", stress_success_rate))
        
        # Step 3: Recovery phase
        print(f"Running recovery phase for {benchmark_name}...")
        recovery_start = time.time()
        
        # Wait for system to recover
        await asyncio.sleep(1)
        
        # Test recovery with single request
        recovery_response = await async_client.get(test_endpoint)
        recovery_end = time.time()
        recovery_time = recovery_end - recovery_start
        
        assert recovery_response.status_code == status.HTTP_200_OK, "System did not recover from stress"
        stress_results.append(("recovery", recovery_time))
        
        # Step 4: Post-stress validation
        print(f"Running post-stress validation for {benchmark_name}...")
        post_stress_response_time = await measure_response_time(async_client, test_endpoint)
        stress_results.append(("post_stress", post_stress_response_time))
        
        # Validate post-stress performance
        post_stress_data = recovery_response.json()
        validate_e2e_response_structure(post_stress_data, "health")
        
        end_time = time.time()
        total_execution_time = end_time - start_time
        
        # Phase 3: Validate Stress Test Results
        # Validate recovery time
        recovery_result = next(result for result in stress_results if result[0] == "recovery")
        validate_e2e_performance(recovery_result[1], target_recovery_time, "Stress Recovery Time")
        
        # Validate stress success rate (should be reasonable)
        stress_result = next(result for result in stress_results if result[0] == "stress")
        assert stress_result[1] >= 0.8, f"Stress test success rate {stress_result[1]:.2%} below 80% target"
        
        # Validate post-stress performance (should be similar to baseline)
        baseline_result = next(result for result in stress_results if result[0] == "baseline")
        post_stress_result = next(result for result in stress_results if result[0] == "post_stress")
        
        performance_degradation = (post_stress_result[1] - baseline_result[1]) / baseline_result[1]
        assert performance_degradation < 0.5, f"Performance degradation {performance_degradation:.2%} exceeds 50% limit"
        
        # Phase 4: Generate Stress Test Report
        performance_stats = {
            "stress_testing": {
                "results": stress_results,
                "stress_duration": stress_duration,
                "stress_success_rate": stress_success_rate,
                "recovery_time": recovery_time,
                "performance_degradation": performance_degradation
            }
        }
        
        benchmark_report = format_benchmark_report(
            benchmark_name,
            total_execution_time,
            performance_stats,
            e2e_benchmark_targets
        )
        print(benchmark_report)
        
        # Validate total execution time
        max_benchmark_time = e2e_test_data["e2e_timeout"]
        assert total_execution_time < max_benchmark_time, f"Stress test took {total_execution_time}s, exceeds {max_benchmark_time}s limit" 