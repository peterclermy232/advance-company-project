from django.db import connection
from django.core.cache import cache
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
@permission_classes([])  # Public health check — no auth required
def health_check(request):
    """
    Simple public health check. Returns 200 when the server is up.
    Does NOT expose internal metrics.
    """
    return Response({'status': 'healthy', 'timestamp': timezone.now()})


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])  # FIX 10: require auth + staff
def metrics(request):
    """
    Detailed health metrics — staff only.
    Previously had no permission class, allowing unauthenticated access.
    """
    checks = {
        'database': _check_db(),
        'cache': _check_cache(),
    }

    all_healthy = all(c['status'] == 'healthy' for c in checks.values())

    from apps.accounts.models import User
    from apps.financial.models import Deposit
    from apps.notifications.models import Notification

    return Response({
        'status': 'healthy' if all_healthy else 'degraded',
        'timestamp': timezone.now(),
        'checks': checks,
        'stats': {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'pending_deposits': Deposit.objects.filter(status='pending').count(),
            'unread_notifications': Notification.objects.filter(is_read=False).count(),
        },
    }, status=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE)


def _check_db():
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return {'status': 'healthy'}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}


def _check_cache():
    try:
        cache.set('_health_check', '1', timeout=10)
        val = cache.get('_health_check')
        return {'status': 'healthy' if val == '1' else 'unhealthy'}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}