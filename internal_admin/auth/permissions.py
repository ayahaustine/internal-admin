"""
Permission system for Internal Admin.

Provides role-based access control and permission checking utilities.
"""

from enum import Enum
from typing import Any


class Permission(Enum):
    """
    Standard admin permissions.

    These are the basic CRUD operations that can be performed
    on models in the admin interface.
    """
    VIEW = "view"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class PermissionManager:
    """
    Manages permission checking for Internal Admin.

    Provides centralized permission logic that can be extended
    by projects for custom authorization rules.
    """

    def __init__(self) -> None:
        """Initialize PermissionManager."""
        pass

    def has_model_permission(
        self,
        user: Any,
        model_class: Any,
        permission: Permission
    ) -> bool:
        """
        Check if user has permission for a model.

        Args:
            user: User object to check permissions for
            model_class: SQLAlchemy model class
            permission: Permission type to check

        Returns:
            True if user has permission
        """
        if not user or not hasattr(user, "is_active") or not user.is_active:
            return False

        # Superusers have all permissions
        if hasattr(user, "is_superuser") and user.is_superuser:
            return True

        # Check if user has permission method
        if hasattr(user, "has_permission"):
            permission_string = f"{model_class.__name__.lower()}_{permission.value}"
            return user.has_permission(permission_string)

        # Default: deny all permissions for regular users
        return False

    def has_object_permission(
        self,
        user: Any,
        obj: Any,
        permission: Permission
    ) -> bool:
        """
        Check if user has permission for a specific object.

        This allows for object-level permissions beyond model-level.

        Args:
            user: User object to check permissions for
            obj: Model instance to check permission for
            permission: Permission type to check

        Returns:
            True if user has permission for this specific object
        """
        if not user or not hasattr(user, "is_active") or not user.is_active:
            return False

        # Check model-level permission first
        if not self.has_model_permission(user, obj.__class__, permission):
            return False

        # For now, object-level permissions are same as model-level
        # Projects can override this method for custom object-level logic
        return True

    def check_permission(
        self,
        user: Any,
        model_class: Any,
        permission: Permission,
        obj: Any | None = None
    ) -> None:
        """
        Check permission and raise exception if denied.

        Args:
            user: User to check permissions for
            model_class: Model class
            permission: Permission to check
            obj: Optional specific object for object-level permissions

        Raises:
            PermissionError: If user doesn't have permission
        """
        if obj is not None:
            has_perm = self.has_object_permission(user, obj, permission)
            context = f"{permission.value} {obj.__class__.__name__} object"
        else:
            has_perm = self.has_model_permission(user, model_class, permission)
            context = f"{permission.value} {model_class.__name__} objects"

        if not has_perm:
            user_display = getattr(user, "display_name", "Anonymous") if user else "Anonymous"
            raise PermissionError(f"User {user_display} does not have permission to {context}")


# Global permission manager
_permission_manager = PermissionManager()


def get_permission_manager() -> PermissionManager:
    """Get the global permission manager instance."""
    return _permission_manager


def has_permission(
    user: Any,
    model_class: Any,
    permission: Permission,
    obj: Any | None = None
) -> bool:
    """
    Check if user has permission using global permission manager.

    Args:
        user: User to check permissions for
        model_class: Model class
        permission: Permission to check
        obj: Optional specific object

    Returns:
        True if user has permission
    """
    if obj is not None:
        return _permission_manager.has_object_permission(user, obj, permission)
    else:
        return _permission_manager.has_model_permission(user, model_class, permission)
