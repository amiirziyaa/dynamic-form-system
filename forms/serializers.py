from rest_framework import serializers
from .models import FormField, FieldOption, Form
from django.db import transaction
import re

class FieldOptionSerializer(serializers.ModelSerializer):
    """
    Field Options Serializer (Select, Radio, Checkbox)
    """
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = FieldOption
        fields = ['id', 'label', 'value', 'order_index', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_order_index(self, value):
        """Order Validation"""
        if value < 0:
            raise serializers.ValidationError("Order cannot be negative")
        return value

    def validate_label(self, value):
        """Label must not be empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Label cannot be empty")
        return value.strip()

    def validate_value(self, value):
        """Value must not be empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Value cannot be empty")
        return value.strip()


class FormFieldSerializer(serializers.ModelSerializer):
    """
    Main Field Serializer with Options Support
    """
    id = serializers.UUIDField(read_only=True)
    options = FieldOptionSerializer(many=True, required=False)
    form_slug = serializers.SlugField(source='form.unique_slug', read_only=True)

    class Meta:
        model = FormField
        fields = [
            'id', 'form', 'form_slug', 'field_type', 'label', 'description',
            'is_required', 'order_index', 'validation_rules', 'settings',
            'options', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'form_slug']
        extra_kwargs = {
            'form': {'write_only': True}
        }

    def validate_field_type(self, value):
        """Field Type Validation"""
        valid_types = [choice[0] for choice in FormField.FIELD_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Field type must be one of {valid_types}"
            )
        return value

    def validate_label(self, value):
        """Label must not be empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Label cannot be empty")
        return value.strip()

    def validate(self, data):
        """
        General validation - checking options for choice fields
        """
        field_type = data.get('field_type')
        options = self.initial_data.get('options', [])

        # Fields that require options
        fields_requiring_options = ['select', 'radio', 'checkbox']

        if field_type in fields_requiring_options:
            if not options or len(options) < 2:
                raise serializers.ValidationError({
                    'options': f'{field_type} field must have at least 2 options'
                })

            # Check for duplicate option values
            option_values = [opt['value'] for opt in options if 'value' in opt]
            if len(option_values) != len(set(option_values)):
                raise serializers.ValidationError({
                    'options': 'Option values must be unique'
                })

        # If field doesn't require options, it shouldn't have options
        elif field_type not in fields_requiring_options and options:
            raise serializers.ValidationError({
                'options': f'{field_type} field cannot have options'
            })

        # Validate order_index uniqueness for the form
        form = data.get('form')
        order_index = data.get('order_index')

        if form and order_index is not None:
            # Check if updating existing field
            if self.instance:
                existing = FormField.objects.filter(
                    form=form,
                    order_index=order_index
                ).exclude(id=self.instance.id).exists()
            else:
                existing = FormField.objects.filter(
                    form=form,
                    order_index=order_index
                ).exists()

            if existing:
                raise serializers.ValidationError({
                    'order_index': f'A field with order_index {order_index} already exists in this form'
                })

        return data

    def validate_validation_rules(self, value):
        """
        Enhanced validation rules validation based on field type
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("validation_rules must be a dictionary")

        # Get field_type from initial_data or instance
        field_type = self.initial_data.get('field_type')
        if not field_type and self.instance:
            field_type = self.instance.field_type

        # Define valid keys per field type
        all_valid_keys = {
            'text': ['min_length', 'max_length', 'pattern', 'allowed_chars'],
            'textarea': ['min_length', 'max_length', 'pattern'],
            'number': ['min_value', 'max_value', 'integer_only', 'step'],
            'email': ['pattern', 'allowed_domains', 'blocked_domains'],
            'date': ['min_date', 'max_date', 'disable_past', 'disable_future', 'allowed_days'],
            'file': ['max_size', 'allowed_extensions', 'allowed_mime_types'],
            'select': ['other_option'],
            'radio': ['other_option'],
            'checkbox': ['min_selections', 'max_selections', 'other_option']
        }

        # Get valid keys for this field type
        valid_keys = all_valid_keys.get(field_type, [])

        # Check for invalid keys
        for key in value.keys():
            if key not in valid_keys:
                raise serializers.ValidationError(
                    f"Key '{key}' is not valid for field type '{field_type}'. Valid keys: {valid_keys}"
                )

        # Specific validations based on field type
        if field_type in ['text', 'textarea']:
            if 'min_length' in value and 'max_length' in value:
                if value['min_length'] > value['max_length']:
                    raise serializers.ValidationError("min_length cannot be greater than max_length")

            if 'min_length' in value and value['min_length'] < 0:
                raise serializers.ValidationError("min_length cannot be negative")

            if 'pattern' in value:
                try:
                    re.compile(value['pattern'])
                except re.error:
                    raise serializers.ValidationError("Invalid regex pattern")

        elif field_type == 'number':
            if 'min_value' in value and 'max_value' in value:
                if value['min_value'] > value['max_value']:
                    raise serializers.ValidationError("min_value cannot be greater than max_value")

            if 'step' in value and value['step'] <= 0:
                raise serializers.ValidationError("step must be positive")

        elif field_type == 'file':
            if 'max_size' in value and value['max_size'] <= 0:
                raise serializers.ValidationError("max_size must be positive")

            if 'allowed_extensions' in value:
                if not isinstance(value['allowed_extensions'], list):
                    raise serializers.ValidationError("allowed_extensions must be a list")
                if not value['allowed_extensions']:
                    raise serializers.ValidationError("allowed_extensions cannot be empty")

        elif field_type == 'checkbox':
            if 'min_selections' in value and 'max_selections' in value:
                if value['min_selections'] > value['max_selections']:
                    raise serializers.ValidationError("min_selections cannot be greater than max_selections")

            if 'min_selections' in value and value['min_selections'] < 0:
                raise serializers.ValidationError("min_selections cannot be negative")

        return value

    def validate_settings(self, value):
        """
        Validate settings field structure
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("settings must be a dictionary")

        # Common valid settings keys
        valid_settings_keys = [
            'placeholder',
            'help_text',
            'default_value',
            'prefix',
            'suffix',
            'css_class',
            'show_character_count',
            'rows',  # for textarea
            'cols',  # for textarea
            'multiple',  # for file upload
            'accept',  # for file upload
        ]

        for key in value.keys():
            if key not in valid_settings_keys:
                raise serializers.ValidationError(
                    f"Key '{key}' is not valid in settings. Valid keys: {valid_settings_keys}"
                )

        return value

    @transaction.atomic
    def create(self, validated_data):
        """Create field along with options"""
        options_data = validated_data.pop('options', [])

        # Create field
        field = FormField.objects.create(**validated_data)

        # Create options if they exist
        if options_data:
            for option_data in options_data:
                FieldOption.objects.create(field=field, **option_data)

        return field

    @transaction.atomic
    def update(self, instance, validated_data):
        """Edit field along with options"""
        options_data = validated_data.pop('options', None)

        # Edit field
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Edit options
        if options_data is not None:
            # Delete previous options
            instance.options.all().delete()

            # Create new options
            for option_data in options_data:
                FieldOption.objects.create(field=instance, **option_data)

        return instance


class FormFieldListSerializer(serializers.ModelSerializer):
    """
    Simple serializer for fields list (without options for better performance)
    """
    id = serializers.UUIDField(read_only=True)
    options_count = serializers.SerializerMethodField()

    class Meta:
        model = FormField
        fields = [
            'id', 'field_type', 'label', 'is_required',
            'order_index', 'options_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_options_count(self, obj):
        """Number of options (only for choice fields) """
        if obj.field_type in ['select', 'radio', 'checkbox']:
            return obj.options.count()
        return 0


class FormFieldReorderSerializer(serializers.Serializer):
    """
    Serializer for changing field order
    Input: [{"id": "uuid1", "order_index": 0}, {"id": "uuid2", "order_index": 1}]
    """
    fields = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        min_length=1
    )

    def validate_fields(self, value):
        """Reorder input validation"""
        seen_order_indices = set()

        for item in value:
            if 'id' not in item or 'order_index' not in item:
                raise serializers.ValidationError(
                    "Each item must have id and order_index"
                )

            try:
                order_idx = int(item['order_index'])
                if order_idx < 0:
                    raise serializers.ValidationError("order_index cannot be negative")

                # Check for duplicate order_index in request
                if order_idx in seen_order_indices:
                    raise serializers.ValidationError(
                        f"Duplicate order_index {order_idx} in request"
                    )
                seen_order_indices.add(order_idx)

            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    "order_index must be an integer"
                )

        return value

    @transaction.atomic
    def save(self, form):
        """Save new order"""
        fields_data = self.validated_data['fields']

        # Verify all fields belong to this form
        field_ids = [item['id'] for item in fields_data]
        existing_fields = FormField.objects.filter(
            id__in=field_ids,
            form=form
        ).count()

        if existing_fields != len(field_ids):
            raise serializers.ValidationError(
                "One or more fields do not belong to this form"
            )

        # Update order_index for all fields
        for item in fields_data:
            FormField.objects.filter(
                id=item['id'],
                form=form
            ).update(order_index=int(item['order_index']))

        return FormField.objects.filter(form=form).order_by('order_index')


class FieldOptionReorderSerializer(serializers.Serializer):
    """Serializer for changing options order"""
    options = serializers.ListField(

        child=serializers.DictField(
            child=serializers.CharField()
        ),
        min_length=1
    )

    def validate_options(self, value):
        """Reorder input validation"""
        seen_order_indices = set()

        for item in value:
            if 'id' not in item or 'order_index' not in item:
                raise serializers.ValidationError(
                    "Each item must have id and order_index"
                )
            try:
                order_idx = int(item['order_index'])
                if order_idx < 0:
                    raise serializers.ValidationError("order_index cannot be negative")

                # Check for duplicate order_index in request
                if order_idx in seen_order_indices:
                    raise serializers.ValidationError(
                        f"Duplicate order_index {order_idx} in request"
                    )
                seen_order_indices.add(order_idx)

            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    "order_index must be an integer"
                )

        return value

    @transaction.atomic
    def save(self, field):
        """Save new options order"""
        options_data = self.validated_data['options']

        # Verify all options belong to this field
        option_ids = [item['id'] for item in options_data]
        existing_options = FieldOption.objects.filter(
            id__in=option_ids,
            field=field
        ).count()

        if existing_options != len(option_ids):
            raise serializers.ValidationError(
                "One or more options do not belong to this field"
            )

        # Update order_index for all options
        for item in options_data:
            FieldOption.objects.filter(
                id=item['id'],
                field=field
            ).update(order_index=int(item['order_index']))

        return FieldOption.objects.filter(field=field).order_by('order_index')