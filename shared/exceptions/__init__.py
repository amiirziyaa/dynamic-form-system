"""
Custom exceptions for the dynamic forms system.
"""


class DynamicFormsException(Exception):
    """Base exception for dynamic forms system."""
    pass


class NotFoundError(DynamicFormsException):
    """Raised when a requested resource is not found."""
    pass


class ValidationError(DynamicFormsException):
    """Raised when validation fails."""
    pass


class PermissionError(DynamicFormsException):
    """Raised when user doesn't have required permissions."""
    pass


class BusinessLogicError(DynamicFormsException):
    """Raised when business logic validation fails."""
    pass
