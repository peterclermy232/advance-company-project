from rest_framework.routers import DefaultRouter
from .views import AdminAnalyticsViewSet

router = DefaultRouter()
router.register(r'', AdminAnalyticsViewSet, basename='admin-analytics')

urlpatterns = router.urls

print("✅ apps.analytics.urls LOADED")
