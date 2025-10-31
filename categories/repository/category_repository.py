from typing import List, Optional, Dict, Any
from django.db import models
from django.db.models import QuerySet, Q, Count
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

from categories.models import Category

User = get_user_model()


class CategoryRepository:
    """
    Repository class for Category database operations.
    Handles all database queries and data access logic.
    """

    def get_by_id(self, category_id: str, user: User) -> Optional[Category]:
        """
        Get a category by ID for a specific user.
        
        Args:
            category_id: UUID string of the category
            user: User instance
            
        Returns:
            Category instance or None if not found
        """
        try:
            return Category.objects.get(id=category_id, user=user)
        except Category.DoesNotExist:
            return None

    def get_by_user(self, user: User) -> QuerySet[Category]:
        """
        Get all categories for a specific user.
        
        Args:
            user: User instance
            
        Returns:
            QuerySet of Category instances
        """
        return Category.objects.filter(user=user).order_by('-created_at')

    def create(self, user: User, **kwargs) -> Category:
        """
        Create a new category.
        
        Args:
            user: User instance
            **kwargs: Category fields (name, description, color)
            
        Returns:
            Created Category instance
        """
        return Category.objects.create(user=user, **kwargs)

    def update(self, category: Category, **kwargs) -> Category:
        """
        Update an existing category.
        
        Args:
            category: Category instance to update
            **kwargs: Fields to update
            
        Returns:
            Updated Category instance
        """
        for field, value in kwargs.items():
            setattr(category, field, value)
        category.save()
        return category

    def delete(self, category: Category) -> bool:
        """
        Delete a category.
        
        Args:
            category: Category instance to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            category.delete()
            return True
        except Exception:
            return False

    def search(self, user: User, query: str) -> QuerySet[Category]:
        """
        Search categories by name or description.
        
        Args:
            user: User instance
            query: Search query string
            
        Returns:
            QuerySet of matching Category instances
        """
        return Category.objects.filter(
            user=user
        ).filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by('-created_at')

    def get_paginated(self, user: User, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Get paginated categories for a user.
        
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

    def get_with_stats(self, user: User) -> QuerySet[Category]:
        """
        Get categories with form and process counts.
        
        Args:
            user: User instance
            
        Returns:
            QuerySet with annotated counts
        """
        # For now, return categories without stats since forms/processes aren't implemented yet
        return Category.objects.filter(user=user).order_by('-created_at')

    def exists_by_name(self, user: User, name: str, exclude_id: Optional[str] = None) -> bool:
        """
        Check if a category with the given name exists for the user.
        
        Args:
            user: User instance
            name: Category name to check
            exclude_id: Category ID to exclude from check (for updates)
            
        Returns:
            True if category exists, False otherwise
        """
        queryset = Category.objects.filter(user=user, name__iexact=name)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        return queryset.exists()

    def get_most_used(self, user: User, limit: int = 5) -> QuerySet[Category]:
        """
        Get most used categories by form/process count.
        
        Args:
            user: User instance
            limit: Maximum number of categories to return
            
        Returns:
            QuerySet of most used categories
        """
        # For now, return most recently created categories since forms/processes aren't implemented yet
        return Category.objects.filter(user=user).order_by('-created_at')[:limit]

    def bulk_delete(self, user: User, category_ids: List[str]) -> Dict[str, int]:
        """
        Delete multiple categories.
        
        Args:
            user: User instance
            category_ids: List of category IDs to delete
            
        Returns:
            Dictionary with deletion results
        """
        deleted_count, _ = Category.objects.filter(
            user=user, 
            id__in=category_ids
        ).delete()
        
        return {
            'deleted_count': deleted_count,
            'requested_count': len(category_ids)
        }
