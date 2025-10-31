from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import serializers

class GoogleOAuthRequestSerializer(serializers.Serializer):
    """Serializer for Google OAuth login request"""
    access_token = serializers.CharField(
        required=True,
        help_text="Google OAuth access token"
    )

class GoogleOAuthResponseSerializer(serializers.Serializer):
    """Serializer for Google OAuth login response"""
    access = serializers.CharField(help_text="JWT access token")
    refresh = serializers.CharField(help_text="JWT refresh token")
    user = serializers.DictField(help_text="User profile information")

@extend_schema(
    tags=['Authentication'],
    summary='Google OAuth login',
    description='Authenticate using Google OAuth. Requires a Google OAuth access token.',
    request=GoogleOAuthRequestSerializer,
    responses={
        200: GoogleOAuthResponseSerializer,
        400: {'description': 'Invalid access token or missing required fields'},
        401: {'description': 'Authentication failed'}
    }
)
class GoogleLoginView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.FRONTEND_URL
    client_class = OAuth2Client