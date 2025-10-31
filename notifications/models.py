import uuid
import json
from django.db import models
from django.conf import settings
from django_celery_beat.models import PeriodicTask, CrontabSchedule

class Notification(models.Model):
    """
    Model for storing notification templates and settings
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('webhook', 'Webhook'),
        ('push', 'Push Notification'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    name = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    subject = models.CharField(max_length=255, blank=True, null=True)
    message_template = models.TextField()
    is_active = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['notification_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.notification_type})"


class Webhook(models.Model):
    """
    Model for webhook configurations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='webhooks'
    )
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    secret_key = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    events = models.JSONField(default=list, blank=True)  # List of events to trigger webhook
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'webhook'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} - {self.url}"


class NotificationLog(models.Model):
    """
    Model for logging notification delivery attempts
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
        ('bounced', 'Bounced'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    recipient = models.CharField(max_length=255)  # Email, phone, etc.
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notification_log'
        indexes = [
            models.Index(fields=['notification']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Log for {self.notification.name} to {self.recipient} - {self.status}"
    
class ReportSchedule(models.Model):
    SCHEDULE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    REPORT_TYPE_CHOICES = [
        ('form_submissions', 'Form Submissions'),
        ('process_completions', 'Process Completions'),
        ('system_overview', 'System Overview'),
    ]
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    frequency = models.CharField(max_length=10, choices=SCHEDULE_CHOICES)
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        help_text="Admin user who owns this schedule"
    )
    filters = models.JSONField(default=dict, blank=True, help_text="e.g., {'form_ids': ['uuid1', 'uuid2']}")
    
    send_to_email = models.EmailField(blank=True, null=True)
    send_to_webhook = models.ForeignKey(
        Webhook, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True
    )
    
    output_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='csv')
    is_active = models.BooleanField(default=True)
    
    periodic_task = models.OneToOneField(
        PeriodicTask, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'report_schedule'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.frequency} {self.report_type})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if not self.periodic_task:
            if self.frequency == 'daily':
                crontab, _ = CrontabSchedule.objects.get_or_create(minute='0', hour='0', day_of_week='*', day_of_month='*', month_of_year='*')
            elif self.frequency == 'weekly':
                crontab, _ = CrontabSchedule.objects.get_or_create(minute='0', hour='0', day_of_week='0', day_of_month='*', month_of_year='*')
            elif self.frequency == 'monthly':
                crontab, _ = CrontabSchedule.objects.get_or_create(minute='0', hour='0', day_of_week='*', day_of_month='1', month_of_year='*')
            
            task = PeriodicTask.objects.create(
                name=f"Report Schedule: {self.name} ({self.id})",
                task='notifications.tasks.generate_scheduled_report',
                crontab=crontab,
                enabled=self.is_active,
                kwargs=json.dumps({'schedule_id': str(self.id)})
            )
            self.periodic_task = task
            super().save(update_fields=['periodic_task'])
            
        else:
            self.periodic_task.enabled = self.is_active
            self.periodic_task.save()

    def delete(self, *args, **kwargs):
        if self.periodic_task:
            self.periodic_task.delete()
        super().delete(*args, **kwargs)


class ReportInstance(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(
        ReportSchedule, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        help_text="Scheduled job that triggered this (if any)"
    )
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        help_text="User who manually triggered this (if any)"
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    report_type = models.CharField(max_length=50)
    
    file_url = models.URLField(max_length=1024, blank=True, null=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    
    error_message = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'report_instance'
        ordering = ['-created_at']

    def __str__(self):
        return f"Report {self.report_type} at {self.created_at} ({self.status})"