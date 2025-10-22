import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

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

    def test_user_related_names(self):
        """Test related names for foreign key relationships"""
        user = User.objects.create_user(**self.user_data)
        
        # Test that related managers exist
        self.assertTrue(hasattr(user, 'categories'))
        self.assertTrue(hasattr(user, 'forms'))
        self.assertTrue(hasattr(user, 'processes'))
        self.assertTrue(hasattr(user, 'form_submissions'))
        self.assertTrue(hasattr(user, 'process_progress'))
        self.assertTrue(hasattr(user, 'notifications'))
        self.assertTrue(hasattr(user, 'webhooks'))