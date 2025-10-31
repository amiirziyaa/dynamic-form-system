from typing import List, Optional, Dict, Any
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from categories.models import Category
from categories.repository import CategoryRepository
from shared.exceptions import NotFoundError, ValidationError as CustomValidationError

User = get_user_model()


class CategoryService:
    """
    Service class for Category business logic.
    Handles all business rules and orchestrates repository operations.
    """

    def __init__(self):
        self.repository = CategoryRepository()

    def create_category(self, user: User, name: str, description: Optional[str] = None, 
                       color: Optional[str] = None) -> Category:
        """
        Create a new category with business logic validation.
        
        Args:
            user: User instance
            name: Category name
            description: Optional description
            color: Optional hex color code
            
        Returns:
            Created Category instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate input
        self._validate_category_data(name, description, color)
        
        # Check for duplicate names
        if self.repository.exists_by_name(user, name):
            raise CustomValidationError(
                f"A category with the name '{name}' already exists."
            )
        
        # Create category
        try:
            with transaction.atomic():
                category = self.repository.create(
                    user=user,
                    name=name.strip(),
                    description=description.strip() if description else None,
                    color=self._validate_color(color) if color else None
                )
                return category
        except Exception as e:
            raise CustomValidationError(f"Failed to create category: {str(e)}")

    def get_category(self, user: User, category_id: str) -> Category:
        """
        Get a category by ID for a specific user.
        
        Args:
            user: User instance
            category_id: Category UUID string
            
        Returns:
            Category instance
            
        Raises:
            NotFoundError: If category not found
        """
        category = self.repository.get_by_id(category_id, user)
        if not category:
            raise NotFoundError("Category not found")
        return category

    def list_categories(self, user: User, page: int = 1, page_size: int = 20, 
                       search: Optional[str] = None, include_stats: bool = False) -> Dict[str, Any]:
        """
        List categories for a user with pagination and search.
        
        Args:
            user: User instance
            page: Page number (1-based)
            page_size: Number of items per page
            search: Optional search query
            include_stats: Whether to include form/process counts
            
        Returns:
            Dictionary with paginated results
        """
        if search:
            queryset = self.repository.search(user, search)
            paginator = self._paginate_queryset(queryset, page, page_size)
        elif include_stats:
            queryset = self.repository.get_with_stats(user)
            paginator = self._paginate_queryset(queryset, page, page_size)
        else:
            return self.repository.get_paginated(user, page, page_size)
        
        return {
            'results': list(paginator['results']),
            'pagination': paginator['pagination']
        }

    def update_category(self, user: User, category_id: str, name: Optional[str] = None,
                       description: Optional[str] = None, color: Optional[str] = None) -> Category:
        """
        Update a category with business logic validation.
        
        Args:
            user: User instance
            category_id: Category UUID string
            name: New category name
            description: New description
            color: New hex color code
            
        Returns:
            Updated Category instance
            
        Raises:
            NotFoundError: If category not found
            ValidationError: If validation fails
        """
        category = self.get_category(user, category_id)
        
        # Prepare update data
        update_data = {}
        
        if name is not None:
            self._validate_name(name)
            if self.repository.exists_by_name(user, name, exclude_id=category_id):
                raise CustomValidationError(
                    f"A category with the name '{name}' already exists."
                )
            update_data['name'] = name.strip()
        
        if description is not None:
            self._validate_description(description)
            update_data['description'] = description.strip() if description else None
        
        if color is not None:
            update_data['color'] = self._validate_color(color) if color else None
        
        # Update category
        try:
            with transaction.atomic():
                updated_category = self.repository.update(category, **update_data)
                return updated_category
        except Exception as e:
            raise CustomValidationError(f"Failed to update category: {str(e)}")

    def delete_category(self, user: User, category_id: str) -> bool:
        """
        Delete a category.
        
        Args:
            user: User instance
            category_id: Category UUID string
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If category not found
        """
        category = self.get_category(user, category_id)
        
        try:
            with transaction.atomic():
                return self.repository.delete(category)
        except Exception as e:
            raise CustomValidationError(f"Failed to delete category: {str(e)}")

    def bulk_delete_categories(self, user: User, category_ids: List[str]) -> Dict[str, Any]:
        """
        Delete multiple categories.
        
        Args:
            user: User instance
            category_ids: List of category IDs to delete
            
        Returns:
            Dictionary with deletion results
            
        Raises:
            ValidationError: If validation fails
        """
        if not category_ids:
            raise CustomValidationError("No category IDs provided")
        
        if len(category_ids) > 50:  # Prevent bulk operations that are too large
            raise CustomValidationError("Cannot delete more than 50 categories at once")
        
        try:
            with transaction.atomic():
                result = self.repository.bulk_delete(user, category_ids)
                return {
                    'deleted_count': result['deleted_count'],
                    'requested_count': result['requested_count'],
                    'success': result['deleted_count'] > 0
                }
        except Exception as e:
            raise CustomValidationError(f"Failed to delete categories: {str(e)}")

    def get_category_stats(self, user: User, category_id: str) -> Dict[str, Any]:
        """
        Get statistics for a specific category.
        
        Args:
            user: User instance
            category_id: Category UUID string
            
        Returns:
            Dictionary with category statistics
            
        Raises:
            NotFoundError: If category not found
        """
        category = self.get_category(user, category_id)
        
        # For now, return 0 counts since forms/processes aren't implemented yet
        forms_count = 0  # category.form_set.count() when forms are implemented
        processes_count = 0  # category.process_set.count() when processes are implemented
        
        return {
            'category_id': str(category.id),
            'name': category.name,
            'forms_count': forms_count,
            'processes_count': processes_count,
            'total_items': forms_count + processes_count,
            'created_at': category.created_at,
            'updated_at': category.updated_at
        }

    def get_most_used_categories(self, user: User, limit: int = 5) -> List[Category]:
        """
        Get most used categories by form/process count.
        
        Args:
            user: User instance
            limit: Maximum number of categories to return
            
        Returns:
            List of most used categories
        """
        return list(self.repository.get_most_used(user, limit))

    def _validate_category_data(self, name: str, description: Optional[str], color: Optional[str]):
        """Validate category input data."""
        self._validate_name(name)
        if description:
            self._validate_description(description)
        if color:
            self._validate_color(color)

    def _validate_name(self, name: str):
        """Validate category name."""
        if not name or not name.strip():
            raise CustomValidationError("Category name is required")
        
        if len(name.strip()) > 255:
            raise CustomValidationError("Category name cannot exceed 255 characters")
        
        if len(name.strip()) < 2:
            raise CustomValidationError("Category name must be at least 2 characters long")

    def _validate_description(self, description: str):
        """Validate category description."""
        if description and len(description) > 1000:
            raise CustomValidationError("Category description cannot exceed 1000 characters")

    def _validate_color(self, color: str) -> str:
        """Validate and normalize hex color code."""
        if not color:
            return None
        
        # Remove # if present
        color = color.strip().lstrip('#')
        
        # Validate hex color format
        if len(color) not in [3, 6]:
            raise CustomValidationError("Color must be a valid hex code (3 or 6 characters)")
        
        try:
            int(color, 16)
        except ValueError:
            raise CustomValidationError("Color must be a valid hex code")
        
        return f"#{color.upper()}"

    def _paginate_queryset(self, queryset, page: int, page_size: int) -> Dict[str, Any]:
        """Helper method to paginate a queryset."""
        from django.core.paginator import Paginator
        
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
