from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

# Create router for standard CRUD operations
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

# Explicit URL patterns for @action endpoints
# This ensures permission_classes=[AllowAny] are properly enforced
urlpatterns = [
    # Public authentication endpoints - AllowAny
    path('users/register/', UserViewSet.as_view({'post': 'register'}), name='user-register'),
    path('users/login/', UserViewSet.as_view({'post': 'login'}), name='user-login'),
    path('users/verify-email/', UserViewSet.as_view({'post': 'verify_email'}), name='user-verify-email'),
    path('users/resend-verification/', UserViewSet.as_view({'post': 'resend_verification'}), name='user-resend-verification'),
    path('users/forgot-password/', UserViewSet.as_view({'post': 'forgot_password'}), name='user-forgot-password'),
    path('users/reset-password-confirm/', UserViewSet.as_view({'post': 'reset_password_confirm'}), name='user-reset-password-confirm'),
    path('users/verify-2fa/', UserViewSet.as_view({'post': 'verify_2fa'}), name='user-verify-2fa'),
    path('users/biometric-challenge/', UserViewSet.as_view({'post': 'biometric_challenge'}), name='user-biometric-challenge'),
    path('users/biometric-login/', UserViewSet.as_view({'post': 'biometric_login'}), name='user-biometric-login'),
    
    # Authenticated endpoints - IsAuthenticated
    path('users/enable-2fa/', UserViewSet.as_view({'post': 'enable_2fa'}), name='user-enable-2fa'),
    path('users/confirm-2fa/', UserViewSet.as_view({'post': 'confirm_2fa'}), name='user-confirm-2fa'),
    path('users/register-biometric/', UserViewSet.as_view({'post': 'register_biometric'}), name='user-register-biometric'),
    
    # Include router for remaining CRUD operations (list, retrieve, update, delete)
    path('', include(router.urls)),
]