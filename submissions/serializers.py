from rest_framework import serializers
from submissions.models import FormSubmission, SubmissionAnswer
from forms.models import Form, FormField, FieldOption
from django.db import transaction
from django.utils import timezone
import uuid


class FieldOptionPublicSerializer(serializers.ModelSerializer):
    """Public serializer for field options (no sensitive data)"""

    class Meta:
        model = FieldOption
        fields = ['id', 'label', 'value', 'order_index']


class FormFieldPublicSerializer(serializers.ModelSerializer):
    """Public serializer for form fields"""
    options = FieldOptionPublicSerializer(many=True, read_only=True)

    class Meta:
        model = FormField
        fields = [
            'id', 'field_type', 'label', 'description',
            'is_required', 'order_index', 'validation_rules',
            'settings', 'options'
        ]


class FormPublicSerializer(serializers.ModelSerializer):
    """
    Public serializer for form structure
    Used when users want to view/fill a form
    """
    fields = FormFieldPublicSerializer(many=True, read_only=True)
    is_password_protected = serializers.SerializerMethodField()

    class Meta:
        model = Form
        fields = [
            'id', 'title', 'description', 'unique_slug',
            'is_password_protected', 'fields', 'settings'
        ]

    def get_is_password_protected(self, obj):
        """Check if form requires password"""
        return obj.visibility == 'private' and bool(obj.access_password)


class FormPasswordVerifySerializer(serializers.Serializer):
    """Serializer for verifying private form password"""
    password = serializers.CharField(required=True, write_only=True)

    def validate_password(self, value):
        """Validate password against form"""
        from django.contrib.auth.hashers import check_password
        
        form = self.context.get('form')
        if not form:
            raise serializers.ValidationError("Form not found")

        if form.visibility != 'private':
            raise serializers.ValidationError("This form is not password protected")

        if not form.access_password:
            raise serializers.ValidationError("This form has no password set")

        if not check_password(value, form.access_password):
            raise serializers.ValidationError("Incorrect password")

        return value


