from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db import connection
from django.conf import settings
import platform
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework import serializers
from forms.models import Form
from processes.models import Process
from submissions.models import FormSubmission
from analytics.models import FormView
from forms.serializers import FormListSerializer
from processes.serializers import ProcessListSerializer


@extend_schema(
    tags=['System'],
    summary='Health check',
    description='Returns system health status including database connectivity. Used for monitoring and load balancer health checks.',
    responses={
        200: OpenApiResponse(
            response={
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'healthy', 'description': 'System status'},
                    'timestamp': {'type': 'string', 'format': 'date-time', 'description': 'Current timestamp'},
                    'database': {'type': 'string', 'example': 'connected', 'description': 'Database connection status'},
                    'version': {'type': 'string', 'example': '1.0.0', 'description': 'API version'}
                }
            },
            description='System is healthy'
        ),
        503: OpenApiResponse(
            response={
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'unhealthy'},
                    'timestamp': {'type': 'string', 'format': 'date-time'},
                    'database': {'type': 'string', 'example': 'disconnected'},
                    'error': {'type': 'string', 'description': 'Error message'}
                }
            },
            description='System is unhealthy'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint
    GET /api/v1/health/
    
    Returns system health status including database connectivity
    """
    health_status = {
        'status': 'healthy',
        'timestamp': None,
        'database': 'unknown',
        'version': getattr(settings, 'API_VERSION', '1.0.0')
    }
    
    from django.utils import timezone
    health_status['timestamp'] = timezone.now().isoformat()
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['database'] = 'connected'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['database'] = 'disconnected'
        health_status['error'] = str(e)
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    return Response(health_status, status=status.HTTP_200_OK)


@extend_schema(
    tags=['System'],
    summary='API version information',
    description='Returns API version information, deprecation status, and supported versions according to API specification.',
    responses={
        200: OpenApiResponse(
            response={
                'type': 'object',
                'properties': {
                    'version': {'type': 'string', 'example': '1.0.0', 'description': 'Current API version'},
                    'api_version': {'type': 'string', 'example': 'v1', 'description': 'API version identifier'},
                    'deprecated': {'type': 'boolean', 'example': False, 'description': 'Whether this version is deprecated'},
                    'sunset_date': {'type': 'string', 'format': 'date-time', 'nullable': True, 'description': 'Date when version will be sunset'},
                    'latest_version': {'type': 'string', 'example': 'v1', 'description': 'Latest available version'},
                    'supported_versions': {'type': 'array', 'items': {'type': 'string'}, 'example': ['v1'], 'description': 'List of supported versions'},
                    'changelog_url': {'type': 'string', 'format': 'uri', 'description': 'URL to changelog'},
                    'environment': {'type': 'string', 'example': 'development', 'description': 'Environment name'},
                    'python_version': {'type': 'string', 'description': 'Python version'},
                    'django_version': {'type': 'string', 'nullable': True, 'description': 'Django version'}
                }
            },
            description='Version information'
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def version_info(request):
    """
    API version information endpoint
    GET /api/v1/version/
    
    Returns version information according to API specification
    """
    from django.conf import settings
    
    version_data = {
        'version': getattr(settings, 'API_VERSION', '1.0.0'),
        'api_version': 'v1',
        'deprecated': False,
        'sunset_date': None,
        'latest_version': 'v1',
        'supported_versions': ['v1'],
        'changelog_url': getattr(settings, 'CHANGELOG_URL', None) or 'https://api.example.com/changelog',
        'environment': getattr(settings, 'ENVIRONMENT', 'development'),
        'python_version': platform.python_version(),
        'django_version': settings.VERSION if hasattr(settings, 'VERSION') else None
    }
    
    response = Response(version_data, status=status.HTTP_200_OK)
    
    if version_data['deprecated']:
        if version_data['sunset_date']:
            response['Sunset'] = version_data['sunset_date']
        response['Deprecation'] = 'true'
        response['Link'] = f'<https://api.example.com/{version_data["latest_version"]}/>; rel="successor-version"'
    
    return response


# ============================================
#
# DASHBOARD VIEWS
#
# ============================================

class DashboardStatsSerializer(serializers.Serializer):
    total_forms = serializers.IntegerField()
    total_processes = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    total_views = serializers.IntegerField()
    completion_rate = serializers.FloatField()

@extend_schema(
    tags=['Dashboard'],
    summary='Get dashboard overview statistics',
    description='Returns aggregated statistics for the authenticated user (form/process counts, submission analytics). This covers both /overview/ and /statistics/ endpoints.',
    responses={200: DashboardStatsSerializer}
)
class DashboardOverviewView(APIView):
    """
    GET /api/v1/dashboard/overview/
    GET /api/v1/dashboard/statistics/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        
        total_forms = Form.objects.filter(user=user).count()
        total_processes = Process.objects.filter(user=user).count()
        
        total_submissions = FormSubmission.objects.filter(form__user=user, status='submitted').count()
        total_views = FormView.objects.filter(form__user=user).count()
        
        completion_rate = 0.0
        if total_views > 0:
            completion_rate = (total_submissions / total_views) * 100
            
        data = {
            "total_forms": total_forms,
            "total_processes": total_processes,
            "total_submissions": total_submissions,
            "total_views": total_views,
            "completion_rate": round(completion_rate, 2)
        }
        
        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)


