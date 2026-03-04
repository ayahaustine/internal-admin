"""
Security utilities for Internal Admin.

Provides password hashing, session management, and security helpers.
"""

import secrets
from typing import Optional, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError

from ..config import AdminConfig


class SecurityManager:
    """
    Manages security operations for Internal Admin.
    
    Handles:
    - Password hashing and verification
    - Session token generation and validation
    - Security configuration
    """
    
    def __init__(self, config: AdminConfig) -> None:
        """
        Initialize SecurityManager with configuration.
        
        Args:
            config: AdminConfig instance with security settings
        """
        self.config = config
        # Use bcrypt as primary hasher for reliability
        self.pwd_context = CryptContext(
            schemes=["bcrypt"], 
            deprecated="auto",
            bcrypt__rounds=12
        )
        
        # JWT settings for session tokens
        self.algorithm = "HS256"
        self.session_expire_hours = 24
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password string
        """
        # Ensure password is not too long (bcrypt limitation)
        if len(password.encode('utf-8')) > 72:
            password = password[:72]
            
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored password hash
            
        Returns:
            True if password matches hash
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_session_token(self, user_id: int) -> str:
        """
        Create a session token for a user.
        
        Args:
            user_id: User ID to encode in token
            
        Returns:
            JWT session token
        """
        expire = datetime.utcnow() + timedelta(hours=self.session_expire_hours)
        
        payload = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "session"
        }
        
        return jwt.encode(payload, self.config.secret_key, algorithm=self.algorithm)
    
    def verify_session_token(self, token: str) -> Optional[int]:
        """
        Verify and decode a session token.
        
        Args:
            token: JWT session token to verify
            
        Returns:
            User ID if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token, 
                self.config.secret_key, 
                algorithms=[self.algorithm]
            )
            
            user_id = payload.get("user_id")
            token_type = payload.get("type")
            
            if token_type != "session" or user_id is None:
                return None
            
            return int(user_id)
        
        except JWTError:
            return None
    
    def generate_csrf_token(self) -> str:
        """
        Generate a CSRF token.
        
        Returns:
            Random CSRF token string
        """
        return secrets.token_urlsafe(32)


# Module-level functions for convenience
_security_manager: Optional[SecurityManager] = None


def initialize_security(config: AdminConfig) -> None:
    """Initialize the global security manager."""
    global _security_manager
    _security_manager = SecurityManager(config)


def get_security_manager() -> SecurityManager:
    """
    Get the global security manager.
    
    Returns:
        SecurityManager instance
        
    Raises:
        RuntimeError: If security manager not initialized
    """
    if _security_manager is None:
        raise RuntimeError(
            "SecurityManager not initialized. Call initialize_security() first."
        )
    return _security_manager


def hash_password(password: str) -> str:
    """
    Hash a password using the global security manager.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return get_security_manager().hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password using the global security manager.
    
    Args:
        plain_password: Plain text password
        hashed_password: Stored hash
        
    Returns:
        True if password is valid
    """
    return get_security_manager().verify_password(plain_password, hashed_password)