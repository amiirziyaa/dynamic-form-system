import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class FormSubmission(models.Model):
    """
    Tracks individual form submissions (user responses)
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    form = models.ForeignKey(
        'forms.Form',
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='form_submissions'
    )
    process_progress = models.ForeignKey(
        'ProcessProgress',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submissions'
    )
    session_id = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    metadata = models.JSONField(default=dict, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'form_submission'
        indexes = [
            models.Index(fields=['form']),
            models.Index(fields=['user']),
            models.Index(fields=['session_id']),
            models.Index(fields=['status']),
            models.Index(fields=['submitted_at']),
            models.Index(fields=['process_progress']),
        ]

    def __str__(self):
        return f"Submission {self.id} for {self.form.title}"


class SubmissionAnswer(models.Model):
    """
    Individual field responses within a submission
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(
        FormSubmission,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    field = models.ForeignKey(
        'forms.FormField',
        on_delete=models.CASCADE,
        related_name='answers'
    )
    text_value = models.TextField(blank=True, null=True)
    numeric_value = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        blank=True,
        null=True
    )
    boolean_value = models.BooleanField(blank=True, null=True)
    date_value = models.DateTimeField(blank=True, null=True)
    array_value = models.JSONField(blank=True, null=True)  # For multiple selections
    file_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'submission_answer'
        indexes = [
            models.Index(fields=['submission']),
            models.Index(fields=['field']),
            models.Index(fields=['field', 'numeric_value']),
        ]

    def __str__(self):
        return f"Answer for {self.field.label} in {self.submission}"


class ProcessProgress(models.Model):
    """
    Tracks user's journey through a multi-step process
    """
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    process = models.ForeignKey(
        'processes.Process',
        on_delete=models.CASCADE,
        related_name='progress_records'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='process_progress'
    )
    session_id = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='in_progress')
    current_step_index = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0
    )
    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'process_progress'
        indexes = [
            models.Index(fields=['process']),
            models.Index(fields=['user']),
            models.Index(fields=['session_id']),
            models.Index(fields=['status']),
            models.Index(fields=['last_activity_at']),
        ]

    def __str__(self):
        return f"Progress for {self.process.title} - {self.status}"


class ProcessStepCompletion(models.Model):
    """
    Tracks completion status of individual steps within a process
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    progress = models.ForeignKey(
        ProcessProgress,
        on_delete=models.CASCADE,
        related_name='step_completions'
    )
    step = models.ForeignKey(
        'processes.ProcessStep',
        on_delete=models.CASCADE,
        related_name='completions'
    )
    submission = models.ForeignKey(
        FormSubmission,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='step_completions'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'process_step_completion'
        unique_together = [['progress', 'step']]

    def __str__(self):
        return f"Step completion for {self.step.title} - {self.status}"