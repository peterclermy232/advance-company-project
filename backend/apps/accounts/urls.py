from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

# Create router and register viewset
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

# Use ONLY the router URLs - don't create explicit paths
# The @action decorators with permission_classes will work correctly
urlpatterns = [
    path('', include(router.urls)),
]