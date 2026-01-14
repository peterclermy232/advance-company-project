import re
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class CSRFExemptMiddleware(MiddlewareMixin):
    """
    Middleware to exempt specific URL patterns from CSRF verification.
    
    This is safe for JWT-based APIs since JWT tokens in Authorization headers
    are not vulnerable to CSRF attacks (they're not automatically sent by browsers).
    
    CSRF protection is still active for:
    - Django admin panel
    - Any endpoints not matching CSRF_EXEMPT_URLS patterns
    """
    
    def process_request(self, request):
        """
        Check if the current request path matches any exempt URL pattern.
        If it does, disable CSRF checks for this request.
        """
        exempt_urls = getattr(settings, 'CSRF_EXEMPT_URLS', [])
        path = request.path_info.lstrip('/')
        
        for pattern in exempt_urls:
            if re.match(pattern, path):
                setattr(request, '_dont_enforce_csrf_checks', True)
                break