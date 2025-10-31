from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, ValidationError as DRFValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from processes.service_layers.process_analytics_service import ProcessAnalyticsService
from processes.permissions import IsProcessOwner
from shared.exceptions import NotFoundError


class ProcessAnalyticsViewSet(viewsets.GenericViewSet):
    """
    ViewSet for Process Analytics endpoints
    Requires authentication and process ownership

    Endpoints:
    - GET    /api/v1/processes/{slug}/analytics/
    - GET    /api/v1/processes/{slug}/analytics/views/
    - GET    /api/v1/processes/{slug}/analytics/completions/
    - GET    /api/v1/processes/{slug}/analytics/completion-rate/
    - GET    /api/v1/processes/{slug}/analytics/step-drop-off/
    - GET    /api/v1/processes/{slug}/analytics/average-time/
    - GET    /api/v1/processes/{slug}/progress/
    - GET    /api/v1/processes/{slug}/progress/{id}/
    - GET    /api/v1/processes/{slug}/progress/abandoned/
    """
    permission_classes = [IsAuthenticated, IsProcessOwner]
    lookup_field = 'unique_slug'
    lookup_url_kwarg = 'slug'
    serializer_class = None  # No default serializer, all actions have explicit schemas

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analytics_service = ProcessAnalyticsService()

    def get_object(self):
        """Get process object for permission checking"""
        from processes.repository import ProcessRepository
        process_repo = ProcessRepository()
        slug = self.kwargs.get('slug')
        process = process_repo.get_by_slug(slug, self.request.user)
        if not process:
            from shared.exceptions import NotFoundError
            raise NotFoundError(f"Process with slug '{slug}' not found")
        return process

    @extend_schema(
        tags=['Process Analytics'],
        summary='Get analytics overview',
        description='Get comprehensive analytics overview for a process including key metrics.',
        parameters=[
            OpenApiParameter(
                name='slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Process unique slug',
                required=True
            )
        ],
        responses={200: {'type': 'object', 'description': 'Analytics overview data'}}
    )
    @action(detail=True, methods=['get'], url_path='analytics')
    def analytics_overview(self, request, slug=None):
        """
        Get process analytics overview
        GET /api/v1/processes/{slug}/analytics/
        """
        try:
            result = self.analytics_service.get_analytics_overview(request.user, slug)
            return Response(result)
        except NotFoundError as e:
            raise NotFound(str(e))

    @extend_schema(
        tags=['Process Analytics'],
        summary='Get views over time',
        description='Get view count over time. Defaults to last 30 days, max 365 days.',
        parameters=[
            OpenApiParameter(
                name='slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Process unique slug',
                required=True
            ),
            OpenApiParameter(
                name='days',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Number of days to analyze (1-365)',
                required=False,
                default=30
            )
        ],
        responses={200: {'type': 'object', 'description': 'Views over time data'}}
    )
    @action(detail=True, methods=['get'], url_path='analytics/views')
    def analytics_views(self, request, slug=None):
        """
        Get view count over time
        GET /api/v1/processes/{slug}/analytics/views/
        
        Query params:
        - days: Number of days to analyze (default 30)
        """
        try:
            days = int(request.query_params.get('days', 30))
            if days < 1 or days > 365:
                raise DRFValidationError("days must be between 1 and 365")
            
            result = self.analytics_service.get_views_over_time(request.user, slug, days)
            return Response(result)
        except NotFoundError as e:
            raise NotFound(str(e))
        except ValueError:
            raise DRFValidationError("days must be a valid integer")

    @extend_schema(
        tags=['Process Analytics'],
        summary='Get completions over time',
        description='Get completion count over time. Defaults to last 30 days, max 365 days.',
        parameters=[
            OpenApiParameter(
                name='slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Process unique slug',
                required=True
            ),
            OpenApiParameter(
                name='days',
                type=int,
                location=OpenApiParameter.QUERY,
                description='Number of days to analyze (1-365)',
                required=False,
                default=30
            )
        ],
        responses={200: {'type': 'object', 'description': 'Completions over time data'}}
    )
    @action(detail=True, methods=['get'], url_path='analytics/completions')
    def analytics_completions(self, request, slug=None):
        """
        Get completion count over time
        GET /api/v1/processes/{slug}/analytics/completions/
        
        Query params:
        - days: Number of days to analyze (default 30)
        """
        try:
            days = int(request.query_params.get('days', 30))
            if days < 1 or days > 365:
                raise DRFValidationError("days must be between 1 and 365")
            
            result = self.analytics_service.get_completions_over_time(request.user, slug, days)
            return Response(result)
        except NotFoundError as e:
            raise NotFound(str(e))
        except ValueError:
            raise DRFValidationError("days must be a valid integer")

    @extend_schema(
        tags=['Process Analytics'],
        summary='Get completion rate',
        description='Get overall completion rate percentage for the process.',
        parameters=[
            OpenApiParameter(
                name='slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Process unique slug',
                required=True
            )
        ],
        responses={200: {'type': 'object', 'properties': {'completion_rate': {'type': 'number', 'format': 'float'}}}}
    )
    @action(detail=True, methods=['get'], url_path='analytics/completion-rate')
    def analytics_completion_rate(self, request, slug=None):
        """
        Get overall completion rate
        GET /api/v1/processes/{slug}/analytics/completion-rate/
        """
        try:
            result = self.analytics_service.get_completion_rate(request.user, slug)
            return Response(result)
        except NotFoundError as e:
            raise NotFound(str(e))

    @extend_schema(
        tags=['Process Analytics'],
        summary='Get step drop-off analysis',
        description='Get drop-off analysis showing where users abandon the process.',
        parameters=[
            OpenApiParameter(
                name='slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Process unique slug',
                required=True
            )
        ],
        responses={200: {'type': 'object', 'description': 'Step drop-off data'}}
    )
    @action(detail=True, methods=['get'], url_path='analytics/step-drop-off')
    def analytics_step_drop_off(self, request, slug=None):
        """
        Get drop-off analysis by step
        GET /api/v1/processes/{slug}/analytics/step-drop-off/
        """
        try:
            result = self.analytics_service.get_step_drop_off(request.user, slug)
            return Response(result)
        except NotFoundError as e:
            raise NotFound(str(e))

    @extend_schema(
        tags=['Process Analytics'],
        summary='Get average completion time',
        description='Get average time to complete the process.',
        parameters=[
            OpenApiParameter(
                name='slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Process unique slug',
                required=True
            )
        ],
        responses={200: {'type': 'object', 'properties': {'average_time_minutes': {'type': 'number', 'format': 'float'}}}}
    )
    @action(detail=True, methods=['get'], url_path='analytics/average-time')
    def analytics_average_time(self, request, slug=None):
        """
        Get average completion time
        GET /api/v1/processes/{slug}/analytics/average-time/
        """
        try:
            result = self.analytics_service.get_average_completion_time(request.user, slug)
            return Response(result)
        except NotFoundError as e:
            raise NotFound(str(e))

    @extend_schema(
        tags=['Process Analytics'],
        summary='List process progress',
        description='List all progress records for a process. Supports filtering by status.',
        parameters=[
            OpenApiParameter(
                name='slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Process unique slug',
                required=True
            ),
            OpenApiParameter(
                name='status',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Filter by status',
                required=False,
                enum=['in_progress', 'completed', 'abandoned']
            )
        ],
        operation_id='processes_progress_list',
        responses={200: {'type': 'object', 'properties': {'count': {'type': 'integer'}, 'results': {'type': 'array'}}}}
    )
    @action(detail=True, methods=['get'], url_path='progress')
    def list_progress(self, request, slug=None):
        """
        List all progress records for a process
        GET /api/v1/processes/{slug}/progress/
        
        Query params:
        - status: Filter by status (in_progress/completed/abandoned)
        """
        try:
            status_filter = request.query_params.get('status')
            if status_filter and status_filter not in ['in_progress', 'completed', 'abandoned']:
                raise DRFValidationError("status must be one of: in_progress, completed, abandoned")
            
            result = self.analytics_service.get_all_progress(request.user, slug, status_filter)
            return Response({
                'count': len(result),
                'results': result
            })
        except NotFoundError as e:
            raise NotFound(str(e))

    @extend_schema(
        tags=['Process Analytics'],
        summary='Get progress details',
        description='Get detailed information about a specific progress record.',
        parameters=[
            OpenApiParameter(
                name='slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Process unique slug',
                required=True
            ),
            OpenApiParameter(
                name='progress_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Progress record UUID',
                required=True
            )
        ],
        operation_id='processes_progress_retrieve',
        responses={200: {'type': 'object', 'description': 'Progress details'}}
    )
    @action(detail=True, methods=['get'], url_path='progress/(?P<progress_id>[^/.]+)')
    def get_progress(self, request, slug=None, progress_id=None):
        """
        Get specific progress details
        GET /api/v1/processes/{slug}/progress/{id}/
        """
        try:
            result = self.analytics_service.get_progress_details(request.user, slug, progress_id)
            return Response(result)
        except NotFoundError as e:
            raise NotFound(str(e))

    @extend_schema(
        tags=['Process Analytics'],
        summary='List abandoned progress',
        description='List all abandoned (incomplete) progress records for a process.',
        parameters=[
            OpenApiParameter(
                name='slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Process unique slug',
                required=True
            )
        ],
        operation_id='processes_progress_abandoned',
        responses={200: {'type': 'object', 'properties': {'count': {'type': 'integer'}, 'results': {'type': 'array'}}}}
    )
    @action(detail=True, methods=['get'], url_path='progress/abandoned')
    def list_abandoned(self, request, slug=None):
        """
        List abandoned progress records
        GET /api/v1/processes/{slug}/progress/abandoned/
        """
        try:
            result = self.analytics_service.get_abandoned_progress(request.user, slug)
            return Response({
                'count': len(result),
                'results': result
            })
        except NotFoundError as e:
            raise NotFound(str(e))

