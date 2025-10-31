from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from forms.models import Form
from processes.models import Process
from submissions.models import FormSubmission
from analytics.models import FormView
from categories.models import Category

User = get_user_model()


class DashboardEndpointsTestCase(APITestCase):
    """Test cases for Dashboard endpoints"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create forms for the user
        self.form1 = Form.objects.create(
            user=self.user,
            title='Test Form 1',
            description='Description 1',
            unique_slug='test-form-1'
        )
        
        self.form2 = Form.objects.create(
            user=self.user,
            title='Test Form 2',
            description='Description 2',
            unique_slug='test-form-2'
        )
        
        # Create processes for the user
        self.process1 = Process.objects.create(
            user=self.user,
            title='Test Process 1',
            description='Process Description 1',
            unique_slug='test-process-1'
        )
        
        # Create form views
        FormView.objects.create(
            form=self.form1,
            session_id='session-1'
        )
        FormView.objects.create(
            form=self.form2,
            session_id='session-2'
        )
        
        # Create form submissions
        FormSubmission.objects.create(
            form=self.form1,
            status='submitted',
            session_id='session-1'
        )
        FormSubmission.objects.create(
            form=self.form1,
            status='draft',
            session_id='session-3'
        )

    def test_dashboard_overview_authenticated(self):
        """Test dashboard overview endpoint with authentication"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/dashboard/overview/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_forms'], 2)
        self.assertEqual(response.data['total_processes'], 1)
        self.assertEqual(response.data['total_submissions'], 1)  # Only submitted
        self.assertEqual(response.data['total_views'], 2)
        self.assertEqual(response.data['completion_rate'], 50.0)  # 1 submission / 2 views
        self.assertIn('total_forms', response.data)
        self.assertIn('total_processes', response.data)
        self.assertIn('total_submissions', response.data)
        self.assertIn('total_views', response.data)
        self.assertIn('completion_rate', response.data)

    def test_dashboard_overview_unauthenticated(self):
        """Test dashboard overview endpoint without authentication"""
        url = '/api/v1/dashboard/overview/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_statistics_authenticated(self):
        """Test dashboard statistics endpoint with authentication"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/dashboard/statistics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_forms'], 2)
        self.assertEqual(response.data['total_processes'], 1)
        self.assertEqual(response.data['total_submissions'], 1)
        self.assertEqual(response.data['total_views'], 2)
        self.assertEqual(response.data['completion_rate'], 50.0)

    def test_dashboard_statistics_unauthenticated(self):
        """Test dashboard statistics endpoint without authentication"""
        url = '/api/v1/dashboard/statistics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_statistics_empty_user(self):
        """Test dashboard statistics for user with no data"""
        new_user = User.objects.create_user(
            email='newuser@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=new_user)
        url = '/api/v1/dashboard/statistics/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_forms'], 0)
        self.assertEqual(response.data['total_processes'], 0)
        self.assertEqual(response.data['total_submissions'], 0)
        self.assertEqual(response.data['total_views'], 0)
        self.assertEqual(response.data['completion_rate'], 0.0)

    def test_dashboard_recent_activity_authenticated(self):
        """Test dashboard recent activity endpoint with authentication"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/dashboard/recent-activity/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response from ListAPIView
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
        
        self.assertIsInstance(results, list)
        # Should return up to 5 most recent items
        self.assertLessEqual(len(results), 5)
        
        # Check structure of returned items
        if len(results) > 0:
            item = results[0]
            self.assertIn('type', item)
            self.assertIn('title', item)
            self.assertIn('unique_slug', item)
            self.assertIn('updated_at', item)
            self.assertIn(item['type'], ['form', 'process'])

    def test_dashboard_recent_activity_unauthenticated(self):
        """Test dashboard recent activity endpoint without authentication"""
        url = '/api/v1/dashboard/recent-activity/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SearchEndpointsTestCase(APITestCase):
    """Test cases for Search endpoints"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        
        # Create forms for the user
        self.form1 = Form.objects.create(
            user=self.user,
            title='Survey Form',
            description='A survey about products',
            unique_slug='survey-form'
        )
        
        self.form2 = Form.objects.create(
            user=self.user,
            title='Feedback Form',
            description='Feedback collection',
            unique_slug='feedback-form'
        )
        
        # Create form for other user (should not appear in search)
        self.other_form = Form.objects.create(
            user=self.other_user,
            title='Other Survey',
            description='Should not appear',
            unique_slug='other-survey'
        )
        
        # Create processes for the user
        self.process1 = Process.objects.create(
            user=self.user,
            title='Onboarding Process',
            description='Employee onboarding workflow',
            unique_slug='onboarding-process'
        )
        
        self.process2 = Process.objects.create(
            user=self.user,
            title='Approval Process',
            description='Document approval workflow',
            unique_slug='approval-process'
        )
        
        # Create process for other user
        self.other_process = Process.objects.create(
            user=self.other_user,
            title='Other Process',
            description='Should not appear',
            unique_slug='other-process'
        )

    def test_global_search_success(self):
        """Test global search endpoint with valid query"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/search/'
        response = self.client.get(url, {'search': 'Form'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('forms', response.data)
        self.assertIn('processes', response.data)
        
        # Should find forms containing "Form" in title
        self.assertGreaterEqual(len(response.data['forms']), 2)
        # Should not find other user's forms
        form_slugs = [f['unique_slug'] for f in response.data['forms']]
        self.assertNotIn('other-survey', form_slugs)

    def test_global_search_missing_query(self):
        """Test global search endpoint without query parameter"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/search/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_global_search_unauthenticated(self):
        """Test global search endpoint without authentication"""
        url = '/api/v1/search/'
        response = self.client.get(url, {'search': 'test'})
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_global_search_no_results(self):
        """Test global search with query that matches nothing"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/search/'
        response = self.client.get(url, {'search': 'NonExistentQuery12345'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['forms']), 0)
        self.assertEqual(len(response.data['processes']), 0)

    def test_global_search_by_description(self):
        """Test global search by description"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/search/'
        response = self.client.get(url, {'search': 'products'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should find form with "products" in description
        form_titles = [f['title'] for f in response.data['forms']]
        self.assertIn('Survey Form', form_titles)

    def test_search_forms_success(self):
        """Test forms-only search endpoint"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/search/forms/'
        response = self.client.get(url, {'search': 'Form'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        # Handle paginated response if present
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
        
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 2)
        
        # Should only return forms, not processes
        for item in results:
            self.assertIn('title', item)
            self.assertIn('unique_slug', item)
            # Verify it's a form (has form-specific fields)
            self.assertIn('visibility', item)
            self.assertIn('fields_count', item)  # Should be included via SerializerMethodField

    def test_search_forms_missing_query(self):
        """Test forms search without query parameter"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/search/forms/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_search_forms_unauthenticated(self):
        """Test forms search without authentication"""
        url = '/api/v1/search/forms/'
        response = self.client.get(url, {'search': 'test'})
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_forms_user_isolation(self):
        """Test that forms search only returns current user's forms"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/search/forms/'
        response = self.client.get(url, {'search': 'Survey'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        form_slugs = [f['unique_slug'] for f in response.data]
        self.assertNotIn('other-survey', form_slugs)

    def test_search_processes_success(self):
        """Test processes-only search endpoint"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/search/processes/'
        response = self.client.get(url, {'search': 'Process'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 2)
        
        # Should only return processes
        for item in response.data:
            self.assertIn('title', item)
            self.assertIn('unique_slug', item)

    def test_search_processes_missing_query(self):
        """Test processes search without query parameter"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/search/processes/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_search_processes_unauthenticated(self):
        """Test processes search without authentication"""
        url = '/api/v1/search/processes/'
        response = self.client.get(url, {'search': 'test'})
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_processes_user_isolation(self):
        """Test that processes search only returns current user's processes"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/search/processes/'
        response = self.client.get(url, {'search': 'Process'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        process_slugs = [p['unique_slug'] for p in response.data]
        self.assertNotIn('other-process', process_slugs)

    def test_search_processes_by_slug(self):
        """Test processes search by unique slug"""
        self.client.force_authenticate(user=self.user)
        url = '/api/v1/search/processes/'
        response = self.client.get(url, {'search': 'onboarding'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        process_slugs = [p['unique_slug'] for p in response.data]
        self.assertIn('onboarding-process', process_slugs)

