from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg, Q, F
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.utils import timezone
import csv
import json
from datetime import timedelta

from submissions.models import FormSubmission, SubmissionAnswer
from forms.models import Form

from .serializers import (
    FormSubmissionReadSerializer,
    FormSubmissionDetailSerializer,
    SubmissionStatsSerializer,
    BulkDeleteSerializer,
    ExportSerializer
)


@extend_schema_view(
    list=extend_schema(
        tags=['Submissions'],
        summary='List form submissions',
        description='List all submissions for a form. Supports filtering by status, date range, and search.',
        parameters=[
            OpenApiParameter(
                name='status',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Filter by status',
                required=False,
                enum=['submitted', 'draft', 'archived']
            ),
            OpenApiParameter(
                name='date_from',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Filter from date (YYYY-MM-DD)',
                required=False
            ),
            OpenApiParameter(
                name='date_to',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Filter to date (YYYY-MM-DD)',
                required=False
            ),
            OpenApiParameter(
                name='search',
                type=str,
                location=OpenApiParameter.QUERY,
                description='Search in email or session_id',
                required=False
            ),
        ],
        responses={200: FormSubmissionReadSerializer(many=True)}
    ),
    retrieve=extend_schema(
        tags=['Submissions'],
        summary='Get submission details',
        description='Get detailed information about a specific submission including all answers.',
        responses={200: FormSubmissionDetailSerializer}
    ),
    destroy=extend_schema(
        tags=['Submissions'],
        summary='Delete submission',
        description='Delete a form submission.',
        responses={204: None}
    )
)
class SubmissionManagementViewSet(viewsets.GenericViewSet):
    """
    ViewSet for form owner to manage submissions
    Requires authentication and form ownership

    Endpoints:
    - GET    /api/v1/forms/{slug}/submissions/
    - GET    /api/v1/forms/{slug}/submissions/{id}/
    - DELETE /api/v1/forms/{slug}/submissions/{id}/
    - POST   /api/v1/forms/{slug}/submissions/export/
    - GET    /api/v1/forms/{slug}/submissions/stats/
    - POST   /api/v1/forms/{slug}/submissions/bulk-delete/
    - POST   /api/v1/forms/{slug}/submissions/bulk-export/
    """
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    serializer_class = FormSubmissionReadSerializer  # Default serializer for schema generation

    def get_queryset(self):
        """Get submissions for user's form"""
        form = self.get_form()
        return FormSubmission.objects.filter(form=form).prefetch_related(
            'answers__field', 'user'
        ).order_by('-created_at')

    def get_form(self):
        """Get form from URL - must belong to current user"""
        form_slug = self.kwargs.get('slug')
        return get_object_or_404(
            Form,
            unique_slug=form_slug,
            user=self.request.user  # Only owner's forms
        )

    def list(self, request, slug=None):
        """
        List all submissions for a form
        GET /api/v1/forms/{slug}/submissions/

        Query params:
        - status: filter by status (submitted/draft/archived)
        - date_from: filter submissions from date
        - date_to: filter submissions to date
        - search: search in user email or session_id
        - page: pagination
        - page_size: items per page
        """
        queryset = self.get_queryset()

        # Filters
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        date_from = request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(submitted_at__gte=date_from)

        date_to = request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(submitted_at__lte=date_to)

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search) |
                Q(session_id__icontains=search)
            )

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size

        submissions = queryset[start:end]
        serializer = FormSubmissionReadSerializer(submissions, many=True)

        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
            'results': serializer.data
        })

    def retrieve(self, request, slug=None, id=None):
        """
        Get detailed submission
        GET /api/v1/forms/{slug}/submissions/{id}/
        """
        submission = get_object_or_404(
            self.get_queryset(),
            id=id
        )

        serializer = FormSubmissionDetailSerializer(submission)
        return Response(serializer.data)

    def destroy(self, request, slug=None, id=None):
        """
        Delete a submission
        DELETE /api/v1/forms/{slug}/submissions/{id}/
        """
        submission = get_object_or_404(
            self.get_queryset(),
            id=id
        )

        submission.delete()

        return Response({
            'message': 'Submission deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='stats')
    def statistics(self, request, slug=None):
        """
        Get submission statistics
        GET /api/v1/forms/{slug}/submissions/stats/

        Returns:
        - Total submissions
        - Count by status
        - Unique users
        - Average completion time
        - Submissions by date (last 30 days)
        """
        form = self.get_form()
        queryset = FormSubmission.objects.filter(form=form)

        # Basic counts
        total = queryset.count()
        by_status = queryset.values('status').annotate(count=Count('id'))

        status_counts = {
            'submitted': 0,
            'draft': 0,
            'archived': 0
        }
        for item in by_status:
            status_counts[item['status']] = item['count']

        # Unique users
        unique_users = queryset.filter(user__isnull=False).values('user').distinct().count()
        anonymous = queryset.filter(user__isnull=True).count()

        # Average completion time (draft created_at to submitted_at)
        avg_time = None
        completed = queryset.filter(
            status='submitted',
            submitted_at__isnull=False
        )

        if completed.exists():
            times = []
            for sub in completed:
                if sub.submitted_at and sub.created_at:
                    delta = (sub.submitted_at - sub.created_at).total_seconds()
                    times.append(delta)

            if times:
                avg_time = sum(times) / len(times) / 60  # in minutes

        # First and last submission
        first = queryset.order_by('created_at').first()
        last = queryset.order_by('-created_at').first()

        # Submissions by date (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        by_date = queryset.filter(
            created_at__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        submissions_by_date = {
            str(item['date']): item['count'] for item in by_date
        }

        data = {
            'total_submissions': total,
            'submitted_count': status_counts['submitted'],
            'draft_count': status_counts['draft'],
            'archived_count': status_counts['archived'],
            'unique_users': unique_users,
            'anonymous_count': anonymous,
            'average_completion_time': avg_time,
            'first_submission': first.created_at if first else None,
            'last_submission': last.created_at if last else None,
            'submissions_by_date': submissions_by_date
        }

        serializer = SubmissionStatsSerializer(data)
        return Response(serializer.data)

    @extend_schema(
        tags=['Submissions'],
        summary='Export submissions',
        description='Export form submissions in CSV, JSON, or Excel format. Supports filtering.',
        request=ExportSerializer,
        responses={
            200: {'description': 'File download', 'content': {'application/json': {}, 'text/csv': {}, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': {}}}
        }
    )
    @action(detail=False, methods=['post'], url_path='export')
    def export_submissions(self, request, slug=None):
        """
        Export submissions
        POST /api/v1/forms/{slug}/submissions/export/

        Body: {
            "format": "csv|json|excel",
            "include_drafts": false,
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
            "status": "submitted|draft|all"
        }
        """
        form = self.get_form()

        serializer = ExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        export_format = serializer.validated_data['format']
        include_drafts = serializer.validated_data['include_drafts']
        date_from = serializer.validated_data.get('date_from')
        date_to = serializer.validated_data.get('date_to')
        status_filter = serializer.validated_data['status']

        # Build queryset
        queryset = FormSubmission.objects.filter(form=form)

        if status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
        elif not include_drafts:
            queryset = queryset.filter(status='submitted')

        if date_from:
            queryset = queryset.filter(submitted_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(submitted_at__lte=date_to)

        queryset = queryset.prefetch_related('answers__field').order_by('created_at')

        # Export based on format
        if export_format == 'csv':
            return self._export_csv(form, queryset)
        elif export_format == 'json':
            return self._export_json(form, queryset)
        elif export_format == 'excel':
            return self._export_excel(form, queryset)

    def _export_csv(self, form, submissions):
        """Export to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{form.unique_slug}_submissions.csv"'

        writer = csv.writer(response)

        # Get all fields
        fields = form.fields.all().order_by('order_index')

        # Header row
        header = ['Submission ID', 'User', 'Status', 'Submitted At']
        header.extend([f.label for f in fields])
        writer.writerow(header)

        # Data rows
        for sub in submissions:
            row = [
                str(sub.id),
                sub.user.email if sub.user else 'Anonymous',
                sub.status,
                sub.submitted_at.isoformat() if sub.submitted_at else ''
            ]

            # Get answers for this submission
            answers_dict = {
                ans.field_id: self._get_answer_value(ans)
                for ans in sub.answers.all()
            }

            # Add answer for each field (in order)
            for field in fields:
                row.append(answers_dict.get(field.id, ''))

            writer.writerow(row)

        return response

    def _export_json(self, form, submissions):
        """Export to JSON"""
        data = []

        for sub in submissions:
            answers = {}
            for ans in sub.answers.all():
                answers[ans.field.label] = self._get_answer_value(ans)

            data.append({
                'id': str(sub.id),
                'user': sub.user.email if sub.user else 'Anonymous',
                'status': sub.status,
                'submitted_at': sub.submitted_at.isoformat() if sub.submitted_at else None,
                'answers': answers,
                'metadata': sub.metadata
            })

        response = HttpResponse(
            json.dumps(data, indent=2, ensure_ascii=False),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{form.unique_slug}_submissions.json"'

        return response

    def _export_excel(self, form, submissions):
        """Export to Excel - requires openpyxl"""
        try:
            from openpyxl import Workbook
            from openpyxl.utils import get_column_letter
        except ImportError:
            return Response({
                'error': 'Excel export requires openpyxl package'
            }, status=status.HTTP_400_BAD_REQUEST)

        wb = Workbook()
        ws = wb.active
        ws.title = "Submissions"

        # Get all fields
        fields = form.fields.all().order_by('order_index')

        # Header row
        headers = ['Submission ID', 'User', 'Status', 'Submitted At']
        headers.extend([f.label for f in fields])
        ws.append(headers)

        # Data rows
        for sub in submissions:
            row = [
                str(sub.id),
                sub.user.email if sub.user else 'Anonymous',
                sub.status,
                sub.submitted_at.isoformat() if sub.submitted_at else ''
            ]

            answers_dict = {
                ans.field_id: self._get_answer_value(ans)
                for ans in sub.answers.all()
            }

            for field in fields:
                row.append(answers_dict.get(field.id, ''))

            ws.append(row)

        # Save to response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{form.unique_slug}_submissions.xlsx"'
        wb.save(response)

        return response

    def _get_answer_value(self, answer):
        """Extract appropriate value from answer based on field type"""
        if answer.text_value:
            return answer.text_value
        elif answer.numeric_value is not None:
            return str(answer.numeric_value)
        elif answer.boolean_value is not None:
            return 'Yes' if answer.boolean_value else 'No'
        elif answer.date_value:
            return answer.date_value.isoformat()
        elif answer.array_value:
            return ', '.join(answer.array_value) if isinstance(answer.array_value, list) else str(answer.array_value)
        elif answer.file_url:
            return answer.file_url
        return ''

    @extend_schema(
        tags=['Submissions'],
        summary='Bulk delete submissions',
        description='Delete multiple submissions at once. Maximum 100 submissions per request.',
        request=BulkDeleteSerializer,
        responses={
            200: {'type': 'object', 'properties': {
                'deleted_count': {'type': 'integer'},
                'failed_count': {'type': 'integer'}
            }}
        }
    )
    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request, slug=None):
        """
        Delete multiple submissions at once
        POST /api/v1/forms/{slug}/submissions/bulk-delete/

        Body: {
            "submission_ids": ["uuid1", "uuid2", "uuid3"]
        }
        """
        form = self.get_form()

        serializer = BulkDeleteSerializer(
            data=request.data,
            context={'form': form}
        )
        serializer.is_valid(raise_exception=True)

        submission_ids = serializer.validated_data['submission_ids']

        # Delete
        deleted_count = FormSubmission.objects.filter(
            id__in=submission_ids,
            form=form
        ).delete()[0]

        return Response({
            'message': f'{deleted_count} submissions deleted successfully',
            'deleted_count': deleted_count
        })

    @extend_schema(
        tags=['Submissions'],
        summary='Bulk export submissions',
        description='Export specific submissions by IDs. Maximum 1000 submissions per request.',
        request=ExportSerializer,
        responses={
            200: {'description': 'File download', 'content': {'application/json': {}, 'text/csv': {}, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': {}}}
        }
    )
    @action(detail=False, methods=['post'], url_path='bulk-export')
    def bulk_export(self, request, slug=None):
        """
        Export specific submissions
        POST /api/v1/forms/{slug}/submissions/bulk-export/

        Body: {
            "submission_ids": ["uuid1", "uuid2"],
            "format": "csv|json|excel"
        }
        """
        form = self.get_form()

        submission_ids = request.data.get('submission_ids', [])
        export_format = request.data.get('format', 'csv')

        if not submission_ids:
            return Response({
                'error': 'submission_ids is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get submissions
        queryset = FormSubmission.objects.filter(
            id__in=submission_ids,
            form=form
        ).prefetch_related('answers__field').order_by('created_at')

        # Export
        if export_format == 'csv':
            return self._export_csv(form, queryset)
        elif export_format == 'json':
            return self._export_json(form, queryset)
        elif export_format == 'excel':
            return self._export_excel(form, queryset)

        return Response({
            'error': 'Invalid format'
        }, status=status.HTTP_400_BAD_REQUEST)