import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from processes.models import Process, ProcessStep
from forms.models import Form
from submissions.models import ProcessProgress
from analytics.models import ProcessView
from processes.repository import ProcessProgressRepository, ProcessStepCompletionRepository

User = get_user_model()


class ProcessAnalyticsAPITestCase(APITestCase):
    """Test cases for Process Analytics API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            email='owner@example.com',
            first_name='Owner',
            last_name='User',
            password='testpass123'
        )
        
        self.other_user = User.objects.create_user(
            email='other@example.com',
            first_name='Other',
            last_name='User',
            password='testpass123'
        )
        
        self.form1 = Form.objects.create(
            user=self.owner,
            title='Step 1 Form',
            unique_slug='step-1-form',
            is_active=True
        )
        
        self.form2 = Form.objects.create(
            user=self.owner,
            title='Step 2 Form',
            unique_slug='step-2-form',
            is_active=True
        )
        
        self.form3 = Form.objects.create(
            user=self.owner,
            title='Step 3 Form',
            unique_slug='step-3-form',
            is_active=True
        )
        
        self.process = Process.objects.create(
            user=self.owner,
            title='Test Analytics Process',
            description='Process for testing analytics',
            unique_slug='test-analytics-process',
            visibility='public',
            process_type='linear',
            is_active=True
        )
        
        self.other_process = Process.objects.create(
            user=self.other_user,
            title='Other Process',
            unique_slug='other-process',
            visibility='public',
            process_type='linear',
            is_active=True
        )
        
        self.step1 = ProcessStep.objects.create(
            process=self.process,
            form=self.form1,
            title='Step 1',
            order_index=0,
            is_required=True
        )
        
        self.step2 = ProcessStep.objects.create(
            process=self.process,
            form=self.form2,
            title='Step 2',
            order_index=1,
            is_required=True
        )
        
        self.step3 = ProcessStep.objects.create(
            process=self.process,
            form=self.form3,
            title='Step 3',
            order_index=2,
            is_required=False
        )
        
        self.progress_repo = ProcessProgressRepository()
        self.completion_repo = ProcessStepCompletionRepository()
        
        refresh = RefreshToken.for_user(self.owner)
        self.token = str(refresh.access_token)
        self.auth_header = f'Bearer {self.token}'
        
    def test_analytics_overview_success(self):
        """Test getting analytics overview"""
        ProcessView.objects.create(
            process=self.process,
            session_id='session-1'
        )
        
        progress = self.progress_repo.create(
            process=self.process,
            session_id='session-1',
            status='completed'
        )
        
        url = f'/api/v1/processes/{self.process.unique_slug}/analytics/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_views'], 1)
        self.assertEqual(response.data['total_started'], 1)
        self.assertEqual(response.data['total_completed'], 1)
        self.assertEqual(response.data['completion_rate'], 100.0)
        
    def test_analytics_overview_not_owner(self):
        """Test getting analytics for process user doesn't own"""
        url = f'/api/v1/processes/{self.other_process.unique_slug}/analytics/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_analytics_overview_unauthenticated(self):
        """Test getting analytics without authentication"""
        url = f'/api/v1/processes/{self.process.unique_slug}/analytics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_analytics_views_over_time_success(self):
        """Test getting views over time"""
        ProcessView.objects.create(
            process=self.process,
            session_id='session-1',
            viewed_at=timezone.now()
        )
        
        ProcessView.objects.create(
            process=self.process,
            session_id='session-2',
            viewed_at=timezone.now() - timedelta(days=5)
        )
        
        url = f'/api/v1/processes/{self.process.unique_slug}/analytics/views/?days=30'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_views'], 2)
        self.assertIn('views_by_date', response.data)
        
    def test_analytics_views_invalid_days(self):
        """Test views endpoint with invalid days parameter"""
        url = f'/api/v1/processes/{self.process.unique_slug}/analytics/views/?days=400'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_analytics_completions_over_time_success(self):
        """Test getting completions over time"""
        progress1 = self.progress_repo.create(
            process=self.process,
            session_id='session-1',
            status='completed'
        )
        progress1.completed_at = timezone.now()
        progress1.save()
        
        progress2 = self.progress_repo.create(
            process=self.process,
            session_id='session-2',
            status='completed'
        )
        progress2.completed_at = timezone.now() - timedelta(days=3)
        progress2.save()
        
        url = f'/api/v1/processes/{self.process.unique_slug}/analytics/completions/?days=30'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_completions'], 2)
        self.assertIn('completions_by_date', response.data)
        
    def test_analytics_completion_rate_success(self):
        """Test getting completion rate"""
        self.progress_repo.create(
            process=self.process,
            session_id='session-1',
            status='completed'
        )
        
        self.progress_repo.create(
            process=self.process,
            session_id='session-2',
            status='in_progress'
        )
        
        self.progress_repo.create(
            process=self.process,
            session_id='session-3',
            status='abandoned'
        )
        
        url = f'/api/v1/processes/{self.process.unique_slug}/analytics/completion-rate/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_started'], 3)
        self.assertEqual(response.data['total_completed'], 1)
        self.assertEqual(response.data['total_abandoned'], 1)
        self.assertAlmostEqual(response.data['completion_rate'], 33.33, places=1)
        
    def test_analytics_step_drop_off_success(self):
        """Test getting step drop-off analysis"""
        progress1 = self.progress_repo.create(
            process=self.process,
            session_id='session-1',
            status='completed'
        )
        
        progress2 = self.progress_repo.create(
            process=self.process,
            session_id='session-2',
            status='in_progress'
        )
        
        completion1_1 = self.completion_repo.create(progress=progress1, step=self.step1, status='completed')
        completion1_2 = self.completion_repo.create(progress=progress1, step=self.step2, status='completed')
        completion1_3 = self.completion_repo.create(progress=progress1, step=self.step3, status='completed')
        
        completion2_1 = self.completion_repo.create(progress=progress2, step=self.step1, status='completed')
        completion2_2 = self.completion_repo.create(progress=progress2, step=self.step2, status='pending')
        
        url = f'/api/v1/processes/{self.process.unique_slug}/analytics/step-drop-off/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_started'], 2)
        self.assertEqual(len(response.data['steps_drop_off']), 3)
        
    def test_analytics_average_time_success(self):
        """Test getting average completion time"""
        progress1 = self.progress_repo.create(
            process=self.process,
            session_id='session-1',
            status='completed'
        )
        progress1.started_at = timezone.now() - timedelta(minutes=30)
        progress1.completed_at = timezone.now()
        progress1.save()
        
        progress2 = self.progress_repo.create(
            process=self.process,
            session_id='session-2',
            status='completed'
        )
        progress2.started_at = timezone.now() - timedelta(minutes=60)
        progress2.completed_at = timezone.now()
        progress2.save()
        
        url = f'/api/v1/processes/{self.process.unique_slug}/analytics/average-time/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['average_time_minutes'])
        self.assertAlmostEqual(response.data['average_time_minutes'], 45.0, places=0)
        self.assertEqual(response.data['sample_size'], 2)
        
    def test_analytics_average_time_no_completions(self):
        """Test getting average time with no completed processes"""
        url = f'/api/v1/processes/{self.process.unique_slug}/analytics/average-time/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['average_time_minutes'])
        self.assertEqual(response.data['sample_size'], 0)
        
    def test_list_progress_success(self):
        """Test listing all progress records"""
        self.progress_repo.create(
            process=self.process,
            session_id='session-1',
            status='completed'
        )
        
        self.progress_repo.create(
            process=self.process,
            session_id='session-2',
            status='in_progress'
        )
        
        url = f'/api/v1/processes/{self.process.unique_slug}/progress/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        
    def test_list_progress_filter_by_status(self):
        """Test filtering progress by status"""
        self.progress_repo.create(
            process=self.process,
            session_id='session-1',
            status='completed'
        )
        
        self.progress_repo.create(
            process=self.process,
            session_id='session-2',
            status='in_progress'
        )
        
        url = f'/api/v1/processes/{self.process.unique_slug}/progress/?status=completed'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['status'], 'completed')
        
    def test_list_progress_invalid_status(self):
        """Test filtering with invalid status"""
        url = f'/api/v1/processes/{self.process.unique_slug}/progress/?status=invalid'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_get_progress_details_success(self):
        """Test getting specific progress details"""
        progress = self.progress_repo.create(
            process=self.process,
            session_id='session-1',
            status='completed'
        )
        
        completion1 = self.completion_repo.create(progress=progress, step=self.step1, status='completed')
        completion2 = self.completion_repo.create(progress=progress, step=self.step2, status='completed')
        
        url = f'/api/v1/processes/{self.process.unique_slug}/progress/{progress.id}/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(progress.id))
        self.assertEqual(len(response.data['step_completions']), 2)
        
    def test_get_progress_details_not_found(self):
        """Test getting non-existent progress"""
        url = f'/api/v1/processes/{self.process.unique_slug}/progress/{uuid.uuid4()}/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_get_progress_details_wrong_process(self):
        """Test getting progress from different process"""
        other_progress = self.progress_repo.create(
            process=self.other_process,
            session_id='session-1',
            status='completed'
        )
        
        url = f'/api/v1/processes/{self.process.unique_slug}/progress/{other_progress.id}/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_list_abandoned_progress_success(self):
        """Test listing abandoned progress"""
        abandoned1 = self.progress_repo.create(
            process=self.process,
            session_id='session-1',
            status='abandoned'
        )
        abandoned1.last_activity_at = timezone.now() - timedelta(hours=10)
        abandoned1.save()
        
        abandoned2 = self.progress_repo.create(
            process=self.process,
            session_id='session-2',
            status='abandoned'
        )
        abandoned2.last_activity_at = timezone.now() - timedelta(hours=5)
        abandoned2.save()
        
        url = f'/api/v1/processes/{self.process.unique_slug}/progress/abandoned/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertIsNotNone(response.data['results'][0]['hours_inactive'])

