from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, ActivityLogViewSet

router = DefaultRouter()
# activity-logs MUST be registered before the root '' ReportViewSet — the
# root registration's catch-all detail route (^(?P<pk>[^/.]+)/$) otherwise
# matches "activity-logs" as a Report pk lookup first, shadowing this
# viewset's own routes entirely (a real, previously-undetected 404 bug —
# not just a test artifact).
router.register(r'activity-logs', ActivityLogViewSet)
router.register(r'', ReportViewSet)

urlpatterns = [
    path('', include(router.urls)),
]