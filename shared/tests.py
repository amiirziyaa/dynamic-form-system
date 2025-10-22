import uuid
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from accounts.models import User
from categories.models import Category
from forms.models import Form, FormField, FieldOption
from processes.models import Process, ProcessStep
from submissions.models import FormSubmission, SubmissionAnswer, ProcessProgress, ProcessStepCompletion
from analytics.models import FormView, ProcessView
from notifications.models import Notification, Webhook, NotificationLog

User = get_user_model()


class ModelRelationshipsIntegrationTest(TransactionTestCase):
    """Integration tests for all model relationships according to ERD"""

    def setUp(self):
        """Set up comprehensive test data"""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            user=self.user,
            name='HR Forms',
            color='#FF5733'
        )
        
        self.form = Form.objects.create(
            user=self.user,
            category=self.category,
            title='Employee Feedback Form',
            unique_slug='employee-feedback-2024',
            visibility='public'
        )
        
        self.field = FormField.objects.create(
            form=self.form,
            field_type='select',
            label='Satisfaction Level',
            order_index=0,
            is_required=True
        )
        
        self.option = FieldOption.objects.create(
            field=self.field,
            label='Very Satisfied',
            value='5',
            order_index=0
        )
        
        self.process = Process.objects.create(
            user=self.user,
            category=self.category,
            title='Employee Onboarding',
            unique_slug='employee-onboarding-2024',
            process_type='linear'
        )
        
        self.step = ProcessStep.objects.create(
            process=self.process,
            form=self.form,
            title='Personal Information',
            order_index=0
        )

    def test_user_relationships(self):
        """Test all User model relationships"""
        # Test direct relationships
        self.assertIn(self.category, self.user.categories.all())
        self.assertIn(self.form, self.user.forms.all())
        self.assertIn(self.process, self.user.processes.all())
        
        # Test reverse relationships
        self.assertEqual(self.category.user, self.user)
        self.assertEqual(self.form.user, self.user)
        self.assertEqual(self.process.user, self.user)

    def test_category_relationships(self):
        """Test Category model relationships"""
        # Test forms relationship
        self.assertIn(self.form, self.category.forms.all())
        self.assertEqual(self.form.category, self.category)
        
        # Test processes relationship
        self.assertIn(self.process, self.category.processes.all())
        self.assertEqual(self.process.category, self.category)

    def test_form_relationships(self):
        """Test Form model relationships"""
        # Test fields relationship
        self.assertIn(self.field, self.form.fields.all())
        self.assertEqual(self.field.form, self.form)
        
        # Test options through field
        self.assertIn(self.option, self.field.options.all())
        self.assertEqual(self.option.field, self.field)
        
        # Test process steps relationship
        self.assertIn(self.step, self.form.process_steps.all())
        self.assertEqual(self.step.form, self.form)

    def test_process_relationships(self):
        """Test Process model relationships"""
        # Test steps relationship
        self.assertIn(self.step, self.process.steps.all())
        self.assertEqual(self.step.process, self.process)

    def test_submission_workflow(self):
        """Test complete submission workflow"""
        # Create form submission
        submission = FormSubmission.objects.create(
            form=self.form,
            user=self.user,
            session_id='test-session-123',
            status='submitted'
        )
        
        # Create submission answer
        answer = SubmissionAnswer.objects.create(
            submission=submission,
            field=self.field,
            text_value='Very Satisfied'
        )
        
        # Test relationships
        self.assertIn(answer, submission.answers.all())
        self.assertEqual(answer.submission, submission)
        self.assertEqual(answer.field, self.field)
        
        # Test form relationship
        self.assertIn(submission, self.form.submissions.all())
        self.assertEqual(submission.form, self.form)

    def test_process_progress_workflow(self):
        """Test complete process progress workflow"""
        # Create process progress
        progress = ProcessProgress.objects.create(
            process=self.process,
            user=self.user,
            session_id='test-session-456',
            status='in_progress',
            current_step_index=0,
            completion_percentage=25.00
        )
        
        # Create form submission linked to progress
        submission = FormSubmission.objects.create(
            form=self.form,
            user=self.user,
            session_id='test-session-456',
            status='submitted',
            process_progress=progress
        )
        
        # Create step completion
        completion = ProcessStepCompletion.objects.create(
            progress=progress,
            step=self.step,
            submission=submission,
            status='completed'
        )
        
        # Test relationships
        self.assertIn(completion, progress.step_completions.all())
        self.assertEqual(completion.progress, progress)
        self.assertEqual(completion.step, self.step)
        self.assertEqual(completion.submission, submission)
        
        # Test process relationship
        self.assertIn(progress, self.process.progress_records.all())
        self.assertEqual(progress.process, self.process)

    def test_analytics_relationships(self):
        """Test analytics model relationships"""
        # Create form view
        form_view = FormView.objects.create(
            form=self.form,
            session_id='test-session-view',
            ip_address='192.168.1.1'
        )
        
        # Create process view
        process_view = ProcessView.objects.create(
            process=self.process,
            session_id='test-session-view',
            ip_address='192.168.1.1'
        )
        
        # Test relationships
        self.assertIn(form_view, self.form.views.all())
        self.assertEqual(form_view.form, self.form)
        
        self.assertIn(process_view, self.process.views.all())
        self.assertEqual(process_view.process, self.process)

    def test_notification_relationships(self):
        """Test notification model relationships"""
        # Create notification
        notification = Notification.objects.create(
            user=self.user,
            name='Form Submission Alert',
            notification_type='email',
            message_template='New form submission received'
        )
        
        # Create webhook
        webhook = Webhook.objects.create(
            user=self.user,
            name='Form Webhook',
            url='https://api.example.com/webhooks/form',
            events=['form.submitted']
        )
        
        # Create notification log
        log = NotificationLog.objects.create(
            notification=notification,
            recipient='admin@example.com',
            status='sent'
        )
        
        # Test relationships
        self.assertIn(notification, self.user.notifications.all())
        self.assertEqual(notification.user, self.user)
        
        self.assertIn(webhook, self.user.webhooks.all())
        self.assertEqual(webhook.user, self.user)
        
        self.assertIn(log, notification.logs.all())
        self.assertEqual(log.notification, notification)

    def test_cascade_deletes(self):
        """Test cascade delete behavior"""
        # Create submission and answer
        submission = FormSubmission.objects.create(
            form=self.form,
            user=self.user,
            session_id='test-cascade',
            status='submitted'
        )
        
        answer = SubmissionAnswer.objects.create(
            submission=submission,
            field=self.field,
            text_value='Test Answer'
        )
        
        # Delete form - should cascade to fields, options, submissions, answers
        form_id = self.form.id
        self.form.delete()
        
        # Verify cascade deletes
        self.assertFalse(Form.objects.filter(id=form_id).exists())
        self.assertFalse(FormField.objects.filter(form_id=form_id).exists())
        self.assertFalse(FieldOption.objects.filter(field__form_id=form_id).exists())
        self.assertFalse(FormSubmission.objects.filter(form_id=form_id).exists())
        self.assertFalse(SubmissionAnswer.objects.filter(submission__form_id=form_id).exists())

    def test_foreign_key_constraints(self):
        """Test foreign key constraints"""
        # Test that we can't create submission without form
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FormSubmission.objects.create(
                    user=self.user,
                    session_id='test-constraint',
                    status='submitted'
                )
        
        # Create a submission first for the answer test
        submission = FormSubmission.objects.create(
            form=self.form,
            user=self.user,
            session_id='test-constraint-answer',
            status='submitted'
        )
        
        # Test that we can't create answer without field
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SubmissionAnswer.objects.create(
                    submission=submission,
                    text_value='Test'
                )

    def test_unique_constraints(self):
        """Test unique constraints"""
        # Test form slug uniqueness
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Form.objects.create(
                    user=self.user,
                    title='Duplicate Form',
                    unique_slug='employee-feedback-2024'  # Same as existing
                )
        
        # Test field order uniqueness within form
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FormField.objects.create(
                    form=self.form,
                    field_type='text',
                    label='Duplicate Field',
                    order_index=0  # Same as existing
                )
        
        # Test that we can create a form with different slug
        different_form = Form.objects.create(
            user=self.user,
            title='Different Form',
            unique_slug='different-form-2024'
        )
        self.assertIsNotNone(different_form)
        
        # Test that we can create a field with different order index
        different_field = FormField.objects.create(
            form=self.form,
            field_type='text',
            label='Different Field',
            order_index=1  # Different order index
        )
        self.assertIsNotNone(different_field)

    def test_model_meta_consistency(self):
        """Test that all models have consistent meta information"""
        models_to_test = [
            (User, 'user'),
            (Category, 'category'),
            (Form, 'form'),
            (FormField, 'form_field'),
            (FieldOption, 'field_option'),
            (Process, 'process'),
            (ProcessStep, 'process_step'),
            (FormSubmission, 'form_submission'),
            (SubmissionAnswer, 'submission_answer'),
            (ProcessProgress, 'process_progress'),
            (ProcessStepCompletion, 'process_step_completion'),
            (FormView, 'form_view'),
            (ProcessView, 'process_view'),
            (Notification, 'notification'),
            (Webhook, 'webhook'),
            (NotificationLog, 'notification_log'),
        ]
        
        for model, expected_table in models_to_test:
            self.assertEqual(model._meta.db_table, expected_table)
            self.assertTrue(hasattr(model, 'id'))
            self.assertEqual(model._meta.get_field('id').__class__.__name__, 'UUIDField')

    def test_json_field_consistency(self):
        """Test that JSON fields work consistently across models"""
        # Test form settings
        form = Form.objects.create(
            user=self.user,
            title='JSON Test Form',
            unique_slug='json-test-form',
            settings={'theme': 'dark', 'allow_multiple': True}
        )
        self.assertIsInstance(form.settings, dict)
        self.assertEqual(form.settings['theme'], 'dark')
        
        # Test field validation rules
        field = FormField.objects.create(
            form=form,
            field_type='number',
            label='Age',
            order_index=0,
            validation_rules={'min': 18, 'max': 100}
        )
        self.assertIsInstance(field.validation_rules, dict)
        self.assertEqual(field.validation_rules['min'], 18)
        
        # Test submission metadata
        submission = FormSubmission.objects.create(
            form=form,
            user=self.user,
            session_id='json-test',
            status='submitted',
            metadata={'device': 'mobile', 'browser': 'safari'}
        )
        self.assertIsInstance(submission.metadata, dict)
        self.assertEqual(submission.metadata['device'], 'mobile')

    def test_model_string_representations(self):
        """Test that all models have meaningful string representations"""
        # Test user
        self.assertEqual(str(self.user), 'test@example.com')
        
        # Test category
        expected_category = f"HR Forms ({self.user.email})"
        self.assertEqual(str(self.category), expected_category)
        
        # Test form
        expected_form = "Employee Feedback Form (employee-feedback-2024)"
        self.assertEqual(str(self.form), expected_form)
        
        # Test field
        expected_field = "Satisfaction Level (Employee Feedback Form)"
        self.assertEqual(str(self.field), expected_field)
        
        # Test option
        expected_option = "Very Satisfied (Satisfaction Level)"
        self.assertEqual(str(self.option), expected_option)
        
        # Test process
        expected_process = "Employee Onboarding (employee-onboarding-2024)"
        self.assertEqual(str(self.process), expected_process)
        
        # Test step
        expected_step = "Personal Information (Employee Onboarding)"
        self.assertEqual(str(self.step), expected_step)
