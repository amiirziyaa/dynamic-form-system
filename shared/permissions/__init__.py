"""
Custom permissions for the dynamic forms system.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """

    def has_object_permission(self, request, view, obj):
        # Only allow the owner to access the object.
        return obj.user == request.user


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Custom permission to allow owners or staff members to access objects.
    """

    def has_object_permission(self, request, view, obj):
        # Allow staff members to access any object
        if request.user.is_staff:
            return True
        
        # Allow owners to access their own objects
        return obj.user == request.user
