"""
Tests for Admin Reports and Webhooks endpoints
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from notifications.models import Webhook, ReportSchedule, ReportInstance
import json

User = get_user_model()


class WebhookViewSetTestCase(TestCase):
    """Tests for WebhookViewSet admin endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create regular user (should not have access)
        self.regular_user = User.objects.create_user(
            email='user@test.com',
            password='userpass123'
        )
        
        # Create test webhook
        self.webhook = Webhook.objects.create(
            user=self.admin_user,
            name='Test Webhook',
            url='https://example.com/webhook',
            events=['form.submission', 'process.completion'],
            is_active=True
        )

    def test_list_webhooks_admin(self):
        """Test admin can list webhooks"""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/v1/admin/webhooks/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertIsInstance(response.data['results'], list)
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertIsInstance(response.data, list)
            self.assertEqual(len(response.data), 1)

    def test_list_webhooks_unauthorized(self):
        """Test regular user cannot access webhooks"""
        self.client.force_authenticate(user=self.regular_user)
        url = '/api/v1/admin/webhooks/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_webhook(self):
        """Test creating a new webhook"""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/v1/admin/webhooks/'
        data = {
            'name': 'New Webhook',
            'url': 'https://example.com/new-webhook',
            'events': ['form.submission'],
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['url'], data['url'])
        self.assertTrue(Webhook.objects.filter(url=data['url']).exists())

    def test_get_webhook_detail(self):
        """Test retrieving webhook details"""
        self.client.force_authenticate(user=self.admin_user)
        url = f'/api/v1/admin/webhooks/{self.webhook.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['url'], self.webhook.url)

    def test_update_webhook(self):
        """Test updating webhook"""
        self.client.force_authenticate(user=self.admin_user)
        url = f'/api/v1/admin/webhooks/{self.webhook.id}/'
        data = {'url': 'https://example.com/updated-webhook'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.webhook.refresh_from_db()
        self.assertEqual(self.webhook.url, data['url'])

    def test_delete_webhook(self):
        """Test deleting webhook"""
        self.client.force_authenticate(user=self.admin_user)
        url = f'/api/v1/admin/webhooks/{self.webhook.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Webhook.objects.filter(id=self.webhook.id).exists())

    def test_test_webhook(self):
        """Test webhook test endpoint"""
        self.client.force_authenticate(user=self.admin_user)
        url = f'/api/v1/admin/webhooks/{self.webhook.id}/test/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'test_triggered')
        self.assertIn('message', response.data)


class ReportAdminViewSetTestCase(TestCase):
    """Tests for ReportAdminViewSet endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create test report schedule (is_active=False to avoid periodic task creation)
        # Use update_fields to bypass save() method that creates periodic tasks
        self.report_schedule = ReportSchedule.objects.create(
            name='Daily Submissions Report',
            target=self.admin_user,
            report_type='form_submissions',
            frequency='daily',
            output_format='csv',
            send_to_email='admin@test.com',  # Required by serializer validation
            is_active=False  # Set to False to avoid creating periodic task
        )
        # Delete any periodic task that was created
        from django_celery_beat.models import PeriodicTask
        if self.report_schedule.periodic_task:
            self.report_schedule.periodic_task.delete()
            self.report_schedule.periodic_task = None
            ReportSchedule.objects.filter(id=self.report_schedule.id).update(periodic_task=None)
        
        # Create test report instance
        self.report_instance = ReportInstance.objects.create(
            triggered_by=self.admin_user,
            report_type='form_submissions',
            status='completed',
            file_url='https://example.com/report.csv'
        )

    def test_list_report_configs(self):
        """Test listing report configurations"""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/v1/admin/reports/config/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertIsInstance(response.data['results'], list)
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertIsInstance(response.data, list)
            self.assertEqual(len(response.data), 1)

    def test_create_report_config(self):
        """Test creating report configuration"""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/v1/admin/reports/config/'
        data = {
            'name': 'Weekly Process Analytics',
            'report_type': 'process_completions',
            'frequency': 'weekly',
            'output_format': 'json',
            'send_to_email': 'admin@test.com',  # Required field
            'is_active': False  # Set False to avoid periodic task in tests
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check that report schedule was created
        self.assertTrue(ReportSchedule.objects.filter(
            report_type=data['report_type'],
            target=self.admin_user
        ).exists())

    def test_update_report_config(self):
        """Test updating report configuration"""
        self.client.force_authenticate(user=self.admin_user)
        url = f'/api/v1/admin/reports/{self.report_schedule.id}/config/'
        data = {'frequency': 'weekly'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.report_schedule.refresh_from_db()
        self.assertEqual(self.report_schedule.frequency, 'weekly')

    def test_delete_report_config(self):
        """Test deleting report configuration"""
        self.client.force_authenticate(user=self.admin_user)
        url = f'/api/v1/admin/reports/{self.report_schedule.id}/config/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ReportSchedule.objects.filter(id=self.report_schedule.id).exists())

    def test_generate_manual_report(self):
        """Test manual report generation"""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/v1/admin/reports/generate/'
        data = {
            'name': 'Manual Report',
            'report_type': 'form_submissions',
            'frequency': 'daily',  # Required field
            'output_format': 'csv',
            'send_to_email': 'admin@test.com'  # Required by serializer validation
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('instance_id', response.data)
        self.assertIn('message', response.data)
        instance_id = response.data['instance_id']
        self.assertTrue(ReportInstance.objects.filter(id=instance_id).exists())

    def test_list_report_history(self):
        """Test listing report history"""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/v1/admin/reports/history/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertIsInstance(response.data['results'], list)
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertIsInstance(response.data, list)
            self.assertEqual(len(response.data), 1)

    def test_download_report_completed(self):
        """Test downloading completed report"""
        self.client.force_authenticate(user=self.admin_user)
        url = f'/api/v1/admin/reports/{self.report_instance.id}/download/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('file_url', response.data)

    def test_download_report_pending(self):
        """Test downloading pending report"""
        pending_instance = ReportInstance.objects.create(
            triggered_by=self.admin_user,
            report_type='form_submissions',
            status='pending'
        )
        self.client.force_authenticate(user=self.admin_user)
        url = f'/api/v1/admin/reports/{pending_instance.id}/download/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_unauthorized_access(self):
        """Test that non-admin users cannot access reports"""
        regular_user = User.objects.create_user(
            email='user@test.com',
            password='userpass123'
        )
        self.client.force_authenticate(user=regular_user)
        url = '/api/v1/admin/reports/config/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

