"""
Category-specific permissions and validation.
"""

from rest_framework import permissions
from categories.models import Category


class CategoryPermission(permissions.BasePermission):
    """
    Custom permission for category operations.
    Users can only access their own categories.
    """

    def has_permission(self, request, view):
        # Allow authenticated users to access category endpoints
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Users can only access their own categories
        return obj.user == request.user


class CategoryOwnerPermission(permissions.BasePermission):
    """
    Permission that ensures users can only access their own categories.
    """

    def has_object_permission(self, request, view, obj):
        # Check if the category belongs to the requesting user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False
