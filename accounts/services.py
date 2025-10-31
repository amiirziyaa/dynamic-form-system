import secrets
from datetime import timedelta
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from .models import User


# OTP Service
class OTPService:
    """Service for handling OTP generation and verification"""
    
    CACHE_PREFIX = 'otp_'
    EXPIRY_MINUTES = 10
    CODE_LENGTH = 6
    
    @classmethod
    def generate_otp(cls, phone_number: str) -> str:
        """
        Generate and store OTP for phone number
        Returns the OTP code
        """
        # Generate 6-digit OTP
        otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(cls.CODE_LENGTH)])
        
        # Store in cache with phone number as key
        cache_key = f"{cls.CACHE_PREFIX}{phone_number}"
        cache.set(cache_key, otp_code, timeout=cls.EXPIRY_MINUTES * 60)
        
        # In production, you would send SMS here
        # For now, we'll just store it in cache
        return otp_code
    
    @classmethod
    def verify_otp(cls, phone_number: str, code: str) -> bool:
        """
        Verify OTP code for phone number
        Returns True if valid, False otherwise
        """
        cache_key = f"{cls.CACHE_PREFIX}{phone_number}"
        stored_code = cache.get(cache_key)
        
        if stored_code is None:
            return False
        
        # Verify code matches
        if stored_code != code:
            return False
        
        # Delete OTP after verification (one-time use)
        cache.delete(cache_key)
        return True
    
    @classmethod
    def get_otp_attempts(cls, phone_number: str) -> int:
        """Get number of failed OTP attempts"""
        attempts_key = f"{cls.CACHE_PREFIX}attempts_{phone_number}"
        return cache.get(attempts_key, 0)
    
    @classmethod
    def increment_otp_attempts(cls, phone_number: str):
        """Increment failed OTP attempts"""
        attempts_key = f"{cls.CACHE_PREFIX}attempts_{phone_number}"
        attempts = cache.get(attempts_key, 0)
        cache.set(attempts_key, attempts + 1, timeout=3600)  # Reset after 1 hour
    
    @classmethod
    def is_otp_locked(cls, phone_number: str) -> bool:
        """Check if OTP is locked due to too many attempts"""
        attempts = cls.get_otp_attempts(phone_number)
        return attempts >= 5  # Lock after 5 failed attempts
    
    @classmethod
    def get_otp_code(cls, phone_number: str) -> str:
        """
        Get OTP code from cache (for testing purposes)
        Returns the OTP code if exists, None otherwise
        """
        cache_key = f"{cls.CACHE_PREFIX}{phone_number}"
        return cache.get(cache_key)


# Email Service
class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def send_email(subject: str, message: str, recipient_email: str, html_message: str = None):
        """
        Send email to recipient
        """
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            # Log error in production
            print(f"Email sending failed: {str(e)}")
            return False
    
    @classmethod
    def send_password_reset_email(cls, user: User, reset_token: str):
        """
        Send password reset email with token
        """
        reset_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        
        subject = "Password Reset Request"
        message = f"""
        Hello {user.first_name or user.email},
        
        You requested a password reset. Please click the following link to reset your password:
        
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        """
        
        html_message = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hello {user.first_name or user.email},</p>
            <p>You requested a password reset. Please click the following link to reset your password:</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
        </html>
        """
        
        return cls.send_email(subject, message, user.email, html_message)
    
    @classmethod
    def send_email_verification(cls, user: User, verification_token: str):
        """
        Send email verification email with token
        """
        verification_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={verification_token}"
        
        subject = "Verify Your Email Address"
        message = f"""
        Hello {user.first_name or user.email},
        
        Please verify your email address by clicking the following link:
        
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        """
        
        html_message = f"""
        <html>
        <body>
            <h2>Verify Your Email Address</h2>
            <p>Hello {user.first_name or user.email},</p>
            <p>Please verify your email address by clicking the following link:</p>
            <p><a href="{verification_url}">{verification_url}</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account, please ignore this email.</p>
        </body>
        </html>
        """
        
        return cls.send_email(subject, message, user.email, html_message)


# Token Service
class TokenService:
    """Service for generating and verifying tokens"""
    
    CACHE_PREFIX = 'token_'
    
    @classmethod
    def generate_email_verification_token(cls, user: User) -> str:
        """
        Generate email verification token using Django's token generator
        Store user_id in cache for efficient lookup
        """
        token = default_token_generator.make_token(user)
        # Store user_id with token in cache for efficient lookup
        cache_key = f"{cls.CACHE_PREFIX}email_verify_{token}"
        cache.set(cache_key, str(user.id), timeout=86400)  # 24 hours expiry
        return token
    
    @classmethod
    def get_user_from_email_verification_token(cls, token: str):
        """
        Get user from email verification token
        Returns User object or None
        """
        cache_key = f"{cls.CACHE_PREFIX}email_verify_{token}"
        user_id = cache.get(cache_key)
        
        if not user_id:
            return None
        
        try:
            user = User.objects.get(id=user_id, is_active=True, email_verified=False)
            # Verify token is valid
            if default_token_generator.check_token(user, token):
                return user
        except User.DoesNotExist:
            pass
        
        return None
    
    @classmethod
    def verify_email_verification_token(cls, user: User, token: str) -> bool:
        """
        Verify email verification token
        """
        # Check cache first (for expiry)
        cache_key = f"{cls.CACHE_PREFIX}email_verify_{token}"
        cached_user_id = cache.get(cache_key)
        
        if not cached_user_id or str(user.id) != cached_user_id:
            return False
        
        # Verify token is valid
        if not default_token_generator.check_token(user, token):
            return False
        
        return True
    
    @classmethod
    def invalidate_email_verification_token(cls, token: str):
        """
        Invalidate email verification token after use
        """
        cache_key = f"{cls.CACHE_PREFIX}email_verify_{token}"
        cache.delete(cache_key)
    
    @classmethod
    def generate_password_reset_token(cls, user: User) -> str:
        """
        Generate password reset token using Django's token generator
        Store user_id in cache for efficient lookup
        """
        token = default_token_generator.make_token(user)
        # Store user_id with token in cache for efficient lookup
        cache_key = f"{cls.CACHE_PREFIX}password_reset_{token}"
        cache.set(cache_key, str(user.id), timeout=3600)  # 1 hour expiry
        return token
    
    @classmethod
    def get_user_from_password_reset_token(cls, token: str):
        """
        Get user from password reset token
        Returns User object or None
        """
        cache_key = f"{cls.CACHE_PREFIX}password_reset_{token}"
        user_id = cache.get(cache_key)
        
        if not user_id:
            return None
        
        try:
            user = User.objects.get(id=user_id, is_active=True)
            # Verify token is valid
            if default_token_generator.check_token(user, token):
                return user
        except User.DoesNotExist:
            pass
        
        return None
    
    @classmethod
    def verify_password_reset_token(cls, user: User, token: str) -> bool:
        """
        Verify password reset token
        """
        # Check cache first (for expiry)
        cache_key = f"{cls.CACHE_PREFIX}password_reset_{token}"
        cached_user_id = cache.get(cache_key)
        
        if not cached_user_id or str(user.id) != cached_user_id:
            return False
        
        # Verify token is valid
        if not default_token_generator.check_token(user, token):
            return False
        
        return True
    
    @classmethod
    def invalidate_password_reset_token(cls, token: str):
        """
        Invalidate password reset token after use
        """
        cache_key = f"{cls.CACHE_PREFIX}password_reset_{token}"
        cache.delete(cache_key)

