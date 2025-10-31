from rest_framework import serializers
from .models import Webhook, ReportSchedule, ReportInstance

class WebhookSerializer(serializers.ModelSerializer):
    """
    Serializer for Webhook CRUD operations.
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Webhook
        fields = [
            'id', 'user', 'name', 'url', 'secret_key', 
            'is_active', 'events', 'settings', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'secret_key': {'write_only': True}
        }

    def validate_events(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Events must be a list of strings.")
        return value


class ReportScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for ReportSchedule CRUD operations.
    """
    target = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ReportSchedule
        fields = [
            'id', 'name', 'report_type', 'frequency', 'target', 
            'filters', 'send_to_email', 'send_to_webhook', 
            'output_format', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        if not data.get('send_to_email') and not data.get('send_to_webhook'):
            raise serializers.ValidationError("Either send_to_email or send_to_webhook must be set.")
        return data

    def validate_send_to_webhook(self, value):
        if value and value.user != self.context['request'].user:
            raise serializers.ValidationError("This webhook does not belong to the current user.")
        return value


class ReportInstanceSerializer(serializers.ModelSerializer):
    """
    Serializer for listing report history (Read-Only).
    """
    schedule_name = serializers.CharField(source='schedule.name', read_only=True, default=None)
    triggered_by_email = serializers.EmailField(source='triggered_by.email', read_only=True, default=None)

    class Meta:
        model = ReportInstance
        fields = [
            'id', 'status', 'report_type', 'file_url', 'file_size',
            'error_message', 'started_at', 'completed_at', 'created_at',
            'schedule_name', 'triggered_by_email'
        ]
        read_only_fields = fields