from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BeneficiaryViewSet

router = DefaultRouter()
router.register(r'', BeneficiaryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]