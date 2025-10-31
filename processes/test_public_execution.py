import uuid
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from processes.models import Process, ProcessStep
from forms.models import Form
from submissions.models import ProcessProgress, FormSubmission
from analytics.models import ProcessView

User = get_user_model()


class PublicProcessExecutionAPITestCase(APITestCase):
    """Test cases for Public Process Execution API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='owner@example.com',
            first_name='Owner',
            last_name='User',
            password='testpass123'
        )
        
        self.form1 = Form.objects.create(
            user=self.user,
            title='Step 1 Form',
            unique_slug='step-1-form',
            is_active=True
        )
        
        self.form2 = Form.objects.create(
            user=self.user,
            title='Step 2 Form',
            unique_slug='step-2-form',
            is_active=True
        )
        
        self.form3 = Form.objects.create(
            user=self.user,
            title='Step 3 Form',
            unique_slug='step-3-form',
            is_active=True
        )
        
        self.public_process = Process.objects.create(
            user=self.user,
            title='Public Onboarding Process',
            description='A public onboarding process',
            unique_slug='public-onboarding',
            visibility='public',
            process_type='linear',
            is_active=True,
            settings={}
        )
        
        self.private_process = Process.objects.create(
            user=self.user,
            title='Private Process',
            description='A private process',
            unique_slug='private-process',
            visibility='private',
            access_password='testpass123',
            process_type='linear',
            is_active=True,
            settings={}
        )
        
        self.inactive_process = Process.objects.create(
            user=self.user,
            title='Inactive Process',
            unique_slug='inactive-process',
            visibility='public',
            process_type='linear',
            is_active=False,
            settings={}
        )
        
        from django.contrib.auth.hashers import make_password
        self.private_process.access_password = make_password('testpass123')
        self.private_process.save()
        
        self.step1 = ProcessStep.objects.create(
            process=self.public_process,
            form=self.form1,
            title='Step 1: Personal Info',
            description='Enter your personal information',
            order_index=0,
            is_required=True
        )
        
        self.step2 = ProcessStep.objects.create(
            process=self.public_process,
            form=self.form2,
            title='Step 2: Documents',
            description='Upload required documents',
            order_index=1,
            is_required=True
        )
        
        self.step3 = ProcessStep.objects.create(
            process=self.public_process,
            form=self.form3,
            title='Step 3: Review',
            description='Review and confirm',
            order_index=2,
            is_required=False
        )
        
        self.session_id = 'test-session-123'
        
    def test_get_public_process_success(self):
        """Test getting public process structure"""
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Public Onboarding Process')
        self.assertEqual(response.data['unique_slug'], 'public-onboarding')
        self.assertFalse(response.data['requires_password'])
        self.assertEqual(len(response.data['steps']), 3)
        self.assertIn('visibility', response.data)
        
    def test_get_public_process_private_without_password(self):
        """Test getting private process without password verification"""
        url = f'/api/v1/public/processes/{self.private_process.unique_slug}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['requires_password'])
        self.assertNotIn('visibility', response.data)
        
    def test_get_public_process_private_with_password_verified(self):
        """Test getting private process after password verification"""
        url = f'/api/v1/public/processes/{self.private_process.unique_slug}/'
        
        session = self.client.session
        session[f'process_access_{self.private_process.unique_slug}'] = True
        session.save()
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['requires_password'])
        self.assertIn('visibility', response.data)
        
    def test_get_public_process_not_found(self):
        """Test getting non-existent process"""
        url = '/api/v1/public/processes/non-existent-process/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_get_public_process_inactive(self):
        """Test getting inactive process"""
        url = f'/api/v1/public/processes/{self.inactive_process.unique_slug}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_verify_password_success(self):
        """Test successful password verification"""
        url = f'/api/v1/public/processes/{self.private_process.unique_slug}/verify-password/'
        data = {'password': 'testpass123'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['access_granted'])
        self.assertIn('message', response.data)
        
    def test_verify_password_invalid(self):
        """Test password verification with wrong password"""
        url = f'/api/v1/public/processes/{self.private_process.unique_slug}/verify-password/'
        data = {'password': 'wrongpassword'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['access_granted'])
        
    def test_verify_password_missing(self):
        """Test password verification without password"""
        url = f'/api/v1/public/processes/{self.private_process.unique_slug}/verify-password/'
        data = {}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_verify_password_public_process(self):
        """Test password verification for public process"""
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/verify-password/'
        data = {'password': 'testpass123'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_track_view_success(self):
        """Test tracking process view"""
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/view/'
        data = {'session_id': self.session_id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('view_id', response.data)
        
        view = ProcessView.objects.get(id=response.data['view_id'])
        self.assertEqual(view.process, self.public_process)
        self.assertEqual(view.session_id, self.session_id)
        
    def test_track_view_auto_session(self):
        """Test tracking view with auto-generated session"""
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/view/'
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('view_id', response.data)
        
    def test_track_view_not_found(self):
        """Test tracking view for non-existent process"""
        url = '/api/v1/public/processes/non-existent-process/view/'
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_start_process_success(self):
        """Test starting a new process"""
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/start/'
        data = {'session_id': self.session_id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('progress_id', response.data)
        self.assertEqual(response.data['session_id'], self.session_id)
        self.assertEqual(response.data['status'], 'in_progress')
        self.assertEqual(response.data['current_step_index'], 0)
        self.assertEqual(float(response.data['completion_percentage']), 0.0)
        
        progress = ProcessProgress.objects.get(id=response.data['progress_id'])
        self.assertEqual(progress.process, self.public_process)
        self.assertEqual(progress.session_id, self.session_id)
        
    def test_start_process_existing_progress(self):
        """Test starting process with existing progress"""
        from processes.repository import ProcessProgressRepository
        
        progress_repo = ProcessProgressRepository()
        existing_progress = progress_repo.create(
            process=self.public_process,
            session_id=self.session_id,
            current_step_index=1,
            status='in_progress'
        )
        
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/start/'
        data = {'session_id': self.session_id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['progress_id'], str(existing_progress.id))
        
    def test_start_process_inactive(self):
        """Test starting inactive process"""
        url = f'/api/v1/public/processes/{self.inactive_process.unique_slug}/start/'
        data = {'session_id': self.session_id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_start_process_not_found(self):
        """Test starting non-existent process"""
        url = '/api/v1/public/processes/non-existent-process/start/'
        data = {'session_id': self.session_id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_get_progress_success(self):
        """Test getting process progress"""
        from processes.repository import ProcessProgressRepository, ProcessStepCompletionRepository
        
        progress_repo = ProcessProgressRepository()
        completion_repo = ProcessStepCompletionRepository()
        
        progress = progress_repo.create(
            process=self.public_process,
            session_id=self.session_id,
            current_step_index=1,
            status='in_progress'
        )
        
        completion_repo.create(progress=progress, step=self.step1, status='pending')
        completion_repo.create(progress=progress, step=self.step2, status='pending')
        completion_repo.create(progress=progress, step=self.step3, status='pending')
        
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/progress/{self.session_id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')
        self.assertEqual(response.data['current_step_index'], 1)
        self.assertIsNotNone(response.data['current_step'])
        self.assertIn('step_completions', response.data)
        self.assertEqual(len(response.data['step_completions']), 3)
        
    def test_get_progress_not_found(self):
        """Test getting progress for non-existent session"""
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/progress/non-existent-session/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_get_current_step_success(self):
        """Test getting current step"""
        from processes.repository import ProcessProgressRepository, ProcessStepCompletionRepository
        
        progress_repo = ProcessProgressRepository()
        completion_repo = ProcessStepCompletionRepository()
        
        progress = progress_repo.create(
            process=self.public_process,
            session_id=self.session_id,
            current_step_index=1,
            status='in_progress'
        )
        
        completion_repo.create(progress=progress, step=self.step1, status='pending')
        completion_repo.create(progress=progress, step=self.step2, status='pending')
        completion_repo.create(progress=progress, step=self.step3, status='pending')
        
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/progress/{self.session_id}/current-step/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_index'], 1)
        self.assertEqual(response.data['title'], 'Step 2: Documents')
        
    def test_get_current_step_first(self):
        """Test getting first step"""
        from processes.repository import ProcessProgressRepository, ProcessStepCompletionRepository
        
        progress_repo = ProcessProgressRepository()
        completion_repo = ProcessStepCompletionRepository()
        
        progress = progress_repo.create(
            process=self.public_process,
            session_id=self.session_id,
            current_step_index=0,
            status='in_progress'
        )
        
        completion_repo.create(progress=progress, step=self.step1, status='pending')
        completion_repo.create(progress=progress, step=self.step2, status='pending')
        completion_repo.create(progress=progress, step=self.step3, status='pending')
        
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/progress/{self.session_id}/current-step/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['order_index'], 0)
        
    def test_get_current_step_not_found(self):
        """Test getting current step for non-existent progress"""
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/progress/non-existent-session/current-step/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_move_next_step_success(self):
        """Test moving to next step"""
        from processes.repository import ProcessProgressRepository, ProcessStepCompletionRepository
        
        progress_repo = ProcessProgressRepository()
        completion_repo = ProcessStepCompletionRepository()
        
        progress = progress_repo.create(
            process=self.public_process,
            session_id=self.session_id,
            current_step_index=0,
            status='in_progress'
        )
        
        completion_repo.create(progress=progress, step=self.step1, status='pending')
        completion_repo.create(progress=progress, step=self.step2, status='pending')
        completion_repo.create(progress=progress, step=self.step3, status='pending')
        
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/progress/{self.session_id}/next/'
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['current_step_index'], 1)
        
        progress.refresh_from_db()
        self.assertEqual(progress.current_step_index, 1)
        
    def test_move_next_step_last_step(self):
        """Test moving next from last step"""
        from processes.repository import ProcessProgressRepository, ProcessStepCompletionRepository
        
        progress_repo = ProcessProgressRepository()
        completion_repo = ProcessStepCompletionRepository()
        
        progress = progress_repo.create(
            process=self.public_process,
            session_id=self.session_id,
            current_step_index=2,
            status='in_progress'
        )
        
        completion_repo.create(progress=progress, step=self.step1, status='pending')
        completion_repo.create(progress=progress, step=self.step2, status='pending')
        completion_repo.create(progress=progress, step=self.step3, status='pending')
        
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/progress/{self.session_id}/next/'
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_move_next_step_not_found(self):
        """Test moving next for non-existent progress"""
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/progress/non-existent-session/next/'
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_move_previous_step_success(self):
        """Test moving to previous step"""
        from processes.repository import ProcessProgressRepository, ProcessStepCompletionRepository
        
        progress_repo = ProcessProgressRepository()
        completion_repo = ProcessStepCompletionRepository()
        
        progress = progress_repo.create(
            process=self.public_process,
            session_id=self.session_id,
            current_step_index=1,
            status='in_progress'
        )
        
        completion_repo.create(progress=progress, step=self.step1, status='pending')
        completion_repo.create(progress=progress, step=self.step2, status='pending')
        completion_repo.create(progress=progress, step=self.step3, status='pending')
        
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/progress/{self.session_id}/previous/'
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['current_step_index'], 0)
        
        progress.refresh_from_db()
        self.assertEqual(progress.current_step_index, 0)
        
    def test_move_previous_step_first_step(self):
        """Test moving previous from first step"""
        from processes.repository import ProcessProgressRepository, ProcessStepCompletionRepository
        
        progress_repo = ProcessProgressRepository()
        completion_repo = ProcessStepCompletionRepository()
        
        progress = progress_repo.create(
            process=self.public_process,
            session_id=self.session_id,
            current_step_index=0,
            status='in_progress'
        )
        
        completion_repo.create(progress=progress, step=self.step1, status='pending')
        completion_repo.create(progress=progress, step=self.step2, status='pending')
        completion_repo.create(progress=progress, step=self.step3, status='pending')
        
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/progress/{self.session_id}/previous/'
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_move_previous_step_not_found(self):
        """Test moving previous for non-existent progress"""
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/progress/non-existent-session/previous/'
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_get_step_form_success(self):
        """Test getting form for a step"""
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/steps/{self.step1.id}/form/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['step_id'], str(self.step1.id))
        self.assertEqual(response.data['step_title'], 'Step 1: Personal Info')
        self.assertEqual(response.data['form_id'], str(self.form1.id))
        self.assertEqual(response.data['form_slug'], 'step-1-form')
        
    def test_get_step_form_not_found(self):
        """Test getting form for non-existent step"""
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/steps/00000000-0000-0000-0000-000000000000/form/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_get_step_form_wrong_process(self):
        """Test getting form for step from different process"""
        other_process = Process.objects.create(
            user=self.user,
            title='Other Process',
            unique_slug='other-process',
            visibility='public',
            process_type='linear',
            is_active=True
        )
        
        url = f'/api/v1/public/processes/{other_process.unique_slug}/steps/{self.step1.id}/form/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_complete_step_success(self):
        """Test completing a step"""
        from processes.repository import ProcessProgressRepository, ProcessStepCompletionRepository
        
        progress_repo = ProcessProgressRepository()
        completion_repo = ProcessStepCompletionRepository()
        
        progress = progress_repo.create(
            process=self.public_process,
            session_id=self.session_id,
            current_step_index=0,
            status='in_progress'
        )
        
        completion = completion_repo.create(progress=progress, step=self.step1, status='pending')
        
        submission = FormSubmission.objects.create(
            form=self.form1,
            session_id=self.session_id,
            status='submitted'
        )
        
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/steps/{self.step1.id}/complete/'
        data = {
            'session_id': self.session_id,
            'submission_id': str(submission.id)
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        
        completion.refresh_from_db()
        self.assertEqual(completion.status, 'completed')
        self.assertEqual(completion.submission, submission)
        
        progress.refresh_from_db()
        self.assertGreater(float(progress.completion_percentage), 0.0)
        
    def test_complete_step_without_submission(self):
        """Test completing a step without submission"""
        from processes.repository import ProcessProgressRepository, ProcessStepCompletionRepository
        
        progress_repo = ProcessProgressRepository()
        completion_repo = ProcessStepCompletionRepository()
        
        progress = progress_repo.create(
            process=self.public_process,
            session_id=self.session_id,
            current_step_index=0,
            status='in_progress'
        )
        
        completion_repo.create(progress=progress, step=self.step1, status='pending')
        
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/steps/{self.step1.id}/complete/'
        data = {'session_id': self.session_id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        completion = completion_repo.get_by_progress_and_step(progress, self.step1)
        self.assertEqual(completion.status, 'completed')
        
    def test_complete_step_wrong_submission_session(self):
        """Test completing step with submission from different session"""
        from processes.repository import ProcessProgressRepository, ProcessStepCompletionRepository
        
        progress_repo = ProcessProgressRepository()
        completion_repo = ProcessStepCompletionRepository()
        
        progress = progress_repo.create(
            process=self.public_process,
            session_id=self.session_id,
            current_step_index=0,
            status='in_progress'
        )
        
        completion_repo.create(progress=progress, step=self.step1, status='pending')
        
        submission = FormSubmission.objects.create(
            form=self.form1,
            session_id='different-session',
            status='submitted'
        )
        
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/steps/{self.step1.id}/complete/'
        data = {
            'session_id': self.session_id,
            'submission_id': str(submission.id)
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_complete_step_not_found(self):
        """Test completing non-existent step"""
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/steps/00000000-0000-0000-0000-000000000000/complete/'
        data = {'session_id': self.session_id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_complete_process_success(self):
        """Test completing entire process"""
        from processes.repository import ProcessProgressRepository, ProcessStepCompletionRepository
        
        progress_repo = ProcessProgressRepository()
        completion_repo = ProcessStepCompletionRepository()
        
        progress = progress_repo.create(
            process=self.public_process,
            session_id=self.session_id,
            current_step_index=2,
            status='in_progress'
        )
        
        completion1 = completion_repo.create(progress=progress, step=self.step1, status='pending')
        completion2 = completion_repo.create(progress=progress, step=self.step2, status='pending')
        completion3 = completion_repo.create(progress=progress, step=self.step3, status='pending')
        
        completion_repo.mark_completed(completion1)
        completion_repo.mark_completed(completion2)
        
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/complete/'
        data = {'session_id': self.session_id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        
        progress.refresh_from_db()
        self.assertEqual(progress.status, 'completed')
        self.assertIsNotNone(progress.completed_at)
        self.assertEqual(float(progress.completion_percentage), 100.0)
        
    def test_complete_process_missing_required_steps(self):
        """Test completing process without all required steps"""
        from processes.repository import ProcessProgressRepository, ProcessStepCompletionRepository
        
        progress_repo = ProcessProgressRepository()
        completion_repo = ProcessStepCompletionRepository()
        
        progress = progress_repo.create(
            process=self.public_process,
            session_id=self.session_id,
            current_step_index=2,
            status='in_progress'
        )
        
        completion1 = completion_repo.create(progress=progress, step=self.step1, status='pending')
        completion_repo.create(progress=progress, step=self.step2, status='pending')
        completion_repo.create(progress=progress, step=self.step3, status='pending')
        
        completion_repo.mark_completed(completion1)
        
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/complete/'
        data = {'session_id': self.session_id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_complete_process_already_completed(self):
        """Test completing already completed process"""
        from processes.repository import ProcessProgressRepository, ProcessStepCompletionRepository
        
        progress_repo = ProcessProgressRepository()
        completion_repo = ProcessStepCompletionRepository()
        
        progress = progress_repo.create(
            process=self.public_process,
            session_id=self.session_id,
            current_step_index=2,
            status='in_progress'
        )
        
        completion1 = completion_repo.create(progress=progress, step=self.step1, status='pending')
        completion2 = completion_repo.create(progress=progress, step=self.step2, status='pending')
        completion3 = completion_repo.create(progress=progress, step=self.step3, status='pending')
        
        completion_repo.mark_completed(completion1)
        completion_repo.mark_completed(completion2)
        
        progress_repo.mark_completed(progress)
        
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/complete/'
        data = {'session_id': self.session_id}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertIn('already completed', response.data['message'].lower())
        
    def test_complete_process_not_found(self):
        """Test completing non-existent process progress"""
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/complete/'
        data = {'session_id': 'non-existent-session'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_complete_process_missing_session_id(self):
        """Test completing process without session_id"""
        url = f'/api/v1/public/processes/{self.public_process.unique_slug}/complete/'
        data = {'session_id': ''}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

