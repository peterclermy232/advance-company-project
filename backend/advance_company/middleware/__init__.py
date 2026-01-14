"""
Middleware package for advance_company project.
"""
from .middleware import CSRFExemptMiddleware

__all__ = ['CSRFExemptMiddleware']