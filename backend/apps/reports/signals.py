from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Report, ActivityLog

@receiver(post_save, sender=Report)
def log_report_created_or_updated(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            user=instance.user,
            action='CREATED',
            description=f"Report '{instance.title}' was created"
        )
    else:
        ActivityLog.objects.create(
            user=instance.user,
            action='UPDATED',
            description=f"Report '{instance.title}' was updated"
        )

@receiver(pre_save, sender=Report)
def log_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Report.objects.get(pk=instance.pk)
    except Report.DoesNotExist:
        return
    if old.status != instance.status:
        ActivityLog.objects.create(
            user=instance.user,
            action='STATUS_CHANGED',
            description=f"Status changed from {old.status} to {instance.status}"
        )
