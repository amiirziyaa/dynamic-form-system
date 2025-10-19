import uuid
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from analytics.models import FormView, ProcessView
from forms.models import Form
from processes.models import Process

User = get_user_model()


class FormViewModelTest(TestCase):
    """Test cases for FormView model according to database schema"""

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
        
        self.view_data = {
            'form': self.form,
            'session_id': 'test-session-123',
            'ip_address': '192.168.1.1',
            'metadata': {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'referer': 'https://google.com/search?q=survey',
                'language': 'en-US',
                'device_type': 'desktop',
                'browser': 'Chrome',
                'os': 'Windows'
            }
        }

    def test_view_creation(self):
        """Test basic view creation"""
        view = FormView.objects.create(**self.view_data)
        
        # Test primary key is UUID
        self.assertIsInstance(view.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(view.form, self.form)
        self.assertEqual(view.session_id, 'test-session-123')
        self.assertEqual(view.ip_address, '192.168.1.1')
        
        # Test JSON metadata
        self.assertIsInstance(view.metadata, dict)
        self.assertEqual(view.metadata['user_agent'], 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.assertEqual(view.metadata['device_type'], 'desktop')
        
        # Test timestamp
        self.assertIsNotNone(view.viewed_at)

    def test_view_optional_ip_address(self):
        """Test optional IP address field"""
        view = FormView.objects.create(
            form=self.form,
            session_id='test-session-no-ip'
        )
        self.assertIsNone(view.ip_address)

    def test_view_optional_metadata(self):
        """Test optional metadata field"""
        view = FormView.objects.create(
            form=self.form,
            session_id='test-session-no-metadata'
        )
        self.assertEqual(view.metadata, {})

    def test_view_string_representation(self):
        """Test string representation"""
        view = FormView.objects.create(**self.view_data)
        expected = f"View of Test Form at {view.viewed_at}"
        self.assertEqual(str(view), expected)

    def test_view_database_table_name(self):
        """Test database table name"""
        self.assertEqual(FormView._meta.db_table, 'form_view')

    def test_view_indexes(self):
        """Test that proper indexes are created"""
        indexes = [index.fields for index in FormView._meta.indexes]
        self.assertIn(['form', 'viewed_at'], indexes)

    def test_view_related_names(self):
        """Test related names for foreign key relationships"""
        view = FormView.objects.create(**self.view_data)
        
        # Test that related managers exist
        self.assertTrue(hasattr(view, 'form'))

    def test_view_cascade_delete(self):
        """Test cascade delete when form is deleted"""
        view = FormView.objects.create(**self.view_data)
        view_id = view.id
        
        # Delete form
        self.form.delete()
        
        # View should be deleted too
        self.assertFalse(FormView.objects.filter(id=view_id).exists())

    def test_view_ip_address_validation(self):
        """Test IP address validation"""
        # Test valid IPv4
        view = FormView.objects.create(
            form=self.form,
            session_id='test-ipv4',
            ip_address='192.168.1.1'
        )
        self.assertEqual(view.ip_address, '192.168.1.1')
        
        # Test valid IPv6
        view = FormView.objects.create(
            form=self.form,
            session_id='test-ipv6',
            ip_address='2001:0db8:85a3:0000:0000:8a2e:0370:7334'
        )
        self.assertEqual(view.ip_address, '2001:0db8:85a3:0000:0000:8a2e:0370:7334')

    def test_view_metadata_structure(self):
        """Test metadata structure for analytics"""
        metadata = {
            'user_agent': 'Mozilla/5.0...',
            'referer': 'https://google.com',
            'language': 'en-US',
            'device_type': 'mobile',
            'browser': 'Safari',
            'os': 'iOS',
            'screen_resolution': '375x667',
            'timezone': 'America/New_York'
        }
        
        view = FormView.objects.create(
            form=self.form,
            session_id='test-metadata',
            metadata=metadata
        )
        
        self.assertEqual(view.metadata['device_type'], 'mobile')
        self.assertEqual(view.metadata['browser'], 'Safari')
        self.assertEqual(view.metadata['os'], 'iOS')


class ProcessViewModelTest(TestCase):
    """Test cases for ProcessView model according to database schema"""

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
        
        self.view_data = {
            'process': self.process,
            'session_id': 'test-session-123',
            'ip_address': '192.168.1.1',
            'metadata': {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'referer': 'https://company.com/onboarding',
                'language': 'en-US',
                'device_type': 'desktop',
                'browser': 'Chrome',
                'os': 'macOS'
            }
        }

    def test_view_creation(self):
        """Test basic view creation"""
        view = ProcessView.objects.create(**self.view_data)
        
        # Test primary key is UUID
        self.assertIsInstance(view.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(view.process, self.process)
        self.assertEqual(view.session_id, 'test-session-123')
        self.assertEqual(view.ip_address, '192.168.1.1')
        
        # Test JSON metadata
        self.assertIsInstance(view.metadata, dict)
        self.assertEqual(view.metadata['user_agent'], 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        self.assertEqual(view.metadata['device_type'], 'desktop')
        
        # Test timestamp
        self.assertIsNotNone(view.viewed_at)

    def test_view_optional_ip_address(self):
        """Test optional IP address field"""
        view = ProcessView.objects.create(
            process=self.process,
            session_id='test-session-no-ip'
        )
        self.assertIsNone(view.ip_address)

    def test_view_optional_metadata(self):
        """Test optional metadata field"""
        view = ProcessView.objects.create(
            process=self.process,
            session_id='test-session-no-metadata'
        )
        self.assertEqual(view.metadata, {})

    def test_view_string_representation(self):
        """Test string representation"""
        view = ProcessView.objects.create(**self.view_data)
        expected = f"View of Test Process at {view.viewed_at}"
        self.assertEqual(str(view), expected)

    def test_view_database_table_name(self):
        """Test database table name"""
        self.assertEqual(ProcessView._meta.db_table, 'process_view')

    def test_view_indexes(self):
        """Test that proper indexes are created"""
        indexes = [index.fields for index in ProcessView._meta.indexes]
        self.assertIn(['process', 'viewed_at'], indexes)

    def test_view_related_names(self):
        """Test related names for foreign key relationships"""
        view = ProcessView.objects.create(**self.view_data)
        
        # Test that related managers exist
        self.assertTrue(hasattr(view, 'process'))

    def test_view_cascade_delete(self):
        """Test cascade delete when process is deleted"""
        view = ProcessView.objects.create(**self.view_data)
        view_id = view.id
        
        # Delete process
        self.process.delete()
        
        # View should be deleted too
        self.assertFalse(ProcessView.objects.filter(id=view_id).exists())

    def test_view_consistency_with_form_view(self):
        """Test that ProcessView has same structure as FormView"""
        # Both should have same field structure
        form_view_fields = [field.name for field in FormView._meta.fields]
        process_view_fields = [field.name for field in ProcessView._meta.fields]
        
        # Remove the foreign key field names (form vs process)
        form_view_fields.remove('form')
        process_view_fields.remove('process')
        
        # All other fields should be the same
        self.assertEqual(set(form_view_fields), set(process_view_fields))

    def test_view_analytics_data_collection(self):
        """Test analytics data collection capabilities"""
        analytics_data = {
            'user_agent': 'Mozilla/5.0...',
            'referer': 'https://company.com/processes',
            'language': 'en-US',
            'device_type': 'tablet',
            'browser': 'Safari',
            'os': 'iPadOS',
            'screen_resolution': '1024x768',
            'timezone': 'Europe/London',
            'session_duration': 300,
            'pages_viewed': 3
        }
        
        view = ProcessView.objects.create(
            process=self.process,
            session_id='test-analytics',
            metadata=analytics_data
        )
        
        self.assertEqual(view.metadata['device_type'], 'tablet')
        self.assertEqual(view.metadata['session_duration'], 300)
        self.assertEqual(view.metadata['pages_viewed'], 3)