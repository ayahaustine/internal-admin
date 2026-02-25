"""
Database management for Internal Admin.

This module handles SQLAlchemy engine and session management,
supporting both SQLite and PostgreSQL databases.
"""

from .engine import get_engine, create_engine_from_config
from .session import get_session, SessionManager

__all__ = [
    "get_engine",
    "create_engine_from_config", 
    "get_session",
    "SessionManager",
]