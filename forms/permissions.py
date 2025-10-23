from rest_framework import permissions


class IsFormOwner(permissions.BasePermission):
    """
    Permission: Only form owner can access
    Used for FormField and FieldOption management
    """
    message = "You do not have permission to access this form"

    def has_permission(self, request, view):
        """Check permission at view level"""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check permission at object level
        obj can be Form, FormField, or FieldOption
        """
        # Find form owner based on obj type
        if hasattr(obj, 'user'):
            # If obj is Form itself
            return obj.user == request.user
        elif hasattr(obj, 'form'):
            # If obj is FormField
            return obj.form.user == request.user
        elif hasattr(obj, 'field'):
            # If obj is FieldOption
            return obj.field.form.user == request.user

        return False


class IsFieldOwner(permissions.BasePermission):
    """
    Permission: Only field owner (through form) can access
    """
    message = "You do not have permission to access this field"

    def has_permission(self, request, view):
        """Check permission at view level"""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check permission at object level"""
        if hasattr(obj, 'form'):
            return obj.form.user == request.user
        return False


class CanManageFieldOptions(permissions.BasePermission):
    """
    Permission: Can manage options only for select/radio/checkbox fields
    """
    message = "This field type cannot have options"

    def has_permission(self, request, view):
        """Check at view level - basic authentication"""
        if not (request.user and request.user.is_authenticated):
            return False

        # Allow read operations
        if request.method in permissions.SAFE_METHODS:
            return True

        return True

    def has_object_permission(self, request, view, obj):
        """Check at object level"""
        # Check ownership
        if hasattr(obj, 'field'):
            field = obj.field
            if field.form.user != request.user:
                return False

            # Check field type
            if field.field_type not in ['select', 'radio', 'checkbox']:
                self.message = f"Field type '{field.field_type}' cannot have options"
                return False

        return True