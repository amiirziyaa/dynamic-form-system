from typing import List, Optional, Dict, Any
from django.db.models import QuerySet, F, Max
from django.contrib.auth import get_user_model

from processes.models import Process, ProcessStep

User = get_user_model()


class ProcessStepRepository:
    """
    Repository class for ProcessStep database operations.
    Handles all database queries and data access logic.
    """

    def get_by_id(self, step_id: str, process: Process) -> Optional[ProcessStep]:
        """
        Get a step by ID for a specific process.
        
        Args:
            step_id: UUID string of the step
            process: Process instance
            
        Returns:
            ProcessStep instance or None if not found
        """
        try:
            return ProcessStep.objects.get(id=step_id, process=process)
        except ProcessStep.DoesNotExist:
            return None

    def get_by_process(self, process: Process) -> QuerySet[ProcessStep]:
        """
        Get all steps for a specific process.
        
        Args:
            process: Process instance
            
        Returns:
            QuerySet of ProcessStep instances ordered by order_index
        """
        return ProcessStep.objects.filter(
            process=process
        ).select_related('form').order_by('order_index')

    def create(self, process: Process, **kwargs) -> ProcessStep:
        """
        Create a new process step.
        
        Args:
            process: Process instance
            **kwargs: ProcessStep fields
            
        Returns:
            Created ProcessStep instance
        """
        return ProcessStep.objects.create(process=process, **kwargs)

    def update(self, step: ProcessStep, **kwargs) -> ProcessStep:
        """
        Update an existing process step.
        
        Args:
            step: ProcessStep instance to update
            **kwargs: Fields to update
            
        Returns:
            Updated ProcessStep instance
        """
        for field, value in kwargs.items():
            setattr(step, field, value)
        step.save()
        return step

    def delete(self, step: ProcessStep) -> bool:
        """
        Delete a process step.
        
        Args:
            step: ProcessStep instance to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            step.delete()
            return True
        except Exception:
            return False

    def get_max_order_index(self, process: Process) -> int:
        """
        Get the maximum order_index for steps in a process.
        
        Args:
            process: Process instance
            
        Returns:
            Maximum order_index or -1 if no steps exist
        """
        result = ProcessStep.objects.filter(
            process=process
        ).aggregate(max_order=Max('order_index'))
        
        return result['max_order'] if result['max_order'] is not None else -1

    def shift_order_indices(self, process: Process, start_index: int, offset: int) -> int:
        """
        Shift order indices for steps starting from a given index.
        
        Args:
            process: Process instance
            start_index: Starting order_index to shift
            offset: Number of positions to shift (positive = right, negative = left)
            
        Returns:
            Number of steps updated
        """
        if offset > 0:
            # Shift right (increment)
            return ProcessStep.objects.filter(
                process=process,
                order_index__gte=start_index
            ).update(order_index=F('order_index') + offset)
        elif offset < 0:
            # Shift left (decrement)
            return ProcessStep.objects.filter(
                process=process,
                order_index__gte=start_index
            ).update(order_index=F('order_index') + offset)
        
        return 0

    def bulk_update_order(self, step_orders: List[Dict[str, Any]]) -> int:
        """
        Bulk update order indices for multiple steps.
        
        Args:
            step_orders: List of dicts with 'id' and 'order_index' keys
            
        Returns:
            Number of steps updated
        """
        if not step_orders:
            return 0
        
        # Use raw SQL update to avoid unique constraint violations
        from django.db import connection
        
        with connection.cursor() as cursor:
            updated_count = 0
            for step_order in step_orders:
                cursor.execute(
                    """
                    UPDATE process_step
                    SET order_index = %s
                    WHERE id = %s
                    """,
                    [step_order['order_index'], step_order['id']]
                )
                updated_count += cursor.rowcount
        
        return updated_count

    def count_by_process(self, process: Process) -> int:
        """
        Count steps for a process.
        
        Args:
            process: Process instance
            
        Returns:
            Number of steps
        """
        return ProcessStep.objects.filter(process=process).count()

    def get_by_order_index(self, process: Process, order_index: int) -> Optional[ProcessStep]:
        """
        Get step by order index for a process.
        
        Args:
            process: Process instance
            order_index: Order index to find
            
        Returns:
            ProcessStep instance or None if not found
        """
        try:
            return ProcessStep.objects.get(process=process, order_index=order_index)
        except ProcessStep.DoesNotExist:
            return None

