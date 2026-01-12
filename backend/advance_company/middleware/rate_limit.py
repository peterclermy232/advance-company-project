from django.core.cache import cache
from django.http import JsonResponse
from django.utils.decorators import decorator_from_middleware
from functools import wraps
import time

class RateLimitMiddleware:
    """Global rate limiting middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip rate limiting for static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
        
        # Get client IP
        ip = self.get_client_ip(request)
        
        # Check rate limit
        if self.is_rate_limited(ip, request.path):
            return JsonResponse({
                'error': 'Too many requests. Please try again later.',
                'retry_after': 60
            }, status=429)
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_rate_limited(self, ip, path):
        """Check if IP has exceeded rate limits"""
        # Global limit: 100 requests per minute
        global_key = f'rate_limit:global:{ip}'
        global_count = cache.get(global_key, 0)
        
        if global_count >= 100:
            return True
        
        cache.set(global_key, global_count + 1, 60)
        return False
