"""
Authentication models for Internal Admin.

Provides base user model and authentication-related database models.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class AdminUser(Base):
    """
    Base admin user model.

    This provides the minimum contract required for authentication.
    Projects can extend this or provide their own user model that
    implements the same interface.

    Required attributes:
    - id: Primary key
    - password_hash: Hashed password
    - is_active: Whether user can log in

    Optional attributes:
    - username: Login username
    - email: User email
    - is_superuser: Full admin access
    - created_at: Account creation timestamp
    - last_login: Last successful login
    """

    __tablename__ = "admin_users"

    # Required fields
    id = Column(Integer, primary_key=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Common optional fields
    username = Column(String(50), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        identifier = self.username or self.email or f"ID:{self.id}"
        return f"<AdminUser({identifier})>"

    @property
    def display_name(self) -> str:
        """Get a display name for the user."""
        return self.username or self.email or f"User {self.id}"

    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission.

        Base implementation - superusers have all permissions.
        Projects can override this method for custom permission logic.

        Args:
            permission: Permission string to check

        Returns:
            True if user has permission
        """
        if not self.is_active:
            return False

        if self.is_superuser:
            return True

        # Base implementation denies all permissions for regular users
        # Projects should override this for custom permission logic
        return False


class ActivityLog(Base):
    """
    Activity log model to track admin user actions.

    This model tracks all significant actions performed by admin users
    including create, update, delete operations and login events.
    """

    __tablename__ = "admin_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)  # create, update, delete, login, etc.
    model_name = Column(String(100), nullable=True, index=True)  # Target model name
    object_id = Column(String(50), nullable=True)  # ID of the affected object
    object_repr = Column(String(255), nullable=True)  # String representation of the object
    description = Column(Text, nullable=True)  # Additional details
    ip_address = Column(String(45), nullable=True)  # User's IP address
    user_agent = Column(Text, nullable=True)  # User's browser/client info
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationship to user (nullable for system actions)
    user = relationship("AdminUser", backref="activity_logs")

    def __repr__(self) -> str:
        return f"<ActivityLog({self.action} on {self.model_name or 'system'})>"

    @property
    def display_description(self) -> str:
        """Get a human-readable description of the activity."""
        if self.object_repr:
            return f"{self.action.title()} {self.model_name}: {self.object_repr}"
        elif self.model_name:
            return f"{self.action.title()} {self.model_name}"
        else:
            return f"{self.action.title()}"


def validate_user_model(user_model_class) -> None:
    """
    Validate that a user model class meets the required contract.

    Args:
        user_model_class: User model class to validate

    Raises:
        ValueError: If model doesn't meet requirements
    """
    required_attributes = ["id", "password_hash", "is_active"]

    for attr in required_attributes:
        if not hasattr(user_model_class, attr):
            raise ValueError(
                f"User model {user_model_class.__name__} must have '{attr}' attribute"
            )

    # Check if it has a table (SQLAlchemy model)
    if not hasattr(user_model_class, "__table__"):
        raise ValueError(
            f"User model {user_model_class.__name__} must be a SQLAlchemy model"
        )
