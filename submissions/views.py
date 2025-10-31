from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from submissions.models import FormSubmission
from forms.models import Form
from analytics.models import FormView  # Assuming you have this model

from .serializers import (
    FormPublicSerializer,
    FormPasswordVerifySerializer,
    FormSubmissionSerializer,
    FormSubmissionReadSerializer
)


class PublicFormViewSet(viewsets.GenericViewSet):
    """
    Public API for viewing and submitting forms
    No authentication required!

    Endpoints:
    - GET    /api/v1/public/forms/{slug}/
    - POST   /api/v1/public/forms/{slug}/verify-password/
    - POST   /api/v1/public/forms/{slug}/view/
    - POST   /api/v1/public/forms/{slug}/submit/
    - POST   /api/v1/public/forms/{slug}/submissions/draft/
    - GET    /api/v1/public/forms/{slug}/submissions/draft/{session_id}/
    - PATCH  /api/v1/public/forms/{slug}/submissions/draft/{session_id}/
    """
    permission_classes = [AllowAny]  # Public access!
    lookup_field = 'unique_slug'
    lookup_url_kwarg = 'slug'

    def get_queryset(self):
        """Get active forms only"""
        return Form.objects.filter(is_active=True).prefetch_related('fields__options')

    def retrieve(self, request, slug=None):
        """
        Get public form structure
        GET /api/v1/public/forms/{slug}/

        Returns form fields and structure for display
        Private forms require password verification first
        """
        form = get_object_or_404(self.get_queryset(), unique_slug=slug)

        # Check if password protected
        if form.visibility == 'private':
            # Check if password was verified in this session
            session_key = f'form_access_{form.id}'
            if not request.session.get(session_key):
                return Response({
                    'error': 'Password required',
                    'message': 'This form is password protected',
                    'requires_password': True
                }, status=status.HTTP_403_FORBIDDEN)

        serializer = FormPublicSerializer(form)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='verify-password')
    def verify_password(self, request, slug=None):
        """
        Verify password for private form
        POST /api/v1/public/forms/{slug}/verify-password/

        Body: {"password": "secret"}
        """
        form = get_object_or_404(self.get_queryset(), unique_slug=slug)

        if form.visibility != 'private':
            return Response({
                'error': 'This form is not password protected'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = FormPasswordVerifySerializer(
            data=request.data,
            context={'form': form}
        )
        serializer.is_valid(raise_exception=True)

        # Store access in session
        session_key = f'form_access_{form.id}'
        request.session[session_key] = True
        request.session.set_expiry(3600)  # 1 hour

        return Response({
            'message': 'Password verified successfully',
            'access_granted': True
        })

    @action(detail=True, methods=['post'], url_path='view')
    def track_view(self, request, slug=None):
        """
        Track form view (analytics)
        POST /api/v1/public/forms/{slug}/view/

        Body: {
            "session_id": "optional-session-id",
            "metadata": {"user_agent": "...", "referer": "..."}
        }
        """
        form = get_object_or_404(self.get_queryset(), unique_slug=slug)

        # Extract metadata
        session_id = request.data.get('session_id', request.session.session_key)
        metadata = request.data.get('metadata', {})

        # Add request metadata
        metadata.update({
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referer': request.META.get('HTTP_REFERER', ''),
        })

        # Create view record
        # NOTE: You need to create FormView model in analytics app
        # Or skip this if you don't have analytics yet
        try:
            from analytics.models import FormView
            FormView.objects.create(
                form=form,
                session_id=session_id or 'anonymous',
                ip_address=request.META.get('REMOTE_ADDR'),
                metadata=metadata
            )
        except ImportError:
            # Analytics app not ready yet, skip
            pass

        return Response({
            'message': 'View tracked successfully'
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit_form(self, request, slug=None):
        """
        Submit form response (final submission)
        POST /api/v1/public/forms/{slug}/submit/

        Body: {
            "session_id": "optional-uuid",
            "answers": [
                {
                    "field_id": "uuid",
                    "text_value": "answer"
                }
            ],
            "metadata": {}
        }
        """
        form = get_object_or_404(self.get_queryset(), unique_slug=slug)

        # Check password for private forms
        if form.visibility == 'private':
            session_key = f'form_access_{form.id}'
            if not request.session.get(session_key):
                return Response({
                    'error': 'Password verification required'
                }, status=status.HTTP_403_FORBIDDEN)

        # Prepare data
        data = request.data.copy()
        data['form_slug'] = slug
        data['status'] = 'submitted'  # Force status to submitted

        serializer = FormSubmissionSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()

        try:
            channel_layer = get_channel_layer()
            group_name = f'form_report_{slug}'
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "report.update",
                    "message": {
                        "status": "new_submission_received",
                        "submission_id": str(submission.id),
                        "submitted_at": submission.submitted_at.isoformat()
                    }
                }
            )
        except Exception as e:
            print(f"Error sending WebSocket signal: {e}") 

        return Response({
            'message': 'Form submitted successfully',
            'submission_id': submission.id,
            'session_id': submission.session_id
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='submissions/draft')
    def save_draft(self, request, slug=None):
        """
        Save draft submission
        POST /api/v1/public/forms/{slug}/submissions/draft/

        Body: {
            "session_id": "optional-uuid",
            "answers": [...],
            "metadata": {}
        }
        """
        form = get_object_or_404(self.get_queryset(), unique_slug=slug)

        # Prepare data
        data = request.data.copy()
        data['form_slug'] = slug
        data['status'] = 'draft'  # Force status to draft

        serializer = FormSubmissionSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()

        return Response({
            'message': 'Draft saved successfully',
            'submission_id': submission.id,
            'session_id': submission.session_id
        }, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['get'],
        url_path='submissions/draft/(?P<session_id>[^/.]+)'
    )
    def get_draft(self, request, slug=None, session_id=None):
        """
        Get draft submission
        GET /api/v1/public/forms/{slug}/submissions/draft/{session_id}/
        """
        form = get_object_or_404(self.get_queryset(), unique_slug=slug)

        submission = get_object_or_404(
            FormSubmission,
            form=form,
            session_id=session_id,
            status='draft'
        )

        serializer = FormSubmissionReadSerializer(submission)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['patch'],
        url_path='submissions/draft/(?P<session_id>[^/.]+)'
    )
    def update_draft(self, request, slug=None, session_id=None):
        """
        Update draft submission
        PATCH /api/v1/public/forms/{slug}/submissions/draft/{session_id}/

        Body: {
            "answers": [...],
            "metadata": {}
        }
        """
        form = get_object_or_404(self.get_queryset(), unique_slug=slug)

        submission = get_object_or_404(
            FormSubmission,
            form=form,
            session_id=session_id,
            status='draft'
        )

        data = request.data.copy()
        data['form_slug'] = slug
        data['status'] = 'draft'

        serializer = FormSubmissionSerializer(
            submission,
            data=data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Draft updated successfully',
            'submission_id': submission.id
        })