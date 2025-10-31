from typing import List, Optional, Dict, Any
from django.db.models import QuerySet, Q, Count
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

from processes.models import Process

User = get_user_model()


class ProcessRepository:
    """
    Repository class for Process database operations.
    Handles all database queries and data access logic.
    """

    def get_by_id(self, process_id: str, user: User) -> Optional[Process]:
        """
        Get a process by ID for a specific user.
        
        Args:
            process_id: UUID string of the process
            user: User instance
            
        Returns:
            Process instance or None if not found
        """
        try:
            return Process.objects.get(id=process_id, user=user)
        except Process.DoesNotExist:
            return None

    def get_by_slug(self, slug: str, user: User) -> Optional[Process]:
        """
        Get a process by unique slug for a specific user.
        
        Args:
            slug: Unique slug of the process
            user: User instance
            
        Returns:
            Process instance or None if not found
        """
        try:
            return Process.objects.get(unique_slug=slug, user=user)
        except Process.DoesNotExist:
            return None

    def get_by_slug_public(self, slug: str) -> Optional[Process]:
        """
        Get a process by unique slug for public access (active processes only).
        
        Args:
            slug: Unique slug of the process
            
        Returns:
            Process instance or None if not found
        """
        try:
            return Process.objects.get(unique_slug=slug, is_active=True)
        except Process.DoesNotExist:
            return None

    def get_by_user(self, user: User, prefetch_steps: bool = False) -> QuerySet[Process]:
        """
        Get all processes for a specific user.
        
        Args:
            user: User instance
            prefetch_steps: Whether to prefetch related steps
            
        Returns:
            QuerySet of Process instances
        """
        queryset = Process.objects.filter(user=user)
        
        if prefetch_steps:
            queryset = queryset.prefetch_related('steps__form')
        else:
            queryset = queryset.annotate(steps_count=Count('steps'))
            
        return queryset.order_by('-created_at')

    def create(self, user: User, **kwargs) -> Process:
        """
        Create a new process.
        
        Args:
            user: User instance
            **kwargs: Process fields
            
        Returns:
            Created Process instance
        """
        return Process.objects.create(user=user, **kwargs)

    def update(self, process: Process, **kwargs) -> Process:
        """
        Update an existing process.
        
        Args:
            process: Process instance to update
            **kwargs: Fields to update
            
        Returns:
            Updated Process instance
        """
        for field, value in kwargs.items():
            setattr(process, field, value)
        process.save()
        return process

    def delete(self, process: Process) -> bool:
        """
        Delete a process.
        
        Args:
            process: Process instance to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            process.delete()
            return True
        except Exception:
            return False

    def search(self, user: User, query: str) -> QuerySet[Process]:
        """
        Search processes by title or description.
        
        Args:
            user: User instance
            query: Search query string
            
        Returns:
            QuerySet of matching Process instances
        """
        return Process.objects.filter(
            user=user
        ).filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).order_by('-created_at')

    def exists_by_slug(self, slug: str, exclude_id: Optional[str] = None) -> bool:
        """
        Check if a process with the given slug exists.
        
        Args:
            slug: Process slug to check
            exclude_id: Process ID to exclude from check (for updates)
            
        Returns:
            True if process exists, False otherwise
        """
        queryset = Process.objects.filter(unique_slug=slug)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()

    def get_paginated(self, user: User, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Get paginated processes for a user.
        
        Args:
            user: User instance
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Dictionary with paginated results and metadata
        """
        queryset = self.get_by_user(user)
        paginator = Paginator(queryset, page_size)
        
        try:
            page_obj = paginator.page(page)
        except Exception:
            page_obj = paginator.page(1)
            
        return {
            'results': page_obj.object_list,
            'pagination': {
                'page': page_obj.number,
                'pages': paginator.num_pages,
                'total': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
                'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
            }
        }

    def filter_by_category(self, user: User, category_id: str) -> QuerySet[Process]:
        """
        Get processes filtered by category.
        
        Args:
            user: User instance
            category_id: Category ID to filter by
            
        Returns:
            QuerySet of Process instances
        """
        return Process.objects.filter(
            user=user,
            category_id=category_id
        ).annotate(steps_count=Count('steps')).order_by('-created_at')

    def filter_by_type(self, user: User, process_type: str) -> QuerySet[Process]:
        """
        Get processes filtered by process type.
        
        Args:
            user: User instance
            process_type: Process type ('linear' or 'free')
            
        Returns:
            QuerySet of Process instances
        """
        return Process.objects.filter(
            user=user,
            process_type=process_type
        ).annotate(steps_count=Count('steps')).order_by('-created_at')

    def filter_by_visibility(self, user: User, visibility: str) -> QuerySet[Process]:
        """
        Get processes filtered by visibility.
        
        Args:
            user: User instance
            visibility: Visibility level ('public' or 'private')
            
        Returns:
            QuerySet of Process instances
        """
        return Process.objects.filter(
            user=user,
            visibility=visibility
        ).annotate(steps_count=Count('steps')).order_by('-created_at')