class RecentActivitySerializer(serializers.Serializer):
    type = serializers.CharField()
    title = serializers.CharField()
    unique_slug = serializers.SlugField()
    updated_at = serializers.DateTimeField()
    
    def to_representation(self, instance):
        if isinstance(instance, Form):
            return {
                'type': 'form',
                'title': instance.title,
                'unique_slug': instance.unique_slug,
                'updated_at': instance.updated_at
            }
        if isinstance(instance, Process):
            return {
                'type': 'process',
                'title': instance.title,
                'unique_slug': instance.unique_slug,
                'updated_at': instance.updated_at
            }
        return None

@extend_schema(
    tags=['Dashboard'],
    summary='Get recent activity',
    description='Returns a list of the 5 most recently updated forms and processes for the authenticated user.',
    responses={200: RecentActivitySerializer(many=True)}
)
class RecentActivityView(ListAPIView):
    """
    GET /api/v1/dashboard/recent-activity/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RecentActivitySerializer

    def get_queryset(self):
        user = self.request.user
        
        recent_forms = list(Form.objects.filter(user=user).order_by('-updated_at')[:5])
        recent_processes = list(Process.objects.filter(user=user).order_by('-updated_at')[:5])
        
        combined_list = sorted(
            recent_forms + recent_processes,
            key=lambda x: x.updated_at,
            reverse=True
        )
        
        return combined_list[:5]


# ============================================
#
# SEARCH VIEWS
#
# ============================================

class GlobalSearchSerializer(serializers.Serializer):
    """
    سریالایزر برای نتایج جستجوی کلی
    """
    forms = FormListSerializer(many=True)
    processes = ProcessListSerializer(many=True)

@extend_schema(
    tags=['Dashboard'],
    summary='Global search',
    description='Searches across all forms and processes for the authenticated user.',
    parameters=[
        OpenApiParameter(
            name='search', 
            type=OpenApiTypes.STR, 
            location=OpenApiParameter.QUERY,
            description='The search term to look for in titles, descriptions, and slugs.',
            required=True
        )
    ],
    responses={200: GlobalSearchSerializer}
)
class GlobalSearchView(APIView):
    """
    GET /api/v1/search/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('search', None)
        if not query:
            return Response({"error": "A 'search' query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        search_query = (
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(unique_slug__icontains=query)
        )
        
        forms = Form.objects.filter(user=user).filter(search_query)
        form_serializer = FormListSerializer(forms, many=True)
        
        processes = Process.objects.filter(user=user).filter(search_query)
        process_serializer = ProcessListSerializer(processes, many=True)
        
        data = {
            'forms': form_serializer.data,
            'processes': process_serializer.data
        }
        
        return Response(data)