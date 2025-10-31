from rest_framework import serializers

class AnalyticsOverviewSerializer(serializers.Serializer):
    total_views = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    last_viewed_at = serializers.DateTimeField(allow_null=True)
    last_submitted_at = serializers.DateTimeField(allow_null=True)


class TimeSeriesDataPointSerializer(serializers.Serializer):
    period_group = serializers.DateTimeField()
    count = serializers.IntegerField()


class DropOffReportSerializer(serializers.Serializer):
    views = serializers.IntegerField()
    started_submission = serializers.IntegerField()
    completed_submission = serializers.IntegerField()


class SummaryReportSerializer(serializers.Serializer):
    field_id = serializers.UUIDField()
    label = serializers.CharField()
    field_type = serializers.CharField()
    total_responses = serializers.IntegerField()
    aggregation = serializers.DictField()


class FieldSpecificReportSerializer(SummaryReportSerializer):
    pass