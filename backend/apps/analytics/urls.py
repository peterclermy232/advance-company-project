from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import AdminAnalyticsViewSet

router = DefaultRouter()
router.register(r'', AdminAnalyticsViewSet, basename='admin-analytics')

# Explicit path for export so it is guaranteed to resolve regardless of router state
urlpatterns = [
    path('export/', AdminAnalyticsViewSet.as_view({'get': 'export_analytics'}), name='analytics-export'),
] + router.urls
