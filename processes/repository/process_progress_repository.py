from typing import List, Optional, Dict, Any
from django.db.models import QuerySet
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from submissions.models import ProcessProgress, ProcessStepCompletion

User = get_user_model()


class ProcessProgressRepository:
    """
    Repository class for ProcessProgress database operations.
    Handles all database queries and data access logic.
    """

    def get_by_id(self, progress_id: str) -> Optional[ProcessProgress]:
        """
        Get a progress record by ID.
        
        Args:
            progress_id: UUID string of the progress
            
        Returns:
            ProcessProgress instance or None if not found
        """
        try:
            return ProcessProgress.objects.get(id=progress_id)
        except ProcessProgress.DoesNotExist:
            return None

    def get_by_process_and_session(
        self,
        process,
        session_id: str
    ) -> Optional[ProcessProgress]:
        """
        Get progress record for a process and session.
        
        Args:
            process: Process instance
            session_id: Session identifier
            
        Returns:
            ProcessProgress instance or None if not found
        """
        try:
            return ProcessProgress.objects.get(
                process=process,
                session_id=session_id
            )
        except ProcessProgress.DoesNotExist:
            return None

    def get_by_session(self, session_id: str) -> QuerySet[ProcessProgress]:
        """
        Get all progress records for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            QuerySet of ProcessProgress instances
        """
        return ProcessProgress.objects.filter(session_id=session_id)

    def create(
        self,
        process,
        session_id: str,
        user: Optional[User] = None,
        current_step_index: int = 0,
        status: str = 'in_progress'
    ) -> ProcessProgress:
        """
        Create a new progress record.
        
        Args:
            process: Process instance
            session_id: Session identifier
            user: Optional User instance
            current_step_index: Initial step index
            status: Initial status
            
        Returns:
            Created ProcessProgress instance
        """
        return ProcessProgress.objects.create(
            process=process,
            user=user,
            session_id=session_id,
            status=status,
            current_step_index=current_step_index,
            completion_percentage=Decimal('0.00')
        )

    def update(
        self,
        progress: ProcessProgress,
        **kwargs
    ) -> ProcessProgress:
        """
        Update a progress record.
        
        Args:
            progress: ProcessProgress instance to update
            **kwargs: Fields to update
            
        Returns:
            Updated ProcessProgress instance
        """
        for field, value in kwargs.items():
            setattr(progress, field, value)
        progress.save()
        return progress

    def update_current_step(
        self,
        progress: ProcessProgress,
        step_index: int
    ) -> ProcessProgress:
        """
        Update current step index and last activity.
        
        Args:
            progress: ProcessProgress instance
            step_index: New step index
            
        Returns:
            Updated ProcessProgress instance
        """
        progress.current_step_index = step_index
        progress.last_activity_at = timezone.now()
        progress.save(update_fields=['current_step_index', 'last_activity_at'])
        return progress

    def calculate_completion_percentage(
        self,
        progress: ProcessProgress
    ) -> Decimal:
        """
        Calculate completion percentage based on completed steps.
        
        Args:
            progress: ProcessProgress instance
            
        Returns:
            Completion percentage (0.00 to 100.00)
        """
        total_steps = progress.process.steps.count()
        if total_steps == 0:
            return Decimal('0.00')
        
        completed_steps = ProcessStepCompletion.objects.filter(
            progress=progress,
            status='completed'
        ).count()
        
        percentage = (Decimal(completed_steps) / Decimal(total_steps)) * Decimal('100.00')
        return percentage.quantize(Decimal('0.01'))

    def update_completion_percentage(self, progress: ProcessProgress) -> ProcessProgress:
        """
        Update completion percentage for a progress record.
        
        Args:
            progress: ProcessProgress instance
            
        Returns:
            Updated ProcessProgress instance
        """
        progress.completion_percentage = self.calculate_completion_percentage(progress)
        progress.save(update_fields=['completion_percentage'])
        return progress

    def mark_completed(self, progress: ProcessProgress) -> ProcessProgress:
        """
        Mark progress as completed.
        
        Args:
            progress: ProcessProgress instance
            
        Returns:
            Updated ProcessProgress instance
        """
        progress.status = 'completed'
        progress.completed_at = timezone.now()
        progress.completion_percentage = Decimal('100.00')
        progress.last_activity_at = timezone.now()
        progress.save()
        return progress

    def mark_abandoned(self, progress: ProcessProgress) -> ProcessProgress:
        """
        Mark progress as abandoned.
        
        Args:
            progress: ProcessProgress instance
            
        Returns:
            Updated ProcessProgress instance
        """
        progress.status = 'abandoned'
        progress.last_activity_at = timezone.now()
        progress.save()
        return progress

    def delete(self, progress: ProcessProgress) -> bool:
        """
        Delete a progress record.
        
        Args:
            progress: ProcessProgress instance to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            progress.delete()
            return True
        except Exception:
            return False


class ProcessStepCompletionRepository:
    """
    Repository class for ProcessStepCompletion database operations.
    """

    def get_by_id(self, completion_id: str) -> Optional[ProcessStepCompletion]:
        """
        Get a completion record by ID.
        
        Args:
            completion_id: UUID string of the completion
            
        Returns:
            ProcessStepCompletion instance or None if not found
        """
        try:
            return ProcessStepCompletion.objects.get(id=completion_id)
        except ProcessStepCompletion.DoesNotExist:
            return None

    def get_by_progress_and_step(
        self,
        progress: ProcessProgress,
        step
    ) -> Optional[ProcessStepCompletion]:
        """
        Get completion record for a progress and step.
        
        Args:
            progress: ProcessProgress instance
            step: ProcessStep instance
            
        Returns:
            ProcessStepCompletion instance or None if not found
        """
        try:
            return ProcessStepCompletion.objects.get(
                progress=progress,
                step=step
            )
        except ProcessStepCompletion.DoesNotExist:
            return None

    def get_by_progress(
        self,
        progress: ProcessProgress
    ) -> QuerySet[ProcessStepCompletion]:
        """
        Get all completion records for a progress.
        
        Args:
            progress: ProcessProgress instance
            
        Returns:
            QuerySet of ProcessStepCompletion instances
        """
        return ProcessStepCompletion.objects.filter(progress=progress)

    def create(
        self,
        progress: ProcessProgress,
        step,
        submission=None,
        status: str = 'pending'
    ) -> ProcessStepCompletion:
        """
        Create a new completion record.
        
        Args:
            progress: ProcessProgress instance
            step: ProcessStep instance
            submission: Optional FormSubmission instance
            status: Initial status
            
        Returns:
            Created ProcessStepCompletion instance
        """
        return ProcessStepCompletion.objects.create(
            progress=progress,
            step=step,
            submission=submission,
            status=status
        )

    def update(
        self,
        completion: ProcessStepCompletion,
        **kwargs
    ) -> ProcessStepCompletion:
        """
        Update a completion record.
        
        Args:
            completion: ProcessStepCompletion instance to update
            **kwargs: Fields to update
            
        Returns:
            Updated ProcessStepCompletion instance
        """
        for field, value in kwargs.items():
            setattr(completion, field, value)
        completion.save()
        return completion

    def mark_completed(
        self,
        completion: ProcessStepCompletion,
        submission=None
    ) -> ProcessStepCompletion:
        """
        Mark step as completed.
        
        Args:
            completion: ProcessStepCompletion instance
            submission: Optional FormSubmission instance
            
        Returns:
            Updated ProcessStepCompletion instance
        """
        completion.status = 'completed'
        completion.completed_at = timezone.now()
        if submission:
            completion.submission = submission
        completion.save()
        return completion

    def mark_skipped(self, completion: ProcessStepCompletion) -> ProcessStepCompletion:
        """
        Mark step as skipped.
        
        Args:
            completion: ProcessStepCompletion instance
            
        Returns:
            Updated ProcessStepCompletion instance
        """
        completion.status = 'skipped'
        completion.save()
        return completion

    def delete(self, completion: ProcessStepCompletion) -> bool:
        """
        Delete a completion record.
        
        Args:
            completion: ProcessStepCompletion instance to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            completion.delete()
            return True
        except Exception:
            return False

