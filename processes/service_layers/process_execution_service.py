from typing import List, Optional, Dict, Any
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password
from decimal import Decimal

from processes.models import Process, ProcessStep
from processes.repository import ProcessRepository, ProcessProgressRepository, ProcessStepCompletionRepository
from submissions.models import ProcessProgress, ProcessStepCompletion, FormSubmission
from analytics.models import ProcessView
from shared.exceptions import NotFoundError, ValidationError as CustomValidationError

User = get_user_model()


class ProcessExecutionService:
    """
    Service class for Process execution business logic.
    Handles public process access, progress tracking, and step completion.
    """

    def __init__(self):
        self.process_repository = ProcessRepository()
        self.progress_repository = ProcessProgressRepository()
        self.completion_repository = ProcessStepCompletionRepository()

    def get_public_process(self, slug: str, check_password_required: bool = True) -> Dict[str, Any]:
        """
        Get public process structure for display.
        
        Args:
            slug: Process unique slug
            check_password_required: Whether to check if password is required
            
        Returns:
            Dictionary with process structure
            
        Raises:
            NotFoundError: If process not found
            CustomValidationError: If password required
        """
        process = self.process_repository.get_by_slug_public(slug)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")
        
        if not process.is_active:
            raise CustomValidationError("This process is not active")
        
        requires_password = (
            check_password_required and
            process.visibility == 'private' and
            process.access_password
        )
        
        steps = process.steps.all().order_by('order_index').select_related('form')
        steps_data = []
        for step in steps:
            steps_data.append({
                'id': str(step.id),
                'title': step.title,
                'description': step.description,
                'order_index': step.order_index,
                'is_required': step.is_required,
                'form_slug': step.form.unique_slug,
                'form_title': step.form.title
            })
        
        response = {
            'id': str(process.id),
            'title': process.title,
            'description': process.description,
            'unique_slug': process.unique_slug,
            'process_type': process.process_type,
            'requires_password': requires_password,
            'steps': steps_data,
            'settings': process.settings
        }
        
        if not requires_password:
            response['visibility'] = process.visibility
            response['total_steps'] = len(steps_data)
        
        return response

    def verify_password(self, slug: str, password: str) -> bool:
        """
        Verify password for private process.
        
        Args:
            slug: Process unique slug
            password: Password to verify
            
        Returns:
            True if password is correct
            
        Raises:
            NotFoundError: If process not found
            CustomValidationError: If process is not private
        """
        process = self.process_repository.get_by_slug_public(slug)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")
        
        if process.visibility != 'private':
            raise CustomValidationError("This process is not password protected")
        
        if not process.access_password:
            raise CustomValidationError("This process has no password set")
        
        return check_password(password, process.access_password)

    def track_view(
        self,
        slug: str,
        session_id: str,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessView:
        """
        Track a process view for analytics.
        
        Args:
            slug: Process unique slug
            session_id: Session identifier
            ip_address: Optional IP address
            metadata: Optional metadata
            
        Returns:
            Created ProcessView instance
            
        Raises:
            NotFoundError: If process not found
        """
        process = self.process_repository.get_by_slug_public(slug)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")
        
        return ProcessView.objects.create(
            process=process,
            session_id=session_id,
            ip_address=ip_address,
            metadata=metadata or {}
        )

    def start_process(
        self,
        slug: str,
        session_id: str,
        user: Optional[User] = None
    ) -> ProcessProgress:
        """
        Start a new process progress.
        
        Args:
            slug: Process unique slug
            session_id: Session identifier
            user: Optional authenticated user
            
        Returns:
            Created ProcessProgress instance
            
        Raises:
            NotFoundError: If process not found
            CustomValidationError: If process not active or already started
        """
        process = self.process_repository.get_by_slug_public(slug)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")
        
        if not process.is_active:
            raise CustomValidationError("This process is not active")
        
        existing_progress = self.progress_repository.get_by_process_and_session(
            process,
            session_id
        )
        
        if existing_progress and existing_progress.status == 'in_progress':
            existing_progress.last_activity_at = timezone.now()
            existing_progress.save(update_fields=['last_activity_at'])
            return existing_progress
        
        with transaction.atomic():
            progress = self.progress_repository.create(
                process=process,
                session_id=session_id,
                user=user,
                current_step_index=0,
                status='in_progress'
            )
            
            steps = process.steps.all().order_by('order_index')
            for step in steps:
                self.completion_repository.create(
                    progress=progress,
                    step=step,
                    status='pending'
                )
        
        return progress

    def get_progress(
        self,
        slug: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get progress for a process and session.
        
        Args:
            slug: Process unique slug
            session_id: Session identifier
            
        Returns:
            Dictionary with progress information
            
        Raises:
            NotFoundError: If process or progress not found
        """
        process = self.process_repository.get_by_slug_public(slug)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")
        
        progress = self.progress_repository.get_by_process_and_session(
            process,
            session_id
        )
        
        if not progress:
            raise NotFoundError("No progress found for this process and session")
        
        completions = self.completion_repository.get_by_progress(progress)
        completions_dict = {
            str(comp.step.id): {
                'status': comp.status,
                'completed_at': comp.completed_at.isoformat() if comp.completed_at else None
            }
            for comp in completions
        }
        
        current_step = None
        steps = process.steps.all().order_by('order_index')
        if progress.current_step_index < steps.count():
            current_step_obj = steps[progress.current_step_index]
            current_step = {
                'id': str(current_step_obj.id),
                'title': current_step_obj.title,
                'order_index': current_step_obj.order_index,
                'form_slug': current_step_obj.form.unique_slug
            }
        
        return {
            'id': str(progress.id),
            'status': progress.status,
            'current_step_index': progress.current_step_index,
            'current_step': current_step,
            'completion_percentage': float(progress.completion_percentage),
            'started_at': progress.started_at.isoformat(),
            'last_activity_at': progress.last_activity_at.isoformat(),
            'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
            'step_completions': completions_dict
        }

    def get_current_step(
        self,
        slug: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get current step information.
        
        Args:
            slug: Process unique slug
            session_id: Session identifier
            
        Returns:
            Dictionary with current step information
            
        Raises:
            NotFoundError: If process or progress not found
        """
        progress_data = self.get_progress(slug, session_id)
        
        if not progress_data.get('current_step'):
            raise NotFoundError("No current step available")
        
        return progress_data['current_step']

    def move_to_next_step(
        self,
        slug: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Move to next step (linear processes only).
        
        Args:
            slug: Process unique slug
            session_id: Session identifier
            
        Returns:
            Dictionary with updated progress
            
        Raises:
            NotFoundError: If process or progress not found
            CustomValidationError: If process is not linear or already at last step
        """
        process = self.process_repository.get_by_slug_public(slug)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")
        
        if process.process_type != 'linear':
            raise CustomValidationError("This operation is only available for linear processes")
        
        progress = self.progress_repository.get_by_process_and_session(
            process,
            session_id
        )
        
        if not progress:
            raise NotFoundError("No progress found for this process and session")
        
        total_steps = process.steps.count()
        current_index = progress.current_step_index
        
        if current_index >= total_steps - 1:
            raise CustomValidationError("Already at the last step")
        
        with transaction.atomic():
            self.progress_repository.update_current_step(
                progress,
                current_index + 1
            )
        
        return self.get_progress(slug, session_id)

    def move_to_previous_step(
        self,
        slug: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Move to previous step (linear processes only).
        
        Args:
            slug: Process unique slug
            session_id: Session identifier
            
        Returns:
            Dictionary with updated progress
            
        Raises:
            NotFoundError: If process or progress not found
            CustomValidationError: If process is not linear or already at first step
        """
        process = self.process_repository.get_by_slug_public(slug)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")
        
        if process.process_type != 'linear':
            raise CustomValidationError("This operation is only available for linear processes")
        
        progress = self.progress_repository.get_by_process_and_session(
            process,
            session_id
        )
        
        if not progress:
            raise NotFoundError("No progress found for this process and session")
        
        current_index = progress.current_step_index
        
        if current_index <= 0:
            raise CustomValidationError("Already at the first step")
        
        with transaction.atomic():
            self.progress_repository.update_current_step(
                progress,
                current_index - 1
            )
        
        return self.get_progress(slug, session_id)

    def get_step_form(self, slug: str, step_id: str) -> Dict[str, Any]:
        """
        Get form structure for a step.
        
        Args:
            slug: Process unique slug
            step_id: Step UUID string
            
        Returns:
            Dictionary with form structure
            
        Raises:
            NotFoundError: If process or step not found
        """
        process = self.process_repository.get_by_slug_public(slug)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")
        
        try:
            step = process.steps.get(id=step_id)
        except ProcessStep.DoesNotExist:
            raise NotFoundError(f"Step with id '{step_id}' not found in this process")
        
        return {
            'step_id': str(step.id),
            'step_title': step.title,
            'step_description': step.description,
            'form_id': str(step.form.id),
            'form_slug': step.form.unique_slug,
            'form_title': step.form.title,
            'form_description': step.form.description
        }

    def complete_step(
        self,
        slug: str,
        step_id: str,
        session_id: str,
        submission_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete a step with optional form submission.
        
        Args:
            slug: Process unique slug
            step_id: Step UUID string
            session_id: Session identifier
            submission_id: Optional form submission UUID
            
        Returns:
            Dictionary with completion information
            
        Raises:
            NotFoundError: If process, step, or progress not found
            CustomValidationError: If validation fails
        """
        process = self.process_repository.get_by_slug_public(slug)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")
        
        try:
            step = process.steps.get(id=step_id)
        except ProcessStep.DoesNotExist:
            raise NotFoundError(f"Step with id '{step_id}' not found in this process")
        
        progress = self.progress_repository.get_by_process_and_session(
            process,
            session_id
        )
        
        if not progress:
            raise NotFoundError("No progress found for this process and session")
        
        completion = self.completion_repository.get_by_progress_and_step(
            progress,
            step
        )
        
        if not completion:
            completion = self.completion_repository.create(
                progress=progress,
                step=step,
                status='pending'
            )
        
        submission = None
        if submission_id:
            try:
                submission = FormSubmission.objects.get(id=submission_id)
                if submission.session_id != session_id:
                    raise CustomValidationError("Submission does not belong to this session")
            except FormSubmission.DoesNotExist:
                raise NotFoundError(f"Submission with id '{submission_id}' not found")
        
        with transaction.atomic():
            self.completion_repository.mark_completed(completion, submission)
            self.progress_repository.update_completion_percentage(progress)
            progress.last_activity_at = timezone.now()
            progress.save(update_fields=['last_activity_at'])
        
        return {
            'step_id': str(step.id),
            'step_title': step.title,
            'status': 'completed',
            'completed_at': completion.completed_at.isoformat() if completion.completed_at else None,
            'completion_percentage': float(progress.completion_percentage)
        }

    def complete_process(
        self,
        slug: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Mark process as completed.
        
        Args:
            slug: Process unique slug
            session_id: Session identifier
            
        Returns:
            Dictionary with completion information
            
        Raises:
            NotFoundError: If process or progress not found
            CustomValidationError: If not all required steps are completed
        """
        process = self.process_repository.get_by_slug_public(slug)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")
        
        progress = self.progress_repository.get_by_process_and_session(
            process,
            session_id
        )
        
        if not progress:
            raise NotFoundError("No progress found for this process and session")
        
        if progress.status == 'completed':
            return {
                'status': 'completed',
                'message': 'Process already completed',
                'completed_at': progress.completed_at.isoformat() if progress.completed_at else None
            }
        
        required_steps = process.steps.filter(is_required=True)
        completions = self.completion_repository.get_by_progress(progress)
        
        completed_required_steps = completions.filter(
            step__in=required_steps,
            status='completed'
        ).count()
        
        if completed_required_steps < required_steps.count():
            raise CustomValidationError(
                f"Not all required steps are completed. "
                f"Completed: {completed_required_steps}/{required_steps.count()}"
            )
        
        with transaction.atomic():
            self.progress_repository.mark_completed(progress)
        
        return {
            'status': 'completed',
            'message': 'Process completed successfully',
            'completed_at': progress.completed_at.isoformat(),
            'completion_percentage': 100.0
        }

