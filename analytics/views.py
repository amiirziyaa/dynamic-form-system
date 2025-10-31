from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from forms.models import Form, FormField
from forms.permissions import IsFormOwner
from . import services
from .serializers import (
    AnalyticsOverviewSerializer,
    TimeSeriesDataPointSerializer,
    DropOffReportSerializer,
    SummaryReportSerializer,
    FieldSpecificReportSerializer
)

class FormAnalyticsViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsFormOwner]

    
    def get_form_object(self):
        form_slug = self.kwargs.get('form_slug')
        form_obj = get_object_or_404(Form, unique_slug=form_slug)
        
        self.check_object_permission(self.request, form_obj)
        return form_obj

    def get_field_object(self):
        form = self.get_form_object()
        field_id = self.kwargs.get('field_id')
        
        return get_object_or_404(
            form.fields.all(),
            id=field_id
        )

    @action(detail=False, methods=['get'], url_path='overview')
    def overview(self, request, *args, **kwargs):
        """
        GET /api/v1/forms/{slug}/analytics/overview/
        """
        form = self.get_form_object()
        stats = services.get_overview_stats(form)
        serializer = AnalyticsOverviewSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='views')
    def views_timeseries(self, request, *args, **kwargs):
        """
        GET /api/v1/forms/{slug}/analytics/views/
        """
        form = self.get_form_object()
        period = request.query_params.get('period', 'day') # ?period=day
        queryset = services.get_timeseries_report(
            form.views.all(), 
            'viewed_at', 
            period
        )
        serializer = TimeSeriesDataPointSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='submissions')
    def submissions_timeseries(self, request, *args, **kwargs):
        """
        GET /api/v1/forms/{slug}/analytics/submissions/
        """
        form = self.get_form_object()
        period = request.query_params.get('period', 'day')
        queryset = services.get_timeseries_report(
            form.submissions.filter(status='submitted'),
            'submitted_at',
            period
        )
        serializer = TimeSeriesDataPointSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='completion-rate')
    def completion_rate(self, request, *args, **kwargs):
        """
        GET /api/v1/forms/{slug}/analytics/completion-rate/
        """
        form = self.get_form_object()
        stats = services.get_overview_stats(form)
        return Response({"completion_rate": stats["completion_rate"]})

    @action(detail=False, methods=['get'], url_path='drop-off')
    def drop_off(self, request, *args, **kwargs):
        """
        GET /api/v1/forms/{slug}/analytics/drop-off/
        """
        form = self.get_form_object()
        report = services.get_drop_off_report(form)
        serializer = DropOffReportSerializer(report)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='reports/summary')
    def summary_report(self, request, *args, **kwargs):
        """
        GET /api/v1/forms/{slug}/reports/summary/
        """
        form = self.get_form_object()
        report = services.get_summary_report(form)
        serializer = SummaryReportSerializer(report, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='reports/field/(?P<field_id>[^/.]+)')
    def field_report(self, request, *args, **kwargs):
        """
        GET /api/v1/forms/{slug}/reports/field/{field_id}/
        """
        field = self.get_field_object()
        report = services.get_field_specific_report(field)
        serializer = FieldSpecificReportSerializer(report)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='reports/real-time')
    def real_time_report(self, request, *args, **kwargs):
        form = self.get_form_object()
        report = services.get_summary_report(form)
        serializer = SummaryReportSerializer(report, many=True)
        return Response(serializer.data)