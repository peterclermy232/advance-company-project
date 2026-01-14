import re
import logging
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class CSRFExemptMiddleware(MiddlewareMixin):
    """
    Middleware to exempt specific URL patterns from CSRF verification.
    """

    def process_request(self, request):
        exempt_urls = getattr(settings, 'CSRF_EXEMPT_URLS', [])
        path = request.path_info  # includes leading slash

        # ✅ Initialize before the loop
        csrf_exempted = False

        for pattern in exempt_urls:
            if re.fullmatch(pattern, path):
                setattr(request, '_dont_enforce_csrf_checks', True)
                csrf_exempted = True
                break

        # DEBUG logging for all requests
        logger.debug(f"Request path: {path}, CSRF exempt: {csrf_exempted}")
