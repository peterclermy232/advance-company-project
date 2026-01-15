# backend/apps/accounts/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from . import auth_views

# Create router for protected user endpoints
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Public authentication endpoints (no authentication required)
    path('register/', auth_views.register, name='register'),
    path('login/', auth_views.login, name='login'),
    path('verify-email/', auth_views.verify_email, name='verify-email'),
    path('resend-verification/', auth_views.resend_verification, name='resend-verification'),
    path('verify-2fa/', auth_views.verify_2fa, name='verify-2fa'),
    path('biometric-challenge/', auth_views.biometric_challenge, name='biometric-challenge'),
    path('biometric-login/', auth_views.biometric_login, name='biometric-login'),
    path('forgot-password/', auth_views.forgot_password, name='forgot-password'),
    path('reset-password-confirm/', auth_views.reset_password_confirm, name='reset-password-confirm'),
    
    # Protected user endpoints (require authentication)
    path('', include(router.urls)),
]