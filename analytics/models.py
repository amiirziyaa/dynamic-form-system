import uuid
from django.db import models


class FormView(models.Model):
    """
    Tracks each view/visit to a form (for analytics)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(
        'forms.Form',
        on_delete=models.CASCADE,
        related_name='views'
    )
    session_id = models.CharField(max_length=255, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'form_view'
        indexes = [
            models.Index(fields=['form', 'viewed_at']),
        ]

    def __str__(self):
        return f"View of {self.form.title} at {self.viewed_at}"


class ProcessView(models.Model):
    """
    Tracks each view/visit to a process (for analytics)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    process = models.ForeignKey(
        'processes.Process',
        on_delete=models.CASCADE,
        related_name='views'
    )
    session_id = models.CharField(max_length=255, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'process_view'
        indexes = [
            models.Index(fields=['process', 'viewed_at']),
        ]

    def __str__(self):
        return f"View of {self.process.title} at {self.viewed_at}"