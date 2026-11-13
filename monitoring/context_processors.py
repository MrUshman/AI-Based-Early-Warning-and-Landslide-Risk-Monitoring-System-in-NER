from django.utils import timezone
from .models import Alert, MonitoringLocation


def global_context(request):
    """
    Context processor providing system-wide alert counters and emergency data
    to every template without redundant database hits.
    """
    active_alerts = Alert.objects.filter(status__in=['ACTIVE', 'ACKNOWLEDGED'])
    active_count = active_alerts.count()
    critical_count = active_alerts.filter(level='CRITICAL').count()
    high_count = active_alerts.filter(level='HIGH').count()

    is_ddma_or_admin = False
    is_operator = False

    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.groups.filter(name='DDMA_Officer').exists():
            is_ddma_or_admin = True
        if request.user.is_superuser or request.user.groups.filter(name__in=['Field_Operator', 'DDMA_Officer']).exists():
            is_operator = True

    return {
        'global_active_alerts_count': active_count,
        'global_critical_alerts_count': critical_count,
        'global_high_alerts_count': high_count,
        'emergency_number': '112',
        'is_ddma_or_admin': is_ddma_or_admin,
        'is_operator': is_operator,
        'system_now_ist': timezone.now(),
    }
