from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis
from apps.accounts.models import User
from apps.financial.models import Deposit
from django.utils import timezone
from datetime import timedelta

def health_check(request):
    """
    Health check endpoint
    GET /api/health/
    """
    checks = {
        'database': False,
        'cache': False,
        'overall': False
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks['database'] = True
    except Exception as e:
        checks['database_error'] = str(e)
    
    # Check cache/redis
    try:
        cache.set('health_check', 'ok', 10)
        checks['cache'] = cache.get('health_check') == 'ok'
    except Exception as e:
        checks['cache_error'] = str(e)
    
    checks['overall'] = checks['database'] and checks['cache']
    
    status_code = 200 if checks['overall'] else 503
    
    return JsonResponse(checks, status=status_code)


def metrics(request):
    """
    Basic metrics endpoint
    GET /api/health/metrics/
    Requires admin authentication
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    
    metrics = {
        'timestamp': now.isoformat(),
        'users': {
            'total': User.objects.count(),
            'active': User.objects.filter(is_active=True).count(),
            'new_24h': User.objects.filter(created_at__gte=last_24h).count(),
        },
        'deposits': {
            'total': Deposit.objects.count(),
            'pending': Deposit.objects.filter(status='pending').count(),
            'completed_24h': Deposit.objects.filter(
                status='completed',
                created_at__gte=last_24h
            ).count(),
        }
    }
    
    return JsonResponse(metrics)