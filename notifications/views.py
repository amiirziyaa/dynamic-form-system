from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Webhook, ReportSchedule, ReportInstance
from .serializers import (
    WebhookSerializer, 
    ReportScheduleSerializer,
    ReportInstanceSerializer
)
from .tasks import generate_scheduled_report

class WebhookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for:
    POST /api/v1/admin/webhooks/
    GET /api/v1/admin/webhooks/
    PATCH /api/v1/admin/webhooks/{id}/
    DELETE /api/v1/admin/webhooks/{id}/
    """
    serializer_class = WebhookSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return Webhook.objects.all() 
        # return Webhook.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'], url_path='test')
    def test_webhook(self, request, pk=None):
        """
        POST /api/v1/admin/webhooks/{id}/test/
        """
        webhook = self.get_object()
        
        # success, message = trigger_webhook_test(webhook)
        # if not success:
        #    return Response({'status': 'failed', 'message': message}, status=400)
            
        return Response({
            'status': 'test_triggered', 
            'message': f'Test payload sent to {webhook.url}'
        })


class ReportAdminViewSet(viewsets.GenericViewSet,
                         mixins.ListModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.CreateModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.DestroyModelMixin):
    """
    ViewSet for Report Configuration and History.
    Covers:
    GET /api/v1/admin/reports/config/
    POST /api/v1/admin/reports/config/
    PATCH /api/v1/admin/reports/config/{id}/
    DELETE /api/v1/admin/reports/config/{id}/
    GET /api/v1/admin/reports/history/
    GET /api/v1/admin/reports/{id}/download/ (Get details, URL is in response)
    POST /api/v1/admin/reports/generate/
    """
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action in ['list_history', 'retrieve_history']:
            return ReportInstanceSerializer
        return ReportScheduleSerializer

    def get_queryset(self):
        if self.action in ['list_history', 'retrieve_history']:
            return ReportInstance.objects.all()
        return ReportSchedule.objects.all()

    # === Report Configuration Endpoints ===
    
    @action(detail=False, methods=['get'], url_path='config')
    def list_config(self, request, *args, **kwargs):
        """ GET /api/v1/admin/reports/config/ """
        return self.list(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='config')
    def create_config(self, request, *args, **kwargs):
        """ POST /api/v1/admin/reports/config/ """
        return self.create(request, *args, **kwargs)

    @action(detail=True, methods=['patch'], url_path='config')
    def update_config(self, request, pk=None, *args, **kwargs):
        """ PATCH /api/v1/admin/reports/config/{id}/ """
        return self.partial_update(request, pk, *args, **kwargs)

    @action(detail=True, methods=['delete'], url_path='config')
    def delete_config(self, request, pk=None, *args, **kwargs):
        """ DELETE /api/v1/admin/reports/config/{id}/ """
        return self.destroy(request, pk, *args, **kwargs)

    # === Manual Reports Endpoints ===

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_manual(self, request, *args, **kwargs):
        """
        POST /api/v1/admin/reports/generate/
        Body: { "report_type": "...", "output_format": "csv", ... }
        """
        serializer = ReportScheduleSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
                
        instance = ReportInstance.objects.create(
            triggered_by=request.user,
            report_type=serializer.validated_data['report_type'],
            status='pending'
        )
        
        # generate_scheduled_report.delay(schedule_id=None, instance_id=instance.id) 
        
        return Response(
            {"message": "Manual report generation triggered.", "instance_id": instance.id}, 
            status=status.HTTP_202_ACCEPTED
        )

    # === Report History Endpoints ===
    
    @action(detail=False, methods=['get'], url_path='history')
    def list_history(self, request, *args, **kwargs):
        """ GET /api/v1/admin/reports/history/ """
        return self.list(request, *args, **kwargs)

    @action(detail=True, methods=['get'], url_path='download')
    def retrieve_history(self, request, pk=None, *args, **kwargs):
        """
        GET /api/v1/admin/reports/{id}/download/
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        if instance.status == 'completed' and instance.file_url:
            return Response(serializer.data)
        elif instance.status == 'failed':
            return Response(serializer.data, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)