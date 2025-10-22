import uuid
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from notifications.models import Notification, Webhook, NotificationLog

User = get_user_model()


class NotificationModelTest(TestCase):
    """Test cases for Notification model according to database schema"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )
        
        self.notification_data = {
            'user': self.user,
            'name': 'Form Submission Notification',
            'notification_type': 'email',
            'subject': 'New Form Submission',
            'message_template': 'Hello {{user_name}}, you have received a new form submission.',
            'is_active': True,
            'settings': {
                'from_email': 'noreply@example.com',
                'reply_to': 'support@example.com',
                'priority': 'normal'
            }
        }

    def test_notification_creation(self):
        """Test basic notification creation"""
        notification = Notification.objects.create(**self.notification_data)
        
        # Test primary key is UUID
        self.assertIsInstance(notification.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.name, 'Form Submission Notification')
        self.assertEqual(notification.notification_type, 'email')
        self.assertEqual(notification.subject, 'New Form Submission')
        self.assertEqual(notification.message_template, 'Hello {{user_name}}, you have received a new form submission.')
        self.assertTrue(notification.is_active)
        
        # Test JSON settings
        self.assertIsInstance(notification.settings, dict)
        self.assertEqual(notification.settings['from_email'], 'noreply@example.com')
        
        # Test timestamps
        self.assertIsNotNone(notification.created_at)
        self.assertIsNotNone(notification.updated_at)

    def test_notification_type_choices(self):
        """Test notification type choices"""
        types = ['email', 'sms', 'webhook', 'push']
        
        for notification_type in types:
            notification = Notification.objects.create(
                user=self.user,
                name=f'{notification_type.title()} Notification',
                notification_type=notification_type,
                message_template=f'Test {notification_type} message'
            )
            self.assertEqual(notification.notification_type, notification_type)

    def test_notification_optional_fields(self):
        """Test optional fields"""
        notification = Notification.objects.create(
            user=self.user,
            name='Simple Notification',
            notification_type='email',
            message_template='Simple message'
        )
        
        self.assertIsNone(notification.subject)
        self.assertTrue(notification.is_active)  # Default value
        self.assertEqual(notification.settings, {})

    def test_notification_is_active_default(self):
        """Test is_active default value"""
        notification = Notification.objects.create(
            user=self.user,
            name='Inactive Notification',
            notification_type='email',
            message_template='Test message',
            is_active=False
        )
        self.assertFalse(notification.is_active)

    def test_notification_string_representation(self):
        """Test string representation"""
        notification = Notification.objects.create(**self.notification_data)
        expected = "Form Submission Notification (email)"
        self.assertEqual(str(notification), expected)

    def test_notification_database_table_name(self):
        """Test database table name"""
        self.assertEqual(Notification._meta.db_table, 'notification')

    def test_notification_indexes(self):
        """Test that proper indexes are created"""
        indexes = [index.fields for index in Notification._meta.indexes]
        self.assertIn(['user'], indexes)
        self.assertIn(['notification_type'], indexes)

    def test_notification_related_names(self):
        """Test related names for foreign key relationships"""
        notification = Notification.objects.create(**self.notification_data)
        
        # Test that related managers exist
        self.assertTrue(hasattr(notification, 'logs'))

    def test_notification_cascade_delete(self):
        """Test cascade delete when user is deleted"""
        notification = Notification.objects.create(**self.notification_data)
        notification_id = notification.id
        
        # Delete user
        self.user.delete()
        
        # Notification should be deleted too
        self.assertFalse(Notification.objects.filter(id=notification_id).exists())

    def test_notification_template_variables(self):
        """Test message template with variables"""
        template = """
        Hello {{user_name}},
        
        You have received a new form submission for "{{form_title}}".
        
        Submission details:
        - Form: {{form_title}}
        - Submitted by: {{submitter_name}}
        - Date: {{submission_date}}
        
        Best regards,
        {{company_name}}
        """
        
        notification = Notification.objects.create(
            user=self.user,
            name='Template Test',
            notification_type='email',
            message_template=template
        )
        
        self.assertIn('{{user_name}}', notification.message_template)
        self.assertIn('{{form_title}}', notification.message_template)
        self.assertIn('{{submitter_name}}', notification.message_template)


class WebhookModelTest(TestCase):
    """Test cases for Webhook model according to database schema"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )
        
        self.webhook_data = {
            'user': self.user,
            'name': 'Form Submission Webhook',
            'url': 'https://api.example.com/webhooks/form-submission',
            'secret_key': 'webhook_secret_123',
            'is_active': True,
            'events': ['form.submitted', 'form.viewed', 'process.completed'],
            'settings': {
                'timeout': 30,
                'retry_attempts': 3,
                'headers': {
                    'Authorization': 'Bearer token123',
                    'Content-Type': 'application/json'
                }
            }
        }

    def test_webhook_creation(self):
        """Test basic webhook creation"""
        webhook = Webhook.objects.create(**self.webhook_data)
        
        # Test primary key is UUID
        self.assertIsInstance(webhook.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(webhook.user, self.user)
        self.assertEqual(webhook.name, 'Form Submission Webhook')
        self.assertEqual(webhook.url, 'https://api.example.com/webhooks/form-submission')
        self.assertEqual(webhook.secret_key, 'webhook_secret_123')
        self.assertTrue(webhook.is_active)
        
        # Test JSON fields
        self.assertIsInstance(webhook.events, list)
        self.assertIn('form.submitted', webhook.events)
        self.assertIsInstance(webhook.settings, dict)
        self.assertEqual(webhook.settings['timeout'], 30)
        
        # Test timestamps
        self.assertIsNotNone(webhook.created_at)
        self.assertIsNotNone(webhook.updated_at)

    def test_webhook_optional_secret_key(self):
        """Test optional secret key field"""
        webhook = Webhook.objects.create(
            user=self.user,
            name='Public Webhook',
            url='https://api.example.com/webhooks/public'
        )
        self.assertIsNone(webhook.secret_key)

    def test_webhook_optional_fields(self):
        """Test optional fields"""
        webhook = Webhook.objects.create(
            user=self.user,
            name='Simple Webhook',
            url='https://api.example.com/webhooks/simple'
        )
        
        self.assertTrue(webhook.is_active)  # Default value
        self.assertEqual(webhook.events, [])
        self.assertEqual(webhook.settings, {})

    def test_webhook_is_active_default(self):
        """Test is_active default value"""
        webhook = Webhook.objects.create(
            user=self.user,
            name='Inactive Webhook',
            url='https://api.example.com/webhooks/inactive',
            is_active=False
        )
        self.assertFalse(webhook.is_active)

    def test_webhook_string_representation(self):
        """Test string representation"""
        webhook = Webhook.objects.create(**self.webhook_data)
        expected = "Form Submission Webhook - https://api.example.com/webhooks/form-submission"
        self.assertEqual(str(webhook), expected)

    def test_webhook_database_table_name(self):
        """Test database table name"""
        self.assertEqual(Webhook._meta.db_table, 'webhook')

    def test_webhook_indexes(self):
        """Test that proper indexes are created"""
        indexes = [index.fields for index in Webhook._meta.indexes]
        self.assertIn(['user'], indexes)
        self.assertIn(['is_active'], indexes)

    def test_webhook_related_names(self):
        """Test related names for foreign key relationships"""
        webhook = Webhook.objects.create(**self.webhook_data)
        
        # Test that related managers exist
        self.assertTrue(hasattr(webhook, 'user'))

    def test_webhook_cascade_delete(self):
        """Test cascade delete when user is deleted"""
        webhook = Webhook.objects.create(**self.webhook_data)
        webhook_id = webhook.id
        
        # Delete user
        self.user.delete()
        
        # Webhook should be deleted too
        self.assertFalse(Webhook.objects.filter(id=webhook_id).exists())

    def test_webhook_events_validation(self):
        """Test webhook events list"""
        events = [
            'form.created',
            'form.updated',
            'form.deleted',
            'form.submitted',
            'form.viewed',
            'process.created',
            'process.updated',
            'process.completed',
            'user.registered',
            'user.login'
        ]
        
        webhook = Webhook.objects.create(
            user=self.user,
            name='Event Test Webhook',
            url='https://api.example.com/webhooks/events',
            events=events
        )
        
        self.assertEqual(len(webhook.events), 10)
        self.assertIn('form.submitted', webhook.events)
        self.assertIn('process.completed', webhook.events)


class NotificationLogModelTest(TestCase):
    """Test cases for NotificationLog model according to database schema"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )
        
        self.notification = Notification.objects.create(
            user=self.user,
            name='Test Notification',
            notification_type='email',
            message_template='Test message'
        )
        
        self.log_data = {
            'notification': self.notification,
            'recipient': 'test@example.com',
            'status': 'sent',
            'metadata': {
                'delivery_time': '2024-01-01T12:00:00Z',
                'message_id': 'msg_123456',
                'provider': 'sendgrid'
            }
        }

    def test_log_creation(self):
        """Test basic log creation"""
        log = NotificationLog.objects.create(**self.log_data)
        
        # Test primary key is UUID
        self.assertIsInstance(log.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(log.notification, self.notification)
        self.assertEqual(log.recipient, 'test@example.com')
        self.assertEqual(log.status, 'sent')
        
        # Test JSON metadata
        self.assertIsInstance(log.metadata, dict)
        self.assertEqual(log.metadata['message_id'], 'msg_123456')
        
        # Test timestamp
        self.assertIsNotNone(log.created_at)

    def test_log_status_choices(self):
        """Test status choices"""
        statuses = ['pending', 'sent', 'failed', 'delivered', 'bounced']
        
        for status in statuses:
            log = NotificationLog.objects.create(
                notification=self.notification,
                recipient=f'test-{status}@example.com',
                status=status
            )
            self.assertEqual(log.status, status)

    def test_log_optional_fields(self):
        """Test optional fields"""
        log = NotificationLog.objects.create(
            notification=self.notification,
            recipient='test@example.com',
            status='pending'
        )
        
        self.assertIsNone(log.error_message)
        self.assertEqual(log.metadata, {})
        self.assertIsNone(log.sent_at)
        self.assertIsNone(log.delivered_at)

    def test_log_string_representation(self):
        """Test string representation"""
        log = NotificationLog.objects.create(**self.log_data)
        expected = "Log for Test Notification to test@example.com - sent"
        self.assertEqual(str(log), expected)

    def test_log_database_table_name(self):
        """Test database table name"""
        self.assertEqual(NotificationLog._meta.db_table, 'notification_log')

    def test_log_indexes(self):
        """Test that proper indexes are created"""
        indexes = [index.fields for index in NotificationLog._meta.indexes]
        self.assertIn(['notification'], indexes)
        self.assertIn(['status'], indexes)
        self.assertIn(['created_at'], indexes)

    def test_log_related_names(self):
        """Test related names for foreign key relationships"""
        log = NotificationLog.objects.create(**self.log_data)
        
        # Test that related managers exist
        self.assertTrue(hasattr(log, 'notification'))

    def test_log_cascade_delete(self):
        """Test cascade delete when notification is deleted"""
        log = NotificationLog.objects.create(**self.log_data)
        log_id = log.id
        
        # Delete notification
        self.notification.delete()
        
        # Log should be deleted too
        self.assertFalse(NotificationLog.objects.filter(id=log_id).exists())

    def test_log_error_tracking(self):
        """Test error message tracking"""
        log = NotificationLog.objects.create(
            notification=self.notification,
            recipient='invalid@example.com',
            status='failed',
            error_message='Invalid email address format',
            metadata={
                'error_code': 'INVALID_EMAIL',
                'provider_error': 'The email address is not valid'
            }
        )
        
        self.assertEqual(log.status, 'failed')
        self.assertEqual(log.error_message, 'Invalid email address format')
        self.assertEqual(log.metadata['error_code'], 'INVALID_EMAIL')

    def test_log_delivery_tracking(self):
        """Test delivery tracking with timestamps"""
        from django.utils import timezone
        
        now = timezone.now()
        
        log = NotificationLog.objects.create(
            notification=self.notification,
            recipient='test@example.com',
            status='delivered',
            sent_at=now,
            delivered_at=now,
            metadata={
                'delivery_time_seconds': 2.5,
                'provider': 'sendgrid',
                'message_id': 'msg_789012'
            }
        )
        
        self.assertEqual(log.status, 'delivered')
        self.assertEqual(log.sent_at, now)
        self.assertEqual(log.delivered_at, now)
        self.assertEqual(log.metadata['delivery_time_seconds'], 2.5)