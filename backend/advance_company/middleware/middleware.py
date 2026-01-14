import re
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class CSRFExemptMiddleware(MiddlewareMixin):
    """
    Middleware to exempt specific URL patterns from CSRF verification.
    This is safe for JWT-based APIs since JWT tokens in Authorization headers
    are not vulnerable to CSRF attacks.
    """
    def process_request(self, request):
        exempt_urls = getattr(settings, 'CSRF_EXEMPT_URLS', [])
        path = request.path_info.lstrip('/')
        
        for pattern in exempt_urls:
            if re.match(pattern, path):
                setattr(request, '_dont_enforce_csrf_checks', True)
                break