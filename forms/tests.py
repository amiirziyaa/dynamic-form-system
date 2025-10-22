import uuid
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from forms.models import Form, FormField, FieldOption
from categories.models import Category

User = get_user_model()


class FormModelTest(TestCase):
    """Test cases for Form model according to database schema"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            user=self.user,
            name='Test Category',
            color='#FF5733'
        )
        
        self.form_data = {
            'user': self.user,
            'category': self.category,
            'title': 'Customer Feedback Survey',
            'description': 'Help us improve our services',
            'unique_slug': 'customer-feedback-2024',
            'visibility': 'public',
            'is_active': True,
            'settings': {
                'theme': 'default',
                'allow_multiple_submissions': False,
                'show_progress_bar': True
            }
        }

    def test_form_creation(self):
        """Test basic form creation"""
        form = Form.objects.create(**self.form_data)
        
        # Test primary key is UUID
        self.assertIsInstance(form.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(form.user, self.user)
        self.assertEqual(form.category, self.category)
        self.assertEqual(form.title, 'Customer Feedback Survey')
        self.assertEqual(form.description, 'Help us improve our services')
        self.assertEqual(form.unique_slug, 'customer-feedback-2024')
        self.assertEqual(form.visibility, 'public')
        self.assertTrue(form.is_active)
        
        # Test JSON settings
        self.assertIsInstance(form.settings, dict)
        self.assertEqual(form.settings['theme'], 'default')
        
        # Test timestamps
        self.assertIsNotNone(form.created_at)
        self.assertIsNotNone(form.updated_at)

    def test_form_slug_uniqueness(self):
        """Test unique slug constraint"""
        Form.objects.create(**self.form_data)
        
        # Try to create another form with same slug
        with self.assertRaises(IntegrityError):
            Form.objects.create(
                user=self.user,
                title='Another Form',
                unique_slug='customer-feedback-2024'
            )

    def test_form_visibility_choices(self):
        """Test visibility choices"""
        # Test public visibility
        form = Form.objects.create(
            user=self.user,
            title='Public Form',
            unique_slug='public-form',
            visibility='public'
        )
        self.assertEqual(form.visibility, 'public')
        
        # Test private visibility
        form = Form.objects.create(
            user=self.user,
            title='Private Form',
            unique_slug='private-form',
            visibility='private',
            access_password='encrypted_password'
        )
        self.assertEqual(form.visibility, 'private')
        self.assertEqual(form.access_password, 'encrypted_password')

    def test_form_optional_category(self):
        """Test optional category field"""
        form = Form.objects.create(
            user=self.user,
            title='Form Without Category',
            unique_slug='no-category-form'
        )
        self.assertIsNone(form.category)

    def test_form_string_representation(self):
        """Test string representation"""
        form = Form.objects.create(**self.form_data)
        expected = "Customer Feedback Survey (customer-feedback-2024)"
        self.assertEqual(str(form), expected)

    def test_form_database_table_name(self):
        """Test database table name"""
        self.assertEqual(Form._meta.db_table, 'form')

    def test_form_indexes(self):
        """Test that proper indexes are created"""
        indexes = [index.fields for index in Form._meta.indexes]
        self.assertIn(['user'], indexes)
        self.assertIn(['unique_slug'], indexes)
        self.assertIn(['category'], indexes)
        self.assertIn(['visibility', 'is_active'], indexes)
        self.assertIn(['created_at'], indexes)

    def test_form_related_names(self):
        """Test related names for foreign key relationships"""
        form = Form.objects.create(**self.form_data)
        
        # Test that related managers exist
        self.assertTrue(hasattr(form, 'fields'))
        self.assertTrue(hasattr(form, 'submissions'))
        self.assertTrue(hasattr(form, 'views'))
        self.assertTrue(hasattr(form, 'process_steps'))


class FormFieldModelTest(TestCase):
    """Test cases for FormField model according to database schema"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )
        
        self.form = Form.objects.create(
            user=self.user,
            title='Test Form',
            unique_slug='test-form'
        )
        
        self.field_data = {
            'form': self.form,
            'field_type': 'text',
            'label': 'Full Name',
            'description': 'Enter your full name',
            'is_required': True,
            'order_index': 0,
            'validation_rules': {
                'min_length': 2,
                'max_length': 100
            },
            'settings': {
                'placeholder': 'Enter your name',
                'help_text': 'Use your legal name'
            }
        }

    def test_field_creation(self):
        """Test basic field creation"""
        field = FormField.objects.create(**self.field_data)
        
        # Test primary key is UUID
        self.assertIsInstance(field.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(field.form, self.form)
        self.assertEqual(field.field_type, 'text')
        self.assertEqual(field.label, 'Full Name')
        self.assertEqual(field.description, 'Enter your full name')
        self.assertTrue(field.is_required)
        self.assertEqual(field.order_index, 0)
        
        # Test JSON fields
        self.assertIsInstance(field.validation_rules, dict)
        self.assertEqual(field.validation_rules['min_length'], 2)
        self.assertIsInstance(field.settings, dict)
        self.assertEqual(field.settings['placeholder'], 'Enter your name')

    def test_field_type_choices(self):
        """Test field type choices"""
        field_types = ['text', 'number', 'email', 'select', 'checkbox', 'radio', 'textarea', 'date', 'file']
        
        for field_type in field_types:
            field = FormField.objects.create(
                form=self.form,
                field_type=field_type,
                label=f'{field_type.title()} Field',
                order_index=field_types.index(field_type)
            )
            self.assertEqual(field.field_type, field_type)

    def test_field_order_index_uniqueness(self):
        """Test order index uniqueness within form"""
        FormField.objects.create(**self.field_data)
        
        # Try to create another field with same order index
        with self.assertRaises(IntegrityError):
            FormField.objects.create(
                form=self.form,
                field_type='email',
                label='Email Field',
                order_index=0  # Same order index
            )

    def test_field_optional_fields(self):
        """Test optional fields"""
        field = FormField.objects.create(
            form=self.form,
            field_type='text',
            label='Simple Field',
            order_index=1
        )
        
        self.assertIsNone(field.description)
        self.assertFalse(field.is_required)
        self.assertEqual(field.validation_rules, {})
        self.assertEqual(field.settings, {})

    def test_field_string_representation(self):
        """Test string representation"""
        field = FormField.objects.create(**self.field_data)
        expected = "Full Name (Test Form)"
        self.assertEqual(str(field), expected)

    def test_field_database_table_name(self):
        """Test database table name"""
        self.assertEqual(FormField._meta.db_table, 'form_field')

    def test_field_indexes(self):
        """Test that proper indexes are created"""
        indexes = [index.fields for index in FormField._meta.indexes]
        self.assertIn(['form', 'order_index'], indexes)

    def test_field_unique_together(self):
        """Test unique together constraint"""
        self.assertEqual(FormField._meta.unique_together, (('form', 'order_index'),))

    def test_field_related_names(self):
        """Test related names for foreign key relationships"""
        field = FormField.objects.create(**self.field_data)
        
        # Test that related managers exist
        self.assertTrue(hasattr(field, 'options'))
        self.assertTrue(hasattr(field, 'answers'))


class FieldOptionModelTest(TestCase):
    """Test cases for FieldOption model according to database schema"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )
        
        self.form = Form.objects.create(
            user=self.user,
            title='Test Form',
            unique_slug='test-form'
        )
        
        self.field = FormField.objects.create(
            form=self.form,
            field_type='select',
            label='Satisfaction Level',
            order_index=0
        )
        
        self.option_data = {
            'field': self.field,
            'label': 'Very Satisfied',
            'value': '5',
            'order_index': 0
        }

    def test_option_creation(self):
        """Test basic option creation"""
        option = FieldOption.objects.create(**self.option_data)
        
        # Test primary key is UUID
        self.assertIsInstance(option.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(option.field, self.field)
        self.assertEqual(option.label, 'Very Satisfied')
        self.assertEqual(option.value, '5')
        self.assertEqual(option.order_index, 0)
        
        # Test timestamp
        self.assertIsNotNone(option.created_at)

    def test_option_order_index_uniqueness(self):
        """Test order index uniqueness within field"""
        FieldOption.objects.create(**self.option_data)
        
        # Try to create another option with same order index
        with self.assertRaises(IntegrityError):
            FieldOption.objects.create(
                field=self.field,
                label='Satisfied',
                value='4',
                order_index=0  # Same order index
            )

    def test_option_string_representation(self):
        """Test string representation"""
        option = FieldOption.objects.create(**self.option_data)
        expected = "Very Satisfied (Satisfaction Level)"
        self.assertEqual(str(option), expected)

    def test_option_database_table_name(self):
        """Test database table name"""
        self.assertEqual(FieldOption._meta.db_table, 'field_option')

    def test_option_indexes(self):
        """Test that proper indexes are created"""
        indexes = [index.fields for index in FieldOption._meta.indexes]
        self.assertIn(['field', 'order_index'], indexes)

    def test_option_unique_together(self):
        """Test unique together constraint"""
        self.assertEqual(FieldOption._meta.unique_together, (('field', 'order_index'),))

    def test_option_cascade_delete(self):
        """Test cascade delete when field is deleted"""
        option = FieldOption.objects.create(**self.option_data)
        option_id = option.id
        
        # Delete field
        self.field.delete()
        
        # Option should be deleted too
        self.assertFalse(FieldOption.objects.filter(id=option_id).exists())