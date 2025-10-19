import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Process(models.Model):
    """
    Multi-step workflows composed of multiple forms
    """
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]
    
    PROCESS_TYPE_CHOICES = [
        ('linear', 'Linear'),
        ('free', 'Free'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='processes'
    )
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processes'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    unique_slug = models.SlugField(max_length=100, unique=True, db_index=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    access_password = models.CharField(max_length=128, blank=True, null=True)  # Encrypted
    process_type = models.CharField(max_length=10, choices=PROCESS_TYPE_CHOICES, default='linear')
    is_active = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'process'
        verbose_name_plural = 'processes'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['unique_slug']),
            models.Index(fields=['process_type']),
        ]

    def __str__(self):
        return f"{self.title} ({self.unique_slug})"


class ProcessStep(models.Model):
    """
    Individual steps/stages within a process (links to forms)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    process = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        related_name='steps'
    )
    form = models.ForeignKey(
        'forms.Form',
        on_delete=models.CASCADE,
        related_name='process_steps'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order_index = models.PositiveIntegerField(
        validators=[MinValueValidator(0)]
    )
    is_required = models.BooleanField(default=True)
    conditions = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'process_step'
        indexes = [
            models.Index(fields=['process', 'order_index']),
            models.Index(fields=['form']),
        ]
        unique_together = [['process', 'order_index']]

    def __str__(self):
        return f"{self.title} ({self.process.title})"