class SubmissionAnswerSerializer(serializers.ModelSerializer):
    """Serializer for individual field answers"""
    field_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = SubmissionAnswer
        fields = [
            'id', 'field_id', 'text_value', 'numeric_value',
            'boolean_value', 'date_value', 'array_value', 'file_url'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        """Validate answer based on field type and validation rules"""
        field_id = data.get('field_id')

        try:
            field = FormField.objects.get(id=field_id)
        except FormField.DoesNotExist:
            raise serializers.ValidationError({'field_id': 'Field not found'})

        # Check which value field should be filled based on field_type
        field_type = field.field_type
        value_fields = {
            'text': 'text_value',
            'textarea': 'text_value',
            'email': 'text_value',
            'number': 'numeric_value',
            'date': 'date_value',
            'checkbox': 'array_value',
            'select': 'text_value',
            'radio': 'text_value',
            'file': 'file_url',
        }

        expected_field = value_fields.get(field_type)
        if not expected_field:
            raise serializers.ValidationError(
                f"Unsupported field type: {field_type}"
            )

        # Check if correct value field is provided
        if not data.get(expected_field):
            raise serializers.ValidationError({
                expected_field: f"This field is required for {field_type} type"
            })

        # Validate based on field's validation_rules
        self._validate_field_rules(field, data)

        return data

    def _validate_field_rules(self, field, data):
        """Apply field-specific validation rules"""
        rules = field.validation_rules or {}
        field_type = field.field_type

        # Text/Textarea validation
        if field_type in ['text', 'textarea']:
            text = data.get('text_value', '')
            if 'min_length' in rules and len(text) < rules['min_length']:
                raise serializers.ValidationError({
                    'text_value': f"Minimum length is {rules['min_length']}"
                })
            if 'max_length' in rules and len(text) > rules['max_length']:
                raise serializers.ValidationError({
                    'text_value': f"Maximum length is {rules['max_length']}"
                })

        # Number validation
        elif field_type == 'number':
            num = data.get('numeric_value')
            if num is not None:
                if 'min_value' in rules and num < rules['min_value']:
                    raise serializers.ValidationError({
                        'numeric_value': f"Minimum value is {rules['min_value']}"
                    })
                if 'max_value' in rules and num > rules['max_value']:
                    raise serializers.ValidationError({
                        'numeric_value': f"Maximum value is {rules['max_value']}"
                    })

        # Checkbox validation
        elif field_type == 'checkbox':
            selections = data.get('array_value', [])
            if 'min_selections' in rules and len(selections) < rules['min_selections']:
                raise serializers.ValidationError({
                    'array_value': f"Select at least {rules['min_selections']} options"
                })
            if 'max_selections' in rules and len(selections) > rules['max_selections']:
                raise serializers.ValidationError({
                    'array_value': f"Select at most {rules['max_selections']} options"
                })


class FormSubmissionSerializer(serializers.ModelSerializer):
    """
    Main serializer for form submissions
    Handles both draft and final submission
    """
    answers = SubmissionAnswerSerializer(many=True, required=True)
    form_slug = serializers.SlugField(write_only=True)

    class Meta:
        model = FormSubmission
        fields = [
            'id', 'form_slug', 'session_id', 'status',
            'answers', 'metadata', 'submitted_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'submitted_at', 'created_at', 'updated_at']

    def validate(self, data):
        """Validate submission"""
        form_slug = data.get('form_slug')
        answers = data.get('answers', [])

        # Get form
        try:
            form = Form.objects.prefetch_related('fields').get(
                unique_slug=form_slug,
                is_active=True
            )
        except Form.DoesNotExist:
            raise serializers.ValidationError({'form_slug': 'Form not found'})

        # Store form for create method
        self.context['form'] = form

        # Check if it's a final submission (not draft)
        if data.get('status') == 'submitted':
            # Validate all required fields are answered
            required_fields = form.fields.filter(is_required=True)
            answered_field_ids = [ans['field_id'] for ans in answers]

            for req_field in required_fields:
                if req_field.id not in answered_field_ids:
                    raise serializers.ValidationError({
                        'answers': f"Required field '{req_field.label}' is missing"
                    })

        # Validate all answers belong to this form
        form_field_ids = list(form.fields.values_list('id', flat=True))
        for answer in answers:
            if answer['field_id'] not in form_field_ids:
                raise serializers.ValidationError({
                    'answers': f"Field {answer['field_id']} does not belong to this form"
                })

        return data

    @transaction.atomic
    def create(self, validated_data):
        """Create submission with answers"""
        answers_data = validated_data.pop('answers')
        form_slug = validated_data.pop('form_slug')
        form = self.context['form']

        # Generate session_id if not provided
        if 'session_id' not in validated_data:
            validated_data['session_id'] = str(uuid.uuid4())

        # Set submitted_at for final submissions
        if validated_data.get('status') == 'submitted':
            validated_data['submitted_at'] = timezone.now()

        # Get user from request (if authenticated)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user

        # Create submission
        submission = FormSubmission.objects.create(
            form=form,
            **validated_data
        )

        # Create answers
        for answer_data in answers_data:
            field_id = answer_data.pop('field_id')
            SubmissionAnswer.objects.create(
                submission=submission,
                field_id=field_id,
                **answer_data
            )

        return submission

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update draft submission"""
        answers_data = validated_data.pop('answers', None)
        validated_data.pop('form_slug', None)  # Can't change form

        # Update submission
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Set submitted_at if status changed to submitted
        if validated_data.get('status') == 'submitted' and not instance.submitted_at:
            instance.submitted_at = timezone.now()

        instance.save()

        # Update answers if provided
        if answers_data is not None:
            # Delete old answers
            instance.answers.all().delete()

            # Create new answers
            for answer_data in answers_data:
                field_id = answer_data.pop('field_id')
                SubmissionAnswer.objects.create(
                    submission=instance,
                    field_id=field_id,
                    **answer_data
                )

        return instance


class FormSubmissionReadSerializer(serializers.ModelSerializer):
    """Read-only serializer for viewing submissions"""
    answers = SubmissionAnswerSerializer(many=True, read_only=True)
    form_title = serializers.CharField(source='form.title', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True, allow_null=True)

    class Meta:
        model = FormSubmission
        fields = [
            'id', 'form_title', 'user_email', 'session_id', 'status',
            'answers', 'metadata', 'submitted_at',
            'created_at', 'updated_at'
        ]


class SubmissionAnswerDetailSerializer(serializers.ModelSerializer):
    """Detailed answer with field info"""
    field_label = serializers.CharField(source='field.label', read_only=True)
    field_type = serializers.CharField(source='field.field_type', read_only=True)

    class Meta:
        model = SubmissionAnswer
        fields = [
            'id', 'field_label', 'field_type',
            'text_value', 'numeric_value', 'boolean_value',
            'date_value', 'array_value', 'file_url', 'created_at'
        ]


class FormSubmissionDetailSerializer(serializers.ModelSerializer):
    """Detailed submission for owner view"""
    answers = SubmissionAnswerDetailSerializer(many=True, read_only=True)
    form_title = serializers.CharField(source='form.title', read_only=True)
    form_slug = serializers.CharField(source='form.unique_slug', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = FormSubmission
        fields = [
            'id', 'form_title', 'form_slug', 'user_name', 'session_id',
            'status', 'answers', 'metadata', 'submitted_at',
            'created_at', 'updated_at'
        ]

    def get_user_name(self, obj):
        """Get user full name or email"""
        if obj.user:
            return obj.user.full_name or obj.user.email
        return 'Anonymous'


class SubmissionStatsSerializer(serializers.Serializer):
    """Statistics about form submissions"""
    total_submissions = serializers.IntegerField()
    submitted_count = serializers.IntegerField()
    draft_count = serializers.IntegerField()
    archived_count = serializers.IntegerField()
    unique_users = serializers.IntegerField()
    anonymous_count = serializers.IntegerField()
    average_completion_time = serializers.FloatField(allow_null=True)
    first_submission = serializers.DateTimeField(allow_null=True)
    last_submission = serializers.DateTimeField(allow_null=True)
    submissions_by_date = serializers.DictField(child=serializers.IntegerField())


class BulkDeleteSerializer(serializers.Serializer):
    """Serializer for bulk delete operation"""
    submission_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100  # Limit to 100 at once
    )

    def validate_submission_ids(self, value):
        """Check if all submissions exist"""
        form = self.context.get('form')

        existing = FormSubmission.objects.filter(
            id__in=value,
            form=form
        ).count()

        if existing != len(value):
            raise serializers.ValidationError(
                "Some submissions do not exist or don't belong to this form"
            )

        return value


class ExportSerializer(serializers.Serializer):
    """Serializer for export operations"""
    format = serializers.ChoiceField(
        choices=['csv', 'json', 'excel'],
        default='csv'
    )
    include_drafts = serializers.BooleanField(default=False)
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)
    status = serializers.ChoiceField(
        choices=['all', 'submitted', 'draft', 'archived'],
        default='submitted'
    )

    def validate(self, data):
        """Validate date range"""
        date_from = data.get('date_from')
        date_to = data.get('date_to')

        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError({
                'date_from': 'Start date must be before end date'
            })

        return data