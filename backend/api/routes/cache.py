"""
Cache API endpoints for Slice 1B cache management
Handles cache health, warming, and key management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from services.cache_service import get_cache_service
from services.performance_monitor import get_performance_monitor

router = APIRouter()
logger = logging.getLogger(__name__)

# =====================================================
# SLICE 1A CACHE ENDPOINTS (Moved from sectors.py)
# =====================================================


@router.get("/cache/stats")
async def get_cache_statistics():
    """
    Get cache statistics (moved from /sectors/cache/stats)
    Enhanced with Slice 1B performance metrics
    """
    try:
        cache_service = await get_cache_service()
        stats = await cache_service.get_statistics()

        # Add Slice 1B performance metrics
        perf_monitor = await get_performance_monitor()
        perf_stats = await perf_monitor.get_cache_performance()

        return {
            "cache_statistics": stats,
            "performance_metrics": perf_stats,  # Slice 1B
            "hit_rate": stats.get("hit_rate", 0.0),
            "miss_rate": stats.get("miss_rate", 0.0),
            "total_requests": stats.get("total_requests", 0),
            "cache_size": stats.get("cache_size", 0),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get cache statistics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache statistics: {str(e)}"
        )


@router.delete("/cache/clear")
async def clear_cache():
    """
    Clear all cache (moved from /sectors/cache)
    Enhanced with selective clearing options
    """
    try:
        cache_service = await get_cache_service()
        await cache_service.clear_all()

        return {
            "message": "Cache cleared successfully",
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


# =====================================================
# SLICE 1B CACHE ENHANCEMENT ENDPOINTS
# =====================================================


@router.get("/cache/health")
async def get_cache_health():
    """
    SLICE 1B: Get cache system health
    Returns detailed health status and performance metrics
    """
    try:
        cache_service = await get_cache_service()
        health = await cache_service.get_health()

        return {
            "cache_health": health,
            "status": health.get("status", "unknown"),
            "response_time": health.get("response_time", 0),
            "memory_usage": health.get("memory_usage", 0),
            "connection_status": health.get("connection_status", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get cache health: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache health: {str(e)}"
        )


@router.post("/cache/warm")
async def warm_cache(cache_type: str = "all"):
    """
    SLICE 1B: Warm cache with fresh data
    Pre-loads frequently accessed data
    """
    try:
        cache_service = await get_cache_service()

        if cache_type == "all":
            await cache_service.warm_all_caches()
        elif cache_type == "sectors":
            await cache_service.warm_sector_cache()
        elif cache_type == "stocks":
            await cache_service.warm_stock_cache()
        elif cache_type == "themes":
            await cache_service.warm_theme_cache()  # Slice 1B
        else:
            raise HTTPException(
                status_code=400, detail=f"Invalid cache type: {cache_type}"
            )

        return {
            "message": f"Cache warming completed for {cache_type}",
            "cache_type": cache_type,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to warm cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to warm cache: {str(e)}")


@router.get("/cache/keys")
async def list_cached_keys(prefix: Optional[str] = None):
    """
    SLICE 1B: List cached keys
    Returns all cached keys with optional prefix filtering
    """
    try:
        cache_service = await get_cache_service()
        keys = await cache_service.list_keys(prefix=prefix)

        return {
            "cached_keys": keys,
            "key_count": len(keys),
            "prefix_filter": prefix,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to list cached keys: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list cached keys: {str(e)}"
        )


@router.delete("/cache/{key}")
async def clear_specific_cache(key: str):
    """
    SLICE 1B: Clear specific cache key
    Removes a specific cached item
    """
    try:
        cache_service = await get_cache_service()
        await cache_service.clear_key(key)

        return {
            "message": f"Cache key '{key}' cleared successfully",
            "key": key,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to clear cache key: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to clear cache key: {str(e)}"
        )


@router.get("/cache/performance")
async def get_cache_performance():
    """
    SLICE 1B: Get detailed cache performance metrics
    Returns performance analysis and optimization recommendations
    """
    try:
        perf_monitor = await get_performance_monitor()
        performance = await perf_monitor.get_detailed_cache_performance()

        return {
            "cache_performance": performance,
            "recommendations": performance.get("recommendations", []),
            "optimization_opportunities": performance.get(
                "optimization_opportunities", []
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get cache performance: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache performance: {str(e)}"
        )


@router.post("/cache/optimize")
async def optimize_cache():
    """
    SLICE 1B: Optimize cache configuration
    Automatically adjusts cache settings for optimal performance
    """
    try:
        cache_service = await get_cache_service()
        optimization_result = await cache_service.optimize()

        return {
            "message": "Cache optimization completed",
            "optimization_result": optimization_result,
            "improvements": optimization_result.get("improvements", []),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to optimize cache: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to optimize cache: {str(e)}"
        )


@router.get("/cache/patterns")
async def get_cache_access_patterns():
    """
    SLICE 1B: Get cache access patterns
    Returns analysis of cache usage patterns for optimization
    """
    try:
        perf_monitor = await get_performance_monitor()
        patterns = await perf_monitor.get_cache_access_patterns()

        return {
            "access_patterns": patterns,
            "hot_keys": patterns.get("hot_keys", []),
            "cold_keys": patterns.get("cold_keys", []),
            "access_frequency": patterns.get("access_frequency", {}),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get cache access patterns: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get cache access patterns: {str(e)}"
        )
