"""
Tests for WebSocket Analytics Consumer and Real-time Reports
"""
import json
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from analytics.consumers import AnalyticsConsumer
from forms.models import Form

User = get_user_model()


class AnalyticsConsumerTestCase(TestCase):
    """Tests for WebSocket Analytics Consumer structure and REST endpoints"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.form = Form.objects.create(
            user=self.user,
            title='Test Form',
            unique_slug='test-form-websocket',
            visibility='public'
        )

    def test_consumer_class_exists(self):
        """Test that AnalyticsConsumer class exists and has required methods"""
        self.assertTrue(hasattr(AnalyticsConsumer, 'connect'))
        self.assertTrue(hasattr(AnalyticsConsumer, 'disconnect'))
        self.assertTrue(hasattr(AnalyticsConsumer, 'receive'))
        self.assertTrue(hasattr(AnalyticsConsumer, 'report_update'))
        self.assertTrue(hasattr(AnalyticsConsumer, 'submission_update'))
        self.assertTrue(hasattr(AnalyticsConsumer, 'view_update'))
        self.assertTrue(hasattr(AnalyticsConsumer, 'can_access_report'))


class RealTimeReportEndpointTestCase(TestCase):
    """Tests for real-time report REST endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.form = Form.objects.create(
            user=self.user,
            title='Test Form',
            unique_slug='test-form-realtime',
            visibility='public'
        )

    def test_real_time_report_endpoint(self):
        """Test real-time report endpoint returns snapshot and WebSocket URL"""
        self.client.force_authenticate(user=self.user)
        url = f'/api/v1/forms/{self.form.unique_slug}/analytics/reports/real-time/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('websocket_url', response.data)
        self.assertIn('message', response.data)
        self.assertIn('ws://', response.data['websocket_url'])

    def test_real_time_report_unauthorized(self):
        """Test real-time report requires authentication"""
        url = f'/api/v1/forms/{self.form.unique_slug}/analytics/reports/real-time/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_real_time_report_non_owner(self):
        """Test real-time report requires form ownership"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        self.client.force_authenticate(user=other_user)
        url = f'/api/v1/forms/{self.form.unique_slug}/analytics/reports/real-time/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
