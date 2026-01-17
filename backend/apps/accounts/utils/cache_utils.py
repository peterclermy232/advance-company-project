"""
backend/apps/accounts/utils/cache_utils.py
Safe cache operations with fallback handling
"""
import logging
from django.core.cache import cache
from django.core.cache.backends.base import InvalidCacheBackendError

logger = logging.getLogger(__name__)


def safe_cache_get(key, default=None):
    """
    Safely get a value from cache with error handling
    
    Args:
        key: Cache key
        default: Default value if key doesn't exist or cache fails
        
    Returns:
        Cached value or default
    """
    try:
        return cache.get(key, default)
    except (InvalidCacheBackendError, Exception) as e:
        logger.warning(f"Cache get failed for key '{key}': {e}")
        return default


def safe_cache_set(key, value, timeout=None):
    """
    Safely set a value in cache with error handling
    
    Args:
        key: Cache key
        value: Value to cache
        timeout: Cache timeout in seconds (None = default timeout)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cache.set(key, value, timeout)
        return True
    except (InvalidCacheBackendError, Exception) as e:
        logger.error(f"Cache set failed for key '{key}': {e}")
        return False


def safe_cache_delete(key):
    """
    Safely delete a value from cache with error handling
    
    Args:
        key: Cache key to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cache.delete(key)
        return True
    except (InvalidCacheBackendError, Exception) as e:
        logger.warning(f"Cache delete failed for key '{key}': {e}")
        return False


def safe_cache_delete_many(keys):
    """
    Safely delete multiple keys from cache
    
    Args:
        keys: List of cache keys to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cache.delete_many(keys)
        return True
    except (InvalidCacheBackendError, Exception) as e:
        logger.warning(f"Cache delete_many failed: {e}")
        return False


def safe_cache_clear():
    """
    Safely clear all cache with error handling
    
    Returns:
        True if successful, False otherwise
    """
    try:
        cache.clear()
        return True
    except (InvalidCacheBackendError, Exception) as e:
        logger.error(f"Cache clear failed: {e}")
        return False