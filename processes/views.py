from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, ValidationError as DRFValidationError
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from django.db.models import Count

from .serializers import (
    ProcessSerializer,
    ProcessListSerializer,
    ProcessStepSerializer,
    ProcessStepListSerializer,
    ProcessStepReorderSerializer
)
from .models import Process
from .permissions import IsProcessOwner, IsProcessStepOwner
from .services import ProcessService, ProcessStepService
from shared.exceptions import NotFoundError, ValidationError as CustomValidationError


@extend_schema_view(
    list=extend_schema(
        tags=['Processes'],
        summary='List process steps',
        description='List all steps in a process.',
        responses={200: ProcessStepListSerializer(many=True)}
    ),
    create=extend_schema(
        tags=['Processes'],
        summary='Create process step',
        description='Add a new step to a process.',
        request=ProcessStepSerializer,
        responses={201: ProcessStepSerializer}
    ),
    retrieve=extend_schema(
        tags=['Processes'],
        summary='Get process step',
        description='Get details of a specific process step.',
        responses={200: ProcessStepSerializer}
    ),
    update=extend_schema(
        tags=['Processes'],
        summary='Update process step',
        description='Update a process step.',
        request=ProcessStepSerializer,
        responses={200: ProcessStepSerializer}
    ),
    partial_update=extend_schema(
        tags=['Processes'],
        summary='Partially update process step',
        description='Partially update a process step.',
        request=ProcessStepSerializer,
        responses={200: ProcessStepSerializer}
    ),
    destroy=extend_schema(
        tags=['Processes'],
        summary='Delete process step',
        description='Delete a process step.',
        responses={204: None}
    )
)
class ProcessStepViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing process steps

    Endpoints:
    - GET    /api/v1/processes/{slug}/steps/
    - POST   /api/v1/processes/{slug}/steps/
    - GET    /api/v1/processes/{slug}/steps/{id}/
    - PATCH  /api/v1/processes/{slug}/steps/{id}/
    - DELETE /api/v1/processes/{slug}/steps/{id}/
    - POST   /api/v1/processes/{slug}/steps/reorder/
    """
    permission_classes = [IsAuthenticated, IsProcessStepOwner]
    lookup_field = 'id'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.step_service = ProcessStepService()

    def get_serializer_class(self):
        """Select serializer based on action"""
        if self.action == 'list':
            return ProcessStepListSerializer
        elif self.action == 'reorder':
            return ProcessStepReorderSerializer
        return ProcessStepSerializer

    def get_process_slug(self):
        """Get process slug from URL"""
        return self.kwargs.get('process_slug')

    def list(self, request, *args, **kwargs):
        """
        List all steps in a process
        GET /api/v1/processes/{slug}/steps/
        """
        try:
            process_slug = self.get_process_slug()
            steps = self.step_service.get_process_steps(request.user, process_slug)
            
            serializer = self.get_serializer(steps, many=True)
            
            return Response({
                'count': steps.count(),
                'results': serializer.data
            })
        except NotFoundError as e:
            raise NotFound(str(e))

    def create(self, request, *args, **kwargs):
        """
        Create new step
        POST /api/v1/processes/{slug}/steps/
        """
        try:
            process_slug = self.get_process_slug()
            data = request.data.copy()
            
            step = self.step_service.create_step(
                user=request.user,
                process_slug=process_slug,
                form_id=data.get('form'),
                title=data.get('title'),
                description=data.get('description'),
                order_index=data.get('order_index'),
                is_required=data.get('is_required', True),
                conditions=data.get('conditions', {})
            )
            
            serializer = self.get_serializer(step)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except NotFoundError as e:
            raise NotFound(str(e))
        except CustomValidationError as e:
            raise DRFValidationError(str(e))

    def retrieve(self, request, *args, **kwargs):
        """
        Get step details
        GET /api/v1/processes/{slug}/steps/{id}/
        """
        try:
            process_slug = self.get_process_slug()
            step_id = kwargs.get('id')
            step = self.step_service.get_step(request.user, process_slug, step_id)
            
            serializer = ProcessStepSerializer(step)
            return Response(serializer.data)
        except NotFoundError as e:
            raise NotFound(str(e))

    def update(self, request, *args, **kwargs):
        """
        Update step
        PATCH /api/v1/processes/{slug}/steps/{id}/
        """
        try:
            process_slug = self.get_process_slug()
            step_id = kwargs.get('id')
            
            # Prepare update data
            update_data = {}
            if 'title' in request.data:
                update_data['title'] = request.data['title']
            if 'description' in request.data:
                update_data['description'] = request.data['description']
            if 'order_index' in request.data:
                update_data['order_index'] = request.data['order_index']
            if 'is_required' in request.data:
                update_data['is_required'] = request.data['is_required']
            if 'conditions' in request.data:
                update_data['conditions'] = request.data['conditions']
            if 'form' in request.data:
                update_data['form_id'] = request.data['form']
            
            step = self.step_service.update_step(
                request.user,
                process_slug,
                step_id,
                **update_data
            )
            
            serializer = self.get_serializer(step)
            return Response(serializer.data)
        except NotFoundError as e:
            raise NotFound(str(e))
        except CustomValidationError as e:
            raise DRFValidationError(str(e))

    def destroy(self, request, *args, **kwargs):
        """
        Delete step
        DELETE /api/v1/processes/{slug}/steps/{id}/
        """
        try:
            process_slug = self.get_process_slug()
            step_id = kwargs.get('id')
            
            self.step_service.delete_step(request.user, process_slug, step_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except NotFoundError as e:
            raise NotFound(str(e))

    @extend_schema(
        tags=['Processes'],
        summary='Reorder process steps',
        description='Reorder steps within a process by providing new order_index values.',
        request=ProcessStepReorderSerializer,
        responses={
            200: {'type': 'object', 'properties': {
                'message': {'type': 'string'},
                'updated_count': {'type': 'integer'}
            }}
        }
    )
    @action(detail=False, methods=['post'], url_path='reorder')
    def reorder(self, request, *args, **kwargs):
        """
        Reorder steps in bulk
        POST /api/v1/processes/{slug}/steps/reorder/
        Body: {"step_ids": [uuid1, uuid2, ...]}
        """
        try:
            process_slug = self.get_process_slug()
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            step_ids = serializer.validated_data['step_ids']
            
            result = self.step_service.reorder_steps(
                request.user,
                process_slug,
                step_ids
            )
            
            return Response({
                'message': f'Successfully reordered {result["updated_count"]} steps',
                'step_ids': result['step_ids']
            })
        except NotFoundError as e:
            raise NotFound(str(e))
        except CustomValidationError as e:
            raise DRFValidationError(str(e))


@extend_schema_view(
    list=extend_schema(
        tags=['Processes'],
        summary='List processes',
        description='List all processes for the authenticated user.',
        responses={200: ProcessListSerializer(many=True)}
    ),
    create=extend_schema(
        tags=['Processes'],
        summary='Create process',
        description='Create a new process workflow.',
        request=ProcessSerializer,
        responses={201: ProcessSerializer}
    ),
    retrieve=extend_schema(
        tags=['Processes'],
        summary='Get process details',
        description='Get detailed information about a process including all steps.',
        parameters=[
            OpenApiParameter(
                name='unique_slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Process unique slug',
                required=True
            )
        ],
        responses={200: ProcessSerializer}
    ),
    update=extend_schema(
        tags=['Processes'],
        summary='Update process',
        description='Update a process. All fields are required.',
        parameters=[
            OpenApiParameter(
                name='unique_slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Process unique slug',
                required=True
            )
        ],
        request=ProcessSerializer,
        responses={200: ProcessSerializer}
    ),
    partial_update=extend_schema(
        tags=['Processes'],
        summary='Partially update process',
        description='Partially update a process. Only provided fields will be updated.',
        parameters=[
            OpenApiParameter(
                name='unique_slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Process unique slug',
                required=True
            )
        ],
        request=ProcessSerializer,
        responses={200: ProcessSerializer}
    ),
    destroy=extend_schema(
        tags=['Processes'],
        summary='Delete process',
        description='Delete a process. This will also delete all steps and progress records.',
        parameters=[
            OpenApiParameter(
                name='unique_slug',
                type=str,
                location=OpenApiParameter.PATH,
                description='Process unique slug',
                required=True
            )
        ],
        responses={204: None}
    )
)
class ProcessViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Processes (Create, List, Retrieve, Update, Delete)

    Endpoints:
    - GET    /api/v1/processes/
    - POST   /api/v1/processes/
    - GET    /api/v1/processes/{unique_slug}/
    - PATCH  /api/v1/processes/{unique_slug}/
    - DELETE /api/v1/processes/{unique_slug}/
    - POST   /api/v1/processes/{unique_slug}/duplicate/
    - PATCH  /api/v1/processes/{unique_slug}/publish/
    """
    permission_classes = [IsAuthenticated, IsProcessOwner]
    lookup_field = 'unique_slug'
    lookup_url_kwarg = 'unique_slug'
    queryset = Process.objects.none()  # For schema generation only, actual queryset from get_queryset()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process_service = ProcessService()

    def get_queryset(self):
        """
        Get all processes owned by the current user.
        Annotate with steps count for list view.
        """
        if self.action == 'list':
            return self.process_service.get_user_processes(self.request.user, prefetch_steps=False)
        elif self.action == 'retrieve':
            return self.process_service.get_user_processes(self.request.user, prefetch_steps=True)
        return self.process_service.get_user_processes(self.request.user)

    def get_serializer_class(self):
        """
        Return different serializers for list and detail actions.
        """
        if self.action == 'list':
            return ProcessListSerializer
        return ProcessSerializer

    def list(self, request, *args, **kwargs):
        """
        List all processes for the user
        GET /api/v1/processes/
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """
        Create new process
        POST /api/v1/processes/
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            process = self.process_service.create_process(
                user=request.user,
                title=serializer.validated_data['title'],
                description=serializer.validated_data.get('description'),
                category_id=str(serializer.validated_data['category'].id) if serializer.validated_data.get('category') else None,
                unique_slug=serializer.validated_data.get('unique_slug'),
                visibility=serializer.validated_data.get('visibility', 'public'),
                access_password=serializer.validated_data.get('access_password'),
                process_type=serializer.validated_data.get('process_type', 'linear'),
                is_active=serializer.validated_data.get('is_active', True),
                settings=serializer.validated_data.get('settings', {})
            )
            
            response_serializer = ProcessSerializer(process)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except CustomValidationError as e:
            raise DRFValidationError(str(e))

    def retrieve(self, request, *args, **kwargs):
        """
        Get process details
        GET /api/v1/processes/{slug}/
        """
        try:
            slug = kwargs.get('unique_slug')
            process = self.process_service.get_process(request.user, slug)
            
            serializer = self.get_serializer(process)
            return Response(serializer.data)
        except NotFoundError as e:
            raise NotFound(str(e))

    def update(self, request, *args, **kwargs):
        """
        Update process
        PATCH /api/v1/processes/{slug}/
        """
        try:
            slug = kwargs.get('unique_slug')
            
            # Prepare update data
            update_data = {}
            if 'title' in request.data:
                update_data['title'] = request.data['title']
            if 'description' in request.data:
                update_data['description'] = request.data['description']
            if 'category' in request.data:
                update_data['category_id'] = str(request.data['category']) if request.data['category'] else None
            if 'unique_slug' in request.data:
                update_data['unique_slug'] = request.data['unique_slug']
            if 'visibility' in request.data:
                update_data['visibility'] = request.data['visibility']
            if 'access_password' in request.data:
                update_data['access_password'] = request.data['access_password']
            if 'process_type' in request.data:
                update_data['process_type'] = request.data['process_type']
            if 'is_active' in request.data:
                update_data['is_active'] = request.data['is_active']
            if 'settings' in request.data:
                update_data['settings'] = request.data['settings']
            
            process = self.process_service.update_process(
                request.user,
                slug,
                **update_data
            )
            
            serializer = self.get_serializer(process)
            return Response(serializer.data)
        except NotFoundError as e:
            raise NotFound(str(e))
        except CustomValidationError as e:
            raise DRFValidationError(str(e))

    def destroy(self, request, *args, **kwargs):
        """
        Delete process
        DELETE /api/v1/processes/{slug}/
        """
        try:
            slug = kwargs.get('unique_slug')
            self.process_service.delete_process(request.user, slug)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except NotFoundError as e:
            raise NotFound(str(e))

    @action(detail=True, methods=['post'], url_path='duplicate')
    def duplicate(self, request, unique_slug=None):
        """
        Duplicate a process with all its steps
        POST /api/v1/processes/{slug}/duplicate/
        """
        try:
            new_process = self.process_service.duplicate_process(request.user, unique_slug)
            serializer = self.get_serializer(new_process)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except NotFoundError as e:
            raise NotFound(str(e))
        except CustomValidationError as e:
            raise DRFValidationError(str(e))

    @action(detail=True, methods=['patch'], url_path='publish')
    def publish(self, request, unique_slug=None):
        """
        Publish or unpublish a process
        PATCH /api/v1/processes/{slug}/publish/
        Body: {"is_published": true/false}
        """
        try:
            is_published = request.data.get('is_published', True)
            process = self.process_service.publish_process(request.user, unique_slug, is_published)
            
            serializer = self.get_serializer(process)
            return Response(serializer.data)
        except NotFoundError as e:
            raise NotFound(str(e))
