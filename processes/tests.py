import uuid
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from processes.models import Process, ProcessStep
from categories.models import Category
from forms.models import Form

User = get_user_model()


# ============================================================================
# MODEL TESTS (Existing - keeping them)
# ============================================================================

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
        self.assertTrue(hasattr(self.user, 'processes'))


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


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================

class ProcessAPITestCase(APITestCase):
    """Test cases for Process API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )
        
        self.other_user = User.objects.create_user(
            email='other@example.com',
            first_name='Jane',
            last_name='Smith',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            user=self.user,
            name='HR Processes',
            color='#FF5733'
        )
        
        self.process = Process.objects.create(
            user=self.user,
            category=self.category,
            title='Employee Onboarding',
            description='Complete onboarding process',
            unique_slug='employee-onboarding-2024',
            visibility='public',
            process_type='linear',
            is_active=True,
            settings={'allow_save_progress': True}
        )
        
        # Get JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.auth_header = f'Bearer {self.token}'

    def _authenticate(self, user=None):
        """Authenticate request"""
        if user is None:
            user = self.user
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        return f'Bearer {token}'

    # ========================================================================
    # LIST PROCESSES
    # ========================================================================

    def test_list_processes_success(self):
        """Test listing all user's processes"""
        url = '/api/v1/processes/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Employee Onboarding')

    def test_list_processes_unauthenticated(self):
        """Test listing processes without authentication"""
        url = '/api/v1/processes/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_processes_only_own(self):
        """Test that users only see their own processes"""
        # Create process for other user
        Process.objects.create(
            user=self.other_user,
            title='Other Process',
            unique_slug='other-process',
            visibility='public'
        )
        
        url = '/api/v1/processes/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # Only own process

    # ========================================================================
    # CREATE PROCESS
    # ========================================================================

    def test_create_process_success(self):
        """Test creating a new process"""
        url = '/api/v1/processes/'
        data = {
            'title': 'New Process',
            'description': 'A new process',
            'category': str(self.category.id),
            'visibility': 'public',
            'process_type': 'linear',
            'is_active': True,
            'settings': {'allow_save_progress': True}
        }
        
        response = self.client.post(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Process')
        self.assertIn('unique_slug', response.data)
        self.assertTrue(Process.objects.filter(title='New Process').exists())

    def test_create_process_with_slug(self):
        """Test creating process with custom slug"""
        url = '/api/v1/processes/'
        data = {
            'title': 'Custom Slug Process',
            'unique_slug': 'custom-slug-process',
            'visibility': 'public',
            'process_type': 'linear'
        }
        
        response = self.client.post(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['unique_slug'], 'custom-slug-process')

    def test_create_process_private_with_password(self):
        """Test creating private process with password"""
        url = '/api/v1/processes/'
        data = {
            'title': 'Private Process',
            'visibility': 'private',
            'access_password': 'secret123',
            'process_type': 'linear'
        }
        
        response = self.client.post(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        process = Process.objects.get(unique_slug=response.data['unique_slug'])
        self.assertEqual(process.visibility, 'private')
        self.assertIsNotNone(process.access_password)

    def test_create_process_private_without_password(self):
        """Test creating private process without password fails"""
        url = '/api/v1/processes/'
        data = {
            'title': 'Private Process',
            'visibility': 'private',
            'process_type': 'linear'
        }
        
        response = self.client.post(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('access_password', response.data)

    def test_create_process_duplicate_slug(self):
        """Test creating process with duplicate slug fails"""
        url = '/api/v1/processes/'
        data = {
            'title': 'Duplicate Slug',
            'unique_slug': 'employee-onboarding-2024',  # Already exists
            'visibility': 'public',
            'process_type': 'linear'
        }
        
        response = self.client.post(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_process_invalid_category(self):
        """Test creating process with category from another user fails"""
        other_category = Category.objects.create(
            user=self.other_user,
            name='Other Category',
            color='#000000'
        )
        
        url = '/api/v1/processes/'
        data = {
            'title': 'New Process',
            'category': str(other_category.id),
            'visibility': 'public',
            'process_type': 'linear'
        }
        
        response = self.client.post(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data)

    def test_create_process_unauthenticated(self):
        """Test creating process without authentication"""
        url = '/api/v1/processes/'
        data = {
            'title': 'New Process',
            'visibility': 'public',
            'process_type': 'linear'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ========================================================================
    # RETRIEVE PROCESS
    # ========================================================================

    def test_retrieve_process_success(self):
        """Test retrieving process details"""
        url = f'/api/v1/processes/{self.process.unique_slug}/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Employee Onboarding')
        self.assertIn('steps', response.data)
        self.assertIn('id', response.data)

    def test_retrieve_process_not_found(self):
        """Test retrieving non-existent process"""
        url = '/api/v1/processes/non-existent-process/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_process_other_user(self):
        """Test retrieving process from another user fails"""
        other_process = Process.objects.create(
            user=self.other_user,
            title='Other Process',
            unique_slug='other-process'
        )
        
        url = f'/api/v1/processes/{other_process.unique_slug}/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_process_unauthenticated(self):
        """Test retrieving process without authentication"""
        url = f'/api/v1/processes/{self.process.unique_slug}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ========================================================================
    # UPDATE PROCESS
    # ========================================================================

    def test_update_process_success(self):
        """Test updating process"""
        url = f'/api/v1/processes/{self.process.unique_slug}/'
        data = {
            'title': 'Updated Process Title',
            'description': 'Updated description'
        }
        
        response = self.client.patch(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Process Title')
        self.process.refresh_from_db()
        self.assertEqual(self.process.title, 'Updated Process Title')

    def test_update_process_change_visibility(self):
        """Test updating process visibility"""
        url = f'/api/v1/processes/{self.process.unique_slug}/'
        data = {
            'visibility': 'private',
            'access_password': 'newpassword123'
        }
        
        response = self.client.patch(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.process.refresh_from_db()
        self.assertEqual(self.process.visibility, 'private')

    def test_update_process_not_owner(self):
        """Test updating process user doesn't own"""
        other_process = Process.objects.create(
            user=self.other_user,
            title='Other Process',
            unique_slug='other-process'
        )
        
        url = f'/api/v1/processes/{other_process.unique_slug}/'
        data = {'title': 'Hacked Title'}
        
        response = self.client.patch(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ========================================================================
    # DELETE PROCESS
    # ========================================================================

    def test_delete_process_success(self):
        """Test deleting process"""
        url = f'/api/v1/processes/{self.process.unique_slug}/'
        response = self.client.delete(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Process.objects.filter(id=self.process.id).exists())

    def test_delete_process_not_owner(self):
        """Test deleting process user doesn't own"""
        other_process = Process.objects.create(
            user=self.other_user,
            title='Other Process',
            unique_slug='other-process'
        )
        
        url = f'/api/v1/processes/{other_process.unique_slug}/'
        response = self.client.delete(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Process.objects.filter(id=other_process.id).exists())

    # ========================================================================
    # DUPLICATE PROCESS
    # ========================================================================

    def test_duplicate_process_success(self):
        """Test duplicating a process"""
        # Add some steps
        form = Form.objects.create(
            user=self.user,
            title='Test Form',
            unique_slug='test-form'
        )
        ProcessStep.objects.create(
            process=self.process,
            form=form,
            title='Step 1',
            order_index=0
        )
        
        url = f'/api/v1/processes/{self.process.unique_slug}/duplicate/'
        response = self.client.post(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('Copy', response.data['title'])
        self.assertNotEqual(response.data['unique_slug'], self.process.unique_slug)
        
        # Check that steps were duplicated
        duplicated_process = Process.objects.get(unique_slug=response.data['unique_slug'])
        self.assertEqual(duplicated_process.steps.count(), 1)

    def test_duplicate_process_not_owner(self):
        """Test duplicating process user doesn't own"""
        other_process = Process.objects.create(
            user=self.other_user,
            title='Other Process',
            unique_slug='other-process'
        )
        
        url = f'/api/v1/processes/{other_process.unique_slug}/duplicate/'
        response = self.client.post(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ========================================================================
    # PUBLISH PROCESS
    # ========================================================================

    def test_publish_process_success(self):
        """Test publishing a process"""
        url = f'/api/v1/processes/{self.process.unique_slug}/publish/'
        data = {'is_published': True}
        
        response = self.client.patch(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.process.refresh_from_db()
        self.assertIsNotNone(self.process.published_at)

    def test_unpublish_process_success(self):
        """Test unpublishing a process"""
        # First publish it
        from django.utils import timezone
        self.process.published_at = timezone.now()
        self.process.save()
        
        url = f'/api/v1/processes/{self.process.unique_slug}/publish/'
        data = {'is_published': False}
        
        response = self.client.patch(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.process.refresh_from_db()
        self.assertIsNone(self.process.published_at)


class ProcessStepAPITestCase(APITestCase):
    """Test cases for ProcessStep API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )
        
        self.other_user = User.objects.create_user(
            email='other@example.com',
            first_name='Jane',
            last_name='Smith',
            password='testpass123'
        )
        
        self.process = Process.objects.create(
            user=self.user,
            title='Test Process',
            unique_slug='test-process',
            visibility='public',
            process_type='linear'
        )
        
        self.other_process = Process.objects.create(
            user=self.other_user,
            title='Other Process',
            unique_slug='other-process'
        )
        
        self.form = Form.objects.create(
            user=self.user,
            title='Test Form',
            unique_slug='test-form'
        )
        
        self.step = ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            title='Step 1',
            description='First step',
            order_index=0,
            is_required=True
        )
        
        # Get JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.auth_header = f'Bearer {self.token}'

    # ========================================================================
    # LIST STEPS
    # ========================================================================

    def test_list_steps_success(self):
        """Test listing all steps in a process"""
        url = f'/api/v1/processes/{self.process.unique_slug}/steps/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Step 1')

    def test_list_steps_unauthenticated(self):
        """Test listing steps without authentication"""
        url = f'/api/v1/processes/{self.process.unique_slug}/steps/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_steps_other_user_process(self):
        """Test listing steps from another user's process"""
        url = f'/api/v1/processes/{self.other_process.unique_slug}/steps/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ========================================================================
    # CREATE STEP
    # ========================================================================

    def test_create_step_success(self):
        """Test creating a new step"""
        url = f'/api/v1/processes/{self.process.unique_slug}/steps/'
        data = {
            'form': str(self.form.id),
            'title': 'Step 2',
            'description': 'Second step',
            'order_index': 1,
            'is_required': True
        }
        
        response = self.client.post(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Step 2')
        self.assertTrue(ProcessStep.objects.filter(title='Step 2').exists())

    def test_create_step_auto_order_index(self):
        """Test creating step without order_index assigns automatically"""
        url = f'/api/v1/processes/{self.process.unique_slug}/steps/'
        data = {
            'form': str(self.form.id),
            'title': 'Step 2'
        }
        
        response = self.client.post(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('order_index', response.data)

    def test_create_step_other_user_process(self):
        """Test creating step in another user's process fails"""
        url = f'/api/v1/processes/{self.other_process.unique_slug}/steps/'
        data = {
            'form': str(self.form.id),
            'title': 'Step 1'
        }
        
        response = self.client.post(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_step_missing_title(self):
        """Test creating step without title fails"""
        url = f'/api/v1/processes/{self.process.unique_slug}/steps/'
        data = {
            'form': str(self.form.id)
        }
        
        response = self.client.post(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ========================================================================
    # RETRIEVE STEP
    # ========================================================================

    def test_retrieve_step_success(self):
        """Test retrieving step details"""
        url = f'/api/v1/processes/{self.process.unique_slug}/steps/{self.step.id}/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Step 1')
        self.assertEqual(response.data['description'], 'First step')

    def test_retrieve_step_not_found(self):
        """Test retrieving non-existent step"""
        url = f'/api/v1/processes/{self.process.unique_slug}/steps/{uuid.uuid4()}/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ========================================================================
    # UPDATE STEP
    # ========================================================================

    def test_update_step_success(self):
        """Test updating step"""
        url = f'/api/v1/processes/{self.process.unique_slug}/steps/{self.step.id}/'
        data = {
            'title': 'Updated Step Title',
            'description': 'Updated description'
        }
        
        response = self.client.patch(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Step Title')
        self.step.refresh_from_db()
        self.assertEqual(self.step.title, 'Updated Step Title')

    def test_update_step_change_order_index(self):
        """Test updating step order_index"""
        # Create another step
        step2 = ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            title='Step 2',
            order_index=1
        )
        
        url = f'/api/v1/processes/{self.process.unique_slug}/steps/{step2.id}/'
        data = {'order_index': 0}
        
        response = self.client.patch(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        step2.refresh_from_db()
        self.assertEqual(step2.order_index, 0)

    # ========================================================================
    # DELETE STEP
    # ========================================================================

    def test_delete_step_success(self):
        """Test deleting step"""
        url = f'/api/v1/processes/{self.process.unique_slug}/steps/{self.step.id}/'
        response = self.client.delete(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProcessStep.objects.filter(id=self.step.id).exists())

    def test_delete_step_other_user_process(self):
        """Test deleting step from another user's process fails"""
        other_step = ProcessStep.objects.create(
            process=self.other_process,
            form=self.form,
            title='Other Step',
            order_index=0
        )
        
        url = f'/api/v1/processes/{self.other_process.unique_slug}/steps/{other_step.id}/'
        response = self.client.delete(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(ProcessStep.objects.filter(id=other_step.id).exists())

    # ========================================================================
    # REORDER STEPS
    # ========================================================================

    def test_reorder_steps_success(self):
        """Test reordering steps"""
        # Create more steps
        step2 = ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            title='Step 2',
            order_index=1
        )
        step3 = ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            title='Step 3',
            order_index=2
        )
        
        url = f'/api/v1/processes/{self.process.unique_slug}/steps/reorder/'
        # Reorder: step3, step1, step2
        data = {
            'step_ids': [
                str(step3.id),
                str(self.step.id),
                str(step2.id)
            ]
        }
        
        response = self.client.post(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify new order
        step3.refresh_from_db()
        self.step.refresh_from_db()
        step2.refresh_from_db()
        self.assertEqual(step3.order_index, 0)
        self.assertEqual(self.step.order_index, 1)
        self.assertEqual(step2.order_index, 2)

    def test_reorder_steps_duplicate_ids(self):
        """Test reordering with duplicate step IDs fails"""
        step2 = ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            title='Step 2',
            order_index=1
        )
        
        url = f'/api/v1/processes/{self.process.unique_slug}/steps/reorder/'
        data = {
            'step_ids': [
                str(self.step.id),
                str(step2.id),
                str(self.step.id)  # Duplicate
            ]
        }
        
        response = self.client.post(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reorder_steps_from_other_process(self):
        """Test reordering steps from another process fails"""
        other_step = ProcessStep.objects.create(
            process=self.other_process,
            form=self.form,
            title='Other Step',
            order_index=0
        )
        
        url = f'/api/v1/processes/{self.process.unique_slug}/steps/reorder/'
        data = {
            'step_ids': [
                str(self.step.id),
                str(other_step.id)  # From different process
            ]
        }
        
        response = self.client.post(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reorder_steps_empty_list(self):
        """Test reordering with empty list fails"""
        url = f'/api/v1/processes/{self.process.unique_slug}/steps/reorder/'
        data = {'step_ids': []}
        
        response = self.client.post(
            url,
            data,
            format='json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
