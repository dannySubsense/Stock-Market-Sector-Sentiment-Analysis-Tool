"""
E2E-specific fixtures for Market Sector Sentiment Analysis Tool
Extends existing conftest.py with E2E-specific test data and environment setup
"""

import pytest
import time
from typing import Dict, Any
from httpx import AsyncClient


@pytest.fixture
def e2e_test_data():
    """
    E2E test data - extends existing fixtures from conftest.py
    Provides comprehensive test data for E2E scenarios
    """
    return {
        "performance_targets": {
            "sector_grid_load": 5.0,       # seconds (relaxed for dev)
            "analysis_completion": 310.0,   # seconds (5 minutes + 10s buffer)
            "api_response_time": 2.0,       # seconds (relaxed for dev)
            "api_chain_execution": 20.0,    # seconds (relaxed for dev)
            "data_flow_validation": 10.0,   # seconds (relaxed for dev)
            "error_recovery": 5.0,          # seconds (relaxed for dev)
        },
        "workflow_steps": {
            "sector_dashboard": 8,         # steps
            "stock_universe": 8,           # steps
            "analysis_workflow": 7,        # steps
            "error_recovery": 6,           # steps
        },
        "e2e_timeout": 600,  # 10 minutes for E2E tests
        "retry_attempts": 3,
    }


@pytest.fixture
def e2e_test_environment():
    """
    E2E test environment setup - extends existing environment
    Provides isolated test environment for E2E scenarios
    """
    return {
        "database": "test_e2e_db",
        "redis": "test_e2e_redis", 
        "timeout": 600,  # 10 minutes for E2E tests
        "retry_attempts": 3,
    }


@pytest.fixture
def e2e_workflow_steps():
    """
    E2E workflow step definitions for validation
    """
    return {
        "sector_dashboard": [
            "user_opens_dashboard",
            "system_loads_sector_grid",
            "user_clicks_on_sector", 
            "system_shows_sector_details",
            "user_views_top_stocks",
            "user_triggers_refresh",
            "system_completes_analysis",
            "user_sees_updated_data"
        ],
        "stock_universe": [
            "user_accesses_stock_universe",
            "system_shows_universe_stats",
            "user_filters_by_sector",
            "user_views_individual_stock",
            "user_checks_gap_stocks",
            "user_refreshes_universe",
            "system_updates_universe",
            "user_sees_updated_data"
        ],
        "analysis_workflow": [
            "user_triggers_on_demand_analysis",
            "system_starts_analysis",
            "user_monitors_progress",
            "system_completes_analysis",
            "cache_is_updated",
            "user_sees_fresh_data",
            "performance_is_maintained"
        ],
        "error_recovery": [
            "external_api_fails",
            "system_uses_cached_data",
            "user_sees_stale_data_warning",
            "system_retries_api",
            "system_recovers",
            "user_sees_fresh_data"
        ]
    }


@pytest.fixture
def e2e_performance_benchmarks():
    """
    E2E performance benchmark targets
    """
    return {
        "sector_grid_loading": {
            "target_time": 1.0,  # seconds
            "cache_hit_rate": 0.9,  # 90%
            "concurrent_users": 10,
            "memory_usage": 100,  # MB
        },
        "analysis_completion": {
            "target_time": 310.0,  # 5 minutes + 10 seconds buffer
            "background_processing": True,
            "memory_usage": 200,  # MB
            "cpu_usage": 0.8,  # 80%
        },
        "api_response_times": {
            "sectors_endpoint": 2.0,  # seconds (relaxed for dev)
            "stocks_endpoint": 2.0,   # seconds (relaxed for dev)
            "analysis_endpoint": 5.0, # seconds (relaxed for dev)
            "health_endpoint": 1.0,   # seconds (relaxed for dev)
        }
    }


@pytest.fixture
def e2e_api_chains():
    """
    E2E API chain definitions
    
    Returns:
        Dict[str, List[str]]: API chain definitions
    """
    return {
        "api_endpoint_chain": [
            "health_check",
            "sectors_endpoint",
            "stocks_endpoint",
            "analysis_endpoint",
            "cache_endpoint",
            "final_health_check"
        ]
    }


@pytest.fixture
def e2e_data_flows():
    """
    E2E data flow definitions
    
    Returns:
        Dict[str, List[str]]: Data flow definitions
    """
    return {
        "data_flow_integration": [
            "sector_data_flow",
            "stock_data_flow",
            "analysis_data_flow",
            "cache_data_flow",
            "data_consistency_validation"
        ]
    }


@pytest.fixture
def e2e_performance_targets():
    """
    E2E performance target definitions
    
    Returns:
        Dict[str, float]: Performance target definitions
    """
    return {
        "concurrent_requests": 2.0,  # 2 seconds for concurrent requests
        "sequential_requests": 1.0   # 1 second for sequential requests
    }


@pytest.fixture
def e2e_error_scenarios():
    """
    E2E error scenario definitions
    
    Returns:
        Dict[str, List[str]]: Error scenario definitions
    """
    return {
        "error_integration": [
            "invalid_endpoint_handled",
            "malformed_request_handled",
            "rate_limit_handled",
            "system_recovery_validated",
            "system_stability_validated"
        ]
    }


@pytest.fixture
def e2e_benchmark_targets():
    """
    E2E benchmark target definitions
    
    Returns:
        Dict[str, float]: Benchmark target definitions
    """
    return {
        "response_time": 2.0,        # 2.0 seconds average response time (relaxed for dev)
        "throughput": 20.0,          # 20 requests per minute (relaxed for dev)
        "concurrent_users": 10,      # 10 concurrent users
        "stress_recovery": 5.0       # 5 seconds recovery time (relaxed for dev)
    }


@pytest.fixture
def e2e_system_targets():
    """
    E2E system target definitions
    
    Returns:
        Dict[str, float]: System target definitions
    """
    return {
        "health_check": 1.0,         # 1.0 seconds health check (relaxed for dev)
        "data_pipeline": 30.0,       # 30 seconds data pipeline (relaxed for dev)
        "cache_operations": 1.0,     # 1.0 seconds cache operations (relaxed for dev)
        "database_operations": 5.0   # 5 seconds database operations (relaxed for dev)
    } 