import uuid
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from submissions.models import FormSubmission, SubmissionAnswer
from forms.models import Form, FormField, FieldOption
from analytics.models import FormView

User = get_user_model()


# ============================================================================
# PUBLIC FORM API TESTS
# ============================================================================

class PublicFormAPITestCase(APITestCase):
    """Test cases for Public Form API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='owner@example.com',
            first_name='Owner',
            last_name='User',
            password='testpass123'
        )
        
        self.public_form = Form.objects.create(
            user=self.user,
            title='Public Survey Form',
            description='A public survey',
            unique_slug='public-survey',
            visibility='public',
            is_active=True
        )
        
        self.private_form = Form.objects.create(
            user=self.user,
            title='Private Form',
            description='A private form',
            unique_slug='private-form',
            visibility='private',
            access_password=make_password('secret123'),
            is_active=True
        )
        
        self.inactive_form = Form.objects.create(
            user=self.user,
            title='Inactive Form',
            unique_slug='inactive-form',
            visibility='public',
            is_active=False
        )
        
        self.field1 = FormField.objects.create(
            form=self.public_form,
            field_type='text',
            label='Full Name',
            is_required=True,
            order_index=0
        )
        
        self.field2 = FormField.objects.create(
            form=self.public_form,
            field_type='email',
            label='Email Address',
            is_required=True,
            order_index=1
        )
        
        self.field3 = FormField.objects.create(
            form=self.public_form,
            field_type='textarea',
            label='Comments',
            is_required=False,
            order_index=2
        )
        
        self.session_id = 'test-session-123'
        
    def test_get_public_form_success(self):
        """Test getting public form structure"""
        url = f'/api/v1/public/forms/{self.public_form.unique_slug}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Public Survey Form')
        self.assertEqual(response.data['unique_slug'], 'public-survey')
        self.assertFalse(response.data['is_password_protected'])
        self.assertEqual(len(response.data['fields']), 3)
        
    def test_get_public_form_private_without_password(self):
        """Test getting private form without password verification"""
        url = f'/api/v1/public/forms/{self.private_form.unique_slug}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.data['requires_password'])
        
    def test_get_public_form_private_with_password_verified(self):
        """Test getting private form after password verification"""
        url = f'/api/v1/public/forms/{self.private_form.unique_slug}/'
        
        session = self.client.session
        session[f'form_access_{self.private_form.id}'] = True
        session.save()
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('title', response.data)
        
    def test_get_public_form_not_found(self):
        """Test getting non-existent form"""
        url = '/api/v1/public/forms/non-existent-form/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_get_public_form_inactive(self):
        """Test getting inactive form"""
        url = f'/api/v1/public/forms/{self.inactive_form.unique_slug}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_verify_password_success(self):
        """Test successful password verification"""
        url = f'/api/v1/public/forms/{self.private_form.unique_slug}/verify-password/'
        data = {'password': 'secret123'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['access_granted'])
        
    def test_verify_password_invalid(self):
        """Test password verification with wrong password"""
        url = f'/api/v1/public/forms/{self.private_form.unique_slug}/verify-password/'
        data = {'password': 'wrongpassword'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_verify_password_public_form(self):
        """Test password verification for public form"""
        url = f'/api/v1/public/forms/{self.public_form.unique_slug}/verify-password/'
        data = {'password': 'secret123'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_track_view_success(self):
        """Test tracking form view"""
        url = f'/api/v1/public/forms/{self.public_form.unique_slug}/view/'
        data = {'session_id': self.session_id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        view = FormView.objects.filter(form=self.public_form, session_id=self.session_id).first()
        self.assertIsNotNone(view)
        
    def test_submit_form_success(self):
        """Test submitting a form"""
        url = f'/api/v1/public/forms/{self.public_form.unique_slug}/submit/'
        data = {
            'session_id': self.session_id,
            'answers': [
                {
                    'field_id': str(self.field1.id),
                    'text_value': 'John Doe'
                },
                {
                    'field_id': str(self.field2.id),
                    'text_value': 'john@example.com'
                },
                {
                    'field_id': str(self.field3.id),
                    'text_value': 'Great form!'
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('submission_id', response.data)
        
        submission = FormSubmission.objects.get(id=response.data['submission_id'])
        self.assertEqual(submission.status, 'submitted')
        self.assertEqual(submission.answers.count(), 3)
        self.assertIsNotNone(submission.submitted_at)
        
    def test_submit_form_missing_required_fields(self):
        """Test submitting form without required fields"""
        url = f'/api/v1/public/forms/{self.public_form.unique_slug}/submit/'
        data = {
            'session_id': self.session_id,
            'answers': [
                {
                    'field_id': str(self.field1.id),
                    'text_value': 'John Doe'
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_submit_form_private_without_password(self):
        """Test submitting private form without password verification"""
        url = f'/api/v1/public/forms/{self.private_form.unique_slug}/submit/'
        data = {
            'session_id': self.session_id,
            'answers': []
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_save_draft_success(self):
        """Test saving draft submission"""
        url = f'/api/v1/public/forms/{self.public_form.unique_slug}/submissions/draft/'
        data = {
            'session_id': self.session_id,
            'answers': [
                {
                    'field_id': str(self.field1.id),
                    'text_value': 'John Doe'
                }
            ]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        submission = FormSubmission.objects.get(id=response.data['submission_id'])
        self.assertEqual(submission.status, 'draft')
        self.assertIsNone(submission.submitted_at)
        
    def test_get_draft_success(self):
        """Test getting draft submission"""
        submission = FormSubmission.objects.create(
            form=self.public_form,
            session_id=self.session_id,
            status='draft'
        )
        SubmissionAnswer.objects.create(
            submission=submission,
            field=self.field1,
            text_value='John Doe'
        )
        
        url = f'/api/v1/public/forms/{self.public_form.unique_slug}/submissions/draft/{self.session_id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'draft')
        self.assertEqual(len(response.data['answers']), 1)
        
    def test_get_draft_not_found(self):
        """Test getting non-existent draft"""
        url = f'/api/v1/public/forms/{self.public_form.unique_slug}/submissions/draft/non-existent-session/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_update_draft_success(self):
        """Test updating draft submission"""
        submission = FormSubmission.objects.create(
            form=self.public_form,
            session_id=self.session_id,
            status='draft'
        )
        SubmissionAnswer.objects.create(
            submission=submission,
            field=self.field1,
            text_value='John Doe'
        )
        
        url = f'/api/v1/public/forms/{self.public_form.unique_slug}/submissions/draft/{self.session_id}/'
        data = {
            'answers': [
                {
                    'field_id': str(self.field1.id),
                    'text_value': 'Jane Doe'
                },
                {
                    'field_id': str(self.field2.id),
                    'text_value': 'jane@example.com'
                }
            ]
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        submission.refresh_from_db()
        self.assertEqual(submission.answers.count(), 2)
        self.assertEqual(submission.answers.get(field=self.field1).text_value, 'Jane Doe')


# ============================================================================
# OWNER SUBMISSION MANAGEMENT API TESTS
# ============================================================================

class SubmissionManagementAPITestCase(APITestCase):
    """Test cases for Submission Management API endpoints"""

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
        
        self.form = Form.objects.create(
            user=self.owner,
            title='Test Form',
            unique_slug='test-form',
            visibility='public',
            is_active=True
        )
        
        self.other_form = Form.objects.create(
            user=self.other_user,
            title='Other Form',
            unique_slug='other-form',
            visibility='public',
            is_active=True
        )
        
        self.field1 = FormField.objects.create(
            form=self.form,
            field_type='text',
            label='Name',
            is_required=True,
            order_index=0
        )
        
        self.field2 = FormField.objects.create(
            form=self.form,
            field_type='email',
            label='Email',
            is_required=True,
            order_index=1
        )
        
        self.submission1 = FormSubmission.objects.create(
            form=self.form,
            user=self.owner,
            session_id='session-1',
            status='submitted'
        )
        
        self.submission2 = FormSubmission.objects.create(
            form=self.form,
            user=None,
            session_id='session-2',
            status='draft'
        )
        
        SubmissionAnswer.objects.create(
            submission=self.submission1,
            field=self.field1,
            text_value='John Doe'
        )
        
        SubmissionAnswer.objects.create(
            submission=self.submission1,
            field=self.field2,
            text_value='john@example.com'
        )
        
        refresh = RefreshToken.for_user(self.owner)
        self.token = str(refresh.access_token)
        self.auth_header = f'Bearer {self.token}'
        
    def test_list_submissions_success(self):
        """Test listing submissions"""
        url = f'/api/v1/forms/{self.form.unique_slug}/submissions/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        
    def test_list_submissions_filter_by_status(self):
        """Test filtering submissions by status"""
        url = f'/api/v1/forms/{self.form.unique_slug}/submissions/?status=submitted'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['status'], 'submitted')
        
    def test_list_submissions_not_owner(self):
        """Test listing submissions for form user doesn't own"""
        url = f'/api/v1/forms/{self.other_form.unique_slug}/submissions/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_list_submissions_unauthenticated(self):
        """Test listing submissions without authentication"""
        url = f'/api/v1/forms/{self.form.unique_slug}/submissions/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_retrieve_submission_success(self):
        """Test retrieving single submission"""
        url = f'/api/v1/forms/{self.form.unique_slug}/submissions/{self.submission1.id}/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.submission1.id))
        self.assertEqual(len(response.data['answers']), 2)
        
    def test_retrieve_submission_not_found(self):
        """Test retrieving non-existent submission"""
        url = f'/api/v1/forms/{self.form.unique_slug}/submissions/{uuid.uuid4()}/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_delete_submission_success(self):
        """Test deleting a submission"""
        url = f'/api/v1/forms/{self.form.unique_slug}/submissions/{self.submission2.id}/'
        response = self.client.delete(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FormSubmission.objects.filter(id=self.submission2.id).exists())
        
    def test_delete_submission_not_owner(self):
        """Test deleting submission from form user doesn't own"""
        url = f'/api/v1/forms/{self.other_form.unique_slug}/submissions/{self.submission1.id}/'
        response = self.client.delete(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_statistics_success(self):
        """Test getting submission statistics"""
        url = f'/api/v1/forms/{self.form.unique_slug}/submissions/stats/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_submissions'], 2)
        self.assertEqual(response.data['submitted_count'], 1)
        self.assertEqual(response.data['draft_count'], 1)
        self.assertEqual(response.data['unique_users'], 1)
        self.assertEqual(response.data['anonymous_count'], 1)
        
    def test_statistics_not_owner(self):
        """Test getting statistics for form user doesn't own"""
        url = f'/api/v1/forms/{self.other_form.unique_slug}/submissions/stats/'
        response = self.client.get(url, HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_bulk_delete_success(self):
        """Test bulk deleting submissions"""
        submission3 = FormSubmission.objects.create(
            form=self.form,
            session_id='session-3',
            status='submitted'
        )
        
        url = f'/api/v1/forms/{self.form.unique_slug}/submissions/bulk-delete/'
        data = {
            'submission_ids': [str(self.submission1.id), str(submission3.id)]
        }
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['deleted_count'], 2)
        self.assertFalse(FormSubmission.objects.filter(id=self.submission1.id).exists())
        self.assertFalse(FormSubmission.objects.filter(id=submission3.id).exists())
        
    def test_bulk_delete_empty_list(self):
        """Test bulk delete with empty list"""
        url = f'/api/v1/forms/{self.form.unique_slug}/submissions/bulk-delete/'
        data = {'submission_ids': []}
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_export_csv_success(self):
        """Test exporting submissions as CSV"""
        url = f'/api/v1/forms/{self.form.unique_slug}/submissions/export/'
        data = {
            'format': 'csv',
            'status': 'submitted'
        }
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
    def test_export_json_success(self):
        """Test exporting submissions as JSON"""
        url = f'/api/v1/forms/{self.form.unique_slug}/submissions/export/'
        data = {
            'format': 'json',
            'status': 'all'
        }
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        
    def test_bulk_export_success(self):
        """Test bulk exporting specific submissions"""
        url = f'/api/v1/forms/{self.form.unique_slug}/submissions/bulk-export/'
        data = {
            'submission_ids': [str(self.submission1.id)],
            'format': 'json'
        }
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/json')
        
    def test_bulk_export_empty_list(self):
        """Test bulk export with empty list"""
        url = f'/api/v1/forms/{self.form.unique_slug}/submissions/bulk-export/'
        data = {'submission_ids': []}
        response = self.client.post(url, data, format='json', HTTP_AUTHORIZATION=self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

