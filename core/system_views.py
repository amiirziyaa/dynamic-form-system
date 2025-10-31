from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from django.db import connection
from django.conf import settings
import platform


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


