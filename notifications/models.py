import uuid
from django.db import models
from django.conf import settings


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