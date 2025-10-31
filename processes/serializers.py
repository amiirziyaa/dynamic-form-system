from rest_framework import serializers
from django.utils.text import slugify
from django.contrib.auth.hashers import make_password
from rest_framework.validators import UniqueValidator
import uuid
from .models import Process, ProcessStep
from categories.models import Category
from forms.models import Form


class ProcessStepListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing process steps
    """
    form_slug = serializers.SlugField(source='form.unique_slug', read_only=True)
    form_title = serializers.CharField(source='form.title', read_only=True)

    class Meta:
        model = ProcessStep
        fields = [
            'id', 'title', 'description', 'order_index', 
            'is_required', 'form_slug', 'form_title', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'form_slug', 'form_title']


class ProcessStepSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for ProcessStep (Create, Retrieve, Update)
    """
    form_slug = serializers.SlugField(source='form.unique_slug', read_only=True)
    form_title = serializers.CharField(source='form.title', read_only=True)
    
    form = serializers.PrimaryKeyRelatedField(
        queryset=Form.objects.all(),
        write_only=True,
        pk_field=serializers.UUIDField()
    )

    class Meta:
        model = ProcessStep
        fields = [
            'id', 'process', 'form', 'form_slug', 'form_title',
            'title', 'description', 'order_index', 'is_required',
            'conditions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'form_slug', 'form_title']
        extra_kwargs = {
            'process': {'write_only': True}
        }

    def validate_form(self, value):
        """
        Ensure the form exists and is accessible
        """
        if not value:
            raise serializers.ValidationError("Form is required")
        return value

    def validate_order_index(self, value):
        """
        Validate order index is non-negative
        """
        if value < 0:
            raise serializers.ValidationError("Order index cannot be negative")
        return value

    def validate_title(self, value):
        """
        Title must not be empty
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()


class ProcessStepReorderSerializer(serializers.Serializer):
    """
    Serializer for reordering process steps
    """
    step_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="List of step IDs in the desired order"
    )

    def validate_step_ids(self, value):
        """
        Validate all step IDs exist and belong to the same process
        """
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate step IDs are not allowed")
        return value


class ProcessListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing processes
    """
    steps_count = serializers.IntegerField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Process
        fields = [
            'id', 'title', 'description', 'unique_slug', 'visibility',
            'process_type', 'is_active', 'category_name', 'steps_count',
            'published_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'steps_count', 'category_name']


# Serializers for public process endpoints
class ProcessViewSerializer(serializers.Serializer):
    """Serializer for tracking process view"""
    session_id = serializers.CharField(required=False, help_text='Optional session identifier')


class ProcessStartSerializer(serializers.Serializer):
    """Serializer for starting a process"""
    session_id = serializers.CharField(required=False, help_text='Optional session identifier')


class ProcessCompleteStepSerializer(serializers.Serializer):
    """Serializer for completing a process step"""
    submission_id = serializers.UUIDField(required=False, help_text='Optional submission ID')
    session_id = serializers.CharField(required=False, help_text='Optional session ID')


class ProcessCompleteSerializer(serializers.Serializer):
    """Serializer for completing a process"""
    session_id = serializers.CharField(required=True, help_text='Session identifier')


class ProcessSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Process (Create, Retrieve, Update)
    Includes nested steps on retrieve
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    steps = ProcessStepListSerializer(many=True, read_only=True)
    
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
        pk_field=serializers.UUIDField()
    )
    
    unique_slug = serializers.SlugField(
        max_length=100,
        required=False,
        allow_blank=True,
        validators=[UniqueValidator(queryset=Process.objects.all(), message="A process with this slug already exists.")]
    )
    
    access_password = serializers.CharField(
        max_length=128,
        write_only=True,
        required=False,
        allow_null=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = Process
        fields = [
            'id', 'user', 'category', 'title', 'description', 'unique_slug',
            'visibility', 'access_password', 'process_type', 'is_active', 
            'settings', 'published_at', 'created_at', 'updated_at', 'steps'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'steps']

    def validate_category(self, value):
        """
        Check if the category belongs to the request user
        """
        if value and value.user != self.context['request'].user:
            raise serializers.ValidationError("This category does not belong to you.")
        return value

    def validate_unique_slug(self, value):
        """
        Generate slug from title if not provided, ensure uniqueness
        """
        if not value:
            title = self.initial_data.get('title')
            if not title:
                raise serializers.ValidationError({'title': 'Title is required to generate a slug.'})
            
            slug = slugify(title)
            if Process.objects.filter(unique_slug=slug).exists():
                slug = f"{slug}-{uuid.uuid4().hex[:6]}"
            
            return slug
        
        if self.instance:
            if Process.objects.filter(unique_slug=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("A process with this slug already exists.")
        
        return value

    def validate_process_type(self, value):
        """
        Validate process type is valid
        """
        valid_types = [choice[0] for choice in Process.PROCESS_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Process type must be one of {valid_types}"
            )
        return value

    def validate_visibility(self, value):
        """
        Validate visibility choice
        """
        valid_choices = [choice[0] for choice in Process.VISIBILITY_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(
                f"Visibility must be one of {valid_choices}"
            )
        return value

    def validate(self, data):
        """
        Validate password requirement for private processes
        """
        visibility = data.get('visibility', self.instance.visibility if self.instance else 'public')
        access_password = data.get('access_password')

        if visibility == 'private':
            if self.instance and not access_password:
                pass  # Keep existing password if not changing
            elif not access_password:
                raise serializers.ValidationError({
                    'access_password': 'Password is required for private processes.'
                })
        
        elif visibility == 'public':
            data['access_password'] = None

        return data

    def create(self, validated_data):
        """
        Handle password hashing on create
        """
        access_password = validated_data.pop('access_password', None)
        if validated_data.get('visibility') == 'private' and access_password:
            validated_data['access_password'] = make_password(access_password)
            
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Handle password hashing on update
        """
        access_password = validated_data.pop('access_password', None)
        
        if access_password is not None:
            if instance.visibility == 'private' and access_password:
                validated_data['access_password'] = make_password(access_password)
            elif validated_data.get('visibility') == 'private' and access_password:
                validated_data['access_password'] = make_password(access_password)
        
        return super().update(instance, validated_data)

