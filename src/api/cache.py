"""API endpoints for cache management and monitoring."""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from src.services.cache import cache_service
from src.services.auth import get_current_active_user
from src.database.models import User

router = APIRouter()


@router.get("/cache/stats", response_model=Dict[str, Any])
async def get_cache_stats(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get Redis cache statistics.
    
    Requires authentication. Returns cache performance metrics
    and connection status.
    
    Returns:
        Dict containing cache statistics including:
        - enabled: Whether cache is active
        - connected_clients: Number of Redis clients
        - used_memory: Memory usage
        - keyspace_hits/misses: Cache performance
        - redis_version: Redis server version
    """
    return cache_service.get_cache_stats()


@router.delete("/cache/clear")
async def clear_user_cache(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Clear all cache for the current user.
    
    Clears both user profile cache and contacts cache.
    Useful for forcing fresh data from database.
    
    Returns:
        Success message
    """
    success = cache_service.clear_user_all_cache(current_user.id)
    
    if success:
        return {"message": f"Cache cleared successfully for user {current_user.id}"}
    else:
        return {"message": "Cache clearing failed or cache is disabled"}


@router.delete("/cache/contacts")
async def clear_contacts_cache(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Clear only contacts cache for the current user.
    
    User profile cache remains intact.
    
    Returns:
        Success message
    """
    success = cache_service.invalidate_contacts_cache(current_user.id)
    
    if success:
        return {"message": f"Contacts cache cleared successfully for user {current_user.id}"}
    else:
        return {"message": "Cache clearing failed or cache is disabled"}