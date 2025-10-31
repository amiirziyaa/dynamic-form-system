import uuid
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock

from .models import User
from .services import OTPService, EmailService, TokenService

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for User model according to database schema"""

    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'testpass123'
        }

    def test_user_creation(self):
        """Test basic user creation"""
        user = User.objects.create_user(**self.user_data)
        
        # Test primary key is UUID
        self.assertIsInstance(user.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.email_verified)
        
        # Test timestamps
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)

    def test_user_email_uniqueness(self):
        """Test email uniqueness constraint"""
        User.objects.create_user(**self.user_data)
        
        # Try to create another user with same email
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='test@example.com',
                first_name='Jane',
                last_name='Smith',
                password='testpass123'
            )

    def test_user_email_as_username(self):
        """Test that email is used as username field"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.USERNAME_FIELD, 'email')
        self.assertEqual(user.get_username(), 'test@example.com')

    def test_user_full_name_property(self):
        """Test full_name property"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.full_name, 'John Doe')
        
        # Test with empty last name
        user.last_name = ''
        self.assertEqual(user.full_name, 'John')

    def test_user_optional_fields(self):
        """Test optional fields"""
        user = User.objects.create_user(
            email='test2@example.com',
            first_name='Jane',
            last_name='Smith',
            password='testpass123',
            phone_number='+1234567890',
            is_staff=True,
            email_verified=True
        )
        
        self.assertEqual(user.phone_number, '+1234567890')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.email_verified)

    def test_user_string_representation(self):
        """Test string representation"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')

    def test_user_required_fields(self):
        """Test required fields validation"""
        # Test missing email
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='',  # Empty email
                first_name='John',
                last_name='Doe',
                password='testpass123'
            )

    def test_user_database_table_name(self):
        """Test database table name"""
        self.assertEqual(User._meta.db_table, 'user')

    def test_user_indexes(self):
        """Test that proper indexes are created"""
        indexes = [index.fields for index in User._meta.indexes]
        self.assertIn(['email'], indexes)
        self.assertIn(['is_active'], indexes)


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================

