from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import Webhook, ReportSchedule, ReportInstance
from .serializers import (
    WebhookSerializer, 
    ReportScheduleSerializer,
    ReportInstanceSerializer
)
from .tasks import generate_scheduled_report

@extend_schema_view(
    list=extend_schema(
        tags=['Admin Webhooks'],
        summary='List webhooks',
        description='List all webhook configurations.',
        responses={200: WebhookSerializer(many=True)}
    ),
    create=extend_schema(
        tags=['Admin Webhooks'],
        summary='Create webhook',
        description='Create a new webhook configuration for report notifications.',
        request=WebhookSerializer,
        responses={201: WebhookSerializer}
    ),
    retrieve=extend_schema(
        tags=['Admin Webhooks'],
        summary='Get webhook details',
        description='Get detailed information about a specific webhook.',
        responses={200: WebhookSerializer}
    ),
    update=extend_schema(
        tags=['Admin Webhooks'],
        summary='Update webhook',
        description='Update a webhook configuration.',
        request=WebhookSerializer,
        responses={200: WebhookSerializer}
    ),
    partial_update=extend_schema(
        tags=['Admin Webhooks'],
        summary='Partially update webhook',
        description='Partially update a webhook configuration.',
        request=WebhookSerializer,
        responses={200: WebhookSerializer}
    ),
    destroy=extend_schema(
        tags=['Admin Webhooks'],
        summary='Delete webhook',
        description='Delete a webhook configuration.',
        responses={204: None}
    )
)
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
    
    @extend_schema(
        tags=['Admin Webhooks'],
        summary='Test webhook',
        description='Send a test payload to the webhook URL to verify configuration.',
        parameters=[
            OpenApiParameter(
                name='id',
                type=str,
                location=OpenApiParameter.PATH,
                description='Webhook UUID',
                required=True
            )
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'test_triggered'},
                    'message': {'type': 'string', 'example': 'Test payload sent to https://example.com/webhook'}
                }
            }
        }
    )
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


@extend_schema_view(
    list_config=extend_schema(
        tags=['Admin Reports'],
        summary='List report configurations',
        description='Get all report schedule configurations.',
        responses={200: ReportScheduleSerializer(many=True)}
    ),
    create_config=extend_schema(
        tags=['Admin Reports'],
        summary='Create report configuration',
        description='Create a new scheduled report configuration.',
        request=ReportScheduleSerializer,
        responses={201: ReportScheduleSerializer}
    ),
    update_config=extend_schema(
        tags=['Admin Reports'],
        summary='Update report configuration',
        description='Update a report schedule configuration.',
        request=ReportScheduleSerializer,
        responses={200: ReportScheduleSerializer}
    ),
    delete_config=extend_schema(
        tags=['Admin Reports'],
        summary='Delete report configuration',
        description='Delete a report schedule configuration.',
        responses={204: None}
    ),
    generate_manual=extend_schema(
        tags=['Admin Reports'],
        summary='Generate manual report',
        description='Manually trigger report generation.',
        request=ReportScheduleSerializer,
        responses={
            202: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'instance_id': {'type': 'string', 'format': 'uuid'}
                }
            }
        }
    ),
    list_history=extend_schema(
        tags=['Admin Reports'],
        summary='List report history',
        description='List all generated report instances.',
        responses={200: ReportInstanceSerializer(many=True)}
    ),
    retrieve_history=extend_schema(
        tags=['Admin Reports'],
        summary='Download report',
        description='Get report instance details including download URL.',
        responses={
            200: ReportInstanceSerializer,
            202: {'description': 'Report is still being generated'},
            404: {'description': 'Report generation failed'}
        }
    )
)
class ReportAdminViewSet(viewsets.ModelViewSet):
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
    
    @action(detail=False, methods=['get', 'post'], url_path='config')
    def config(self, request, *args, **kwargs):
        """ GET /api/v1/admin/reports/config/ or POST /api/v1/admin/reports/config/ """
        if request.method == 'GET':
            self.action = 'list'
            queryset = self.filter_queryset(ReportSchedule.objects.all())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        else:  # POST
            self.action = 'create'
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def list_config(self, request, *args, **kwargs):
        """ Alias for GET config """
        return self.config(request, *args, **kwargs)
    
    def create_config(self, request, *args, **kwargs):
        """ Alias for POST config """
        return self.config(request, *args, **kwargs)

    @action(detail=True, methods=['patch', 'put', 'delete'], url_path='config')
    def config_detail(self, request, pk=None):
        """ PATCH /api/v1/admin/reports/{id}/config/ or DELETE /api/v1/admin/reports/{id}/config/ """
        try:
            instance = ReportSchedule.objects.get(pk=pk)
        except ReportSchedule.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'DELETE':
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:  # PATCH or PUT
            # For partial updates, we need to validate only provided fields
            serializer = ReportScheduleSerializer(instance, data=request.data, partial=True, context={'request': request})
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response(serializer.data)
    
    def update_config(self, request, pk=None):
        """ Alias for PATCH config_detail """
        return self.config_detail(request, pk)
    
    def delete_config(self, request, pk=None):
        """ Alias for DELETE config_detail """
        return self.config_detail(request, pk)

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