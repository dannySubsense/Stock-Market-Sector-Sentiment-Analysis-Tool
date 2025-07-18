"""
Health check endpoints for monitoring system status
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import os
import redis
from typing import Dict, Any
import asyncio

from core.config import get_settings
from core.database import get_db_info

router = APIRouter()

@router.get("/health")
async def health_check():
    """Overall system health check"""
    try:
        # Check components
        db_status = await get_db_info()
        redis_status = await check_redis_health()
        api_status = await check_api_health()
        
        # Determine overall health
        overall_healthy = (
            db_status["status"] == "healthy" and
            redis_status["status"] == "healthy" and
            api_status["status"] == "healthy"
        )
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "components": {
                "database": db_status,
                "redis": redis_status,
                "apis": api_status
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/health/database")
async def database_health():
    """Database-specific health check"""
    try:
        db_info = await get_db_info()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            **db_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database health check failed: {str(e)}")

@router.get("/health/redis")
async def redis_health():
    """Redis-specific health check"""
    try:
        redis_info = await check_redis_health()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            **redis_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis health check failed: {str(e)}")

@router.get("/health/apis")
async def api_health():
    """External API health check"""
    try:
        api_info = await check_api_health()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            **api_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API health check failed: {str(e)}")

async def check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity and status"""
    settings = get_settings()
    
    try:
        # Get Redis configuration from settings
        if settings.credentials and settings.credentials.redis:
            redis_config = settings.credentials.redis
            host = redis_config.host
            port = redis_config.port
            db = redis_config.db
        else:
            # Default values
            host = "localhost"
            port = 6379
            db = 0
        
        # Try to connect to Redis
        r = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        
        # Test connection
        pong = r.ping()
        info = r.info()
        
        return {
            "status": "healthy" if pong else "unhealthy",
            "host": host,
            "port": port,
            "db": db,
            "connected_clients": info.get("connected_clients", 0),
            "memory_usage": info.get("used_memory_human", "unknown"),
            "uptime": info.get("uptime_in_seconds", 0)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "host": host if 'host' in locals() else "unknown",
            "port": port if 'port' in locals() else "unknown"
        }

async def check_api_health() -> Dict[str, Any]:
    """Check external API connectivity"""
    settings = get_settings()
    
    status = {
        "status": "healthy",
        "apis": {}
    }
    
    # Check if credentials are available
    if not settings.credentials:
        return {
            "status": "unhealthy",
            "error": "No credentials configured",
            "apis": {}
        }
    
    # Check Polygon API
    try:
        polygon_key = settings.credentials.api_keys.get("polygon")
        if polygon_key:
            status["apis"]["polygon"] = {
                "status": "configured",
                "tier": polygon_key.tier,
                "key_present": bool(polygon_key.key and len(polygon_key.key) > 10)
            }
        else:
            status["apis"]["polygon"] = {
                "status": "not_configured",
                "error": "No Polygon API key found"
            }
    except Exception as e:
        status["apis"]["polygon"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check FMP API
    try:
        fmp_key = settings.credentials.api_keys.get("fmp")
        if fmp_key:
            status["apis"]["fmp"] = {
                "status": "configured",
                "tier": fmp_key.tier,
                "key_present": bool(fmp_key.key and len(fmp_key.key) > 10)
            }
        else:
            status["apis"]["fmp"] = {
                "status": "not_configured",
                "error": "No FMP API key found"
            }
    except Exception as e:
        status["apis"]["fmp"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check OpenAI API
    try:
        openai_key = settings.credentials.api_keys.get("openai")
        if openai_key:
            status["apis"]["openai"] = {
                "status": "configured",
                "key_present": bool(openai_key.key and len(openai_key.key) > 10)
            }
        else:
            status["apis"]["openai"] = {
                "status": "not_configured",
                "error": "No OpenAI API key found"
            }
    except Exception as e:
        status["apis"]["openai"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Determine overall API health
    api_errors = [api for api in status["apis"].values() if api["status"] in ["error", "not_configured"]]
    if api_errors:
        status["status"] = "partially_healthy"
    
    return status 