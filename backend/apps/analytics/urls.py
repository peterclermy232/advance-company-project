from django.urls import path
from .views import AdminAnalyticsViewSet

urlpatterns = [
    path('analytics/members/', 
         AdminAnalyticsViewSet.as_view({'get': 'members'}), 
         name='admin-analytics-members'),
    
    path('analytics/summary/', 
         AdminAnalyticsViewSet.as_view({'get': 'summary'}), 
         name='admin-analytics-summary'),
    
    path('analytics/export/', 
         AdminAnalyticsViewSet.as_view({'get': 'export'}), 
         name='admin-analytics-export'),
]