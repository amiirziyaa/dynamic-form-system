import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Form(models.Model):
    """
    Form model for storing form definitions and metadata
    """
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forms'
    )
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='forms'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    unique_slug = models.SlugField(max_length=100, unique=True, db_index=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    access_password = models.CharField(max_length=128, blank=True, null=True)  # Encrypted
    is_active = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'form'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['unique_slug']),
            models.Index(fields=['category']),
            models.Index(fields=['visibility', 'is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.unique_slug})"


class FormField(models.Model):
    """
    Individual questions/inputs within a form
    """
    FIELD_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('email', 'Email'),
        ('select', 'Select'),
        ('checkbox', 'Checkbox'),
        ('radio', 'Radio'),
        ('textarea', 'Textarea'),
        ('date', 'Date'),
        ('file', 'File'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(
        Form,
        on_delete=models.CASCADE,
        related_name='fields'
    )
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES)
    label = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_required = models.BooleanField(default=False)
    order_index = models.PositiveIntegerField(
        validators=[MinValueValidator(0)]
    )
    validation_rules = models.JSONField(default=dict, blank=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'form_field'
        indexes = [
            models.Index(fields=['form', 'order_index']),
        ]
        unique_together = [['form', 'order_index']]

    def __str__(self):
        return f"{self.label} ({self.form.title})"


class FieldOption(models.Model):
    """
    Options for select, radio, and checkbox fields
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    field = models.ForeignKey(
        FormField,
        on_delete=models.CASCADE,
        related_name='options'
    )
    label = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    order_index = models.PositiveIntegerField(
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'field_option'
        indexes = [
            models.Index(fields=['field', 'order_index']),
        ]
        unique_together = [['field', 'order_index']]

    def __str__(self):
        return f"{self.label} ({self.field.label})"