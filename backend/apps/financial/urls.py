from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FinancialAccountViewSet, DepositViewSet, InterestCalculationViewSet

router = DefaultRouter()
router.register(r'accounts', FinancialAccountViewSet, basename='financialaccount')
router.register(r'deposits', DepositViewSet, basename='deposit')
router.register(r'interest', InterestCalculationViewSet, basename='interestcalculation')

urlpatterns = [
    path('', include(router.urls)),
]