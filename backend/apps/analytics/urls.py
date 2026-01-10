from django.urls import path
from .views import AdminAnalyticsViewSet

urlpatterns = [
    path('members/', 
         AdminAnalyticsViewSet.as_view({'get': 'members'}), 
         name='admin-analytics-members'),
    
    path('summary/', 
         AdminAnalyticsViewSet.as_view({'get': 'summary'}), 
         name='admin-analytics-summary'),
    
    path('export/', 
         AdminAnalyticsViewSet.as_view({'get': 'export'}), 
         name='admin-analytics-export'),
]