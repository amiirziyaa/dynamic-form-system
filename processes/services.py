from typing import List, Optional, Dict, Any
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.text import slugify
from django.contrib.auth.hashers import make_password
from django.utils import timezone
import uuid
import uuid as uuid_module

from processes.models import Process, ProcessStep
from django.db.models import F
from processes.repository import ProcessRepository, ProcessStepRepository
from shared.exceptions import NotFoundError, ValidationError as CustomValidationError

User = get_user_model()


class ProcessService:
    """
    Service class for Process business logic.
    Handles all business rules and orchestrates repository operations.
    """

    def __init__(self):
        self.repository = ProcessRepository()

    def create_process(
        self,
        user: User,
        title: str,
        description: Optional[str] = None,
        category_id: Optional[str] = None,
        unique_slug: Optional[str] = None,
        visibility: str = 'public',
        access_password: Optional[str] = None,
        process_type: str = 'linear',
        is_active: bool = True,
        settings: Optional[Dict[str, Any]] = None
    ) -> Process:
        """
        Create a new process with business logic validation.
        
        Args:
            user: User instance
            title: Process title
            description: Optional description
            category_id: Optional category ID
            unique_slug: Optional slug (will be generated if not provided)
            visibility: Visibility level ('public' or 'private')
            access_password: Password for private processes
            process_type: Process type ('linear' or 'free')
            is_active: Whether process is active
            settings: Optional JSON settings
            
        Returns:
            Created Process instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate inputs
        self._validate_process_data(title, visibility, access_password, process_type)
        
        # Generate slug if not provided
        if not unique_slug:
            unique_slug = self._generate_unique_slug(title)
        
        # Validate slug uniqueness
        if self.repository.exists_by_slug(unique_slug):
            unique_slug = self._generate_unique_slug(title)
        
        # Encrypt password if provided
        if visibility == 'private' and access_password:
            access_password = make_password(access_password)
        elif visibility == 'public':
            access_password = None
        
        # Create process
        try:
            with transaction.atomic():
                process = self.repository.create(
                    user=user,
                    title=title.strip(),
                    description=description.strip() if description else None,
                    category_id=category_id,
                    unique_slug=unique_slug,
                    visibility=visibility,
                    access_password=access_password,
                    process_type=process_type,
                    is_active=is_active,
                    settings=settings or {}
                )
                return process
        except Exception as e:
            raise CustomValidationError(f"Failed to create process: {str(e)}")

    def get_process(self, user: User, slug: str) -> Process:
        """
        Get a process by slug for a user.
        
        Args:
            user: User instance
            slug: Process unique slug
            
        Returns:
            Process instance
            
        Raises:
            NotFoundError: If process not found
        """
        process = self.repository.get_by_slug(slug, user)
        if not process:
            raise NotFoundError(f"Process with slug '{slug}' not found")
        return process

    def update_process(
        self,
        user: User,
        slug: str,
        **kwargs
    ) -> Process:
        """
        Update an existing process.
        
        Args:
            user: User instance
            slug: Process unique slug
            **kwargs: Fields to update
            
        Returns:
            Updated Process instance
            
        Raises:
            NotFoundError: If process not found
            ValidationError: If validation fails
        """
        process = self.get_process(user, slug)
        
        # Validate updated fields
        if 'title' in kwargs:
            self._validate_process_data(
                kwargs['title'],
                kwargs.get('visibility', process.visibility),
                kwargs.get('access_password'),
                kwargs.get('process_type', process.process_type)
            )
        
        # Handle slug update
        if 'unique_slug' in kwargs:
            new_slug = kwargs['unique_slug']
            if new_slug != process.unique_slug:
                if self.repository.exists_by_slug(new_slug, exclude_id=str(process.id)):
                    raise CustomValidationError(f"A process with slug '{new_slug}' already exists")
        
        # Handle password update
        if 'access_password' in kwargs and kwargs.get('visibility') == 'private':
            if kwargs['access_password']:
                kwargs['access_password'] = make_password(kwargs['access_password'])
        elif kwargs.get('visibility') == 'public':
            kwargs['access_password'] = None
        
        # Update process
        try:
            return self.repository.update(process, **kwargs)
        except Exception as e:
            raise CustomValidationError(f"Failed to update process: {str(e)}")

    def delete_process(self, user: User, slug: str) -> bool:
        """
        Delete a process.
        
        Args:
            user: User instance
            slug: Process unique slug
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If process not found
        """
        process = self.get_process(user, slug)
        return self.repository.delete(process)

    def duplicate_process(self, user: User, slug: str) -> Process:
        """
        Duplicate a process with all its steps.
        
        Args:
            user: User instance
            slug: Process unique slug to duplicate
            
        Returns:
            Duplicated Process instance
            
        Raises:
            NotFoundError: If process not found
        """
        original_process = self.get_process(user, slug)
        step_repository = ProcessStepRepository()
        
        with transaction.atomic():
            # Create new process
            new_slug = f"{original_process.unique_slug}-copy-{uuid.uuid4().hex[:6]}"
            new_process = self.repository.create(
                user=user,
                category=original_process.category,
                title=f"{original_process.title} (Copy)",
                description=original_process.description,
                unique_slug=new_slug,
                visibility=original_process.visibility,
                access_password=original_process.access_password,
                process_type=original_process.process_type,
                is_active=original_process.is_active,
                settings=original_process.settings.copy() if original_process.settings else {}
            )
            
            # Duplicate steps
            for step in step_repository.get_by_process(original_process):
                step_repository.create(
                    process=new_process,
                    form=step.form,
                    title=step.title,
                    description=step.description,
                    order_index=step.order_index,
                    is_required=step.is_required,
                    conditions=step.conditions.copy() if step.conditions else {}
                )
            
            return new_process

    def publish_process(self, user: User, slug: str, is_published: bool = True) -> Process:
        """
        Publish or unpublish a process.
        
        Args:
            user: User instance
            slug: Process unique slug
            is_published: Whether to publish (True) or unpublish (False)
            
        Returns:
            Updated Process instance
            
        Raises:
            NotFoundError: If process not found
        """
        process = self.get_process(user, slug)
        
        if is_published and not process.published_at:
            return self.repository.update(process, published_at=timezone.now())
        elif not is_published:
            return self.repository.update(process, published_at=None)
        
        return process

    def get_user_processes(self, user: User, prefetch_steps: bool = False):
        """
        Get all processes for a user.
        
        Args:
            user: User instance
            prefetch_steps: Whether to prefetch steps
            
        Returns:
            QuerySet of Process instances
        """
        return self.repository.get_by_user(user, prefetch_steps=prefetch_steps)

    def _generate_unique_slug(self, title: str) -> str:
        """
        Generate a unique slug from title.
        
        Args:
            title: Process title
            
        Returns:
            Unique slug
        """
        base_slug = slugify(title)
        if not base_slug:
            base_slug = "process"
        
        slug = base_slug
        counter = 1
        
        while self.repository.exists_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug

    def _validate_process_data(
        self,
        title: str,
        visibility: str = 'public',
        access_password: Optional[str] = None,
        process_type: str = 'linear'
    ) -> None:
        """
        Validate process data.
        
        Args:
            title: Process title
            visibility: Visibility level
            access_password: Access password
            process_type: Process type
            
        Raises:
            ValidationError: If validation fails
        """
        if not title or not title.strip():
            raise CustomValidationError("Process title is required")
        
        if visibility not in ['public', 'private']:
            raise CustomValidationError("Visibility must be 'public' or 'private'")
        
        if process_type not in ['linear', 'free']:
            raise CustomValidationError("Process type must be 'linear' or 'free'")
        
        if visibility == 'private' and not access_password:
            raise CustomValidationError("Password is required for private processes")


class ProcessStepService:
    """
    Service class for ProcessStep business logic.
    Handles all business rules and orchestrates repository operations.
    """

    def __init__(self):
        self.repository = ProcessStepRepository()
        self.process_repository = ProcessRepository()

    def create_step(
        self,
        user: User,
        process_slug: str,
        form_id: str,
        title: str,
        description: Optional[str] = None,
        order_index: Optional[int] = None,
        is_required: bool = True,
        conditions: Optional[Dict[str, Any]] = None
    ) -> ProcessStep:
        """
        Create a new process step.
        
        Args:
            user: User instance
            process_slug: Process unique slug
            form_id: Form UUID string
            title: Step title
            description: Optional description
            order_index: Optional order index (will be set to last if not provided)
            is_required: Whether step is required
            conditions: Optional conditions JSON
            
        Returns:
            Created ProcessStep instance
            
        Raises:
            NotFoundError: If process not found
            ValidationError: If validation fails
        """
        # Get process
        process = self.process_repository.get_by_slug(process_slug, user)
        if not process:
            raise NotFoundError(f"Process with slug '{process_slug}' not found")
        
        # Validate inputs
        if not title or not title.strip():
            raise CustomValidationError("Step title is required")
        
        # Determine order_index
        if order_index is None:
            order_index = self.repository.count_by_process(process)
        elif order_index < 0:
            raise CustomValidationError("Order index cannot be negative")
        
        # Check if order_index conflicts
        existing_step = self.repository.get_by_order_index(process, order_index)
        if existing_step:
            # Shift existing steps
            self.repository.shift_order_indices(process, order_index, 1)
        
        # Create step
        try:
            from forms.models import Form
            form = Form.objects.get(id=form_id)
            
            return self.repository.create(
                process=process,
                form=form,
                title=title.strip(),
                description=description.strip() if description else None,
                order_index=order_index,
                is_required=is_required,
                conditions=conditions or {}
            )
        except Exception as e:
            raise CustomValidationError(f"Failed to create step: {str(e)}")

    def get_step(self, user: User, process_slug: str, step_id: str) -> ProcessStep:
        """
        Get a step by ID for a process.
        
        Args:
            user: User instance
            process_slug: Process unique slug
            step_id: Step UUID string
            
        Returns:
            ProcessStep instance
            
        Raises:
            NotFoundError: If process or step not found
        """
        process = self.process_repository.get_by_slug(process_slug, user)
        if not process:
            raise NotFoundError(f"Process with slug '{process_slug}' not found")
        
        step = self.repository.get_by_id(step_id, process)
        if not step:
            raise NotFoundError(f"Step with id '{step_id}' not found")
        
        return step

    def update_step(
        self,
        user: User,
        process_slug: str,
        step_id: str,
        **kwargs
    ) -> ProcessStep:
        """
        Update an existing step.
        
        Args:
            user: User instance
            process_slug: Process unique slug
            step_id: Step UUID string
            **kwargs: Fields to update
            
        Returns:
            Updated ProcessStep instance
            
        Raises:
            NotFoundError: If process or step not found
            ValidationError: If validation fails
        """
        step = self.get_step(user, process_slug, step_id)
        
        # Handle order_index change
        if 'order_index' in kwargs:
            new_order = kwargs['order_index']
            old_order = step.order_index
            
            if new_order != old_order:
                if new_order < 0:
                    raise CustomValidationError("Order index cannot be negative")
                
                # Get all steps for this process
                all_steps = list(ProcessStep.objects.filter(process=step.process).order_by('order_index'))
                
                # Get max order_index to use as temporary values
                max_order = self.repository.get_max_order_index(step.process)
                temp_start = max_order + 2000
                
                # Remove the step being updated from the list
                step_to_move = None
                for s in all_steps:
                    if s.id == step.id:
                        step_to_move = s
                        break
                if not step_to_move:
                    step_to_move = step  # Fallback to the passed step
                else:
                    all_steps.remove(step_to_move)
                
                # Create new ordering
                if new_order > len(all_steps):
                    new_order = len(all_steps)
                
                # Insert at new position
                all_steps.insert(new_order, step_to_move)
                
                # Update all order indices using direct DB updates
                # First set all to temporary values to avoid conflicts
                with transaction.atomic():
                    # Step 1: Set all to temporary values
                    for idx, s in enumerate(all_steps):
                        ProcessStep.objects.filter(id=s.id).update(order_index=temp_start + idx)
                    
                    # Step 2: Now set final values
                    for idx, s in enumerate(all_steps):
                        ProcessStep.objects.filter(id=s.id).update(order_index=idx)
                
                # Refresh the step from DB to get updated order_index
                step.refresh_from_db()
                
                # Remove order_index from kwargs since we handled it
                kwargs.pop('order_index')
        
        # Validate title if provided
        if 'title' in kwargs and (not kwargs['title'] or not kwargs['title'].strip()):
            raise CustomValidationError("Step title cannot be empty")
        
        # Handle form update
        if 'form_id' in kwargs:
            from forms.models import Form
            try:
                form = Form.objects.get(id=kwargs.pop('form_id'))
                kwargs['form'] = form
            except Form.DoesNotExist:
                raise CustomValidationError("Form not found")
        
        # Update step
        try:
            return self.repository.update(step, **kwargs)
        except Exception as e:
            raise CustomValidationError(f"Failed to update step: {str(e)}")

    def delete_step(self, user: User, process_slug: str, step_id: str) -> bool:
        """
        Delete a step.
        
        Args:
            user: User instance
            process_slug: Process unique slug
            step_id: Step UUID string
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If process or step not found
        """
        step = self.get_step(user, process_slug, step_id)
        order_index = step.order_index
        
        # Delete step
        result = self.repository.delete(step)
        
        if result:
            # Shift remaining steps
            self.repository.shift_order_indices(step.process, order_index + 1, -1)
        
        return result

    def get_process_steps(self, user: User, process_slug: str):
        """
        Get all steps for a process.
        
        Args:
            user: User instance
            process_slug: Process unique slug
            
        Returns:
            QuerySet of ProcessStep instances
            
        Raises:
            NotFoundError: If process not found
        """
        process = self.process_repository.get_by_slug(process_slug, user)
        if not process:
            raise NotFoundError(f"Process with slug '{process_slug}' not found")
        
        return self.repository.get_by_process(process)

    def reorder_steps(
        self,
        user: User,
        process_slug: str,
        step_ids: List[Any]  # Can be strings or UUIDs
    ) -> Dict[str, Any]:
        """
        Reorder steps in bulk.
        
        Args:
            user: User instance
            process_slug: Process unique slug
            step_ids: List of step IDs in desired order
            
        Returns:
            Dictionary with reorder results
            
        Raises:
            NotFoundError: If process not found
            ValidationError: If validation fails
        """
        process = self.process_repository.get_by_slug(process_slug, user)
        if not process:
            raise NotFoundError(f"Process with slug '{process_slug}' not found")
        
        # Convert step_ids to UUIDs for querying
        step_uuids = []
        for step_id in step_ids:
            if isinstance(step_id, uuid_module.UUID):
                step_uuids.append(step_id)
            elif isinstance(step_id, str):
                try:
                    step_uuids.append(uuid_module.UUID(step_id))
                except (ValueError, AttributeError):
                    raise CustomValidationError(f"Invalid step ID: {step_id}")
        
        # Validate all steps belong to this process
        steps = list(self.repository.get_by_process(process).filter(id__in=step_uuids))
        
        if len(steps) != len(step_ids):
            raise CustomValidationError("Some step IDs do not belong to this process")
        
        # Check for duplicates
        if len(step_ids) != len(set(step_ids)):
            raise CustomValidationError("Duplicate step IDs are not allowed")
        
        # Get max order_index to use as temporary values
        max_order = self.repository.get_max_order_index(process)
        temp_start = max_order + 1000  # Use higher value to ensure no conflicts
        
        # Map step IDs (as strings) to steps
        steps_dict = {str(s.id): s for s in steps}
        # Also create mapping for UUID objects
        for step in steps:
            steps_dict[str(step.id)] = step
        
        # Use direct database updates to avoid conflicts
        with transaction.atomic():
            # Step 1: Move all steps to temporary positions using direct SQL
            for idx, step_id in enumerate(step_ids):
                # Normalize step_id to string for lookup
                step_id_str = str(step_id) if not isinstance(step_id, str) else step_id
                step = steps_dict.get(step_id_str)
                if step:
                    temp_order = temp_start + idx
                    ProcessStep.objects.filter(id=step.id).update(order_index=temp_order)
            
            # Step 2: Now set final order indices
            for index, step_id_val in enumerate(step_ids):
                # Convert to UUID for query
                if isinstance(step_id_val, uuid_module.UUID):
                    step_uuid = step_id_val
                elif isinstance(step_id_val, str):
                    step_uuid = uuid_module.UUID(step_id_val)
                else:
                    continue
                ProcessStep.objects.filter(id=step_uuid).update(order_index=index)
            
            updated_count = len(step_ids)
        
        return {
            'updated_count': updated_count,
            'step_ids': step_ids
        }

