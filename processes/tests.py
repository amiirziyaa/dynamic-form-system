import uuid
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from processes.models import Process, ProcessStep
from categories.models import Category
from forms.models import Form

User = get_user_model()


class ProcessModelTest(TestCase):
    """Test cases for Process model according to database schema"""

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
            name='HR Processes',
            color='#FF5733'
        )
        
        self.process_data = {
            'user': self.user,
            'category': self.category,
            'title': 'Employee Onboarding',
            'description': 'Complete onboarding process for new employees',
            'unique_slug': 'employee-onboarding-2024',
            'visibility': 'public',
            'process_type': 'linear',
            'is_active': True,
            'settings': {
                'allow_save_progress': True,
                'show_step_numbers': True,
                'completion_message': 'Welcome to the team!'
            }
        }

    def test_process_creation(self):
        """Test basic process creation"""
        process = Process.objects.create(**self.process_data)
        
        # Test primary key is UUID
        self.assertIsInstance(process.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(process.user, self.user)
        self.assertEqual(process.category, self.category)
        self.assertEqual(process.title, 'Employee Onboarding')
        self.assertEqual(process.description, 'Complete onboarding process for new employees')
        self.assertEqual(process.unique_slug, 'employee-onboarding-2024')
        self.assertEqual(process.visibility, 'public')
        self.assertEqual(process.process_type, 'linear')
        self.assertTrue(process.is_active)
        
        # Test JSON settings
        self.assertIsInstance(process.settings, dict)
        self.assertEqual(process.settings['allow_save_progress'], True)
        
        # Test timestamps
        self.assertIsNotNone(process.created_at)
        self.assertIsNotNone(process.updated_at)

    def test_process_slug_uniqueness(self):
        """Test unique slug constraint"""
        Process.objects.create(**self.process_data)
        
        # Try to create another process with same slug
        with self.assertRaises(IntegrityError):
            Process.objects.create(
                user=self.user,
                title='Another Process',
                unique_slug='employee-onboarding-2024'
            )

    def test_process_visibility_choices(self):
        """Test visibility choices"""
        # Test public visibility
        process = Process.objects.create(
            user=self.user,
            title='Public Process',
            unique_slug='public-process',
            visibility='public'
        )
        self.assertEqual(process.visibility, 'public')
        
        # Test private visibility
        process = Process.objects.create(
            user=self.user,
            title='Private Process',
            unique_slug='private-process',
            visibility='private',
            access_password='encrypted_password'
        )
        self.assertEqual(process.visibility, 'private')
        self.assertEqual(process.access_password, 'encrypted_password')

    def test_process_type_choices(self):
        """Test process type choices"""
        # Test linear process
        process = Process.objects.create(
            user=self.user,
            title='Linear Process',
            unique_slug='linear-process',
            process_type='linear'
        )
        self.assertEqual(process.process_type, 'linear')
        
        # Test free process
        process = Process.objects.create(
            user=self.user,
            title='Free Process',
            unique_slug='free-process',
            process_type='free'
        )
        self.assertEqual(process.process_type, 'free')

    def test_process_optional_category(self):
        """Test optional category field"""
        process = Process.objects.create(
            user=self.user,
            title='Process Without Category',
            unique_slug='no-category-process'
        )
        self.assertIsNone(process.category)

    def test_process_string_representation(self):
        """Test string representation"""
        process = Process.objects.create(**self.process_data)
        expected = "Employee Onboarding (employee-onboarding-2024)"
        self.assertEqual(str(process), expected)

    def test_process_database_table_name(self):
        """Test database table name"""
        self.assertEqual(Process._meta.db_table, 'process')

    def test_process_verbose_name_plural(self):
        """Test verbose name plural"""
        self.assertEqual(Process._meta.verbose_name_plural, 'processes')

    def test_process_indexes(self):
        """Test that proper indexes are created"""
        indexes = [index.fields for index in Process._meta.indexes]
        self.assertIn(['user'], indexes)
        self.assertIn(['unique_slug'], indexes)
        self.assertIn(['process_type'], indexes)

    def test_process_related_names(self):
        """Test related names for foreign key relationships"""
        process = Process.objects.create(**self.process_data)
        
        # Test that related managers exist
        self.assertTrue(hasattr(process, 'steps'))
        self.assertTrue(hasattr(process, 'progress_records'))
        self.assertTrue(hasattr(process, 'views'))


class ProcessStepModelTest(TestCase):
    """Test cases for ProcessStep model according to database schema"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )
        
        self.process = Process.objects.create(
            user=self.user,
            title='Test Process',
            unique_slug='test-process'
        )
        
        self.form = Form.objects.create(
            user=self.user,
            title='Test Form',
            unique_slug='test-form'
        )
        
        self.step_data = {
            'process': self.process,
            'form': self.form,
            'title': 'Personal Information',
            'description': 'Enter your personal details',
            'order_index': 0,
            'is_required': True,
            'conditions': {
                'show_if': {
                    'field_id': 'some-uuid',
                    'operator': 'equals',
                    'value': 'yes'
                }
            }
        }

    def test_step_creation(self):
        """Test basic step creation"""
        step = ProcessStep.objects.create(**self.step_data)
        
        # Test primary key is UUID
        self.assertIsInstance(step.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(step.process, self.process)
        self.assertEqual(step.form, self.form)
        self.assertEqual(step.title, 'Personal Information')
        self.assertEqual(step.description, 'Enter your personal details')
        self.assertEqual(step.order_index, 0)
        self.assertTrue(step.is_required)
        
        # Test JSON conditions
        self.assertIsInstance(step.conditions, dict)
        self.assertIn('show_if', step.conditions)
        
        # Test timestamps
        self.assertIsNotNone(step.created_at)
        self.assertIsNotNone(step.updated_at)

    def test_step_order_index_uniqueness(self):
        """Test order index uniqueness within process"""
        ProcessStep.objects.create(**self.step_data)
        
        # Try to create another step with same order index
        with self.assertRaises(IntegrityError):
            ProcessStep.objects.create(
                process=self.process,
                form=self.form,
                title='Another Step',
                order_index=0  # Same order index
            )

    def test_step_optional_fields(self):
        """Test optional fields"""
        step = ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            title='Simple Step',
            order_index=1
        )
        
        self.assertIsNone(step.description)
        self.assertTrue(step.is_required)  # Default value
        self.assertEqual(step.conditions, {})

    def test_step_is_required_default(self):
        """Test is_required default value"""
        step = ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            title='Optional Step',
            order_index=1,
            is_required=False
        )
        self.assertFalse(step.is_required)

    def test_step_string_representation(self):
        """Test string representation"""
        step = ProcessStep.objects.create(**self.step_data)
        expected = "Personal Information (Test Process)"
        self.assertEqual(str(step), expected)

    def test_step_database_table_name(self):
        """Test database table name"""
        self.assertEqual(ProcessStep._meta.db_table, 'process_step')

    def test_step_indexes(self):
        """Test that proper indexes are created"""
        indexes = [index.fields for index in ProcessStep._meta.indexes]
        self.assertIn(['process', 'order_index'], indexes)
        self.assertIn(['form'], indexes)

    def test_step_unique_together(self):
        """Test unique together constraint"""
        self.assertEqual(ProcessStep._meta.unique_together, (('process', 'order_index'),))

    def test_step_related_names(self):
        """Test related names for foreign key relationships"""
        step = ProcessStep.objects.create(**self.step_data)
        
        # Test that related managers exist
        self.assertTrue(hasattr(step, 'completions'))

    def test_step_cascade_delete(self):
        """Test cascade delete when process is deleted"""
        step = ProcessStep.objects.create(**self.step_data)
        step_id = step.id
        
        # Delete process
        self.process.delete()
        
        # Step should be deleted too
        self.assertFalse(ProcessStep.objects.filter(id=step_id).exists())

    def test_step_form_relationship(self):
        """Test form relationship"""
        step = ProcessStep.objects.create(**self.step_data)
        
        # Test forward relationship
        self.assertEqual(step.form, self.form)
        
        # Test reverse relationship
        self.assertIn(step, self.form.process_steps.all())