#!/usr/bin/env python3
"""
Demo web server for Internal Admin Framework (No Auth).

This runs a version of the admin interface without authentication
so you can test the UI and CRUD operations immediately.
"""

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import uvicorn

from internal_admin import AdminSite, AdminConfig, ModelAdmin

# Create database models (same as example)
Base = declarative_base()

class DemoUser(Base):
    """Demo user model (no password required)."""
    __tablename__ = "demo_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Required for AdminUser contract (dummy implementations)
    password_hash = Column(String(255), default="demo-no-password")
    
    @property
    def display_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username or self.email or f"User {self.id}"
    
    def has_permission(self, permission: str) -> bool:
        return self.is_active  # Demo: all active users have all permissions


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
    list_display = ["id", "name", "price", "is_active"]
    search_fields = ["name", "description"]
    list_filter = ["is_active", "category_id"]


def create_demo_data(session):
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
    
    # Create demo users
    users = [
        DemoUser(username="admin", email="admin@demo.com", first_name="Admin", last_name="User", is_superuser=True),
        DemoUser(username="demo", email="demo@demo.com", first_name="Demo", last_name="User"),
    ]
    session.add_all(users)
    session.commit()
    
    print("✅ Demo data created!")


def create_demo_app():
    """Create demo FastAPI app with no authentication."""
    
    app = FastAPI(
        title="Internal Admin Demo (No Auth)",
        description="Demo of internal-admin framework without authentication",
        version="1.0.0"
    )
    
    # Admin configuration (no auth required)
    config = AdminConfig(
        database_url="sqlite:///./demo_no_auth.db",
        secret_key="demo-secret-key",
        user_model=DemoUser,
        debug=True,
    )
    
    # Create admin site
    admin = AdminSite(config)
    
    # Override authentication for demo purposes
    class NoAuthAdminSite(AdminSite):
        def _create_auth_dependency(self):
            """Override to disable authentication."""
            async def no_auth_required(request: Request):
                # Create a fake user for demo purposes
                fake_user = DemoUser(
                    id=1,
                    username="demo_user",
                    email="demo@example.com",
                    is_active=True,
                    is_superuser=True
                )
                return fake_user
            return no_auth_required
    
    # Replace with no-auth version
    admin = NoAuthAdminSite(config)
    admin.register(DemoCategory, DemoCategoryAdmin)
    admin.register(DemoProduct, DemoProductAdmin)
    admin.register(DemoUser)
    
    # Mount admin interface
    admin.mount(app)
    
    # Create database and demo data
    engine = create_engine(config.database_url)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    create_demo_data(session)
    session.close()
    
    # Root redirect
    @app.get("/")
    async def root():
        return RedirectResponse(url="/admin/", status_code=302)
    
    return app


if __name__ == "__main__":
    print("🚀 Starting Internal Admin Demo Server (No Authentication)")
    print("=" * 60)
    print("📊 Admin Interface: http://localhost:8080/admin/")
    print("🏠 Auto-redirect: http://localhost:8080/")
    print("=" * 60)
    print("ℹ️  This demo bypasses authentication for easy testing")
    print("ℹ️  All CRUD operations are available immediately")
    print("=" * 60)
    
    app = create_demo_app()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8080,  # Use a common dev port
        reload=False  # Disable reload for demo
    )