"""
SQLAlchemy session management for Internal Admin.

Provides session factory and context management for database operations.
"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session, sessionmaker

from .engine import get_engine


class SessionManager:
    """
    Manages SQLAlchemy session creation and lifecycle.

    Provides session factory and context managers for
    safe database transaction handling.
    """

    def __init__(self) -> None:
        self._session_factory = None

    def initialize(self) -> None:
        """Initialize the session factory with the global engine."""
        engine = get_engine()
        self._session_factory = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    def create_session(self) -> Session:
        """
        Create a new database session.

        Returns:
            New SQLAlchemy session

        Raises:
            RuntimeError: If session factory not initialized
        """
        if self._session_factory is None:
            raise RuntimeError(
                "SessionManager not initialized. Call initialize() first."
            )
        return self._session_factory()

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.

        Provides automatic session cleanup and transaction handling.
        Commits on success, rolls back on exception.

        Yields:
            Database session
        """
        session = self.create_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global session manager instance
_session_manager = SessionManager()


def initialize_session_manager() -> None:
    """Initialize the global session manager."""
    _session_manager.initialize()


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    return _session_manager


def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: Session = Depends(get_session)):
            # Use db session here
            pass

    Yields:
        Database session with automatic cleanup
    """
    with _session_manager.get_session() as session:
        yield session
