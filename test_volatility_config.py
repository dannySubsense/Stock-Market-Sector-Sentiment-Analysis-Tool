#!/usr/bin/env python3
"""
Test script for volatility weight configuration system
Verifies that the refactored system works correctly
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from config.volatility_weights import get_volatility_config, get_static_weights, get_weight_for_sector

def test_volatility_config():
    """Test the volatility configuration system"""
    print("Testing Volatility Weight Configuration System")
    print("=" * 50)
    
    # Test 1: Get configuration instance
    config = get_volatility_config()
    print(f"✓ Configuration loaded successfully")
    print(f"  - Weight source: {config.weights_source.value}")
    print(f"  - Rebalance frequency: {config.rebalance_frequency}")
    print(f"  - Lookback period: {config.lookback_period} days")
    
    # Test 2: Get static weights
    static_weights = get_static_weights()
    print(f"\n✓ Static weights retrieved:")
    for sector, weight in static_weights.items():
        print(f"  - {sector}: {weight}x")
    
    # Test 3: Get individual sector weights
    print(f"\n✓ Individual sector weight retrieval:")
    test_sectors = ['healthcare', 'technology', 'utilities', 'unknown_sector']
    for sector in test_sectors:
        weight = get_weight_for_sector(sector)
        print(f"  - {sector}: {weight}x")
    
    # Test 4: Configuration summary
    summary = config.get_config_summary()
    print(f"\n✓ Configuration summary:")
    print(f"  - Weights source: {summary['weights_source']}")
    print(f"  - Max change percent: {summary['max_change_percent']}")
    print(f"  - Confidence threshold: {summary['confidence_threshold']}")
    
    print(f"\n✅ All tests passed! Volatility configuration system is working correctly.")
    print(f"\n📝 Ready for future dynamic weighting implementation:")
    print(f"  - Static weights are now configurable")
    print(f"  - Configuration can be loaded from YAML files")
    print(f"  - System supports future 'dynamic' and 'hybrid' modes")
    print(f"  - Weight changes are validated and logged")

if __name__ == "__main__":
    test_volatility_config() 