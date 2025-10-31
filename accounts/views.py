from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    CustomTokenObtainPairSerializer,
    LoginSerializer,
    OTPSendSerializer,
    OTPVerifySerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSendSerializer,
    LogoutSerializer,
)
from .services import OTPService, EmailService, TokenService

# User model reference
User = get_user_model()


# Authentication Views

@extend_schema(
    tags=['Authentication'],
    summary='Register new user',
    description='Register a new user account with email and password. Returns JWT tokens upon successful registration.',
    request=UserCreateSerializer,
    responses={
        201: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string', 'example': 'User registered successfully'},
                'user': {'type': 'object'},
                'tokens': {
                    'type': 'object',
                    'properties': {
                        'refresh': {'type': 'string', 'description': 'Refresh token'},
                        'access': {'type': 'string', 'description': 'Access token'}
                    }
                }
            }
        },
        400: {'description': 'Invalid input data'}
    }
)
class RegisterView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Register a new user account
    """
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Send email verification (optional, can be done async)
        # EmailService.send_email_verification(user, TokenService.generate_email_verification_token(user))
        
        return Response({
            'message': 'User registered successfully',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Authentication'],
    summary='Login',
    description='Authenticate user with email and password. Returns JWT tokens upon successful login.',
    request=LoginSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string', 'example': 'Login successful'},
                'user': {'type': 'object'},
                'tokens': {
                    'type': 'object',
                    'properties': {
                        'refresh': {'type': 'string'},
                        'access': {'type': 'string'}
                    }
                }
            }
        },
        400: {'description': 'Invalid credentials'}
    }
)
class LoginView(generics.GenericAPIView):
    """
    POST /api/v1/auth/login/
    Login with email and password
    """
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Generate JWT tokens
        token_serializer = CustomTokenObtainPairSerializer()
        refresh = token_serializer.get_token(user)
        
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Authentication'],
    summary='Logout',
    description='Logout user by blacklisting the refresh token. Requires authentication.',
    request=LogoutSerializer,
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string', 'example': 'Logout successful'}}},
        400: {'description': 'Invalid token or missing refresh token'}
    }
)
class LogoutView(generics.GenericAPIView):
    """
    POST /api/v1/auth/logout/
    Logout user by blacklisting refresh token
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({
                    'message': 'Logout successful'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        except TokenError:
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    summary='Send OTP',
    description='Send OTP code to phone number for authentication.',
    request=OTPSendSerializer,
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
        429: {'description': 'Too many failed attempts'}
    }
)
class OTPSendView(generics.GenericAPIView):
    """
    POST /api/v1/auth/otp/send/
    Send OTP to phone number
    """
    serializer_class = OTPSendSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone_number = serializer.validated_data['phone_number']
        
        # Check if OTP is locked
        if OTPService.is_otp_locked(phone_number):
            return Response({
                'error': 'Too many failed attempts. Please try again later.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Generate and send OTP
        otp_code = OTPService.generate_otp(phone_number)
        
        # In production, send SMS here
        # For development, you might want to return the OTP for testing
        # In production, remove this response and just return success
        if getattr(settings, 'DEBUG', False):
            return Response({
                'message': 'OTP sent successfully',
                'otp': otp_code,  # Remove in production
            }, status=status.HTTP_200_OK)
        
        return Response({
            'message': 'OTP sent successfully'
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Authentication'],
    summary='Verify OTP',
    description='Verify OTP code sent to phone number.',
    request=OTPVerifySerializer,
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string', 'example': 'OTP verified successfully'}}},
        400: {'description': 'Invalid OTP code'}
    }
)
class OTPVerifyView(generics.GenericAPIView):
    """
    POST /api/v1/auth/otp/verify/
    Verify OTP code
    """
    serializer_class = OTPVerifySerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone_number = serializer.validated_data['phone_number']
        code = serializer.validated_data['code']
        
        # Verify OTP
        if OTPService.verify_otp(phone_number, code):
            # Reset failed attempts
            attempts_key = f"{OTPService.CACHE_PREFIX}attempts_{phone_number}"
            cache.delete(attempts_key)
            
            return Response({
                'message': 'OTP verified successfully'
            }, status=status.HTTP_200_OK)
        else:
            # Increment failed attempts
            OTPService.increment_otp_attempts(phone_number)
            return Response({
                'error': 'Invalid OTP code'
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    summary='Request password reset',
    description='Request password reset email. The response does not reveal whether the email exists.',
    request=PasswordResetRequestSerializer,
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}
    }
)
class PasswordResetRequestView(generics.GenericAPIView):
    """
    POST /api/v1/auth/password/reset/
    Request password reset email
    """
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email, is_active=True)
            # Generate reset token
            reset_token = TokenService.generate_password_reset_token(user)
            
            # Send reset email
            EmailService.send_password_reset_email(user, reset_token)
            
            # Don't reveal if email exists
            return Response({
                'message': 'If the email exists, a password reset link has been sent.'
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            # Don't reveal if email exists
            return Response({
                'message': 'If the email exists, a password reset link has been sent.'
            }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Authentication'],
    summary='Confirm password reset',
    description='Confirm password reset with token and set new password.',
    request=PasswordResetConfirmSerializer,
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string', 'example': 'Password reset successfully'}}},
        400: {'description': 'Invalid token or passwords do not match'}
    }
)
class PasswordResetConfirmView(generics.GenericAPIView):
    """
    POST /api/v1/auth/password/reset/confirm/
    Confirm password reset with token
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        new_password_confirm = request.data.get('new_password_confirm')
        
        if not token:
            return Response({
                'error': 'Token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not new_password or new_password != new_password_confirm:
            return Response({
                'error': 'Passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user from token (efficient lookup using cache)
        user = TokenService.get_user_from_password_reset_token(token)
        
        if not user:
            return Response({
                'error': 'Invalid or expired token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Invalidate token
        TokenService.invalidate_password_reset_token(token)
        
        return Response({
            'message': 'Password reset successfully'
        }, status=status.HTTP_200_OK)


# User Profile Views

@extend_schema_view(
    get=extend_schema(
        tags=['Users'],
        summary='Get current user profile',
        description='Retrieve the authenticated user\'s profile information.',
        responses={200: UserSerializer}
    ),
    patch=extend_schema(
        tags=['Users'],
        summary='Update user profile',
        description='Update the authenticated user\'s profile information.',
        request=UserUpdateSerializer,
        responses={200: UserSerializer}
    )
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/v1/users/me/ - Get current user profile
    PATCH /api/v1/users/me/ - Update current user profile
    """
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        """Get user profile"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        """Update user profile"""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Profile updated successfully',
            'user': UserSerializer(request.user).data
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Users'],
    summary='Send email verification',
    description='Send email verification email to the authenticated user.',
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string', 'example': 'Verification email sent successfully'}}},
        400: {'description': 'Email is already verified'}
    }
)
class ResendVerificationEmailView(generics.GenericAPIView):
    """
    POST /api/v1/users/me/verify-email/
    Send email verification email
    """
    serializer_class = EmailVerificationSendSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        
        if user.email_verified:
            return Response({
                'message': 'Email is already verified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate verification token
        verification_token = TokenService.generate_email_verification_token(user)
        
        # Send verification email
        EmailService.send_email_verification(user, verification_token)
        
        return Response({
            'message': 'Verification email sent successfully'
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Users'],
    summary='Verify email',
    description='Verify email address using verification token from email link. Does not require authentication.',
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string', 'example': 'Email verified successfully'}}},
        400: {'description': 'Invalid or expired token'}
    }
)
class EmailVerificationView(generics.GenericAPIView):
    """
    GET /api/v1/users/me/verify-email/{token}/
    Verify email with token
    """
    permission_classes = [permissions.AllowAny]  # Allow unauthenticated for email links

    def get(self, request, token, *args, **kwargs):
        if not token:
            return Response({
                'error': 'Token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user from token (efficient lookup using cache)
        user = TokenService.get_user_from_email_verification_token(token)
        
        if not user:
            return Response({
                'error': 'Invalid or expired token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify email
        user.email_verified = True
        user.save()
        
        # Invalidate token after use
        TokenService.invalidate_email_verification_token(token)
        
        return Response({
            'message': 'Email verified successfully'
        }, status=status.HTTP_200_OK)
