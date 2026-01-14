import re
import logging
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class CSRFExemptMiddleware(MiddlewareMixin):
    """
    Middleware to exempt specific URL patterns from CSRF verification.

    Safe for JWT-based APIs since JWT tokens in Authorization headers
    are not vulnerable to CSRF (they're not sent automatically by browsers).

    CSRF protection is still active for:
    - Django admin
    - Any endpoint not matching CSRF_EXEMPT_URLS
    """

    def process_request(self, request):
        """
        Disable CSRF checks for URLs listed in CSRF_EXEMPT_URLS.
        """
        exempt_urls = getattr(settings, 'CSRF_EXEMPT_URLS', [])
        path = request.path_info  # includes leading slash

        for pattern in exempt_urls:
            if re.fullmatch(pattern, path):
                setattr(request, '_dont_enforce_csrf_checks', True)
                logger.debug(f"CSRF exempted for path: {path}")
                break

            # DEBUG logging for all requests
        logger.debug(
            f"Request path: {path}, CSRF exempt: {csrf_exempted}"
        )