"""
SQLAlchemy engine management for Internal Admin.

Handles creation and configuration of SQLAlchemy engines
for both SQLite and PostgreSQL databases.
"""


from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import StaticPool

from ..config import AdminConfig

# Global engine instance
_engine: Engine | None = None


def create_engine_from_config(config: AdminConfig) -> Engine:
    """
    Create SQLAlchemy engine from AdminConfig.

    Args:
        config: AdminConfig instance with database settings

    Returns:
        Configured SQLAlchemy engine

    Raises:
        ValueError: If database URL is invalid or unsupported
    """
    database_url = config.database_url

    # Engine configuration based on database type
    engine_kwargs = {}

    if config.is_sqlite:
        # SQLite-specific configuration
        engine_kwargs.update({
            "poolclass": StaticPool,
            "connect_args": {
                "check_same_thread": False,  # Required for FastAPI
                "timeout": 20,
            },
            "echo": config.debug,
        })
    elif config.is_postgresql:
        # PostgreSQL-specific configuration
        engine_kwargs.update({
            "pool_size": 5,
            "max_overflow": 10,
            "pool_pre_ping": True,
            "echo": config.debug,
        })
    else:
        # Unsupported database
        raise ValueError(
            f"Unsupported database URL: {database_url}. "
            "Only SQLite and PostgreSQL are supported."
        )

    try:
        engine = create_engine(database_url, **engine_kwargs)
        return engine
    except Exception as e:
        raise ValueError(f"Failed to create database engine: {str(e)}") from e


def get_engine() -> Engine:
    """
    Get the global engine instance.

    Returns:
        The configured SQLAlchemy engine

    Raises:
        RuntimeError: If engine has not been initialized
    """
    if _engine is None:
        raise RuntimeError(
            "Database engine not initialized. "
            "Call create_engine_from_config() first."
        )
    return _engine


def set_engine(engine: Engine) -> None:
    """Set the global engine instance."""
    global _engine
    _engine = engine


def initialize_engine(config: AdminConfig) -> Engine:
    """
    Initialize the global engine from config.

    Args:
        config: AdminConfig instance

    Returns:
        The initialized engine
    """
    engine = create_engine_from_config(config)
    set_engine(engine)
    return engine
