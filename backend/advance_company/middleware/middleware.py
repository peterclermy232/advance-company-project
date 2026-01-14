import re
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

class CSRFExemptMiddleware(MiddlewareMixin):
    """
    Exempts requests from CSRF checks if:
    1. They match a URL in CSRF_EXEMPT_URLS
    2. OR they contain a JWT Authorization header

    This ensures JWT-based APIs are safe from CSRF issues without disabling CSRF
    globally.
    """

    def process_request(self, request):
        path = request.path_info.lstrip('/')

        # 1️⃣ Explicit URL exemptions
        exempt_urls = getattr(settings, 'CSRF_EXEMPT_URLS', [])
        for pattern in exempt_urls:
            if re.match(pattern, path):
                setattr(request, '_dont_enforce_csrf_checks', True)
                # Optional debug logging:
                # print(f"[CSRF] Exempted by URL pattern: {path}")
                return

        # 2️⃣ Exempt automatically if JWT token is present
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            setattr(request, '_dont_enforce_csrf_checks', True)
            # Optional debug logging:
            # print(f"[CSRF] Exempted by JWT header: {path}")
