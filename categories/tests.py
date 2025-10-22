import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from categories.models import Category

User = get_user_model()


class CategoryModelTest(TestCase):
    """Test cases for Category model according to database schema"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )
        
        self.category_data = {
            'user': self.user,
            'name': 'HR Forms',
            'description': 'Human Resources related forms',
            'color': '#FF5733'
        }

    def test_category_creation(self):
        """Test basic category creation"""
        category = Category.objects.create(**self.category_data)
        
        # Test primary key is UUID
        self.assertIsInstance(category.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(category.user, self.user)
        self.assertEqual(category.name, 'HR Forms')
        self.assertEqual(category.description, 'Human Resources related forms')
        self.assertEqual(category.color, '#FF5733')
        
        # Test timestamps
        self.assertIsNotNone(category.created_at)
        self.assertIsNotNone(category.updated_at)

    def test_category_optional_fields(self):
        """Test optional fields"""
        category = Category.objects.create(
            user=self.user,
            name='Simple Category'
        )
        
        self.assertIsNone(category.description)
        self.assertIsNone(category.color)

    def test_category_string_representation(self):
        """Test string representation"""
        category = Category.objects.create(**self.category_data)
        expected = f"HR Forms ({self.user.email})"
        self.assertEqual(str(category), expected)

    def test_category_database_table_name(self):
        """Test database table name"""
        self.assertEqual(Category._meta.db_table, 'category')

    def test_category_verbose_name_plural(self):
        """Test verbose name plural"""
        self.assertEqual(Category._meta.verbose_name_plural, 'categories')

    def test_category_indexes(self):
        """Test that proper indexes are created"""
        indexes = [index.fields for index in Category._meta.indexes]
        self.assertIn(['user'], indexes)

    def test_category_related_names(self):
        """Test related names for foreign key relationships"""
        category = Category.objects.create(**self.category_data)
        
        # Test that related managers exist
        self.assertTrue(hasattr(category, 'forms'))
        self.assertTrue(hasattr(category, 'processes'))

    def test_category_user_relationship(self):
        """Test user relationship"""
        category = Category.objects.create(**self.category_data)
        
        # Test forward relationship
        self.assertEqual(category.user, self.user)
        
        # Test reverse relationship
        self.assertIn(category, self.user.categories.all())

    def test_category_cascade_delete(self):
        """Test cascade delete when user is deleted"""
        category = Category.objects.create(**self.category_data)
        category_id = category.id
        
        # Delete user
        self.user.delete()
        
        # Category should be deleted too
        self.assertFalse(Category.objects.filter(id=category_id).exists())

    def test_category_max_length_constraints(self):
        """Test max length constraints"""
        # Test name max length
        long_name = 'x' * 256  # Exceeds max_length=255
        with self.assertRaises(ValidationError):
            category = Category(name=long_name, user=self.user)
            category.full_clean()
        
        # Test color max length
        long_color = 'x' * 8  # Exceeds max_length=7
        with self.assertRaises(ValidationError):
            category = Category(name='Test', user=self.user, color=long_color)
            category.full_clean()