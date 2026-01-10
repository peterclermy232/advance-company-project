from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminAnalyticsViewSet

router = DefaultRouter()
router.register(r'analytics', AdminAnalyticsViewSet, basename='admin-analytics')

urlpatterns = [
    path('', include(router.urls)),
]