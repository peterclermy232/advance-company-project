from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FinancialAccountViewSet, DepositViewSet, InterestCalculationViewSet

router = DefaultRouter()
router.register(r'accounts', FinancialAccountViewSet)
router.register(r'deposits', DepositViewSet)
router.register(r'interest', InterestCalculationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]