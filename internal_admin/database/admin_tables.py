"""
Database utilities for Internal Admin.

Provides functions for creating admin-specific database tables.
"""

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from ..auth.models import Base as AdminBase


def create_admin_tables(engine: Engine) -> None:
    """
    Create all admin-specific database tables.

    This includes:
    - AdminUser table (if using built-in user model)
    - ActivityLog table (for activity logging)

    Args:
        engine: SQLAlchemy engine to create tables on
    """
    AdminBase.metadata.create_all(bind=engine)


def ensure_admin_tables_exist(session: Session) -> None:
    """
    Ensure admin tables exist in the database.

    This is a convenience function that can be called during
    admin initialization to make sure all required tables exist.

    Args:
        session: SQLAlchemy session to check tables with
    """
    engine = session.bind
    create_admin_tables(engine)
