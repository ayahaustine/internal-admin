"""
Activity logging utilities for Internal Admin.

Provides functions to log user activities and system events.
"""

from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from .models import ActivityLog


def log_activity(
    session: Session,
    action: str,
    user_id: int | None = None,
    model_name: str | None = None,
    object_id: str | None = None,
    object_repr: str | None = None,
    description: str | None = None,
    request: Request | None = None,
) -> ActivityLog:
    """
    Log an activity to the database.

    Args:
        session: Database session
        action: Action type (create, update, delete, login, etc.)
        user_id: ID of the user performing the action
        model_name: Name of the model being affected
        object_id: ID of the object being affected
        object_repr: String representation of the object
        description: Additional description
        request: FastAPI request object for IP/user agent

    Returns:
        Created ActivityLog instance
    """
    ip_address = None
    user_agent = None

    if request:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    activity = ActivityLog(
        user_id=user_id,
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id is not None else None,
        object_repr=object_repr,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    session.add(activity)
    session.flush()  # Flush but don't commit - let caller handle commit
    return activity


def log_login(session: Session, user_id: int, request: Request | None = None) -> ActivityLog:
    """Log a successful login."""
    return log_activity(
        session=session,
        action="login",
        user_id=user_id,
        description="User logged in",
        request=request,
    )


def log_logout(session: Session, user_id: int, request: Request | None = None) -> ActivityLog:
    """Log a logout."""
    return log_activity(
        session=session,
        action="logout",
        user_id=user_id,
        description="User logged out",
        request=request,
    )


def log_create(
    session: Session,
    user_id: int,
    model_name: str,
    object_id: Any,
    object_repr: str,
    request: Request | None = None,
) -> ActivityLog:
    """Log object creation."""
    return log_activity(
        session=session,
        action="create",
        user_id=user_id,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        description=f"Created new {model_name}",
        request=request,
    )


def log_update(
    session: Session,
    user_id: int,
    model_name: str,
    object_id: Any,
    object_repr: str,
    request: Request | None = None,
) -> ActivityLog:
    """Log object update."""
    return log_activity(
        session=session,
        action="update",
        user_id=user_id,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        description=f"Updated {model_name}",
        request=request,
    )


def log_delete(
    session: Session,
    user_id: int,
    model_name: str,
    object_id: Any,
    object_repr: str,
    request: Request | None = None,
) -> ActivityLog:
    """Log object deletion."""
    return log_activity(
        session=session,
        action="delete",
        user_id=user_id,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        description=f"Deleted {model_name}",
        request=request,
    )


def get_recent_activities(session: Session, limit: int = 10) -> list[ActivityLog]:
    """
    Get recent activities for display.

    Args:
        session: Database session
        limit: Maximum number of activities to return

    Returns:
        List of recent ActivityLog instances
    """
    return (
        session.query(ActivityLog)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )
