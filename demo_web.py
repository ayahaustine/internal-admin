#!/usr/bin/env python3
"""
Demo web server for Internal Admin Framework (With Auth).

This runs the admin interface with proper authentication.
Login with: admin / password123
"""

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import uvicorn

from internal_admin import AdminSite, AdminConfig, ModelAdmin
from internal_admin.auth.security import SecurityManager

# Create database models (same as example)
Base = declarative_base()

class DemoUser(Base):
    """Demo user model - compatible with authentication system."""
    __tablename__ = "demo_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    password_hash = Column(String(255), nullable=False)  # Required for auth
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @property
    def display_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username or self.email or f"User {self.id}"


class DemoCategory(Base):
    """Demo category model."""
    __tablename__ = "demo_categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    products = relationship("DemoProduct", back_populates="category")


class DemoProduct(Base):
    """Demo product model."""
    __tablename__ = "demo_products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Integer)  # Price in cents
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    category_id = Column(Integer, ForeignKey("demo_categories.id"))
    
    category = relationship("DemoCategory", back_populates="products")


# Admin classes
class DemoCategoryAdmin(ModelAdmin):
    list_display = ["id", "name", "is_active", "created_at"]
    search_fields = ["name", "description"]
    list_filter = ["is_active"]
    ordering = ["name"]


class DemoProductAdmin(ModelAdmin):
    list_display = ["id", "name", "price", "description", "is_active"]
    search_fields = ["name", "description"]
    list_filter = ["is_active", "category_id"]


def create_demo_data(session, security_manager):
    """Create some demo data for testing."""
    
    # Check if data already exists
    if session.query(DemoCategory).count() > 0:
        return
    
    # Create categories
    electronics = DemoCategory(name="Electronics", description="Electronic devices")
    books = DemoCategory(name="Books", description="Books and literature")
    session.add_all([electronics, books])
    session.commit()
    
    # Create products
    products = [
        DemoProduct(name="Laptop", description="Gaming laptop", price=99999, category=electronics),
        DemoProduct(name="Phone", description="Smartphone", price=79999, category=electronics),
        DemoProduct(name="Python Guide", description="Learn Python programming", price=2999, category=books),
        DemoProduct(name="Django Book", description="Web development with Django", price=3499, category=books),
    ]
    session.add_all(products)
    
    # Create demo users with proper password hashing
    admin_password_hash = security_manager.hash_password("password123")
    demo_password_hash = security_manager.hash_password("demopass")
    
    users = [
        DemoUser(
            username="admin", 
            email="admin@demo.com", 
            first_name="Admin", 
            last_name="User", 
            password_hash=admin_password_hash,
            is_superuser=True,
            is_active=True
        ),
        DemoUser(
            username="demo", 
            email="demo@demo.com", 
            first_name="Demo", 
            last_name="User",
            password_hash=demo_password_hash,
            is_active=True
        ),
    ]
    session.add_all(users)
    session.commit()
    
    print("✅ Demo data created!")
    print("🔑 Admin login: admin / password123")
    print("🔑 Demo login: demo / demopass")


def create_demo_app():
    """Create demo FastAPI app with authentication."""
    
    app = FastAPI(
        title="Internal Admin Demo (With Auth)",
        description="Demo of internal-admin framework with authentication. Login: admin/password123",
        version="1.0.0"
    )
    
    # Admin configuration with authentication enabled
    config = AdminConfig(
        database_url="sqlite:///./demo_with_auth.db",
        secret_key="demo-secret-key-for-auth-session",
        user_model=DemoUser,
        debug=True,
    )
    
    # Create admin site with authentication
    admin = AdminSite(config)
    admin.register(DemoCategory, DemoCategoryAdmin)
    admin.register(DemoProduct, DemoProductAdmin)
    admin.register(DemoUser)
    
    # Mount admin interface
    admin.mount(app)
    
    # Create database and demo data
    from internal_admin.database.admin_tables import create_admin_tables
    engine = create_engine(config.database_url)
    
    # Create both demo tables and admin tables
    Base.metadata.create_all(engine)  # Demo tables
    create_admin_tables(engine)  # Admin tables (users, activity logs)
    
    # Create security manager for password hashing
    security_manager = SecurityManager(config)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    create_demo_data(session, security_manager)
    session.close()
    
    # Root redirect
    @app.get("/")
    async def root():
        return RedirectResponse(url="/admin/", status_code=302)
    
    return app


if __name__ == "__main__":
    print("🚀 Starting Internal Admin Demo Server (With Authentication)")
    print("=" * 60)
    print("📊 Admin Interface: http://localhost:8080/admin/")
    print("🏠 Auto-redirect: http://localhost:8080/")
    print("=" * 60)
    print("🔐 Authentication Required!")
    print("🔑 Admin login: admin / password123")
    print("🔑 Demo login: demo / demopass")
    print("=" * 60)
    
    app = create_demo_app()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8080,  # Use a common dev port
        reload=False  # Disable reload for demo
    )