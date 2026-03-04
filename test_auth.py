"""
Test script to verify authentication functionality.
"""

import os
import asyncio
from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

from internal_admin.config import AdminConfig
from internal_admin.site import AdminSite
from internal_admin.auth.models import AdminUser

# Create test database
Base = declarative_base()


class TestUser(Base):
    """Test user model for authentication."""
    __tablename__ = "test_users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    @property
    def display_name(self):
        return self.username
    
    def has_permission(self, permission: str) -> bool:
        return self.is_superuser if self.is_active else False


def create_test_app():
    """Create test FastAPI app with admin."""
    # Configure admin first
    config = AdminConfig(
        database_url="sqlite:///test_admin.db",
        secret_key="test-secret-key-change-in-production",
        user_model=TestUser,
        debug=True
    )
    
    # Setup test database
    engine = create_engine("sqlite:///test_admin.db", echo=True)
    Base.metadata.create_all(engine)
    
    # Initialize security for password hashing
    from internal_admin.auth.security import initialize_security, hash_password
    initialize_security(config)
    
    # Create test user
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    existing_user = session.query(TestUser).filter(TestUser.username == "admin").first()
    if not existing_user:
        test_user = TestUser(
            username="admin",
            password_hash=hash_password("password123"),
            is_active=True,
            is_superuser=True
        )
        session.add(test_user)
        session.commit()
        print("Created test user: admin / password123")
    else:
        print("Test user already exists: admin / password123")
    
    session.close()
    
    # Create app and mount admin
    app = FastAPI(title="Test Admin")
    admin_site = AdminSite(config)
    
    # Register test user model itself for admin management
    admin_site.register(TestUser)
    
    # Mount admin
    admin_site.mount(app)
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    app = create_test_app()
    
    print("Starting test server...")
    print("Admin panel: http://localhost:8001/admin/")
    print("Login: admin / password123")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)