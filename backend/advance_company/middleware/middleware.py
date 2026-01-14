import re
import logging
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class CSRFExemptMiddleware(MiddlewareMixin):
    """
    Exempts certain API endpoints from CSRF verification.
    Safe for JWT-auth APIs because JWTs are in headers (not cookies).
    """

    def process_request(self, request):
        path = request.path_info.lstrip('/')
        exempt_urls = getattr(settings, 'CSRF_EXEMPT_URLS', [])

        csrf_exempted = False
        for pattern in exempt_urls:
            if re.match(pattern, path):
                setattr(request, '_dont_enforce_csrf_checks', True)
                csrf_exempted = True
                break

        # 🔹 Optional debug
        logger.debug(f"Request path: {path}, CSRF exempt: {csrf_exempted}")
