"""
Database management for Internal Admin.

This module handles SQLAlchemy engine and session management,
supporting both SQLite and PostgreSQL databases.
"""

from .engine import create_engine_from_config, get_engine
from .session import SessionManager, get_session

__all__ = [
    "get_engine",
    "create_engine_from_config",
    "get_session",
    "SessionManager",
]