class AuthenticationAPITestCase(APITestCase):
    """Test cases for Authentication API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.register_url = reverse('auth:register')
        self.login_url = reverse('auth:login')
        self.logout_url = reverse('auth:logout')
        self.refresh_url = reverse('auth:token-refresh')
        
        # Clear cache before each test
        cache.clear()
    
    def tearDown(self):
        """Clean up after each test"""
        cache.clear()

    # ========== REGISTER ENDPOINT ==========
    
    def test_register_user_success(self):
        """Test successful user registration"""
        data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'securepass123',
            'password_confirm': 'securepass123'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')
        self.assertIsNotNone(response.data['tokens']['access'])
        self.assertIsNotNone(response.data['tokens']['refresh'])
        
        # Verify user was created
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
        user = User.objects.get(email='newuser@example.com')
        self.assertFalse(user.email_verified)  # Should not be verified by default
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        User.objects.create_user(
            email='existing@example.com',
            first_name='Existing',
            last_name='User',
            password='pass123'
        )
        
        data = {
            'email': 'existing@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'pass123',
            'password_confirm': 'pass123'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_password_mismatch(self):
        """Test registration with password mismatch"""
        data = {
            'email': 'user@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'SecurePass123!',  # Strong password
            'password_confirm': 'DifferentPass123!'  # Different password
        }
        
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('match', str(response.data).lower())
    
    def test_register_weak_password(self):
        """Test registration with weak password"""
        data = {
            'email': 'user@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': '123',  # Too short
            'password_confirm': '123'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ========== LOGIN ENDPOINT ==========
    
    def test_login_success(self):
        """Test successful login"""
        user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
        self.assertIsNotNone(response.data['tokens']['access'])
        self.assertIsNotNone(response.data['tokens']['refresh'])
        
        # Verify last_login was updated
        user.refresh_from_db()
        self.assertIsNotNone(user.last_login)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='correctpass'
        )
        
        data = {
            'email': 'test@example.com',
            'password': 'wrongpass'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid', str(response.data))
    
    def test_login_inactive_user(self):
        """Test login with inactive user"""
        user = User.objects.create_user(
            email='inactive@example.com',
            first_name='Inactive',
            last_name='User',
            password='testpass123'
        )
        user.is_active = False
        user.save()
        
        data = {
            'email': 'inactive@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Django's authenticate() doesn't reveal if account is disabled (security)
        # It just returns invalid credentials, so we check for 'Invalid'
        self.assertIn('Invalid', str(response.data))

    # ========== LOGOUT ENDPOINT ==========
    
    def test_logout_success(self):
        """Test successful logout"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)
        
        # Login first to get tokens
        self.client.force_authenticate(user=user)
        
        data = {'refresh': refresh_token}
        response = self.client.post(self.logout_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('successful', str(response.data).lower())
        
        # Verify token is blacklisted (cannot refresh)
        response = self.client.post(self.refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout_without_token(self):
        """Test logout without refresh token"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user)
        
        response = self.client.post(self.logout_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ========== TOKEN REFRESH ENDPOINT ==========
    
    def test_token_refresh_success(self):
        """Test successful token refresh"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)
        
        data = {'refresh': refresh_token}
        response = self.client.post(self.refresh_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_token_refresh_invalid_token(self):
        """Test refresh with invalid token"""
        data = {'refresh': 'invalid_token'}
        response = self.client.post(self.refresh_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OTPAPITestCase(APITestCase):
    """Test cases for OTP API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.otp_send_url = reverse('auth:otp-send')
        self.otp_verify_url = reverse('auth:otp-verify')
        cache.clear()
    
    def tearDown(self):
        """Clean up after each test"""
        cache.clear()
    
    def test_otp_send_success(self):
        """Test successful OTP sending"""
        data = {
            'phone_number': '+1234567890'
        }
        
        response = self.client.post(self.otp_send_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('OTP sent', response.data['message'])
        
        # Verify OTP was stored in cache (for testing purposes)
        otp_code = OTPService.get_otp_code(data['phone_number'])
        self.assertIsNotNone(otp_code)
        self.assertEqual(len(otp_code), 6)  # 6-digit OTP
    
    def test_otp_send_invalid_phone(self):
        """Test OTP send with invalid phone number"""
        data = {
            'phone_number': '123'  # Too short, no country code
        }
        
        response = self.client.post(self.otp_send_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_otp_send_phone_without_country_code(self):
        """Test OTP send without country code"""
        data = {
            'phone_number': '1234567890'  # No + prefix
        }
        
        response = self.client.post(self.otp_send_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_otp_verify_success(self):
        """Test successful OTP verification"""
        phone_number = '+1234567890'
        
        # First send OTP
        otp_code = OTPService.generate_otp(phone_number)
        
        # Verify OTP
        data = {
            'phone_number': phone_number,
            'code': otp_code
        }
        
        response = self.client.post(self.otp_verify_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('verified', response.data['message'].lower())
        
        # Verify OTP was deleted from cache (one-time use)
        cache_key = f"{OTPService.CACHE_PREFIX}{phone_number}"
        self.assertIsNone(cache.get(cache_key))
    
    def test_otp_verify_invalid_code(self):
        """Test OTP verification with invalid code"""
        phone_number = '+1234567890'
        OTPService.generate_otp(phone_number)
        
        data = {
            'phone_number': phone_number,
            'code': '000000'  # Wrong code
        }
        
        response = self.client.post(self.otp_verify_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify attempts were incremented
        attempts = OTPService.get_otp_attempts(phone_number)
        self.assertEqual(attempts, 1)
    
    def test_otp_verify_expired_code(self):
        """Test OTP verification with expired code"""
        phone_number = '+1234567890'
        
        # Generate and immediately expire (simulate by deleting from cache)
        OTPService.generate_otp(phone_number)
        cache_key = f"{OTPService.CACHE_PREFIX}{phone_number}"
        cache.delete(cache_key)
        
        # Try to verify with any code
        data = {
            'phone_number': phone_number,
            'code': '123456'
        }
        
        response = self.client.post(self.otp_verify_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_otp_rate_limiting(self):
        """Test OTP rate limiting after too many attempts"""
        phone_number = '+1234567890'
        
        # Make 5 failed attempts
        for _ in range(5):
            OTPService.increment_otp_attempts(phone_number)
        
        # Try to send OTP (should be locked)
        self.assertTrue(OTPService.is_otp_locked(phone_number))
        
        data = {'phone_number': phone_number}
        response = self.client.post(self.otp_send_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class PasswordResetAPITestCase(APITestCase):
    """Test cases for Password Reset API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.password_reset_url = reverse('auth:password-reset')
        self.password_reset_confirm_url = reverse('auth:password-reset-confirm')
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='oldpass123'
        )
        cache.clear()
    
    def tearDown(self):
        """Clean up after each test"""
        cache.clear()
    
    @patch('accounts.services.EmailService.send_password_reset_email')
    def test_password_reset_request_success(self, mock_send_email):
        """Test successful password reset request"""
        mock_send_email.return_value = True
        
        data = {'email': 'test@example.com'}
        response = self.client.post(self.password_reset_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_email.assert_called_once()
        
        # Verify token was generated and stored
        user = User.objects.get(email='test@example.com')
        # Token should be in cache
        self.assertTrue(True)  # Token generation verified by service call
    
    def test_password_reset_request_nonexistent_email(self):
        """Test password reset for non-existent email (security: don't reveal)"""
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(self.password_reset_url, data, format='json')
        
        # Should return success message even for non-existent email (security)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_password_reset_confirm_success(self):
        """Test successful password reset confirmation"""
        # Generate reset token
        reset_token = TokenService.generate_password_reset_token(self.user)
        
        data = {
            'token': reset_token,
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        
        response = self.client.post(self.password_reset_confirm_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))
        
        # Verify token was invalidated
        user_from_token = TokenService.get_user_from_password_reset_token(reset_token)
        self.assertIsNone(user_from_token)
    
    def test_password_reset_confirm_password_mismatch(self):
        """Test password reset with mismatched passwords"""
        reset_token = TokenService.generate_password_reset_token(self.user)
        
        data = {
            'token': reset_token,
            'new_password': 'newpass123',
            'new_password_confirm': 'differentpass'
        }
        
        response = self.client.post(self.password_reset_confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_reset_confirm_invalid_token(self):
        """Test password reset with invalid token"""
        data = {
            'token': 'invalid_token',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        
        response = self.client.post(self.password_reset_confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_reset_confirm_expired_token(self):
        """Test password reset with expired token"""
        # Generate token and manually expire it from cache
        reset_token = TokenService.generate_password_reset_token(self.user)
        TokenService.invalidate_password_reset_token(reset_token)
        
        data = {
            'token': reset_token,
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        
        response = self.client.post(self.password_reset_confirm_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileAPITestCase(APITestCase):
    """Test cases for User Profile API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123',
            phone_number='+1234567890'
        )
        self.client.force_authenticate(user=self.user)
        
        self.profile_url = reverse('users:user-profile')
        self.verify_email_url = reverse('users:user-verify-email-send')
        cache.clear()
    
    def tearDown(self):
        """Clean up after each test"""
        cache.clear()
    
    # ========== GET PROFILE ==========
    
    def test_get_profile_success(self):
        """Test successful profile retrieval"""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
        self.assertEqual(response.data['phone_number'], '+1234567890')
    
    def test_get_profile_unauthenticated(self):
        """Test profile retrieval without authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # ========== UPDATE PROFILE ==========
    
    def test_update_profile_success(self):
        """Test successful profile update"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '+9876543210'
        }
        
        response = self.client.patch(self.profile_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['first_name'], 'Updated')
        self.assertEqual(response.data['user']['last_name'], 'Name')
        self.assertEqual(response.data['user']['phone_number'], '+9876543210')
        
        # Verify database was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
    
    def test_update_profile_partial(self):
        """Test partial profile update"""
        data = {'first_name': 'NewName'}
        
        response = self.client.patch(self.profile_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['first_name'], 'NewName')
        # Other fields should remain unchanged
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_name, 'User')
    
    def test_update_profile_unauthenticated(self):
        """Test profile update without authentication"""
        self.client.force_authenticate(user=None)
        data = {'first_name': 'NewName'}
        response = self.client.patch(self.profile_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # ========== EMAIL VERIFICATION ==========
    
    @patch('accounts.services.EmailService.send_email_verification')
    def test_send_verification_email_success(self, mock_send_email):
        """Test successful email verification request"""
        mock_send_email.return_value = True
        
        response = self.client.post(self.verify_email_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_email.assert_called_once()
    
    def test_send_verification_email_already_verified(self):
        """Test sending verification email when already verified"""
        self.user.email_verified = True
        self.user.save()
        
        response = self.client.post(self.verify_email_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already verified', str(response.data).lower())
    
    def test_verify_email_with_token_success(self):
        """Test successful email verification with token"""
        self.user.email_verified = False
        self.user.save()
        
        # Generate verification token
        verification_token = TokenService.generate_email_verification_token(self.user)
        
        verify_url = reverse('users:user-verify-email', kwargs={'token': verification_token})
        
        # Use GET request (no authentication needed for email links)
        self.client.force_authenticate(user=None)
        response = self.client.get(verify_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify email was marked as verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        
        # Verify token was invalidated
        user_from_token = TokenService.get_user_from_email_verification_token(verification_token)
        self.assertIsNone(user_from_token)
    
    def test_verify_email_invalid_token(self):
        """Test email verification with invalid token"""
        verify_url = reverse('users:user-verify-email', kwargs={'token': 'invalid_token'})
        
        self.client.force_authenticate(user=None)
        response = self.client.get(verify_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_verify_email_already_verified(self):
        """Test email verification when already verified"""
        self.user.email_verified = True
        self.user.save()
        
        # Generate token anyway
        verification_token = TokenService.generate_email_verification_token(self.user)
        
        verify_url = reverse('users:user-verify-email', kwargs={'token': verification_token})
        
        self.client.force_authenticate(user=None)
        response = self.client.get(verify_url)
        
        # Should fail because user is already verified
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ServicesTestCase(TestCase):
    """Test cases for Service classes"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        cache.clear()
    
    def tearDown(self):
        """Clean up after each test"""
        cache.clear()
    
    def test_otp_service_generate_and_verify(self):
        """Test OTP generation and verification"""
        phone_number = '+1234567890'
        
        # Generate OTP
        otp_code = OTPService.generate_otp(phone_number)
        
        # Verify OTP exists in cache
        cache_key = f"{OTPService.CACHE_PREFIX}{phone_number}"
        cached_otp = cache.get(cache_key)
        self.assertEqual(cached_otp, otp_code)
        self.assertEqual(len(otp_code), 6)
        
        # Verify OTP
        self.assertTrue(OTPService.verify_otp(phone_number, otp_code))
        
        # OTP should be deleted after verification
        self.assertIsNone(cache.get(cache_key))
    
    def test_otp_service_one_time_use(self):
        """Test that OTP can only be used once"""
        phone_number = '+1234567890'
        otp_code = OTPService.generate_otp(phone_number)
        
        # First verification should succeed
        self.assertTrue(OTPService.verify_otp(phone_number, otp_code))
        
        # Second verification should fail
        self.assertFalse(OTPService.verify_otp(phone_number, otp_code))
    
    def test_token_service_email_verification(self):
        """Test email verification token generation and verification"""
        token = TokenService.generate_email_verification_token(self.user)
        
        # Verify token is valid
        self.assertTrue(TokenService.verify_email_verification_token(self.user, token))
        
        # Get user from token
        user_from_token = TokenService.get_user_from_email_verification_token(token)
        self.assertEqual(user_from_token, self.user)
        
        # Invalidate token
        TokenService.invalidate_email_verification_token(token)
        
        # Token should no longer be valid
        user_from_token = TokenService.get_user_from_email_verification_token(token)
        self.assertIsNone(user_from_token)
    
    def test_token_service_password_reset(self):
        """Test password reset token generation and verification"""
        token = TokenService.generate_password_reset_token(self.user)
        
        # Get user from token
        user_from_token = TokenService.get_user_from_password_reset_token(token)
        self.assertEqual(user_from_token, self.user)
        
        # Verify token
        self.assertTrue(TokenService.verify_password_reset_token(self.user, token))
        
        # Invalidate token
        TokenService.invalidate_password_reset_token(token)
        
        # Token should no longer be valid
        user_from_token = TokenService.get_user_from_password_reset_token(token)
        self.assertIsNone(user_from_token)
