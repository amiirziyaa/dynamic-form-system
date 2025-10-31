from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import NotFound, ValidationError as DRFValidationError

from processes.service_layers.process_execution_service import ProcessExecutionService
from shared.exceptions import NotFoundError, ValidationError as CustomValidationError


class PublicProcessViewSet(viewsets.GenericViewSet):
    """
    Public API for viewing and executing processes
    No authentication required!
    
    Endpoints:
    - GET    /api/v1/public/processes/{slug}/
    - POST   /api/v1/public/processes/{slug}/verify-password/
    - POST   /api/v1/public/processes/{slug}/start/
    - POST   /api/v1/public/processes/{slug}/view/
    - GET    /api/v1/public/processes/{slug}/progress/{session_id}/
    - GET    /api/v1/public/processes/{slug}/progress/{session_id}/current-step/
    - POST   /api/v1/public/processes/{slug}/progress/{session_id}/next/
    - POST   /api/v1/public/processes/{slug}/progress/{session_id}/previous/
    - GET    /api/v1/public/processes/{slug}/steps/{step_id}/form/
    - POST   /api/v1/public/processes/{slug}/steps/{step_id}/complete/
    - POST   /api/v1/public/processes/{slug}/complete/
    """
    permission_classes = [AllowAny]
    lookup_field = 'unique_slug'
    lookup_url_kwarg = 'slug'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.execution_service = ProcessExecutionService()

    def retrieve(self, request, slug=None):
        """
        Get public process structure
        GET /api/v1/public/processes/{slug}/
        
        Returns process structure for display.
        Private processes require password verification first.
        """
        try:
            session_key = f'process_access_{slug}'
            password_verified = request.session.get(session_key, False)
            
            result = self.execution_service.get_public_process(
                slug,
                check_password_required=not password_verified
            )
            
            return Response(result)
        except NotFoundError as e:
            raise NotFound(str(e))
        except CustomValidationError as e:
            raise DRFValidationError(str(e))

    @action(detail=True, methods=['post'], url_path='verify-password')
    def verify_password(self, request, slug=None):
        """
        Verify password for private process
        POST /api/v1/public/processes/{slug}/verify-password/
        
        Body: {"password": "secret"}
        """
        try:
            password = request.data.get('password')
            if not password:
                raise DRFValidationError("Password is required")
            
            is_valid = self.execution_service.verify_password(slug, password)
            
            if is_valid:
                session_key = f'process_access_{slug}'
                request.session[session_key] = True
                request.session.set_expiry(3600)
                
                return Response({
                    'message': 'Password verified successfully',
                    'access_granted': True
                })
            else:
                return Response({
                    'error': 'Invalid password',
                    'access_granted': False
                }, status=status.HTTP_401_UNAUTHORIZED)
        except NotFoundError as e:
            raise NotFound(str(e))
        except CustomValidationError as e:
            raise DRFValidationError(str(e))

    @action(detail=True, methods=['post'], url_path='view')
    def track_view(self, request, slug=None):
        """
        Track process view (analytics)
        POST /api/v1/public/processes/{slug}/view/
        """
        try:
            session_id = request.data.get('session_id') or self._get_session_id(request)
            ip_address = self._get_client_ip(request)
            metadata = {
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'referer': request.META.get('HTTP_REFERER', '')
            }
            
            view = self.execution_service.track_view(
                slug,
                session_id,
                ip_address=ip_address,
                metadata=metadata
            )
            
            return Response({
                'message': 'View tracked successfully',
                'view_id': str(view.id)
            }, status=status.HTTP_201_CREATED)
        except NotFoundError as e:
            raise NotFound(str(e))

    @action(detail=True, methods=['post'], url_path='start')
    def start(self, request, slug=None):
        """
        Start new process progress
        POST /api/v1/public/processes/{slug}/start/
        
        Body: {"session_id": "optional-session-id"}
        """
        try:
            session_id = request.data.get('session_id') or self._get_session_id(request)
            user = request.user if request.user.is_authenticated else None
            
            progress = self.execution_service.start_process(slug, session_id, user)
            
            return Response({
                'progress_id': str(progress.id),
                'session_id': progress.session_id,
                'status': progress.status,
                'current_step_index': progress.current_step_index,
                'completion_percentage': float(progress.completion_percentage),
                'started_at': progress.started_at.isoformat()
            }, status=status.HTTP_201_CREATED)
        except NotFoundError as e:
            raise NotFound(str(e))
        except CustomValidationError as e:
            raise DRFValidationError(str(e))

    @action(detail=True, methods=['get'], url_path='progress/(?P<session_id>[^/.]+)')
    def get_progress(self, request, slug=None, session_id=None):
        """
        Get user progress
        GET /api/v1/public/processes/{slug}/progress/{session_id}/
        """
        try:
            result = self.execution_service.get_progress(slug, session_id)
            return Response(result)
        except NotFoundError as e:
            raise NotFound(str(e))

    @action(detail=True, methods=['get'], url_path='progress/(?P<session_id>[^/.]+)/current-step')
    def get_current_step(self, request, slug=None, session_id=None):
        """
        Get current step
        GET /api/v1/public/processes/{slug}/progress/{session_id}/current-step/
        """
        try:
            result = self.execution_service.get_current_step(slug, session_id)
            return Response(result)
        except NotFoundError as e:
            raise NotFound(str(e))

    @action(detail=True, methods=['post'], url_path='progress/(?P<session_id>[^/.]+)/next')
    def move_next(self, request, slug=None, session_id=None):
        """
        Move to next step (linear processes only)
        POST /api/v1/public/processes/{slug}/progress/{session_id}/next/
        """
        try:
            result = self.execution_service.move_to_next_step(slug, session_id)
            return Response(result)
        except NotFoundError as e:
            raise NotFound(str(e))
        except CustomValidationError as e:
            raise DRFValidationError(str(e))

    @action(detail=True, methods=['post'], url_path='progress/(?P<session_id>[^/.]+)/previous')
    def move_previous(self, request, slug=None, session_id=None):
        """
        Go to previous step (linear processes only)
        POST /api/v1/public/processes/{slug}/progress/{session_id}/previous/
        """
        try:
            result = self.execution_service.move_to_previous_step(slug, session_id)
            return Response(result)
        except NotFoundError as e:
            raise NotFound(str(e))
        except CustomValidationError as e:
            raise DRFValidationError(str(e))

    @action(detail=True, methods=['get'], url_path='steps/(?P<step_id>[^/.]+)/form')
    def get_step_form(self, request, slug=None, step_id=None):
        """
        Get form for step
        GET /api/v1/public/processes/{slug}/steps/{step_id}/form/
        """
        try:
            result = self.execution_service.get_step_form(slug, step_id)
            return Response(result)
        except NotFoundError as e:
            raise NotFound(str(e))

    @action(detail=True, methods=['post'], url_path='steps/(?P<step_id>[^/.]+)/complete')
    def complete_step(self, request, slug=None, step_id=None):
        """
        Complete step with submission
        POST /api/v1/public/processes/{slug}/steps/{step_id}/complete/
        
        Body: {"submission_id": "optional-uuid", "session_id": "optional"}
        """
        try:
            session_id = request.data.get('session_id') or self._get_session_id(request)
            submission_id = request.data.get('submission_id')
            
            result = self.execution_service.complete_step(
                slug,
                step_id,
                session_id,
                submission_id=submission_id
            )
            return Response(result, status=status.HTTP_200_OK)
        except NotFoundError as e:
            raise NotFound(str(e))
        except CustomValidationError as e:
            raise DRFValidationError(str(e))

    @action(detail=True, methods=['post'], url_path='complete')
    def complete_process(self, request, slug=None):
        """
        Mark process as completed
        POST /api/v1/public/processes/{slug}/complete/
        
        Body: {"session_id": "required"}
        """
        try:
            session_id = request.data.get('session_id')
            if session_id is None or session_id == '':
                raise DRFValidationError("session_id is required")
            
            if not session_id:
                session_id = self._get_session_id(request)
            
            result = self.execution_service.complete_process(slug, session_id)
            return Response(result, status=status.HTTP_200_OK)
        except NotFoundError as e:
            raise NotFound(str(e))
        except CustomValidationError as e:
            raise DRFValidationError(str(e))

    def _get_session_id(self, request):
        """Get or generate session ID"""
        if not request.session.session_key:
            request.session.create()
        return request.session.session_key

    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

