from rest_framework import permissions


class IsProcessOwner(permissions.BasePermission):
    """
    Permission: Only process owner can access
    Used for Process and ProcessStep management
    """
    message = "You do not have permission to access this process"

    def has_permission(self, request, view):
        """Check permission at view level"""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check permission at object level
        obj can be Process or ProcessStep
        """
        # Find process owner based on obj type
        if hasattr(obj, 'user'):
            # If obj is Process itself
            return obj.user == request.user
        elif hasattr(obj, 'process'):
            # If obj is ProcessStep
            return obj.process.user == request.user

        return False


class IsProcessStepOwner(permissions.BasePermission):
    """
    Permission: Only step owner (through process) can access
    """
    message = "You do not have permission to access this process step"

    def has_permission(self, request, view):
        """Check permission at view level"""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check permission at object level"""
        if hasattr(obj, 'process'):
            return obj.process.user == request.user
        return False

