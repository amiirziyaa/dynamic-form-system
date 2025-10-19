import uuid
import json
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from submissions.models import FormSubmission, SubmissionAnswer, ProcessProgress, ProcessStepCompletion
from forms.models import Form, FormField
from processes.models import Process, ProcessStep

User = get_user_model()


class FormSubmissionModelTest(TestCase):
    """Test cases for FormSubmission model according to database schema"""

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
        
        self.submission_data = {
            'form': self.form,
            'user': self.user,
            'session_id': 'test-session-123',
            'status': 'submitted',
            'metadata': {
                'ip_address': '192.168.1.1',
                'user_agent': 'Mozilla/5.0...',
                'submission_duration_seconds': 145
            }
        }

    def test_submission_creation(self):
        """Test basic submission creation"""
        submission = FormSubmission.objects.create(**self.submission_data)
        
        # Test primary key is UUID
        self.assertIsInstance(submission.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(submission.form, self.form)
        self.assertEqual(submission.user, self.user)
        self.assertEqual(submission.session_id, 'test-session-123')
        self.assertEqual(submission.status, 'submitted')
        
        # Test JSON metadata
        self.assertIsInstance(submission.metadata, dict)
        self.assertEqual(submission.metadata['ip_address'], '192.168.1.1')
        
        # Test timestamps
        self.assertIsNotNone(submission.created_at)
        self.assertIsNotNone(submission.updated_at)

    def test_submission_status_choices(self):
        """Test status choices"""
        statuses = ['draft', 'submitted', 'archived']
        
        for status in statuses:
            submission = FormSubmission.objects.create(
                form=self.form,
                session_id=f'test-session-{status}',
                status=status
            )
            self.assertEqual(submission.status, status)

    def test_submission_optional_user(self):
        """Test optional user field for anonymous submissions"""
        submission = FormSubmission.objects.create(
            form=self.form,
            session_id='anonymous-session',
            status='submitted'
        )
        self.assertIsNone(submission.user)

    def test_submission_optional_process_progress(self):
        """Test optional process progress field"""
        submission = FormSubmission.objects.create(
            form=self.form,
            session_id='standalone-session',
            status='submitted'
        )
        self.assertIsNone(submission.process_progress)

    def test_submission_string_representation(self):
        """Test string representation"""
        submission = FormSubmission.objects.create(**self.submission_data)
        expected = f"Submission {submission.id} for Test Form"
        self.assertEqual(str(submission), expected)

    def test_submission_database_table_name(self):
        """Test database table name"""
        self.assertEqual(FormSubmission._meta.db_table, 'form_submission')

    def test_submission_indexes(self):
        """Test that proper indexes are created"""
        indexes = [index.fields for index in FormSubmission._meta.indexes]
        self.assertIn(['form'], indexes)
        self.assertIn(['user'], indexes)
        self.assertIn(['session_id'], indexes)
        self.assertIn(['status'], indexes)
        self.assertIn(['submitted_at'], indexes)
        self.assertIn(['process_progress'], indexes)

    def test_submission_related_names(self):
        """Test related names for foreign key relationships"""
        submission = FormSubmission.objects.create(**self.submission_data)
        
        # Test that related managers exist
        self.assertTrue(hasattr(submission, 'answers'))
        self.assertTrue(hasattr(submission, 'step_completions'))


class SubmissionAnswerModelTest(TestCase):
    """Test cases for SubmissionAnswer model according to database schema"""

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
        
        self.field = FormField.objects.create(
            form=self.form,
            field_type='text',
            label='Full Name',
            order_index=0
        )
        
        self.submission = FormSubmission.objects.create(
            form=self.form,
            user=self.user,
            session_id='test-session',
            status='submitted'
        )
        
        self.answer_data = {
            'submission': self.submission,
            'field': self.field,
            'text_value': 'John Doe'
        }

    def test_answer_creation_text(self):
        """Test text answer creation"""
        answer = SubmissionAnswer.objects.create(**self.answer_data)
        
        # Test primary key is UUID
        self.assertIsInstance(answer.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(answer.submission, self.submission)
        self.assertEqual(answer.field, self.field)
        self.assertEqual(answer.text_value, 'John Doe')
        
        # Test other value fields are None
        self.assertIsNone(answer.numeric_value)
        self.assertIsNone(answer.boolean_value)
        self.assertIsNone(answer.date_value)
        self.assertIsNone(answer.array_value)
        self.assertIsNone(answer.file_url)
        
        # Test timestamp
        self.assertIsNotNone(answer.created_at)

    def test_answer_creation_numeric(self):
        """Test numeric answer creation"""
        answer = SubmissionAnswer.objects.create(
            submission=self.submission,
            field=self.field,
            numeric_value=Decimal('42.5')
        )
        self.assertEqual(answer.numeric_value, Decimal('42.5'))

    def test_answer_creation_boolean(self):
        """Test boolean answer creation"""
        answer = SubmissionAnswer.objects.create(
            submission=self.submission,
            field=self.field,
            boolean_value=True
        )
        self.assertTrue(answer.boolean_value)

    def test_answer_creation_date(self):
        """Test date answer creation"""
        from django.utils import timezone
        now = timezone.now()
        
        answer = SubmissionAnswer.objects.create(
            submission=self.submission,
            field=self.field,
            date_value=now
        )
        self.assertEqual(answer.date_value, now)

    def test_answer_creation_array(self):
        """Test array answer creation for multiple selections"""
        answer = SubmissionAnswer.objects.create(
            submission=self.submission,
            field=self.field,
            array_value=['option1', 'option3', 'option5']
        )
        self.assertEqual(answer.array_value, ['option1', 'option3', 'option5'])

    def test_answer_creation_file(self):
        """Test file answer creation"""
        answer = SubmissionAnswer.objects.create(
            submission=self.submission,
            field=self.field,
            file_url='https://example.com/files/document.pdf'
        )
        self.assertEqual(answer.file_url, 'https://example.com/files/document.pdf')

    def test_answer_string_representation(self):
        """Test string representation"""
        answer = SubmissionAnswer.objects.create(**self.answer_data)
        expected = f"Answer for Full Name in {answer.submission}"
        self.assertEqual(str(answer), expected)

    def test_answer_database_table_name(self):
        """Test database table name"""
        self.assertEqual(SubmissionAnswer._meta.db_table, 'submission_answer')

    def test_answer_indexes(self):
        """Test that proper indexes are created"""
        indexes = [index.fields for index in SubmissionAnswer._meta.indexes]
        self.assertIn(['submission'], indexes)
        self.assertIn(['field'], indexes)
        self.assertIn(['field', 'numeric_value'], indexes)

    def test_answer_related_names(self):
        """Test related names for foreign key relationships"""
        answer = SubmissionAnswer.objects.create(**self.answer_data)
        
        # Test that related managers exist
        self.assertTrue(hasattr(answer, 'submission'))
        self.assertTrue(hasattr(answer, 'field'))


class ProcessProgressModelTest(TestCase):
    """Test cases for ProcessProgress model according to database schema"""

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
        
        self.progress_data = {
            'process': self.process,
            'user': self.user,
            'session_id': 'test-session-123',
            'status': 'in_progress',
            'current_step_index': 0,
            'completion_percentage': Decimal('25.00')
        }

    def test_progress_creation(self):
        """Test basic progress creation"""
        progress = ProcessProgress.objects.create(**self.progress_data)
        
        # Test primary key is UUID
        self.assertIsInstance(progress.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(progress.process, self.process)
        self.assertEqual(progress.user, self.user)
        self.assertEqual(progress.session_id, 'test-session-123')
        self.assertEqual(progress.status, 'in_progress')
        self.assertEqual(progress.current_step_index, 0)
        self.assertEqual(progress.completion_percentage, Decimal('25.00'))
        
        # Test timestamps
        self.assertIsNotNone(progress.started_at)
        self.assertIsNotNone(progress.last_activity_at)
        self.assertIsNotNone(progress.created_at)
        self.assertIsNotNone(progress.updated_at)

    def test_progress_status_choices(self):
        """Test status choices"""
        statuses = ['in_progress', 'completed', 'abandoned']
        
        for status in statuses:
            progress = ProcessProgress.objects.create(
                process=self.process,
                session_id=f'test-session-{status}',
                status=status
            )
            self.assertEqual(progress.status, status)

    def test_progress_optional_user(self):
        """Test optional user field for anonymous progress"""
        progress = ProcessProgress.objects.create(
            process=self.process,
            session_id='anonymous-session',
            status='in_progress'
        )
        self.assertIsNone(progress.user)

    def test_progress_completion_percentage_validation(self):
        """Test completion percentage validation"""
        # Test valid percentage
        progress = ProcessProgress.objects.create(
            process=self.process,
            session_id='test-session',
            completion_percentage=Decimal('50.00')
        )
        self.assertEqual(progress.completion_percentage, Decimal('50.00'))
        
        # Test edge cases
        progress = ProcessProgress.objects.create(
            process=self.process,
            session_id='test-session-0',
            completion_percentage=Decimal('0.00')
        )
        self.assertEqual(progress.completion_percentage, Decimal('0.00'))
        
        progress = ProcessProgress.objects.create(
            process=self.process,
            session_id='test-session-100',
            completion_percentage=Decimal('100.00')
        )
        self.assertEqual(progress.completion_percentage, Decimal('100.00'))

    def test_progress_string_representation(self):
        """Test string representation"""
        progress = ProcessProgress.objects.create(**self.progress_data)
        expected = "Progress for Test Process - in_progress"
        self.assertEqual(str(progress), expected)

    def test_progress_database_table_name(self):
        """Test database table name"""
        self.assertEqual(ProcessProgress._meta.db_table, 'process_progress')

    def test_progress_indexes(self):
        """Test that proper indexes are created"""
        indexes = [index.fields for index in ProcessProgress._meta.indexes]
        self.assertIn(['process'], indexes)
        self.assertIn(['user'], indexes)
        self.assertIn(['session_id'], indexes)
        self.assertIn(['status'], indexes)
        self.assertIn(['last_activity_at'], indexes)

    def test_progress_related_names(self):
        """Test related names for foreign key relationships"""
        progress = ProcessProgress.objects.create(**self.progress_data)
        
        # Test that related managers exist
        self.assertTrue(hasattr(progress, 'submissions'))
        self.assertTrue(hasattr(progress, 'step_completions'))


class ProcessStepCompletionModelTest(TestCase):
    """Test cases for ProcessStepCompletion model according to database schema"""

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
        
        self.step = ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            title='Test Step',
            order_index=0
        )
        
        self.progress = ProcessProgress.objects.create(
            process=self.process,
            user=self.user,
            session_id='test-session',
            status='in_progress'
        )
        
        self.submission = FormSubmission.objects.create(
            form=self.form,
            user=self.user,
            session_id='test-session',
            status='submitted'
        )
        
        self.completion_data = {
            'progress': self.progress,
            'step': self.step,
            'submission': self.submission,
            'status': 'completed'
        }

    def test_completion_creation(self):
        """Test basic completion creation"""
        completion = ProcessStepCompletion.objects.create(**self.completion_data)
        
        # Test primary key is UUID
        self.assertIsInstance(completion.id, uuid.UUID)
        
        # Test required fields
        self.assertEqual(completion.progress, self.progress)
        self.assertEqual(completion.step, self.step)
        self.assertEqual(completion.submission, self.submission)
        self.assertEqual(completion.status, 'completed')
        
        # Test timestamps
        self.assertIsNotNone(completion.created_at)
        self.assertIsNotNone(completion.updated_at)

    def test_completion_status_choices(self):
        """Test status choices"""
        statuses = ['pending', 'completed', 'skipped']
        
        # Create different progress records for each status to avoid unique constraint violation
        for i, status in enumerate(statuses):
            # Create a new progress record for each status
            new_progress = ProcessProgress.objects.create(
                process=self.process,
                user=self.user,
                session_id=f'test-session-{status}-{i}',
                status='in_progress'
            )
            
            # Create a new step for each status
            new_step = ProcessStep.objects.create(
                process=self.process,
                form=self.form,
                title=f'Test Step {status.title()}',
                order_index=i + 1
            )
            
            completion = ProcessStepCompletion.objects.create(
                progress=new_progress,
                step=new_step,
                status=status
            )
            self.assertEqual(completion.status, status)

    def test_completion_optional_submission(self):
        """Test optional submission field"""
        completion = ProcessStepCompletion.objects.create(
            progress=self.progress,
            step=self.step,
            status='skipped'
        )
        self.assertIsNone(completion.submission)

    def test_completion_unique_together(self):
        """Test unique together constraint"""
        ProcessStepCompletion.objects.create(**self.completion_data)
        
        # Try to create another completion for same progress and step
        with self.assertRaises(IntegrityError):
            ProcessStepCompletion.objects.create(
                progress=self.progress,
                step=self.step,
                status='pending'
            )

    def test_completion_string_representation(self):
        """Test string representation"""
        completion = ProcessStepCompletion.objects.create(**self.completion_data)
        expected = "Step completion for Test Step - completed"
        self.assertEqual(str(completion), expected)

    def test_completion_database_table_name(self):
        """Test database table name"""
        self.assertEqual(ProcessStepCompletion._meta.db_table, 'process_step_completion')

    def test_completion_unique_together_constraint(self):
        """Test unique together constraint"""
        self.assertEqual(ProcessStepCompletion._meta.unique_together, (('progress', 'step'),))