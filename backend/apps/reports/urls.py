from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, ActivityLogViewSet

router = DefaultRouter()
router.register(r'', ReportViewSet)
router.register(r'activity-logs', ActivityLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]