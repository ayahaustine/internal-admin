"""
Configuration system for Internal Admin.

AdminConfig is the main configuration container that holds all
settings required for the admin system to function.
"""

import os
from typing import Optional, Type, Any
from dataclasses import dataclass


@dataclass
class AdminConfig:
    """
    Configuration container for Internal Admin.
    
    This class holds all configuration settings required for the admin system.
    Settings can be provided directly or via environment variables.
    
    Required settings:
    - database_url: SQLAlchemy database URL
    - secret_key: Secret key for session encryption  
    - user_model: SQLAlchemy model class for authentication
    
    Optional settings:
    - session_cookie_name: Name of session cookie (default: "admin_session")
    - login_route: Route path for login page (default: "/admin/login")
    - template_path_override: Custom template directory path
    - debug: Enable debug mode (default: False)
    - page_size: Default page size for lists (default: 25)
    """
    
    database_url: str
    secret_key: str
    user_model: Type[Any]
    
    # Optional settings with defaults
    session_cookie_name: str = "admin_session"
    login_route: str = "/admin/login"
    template_path_override: Optional[str] = None
    debug: bool = False
    page_size: int = 25
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate_required_fields()
        self._load_from_environment()
    
    def _validate_required_fields(self) -> None:
        """Validate that all required fields are provided."""
        if not self.database_url:
            raise ValueError("database_url is required")
        
        if not self.secret_key:
            raise ValueError("secret_key is required")
        
        if self.user_model is None:
            raise ValueError("user_model is required")
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables if not set."""
        # Override with environment variables if they exist
        env_database_url = os.getenv("DATABASE_URL")
        if env_database_url:
            self.database_url = env_database_url
        
        env_secret_key = os.getenv("SECRET_KEY")
        if env_secret_key:
            self.secret_key = env_secret_key
        
        env_debug = os.getenv("DEBUG", "").lower()
        if env_debug in ("true", "1", "yes"):
            self.debug = True
        
        env_page_size = os.getenv("ADMIN_PAGE_SIZE")
        if env_page_size and env_page_size.isdigit():
            self.page_size = int(env_page_size)
    
    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return self.database_url.startswith("sqlite")
    
    @property 
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return "postgresql" in self.database_url or "postgres" in self.database_url