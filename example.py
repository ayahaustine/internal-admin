#!/usr/bin/env python3
"""
Example usage of Internal Admin Framework.

This demonstrates how to set up and use the internal-admin framework
with a simple FastAPI application.
"""

from fastapi import FastAPI
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from internal_admin import AdminSite, AdminConfig, ModelAdmin
from internal_admin.auth.models import AdminUser

# Create database models
Base = declarative_base()


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    # Required fields for AdminUser contract
    id = Column(Integer, primary_key=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Additional user fields
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @property
    def display_name(self) -> str:
        """Get a display name for the user."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username or self.email or f"User {self.id}"
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if not self.is_active:
            return False
        if self.is_superuser:
            return True
        return False


class Category(Base):
    """Product category model."""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    products = relationship("Product", back_populates="category")


class Product(Base):
    """Product model."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Integer)  # Price in cents
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign key
    category_id = Column(Integer, ForeignKey("categories.id"))
    
    # Relationship
    category = relationship("Category", back_populates="products")


# Admin configuration classes
class CategoryAdmin(ModelAdmin):
    """Admin configuration for Category model."""
    list_display = ["id", "name", "is_active", "created_at"]
    search_fields = ["name", "description"]
    list_filter = ["is_active"]
    ordering = ["name"]
    
    def get_queryset(self, session):
        """Custom queryset - only show active categories."""
        return session.query(self.model).filter(self.model.is_active == True)


class ProductAdmin(ModelAdmin):
    """Admin configuration for Product model."""
    list_display = ["id", "name", "price", "is_active"]
    search_fields = ["name", "description"]
    list_filter = ["is_active", "category_id"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at"]
    
    def before_save(self, obj, is_create=False):
        """Hook called before saving."""
        if is_create:
            print(f"Creating new product: {obj.name}")
    
    def after_save(self, obj, is_create=False):
        """Hook called after saving."""
        action = "created" if is_create else "updated"
        print(f"Product {obj.name} {action} successfully")


def create_app():
    """Create and configure the FastAPI application."""
    
    # FastAPI app
    app = FastAPI(
        title="Internal Admin Example",
        description="Example application using internal-admin framework",
        version="1.0.0"
    )
    
    # Admin configuration
    config = AdminConfig(
        database_url="sqlite:///./example.db",  # SQLite for simplicity
        secret_key="your-secret-key-change-in-production",
        user_model=User,
        debug=True,  # Enable debug mode for development
    )
    
    # Create admin site
    admin = AdminSite(config)
    
    # Register models with their admin classes
    admin.register(Category, CategoryAdmin)
    admin.register(Product, ProductAdmin)
    admin.register(User)  # Use default ModelAdmin
    
    # Mount admin interface
    admin.mount(app)
    
    # Create database tables
    engine = create_engine(config.database_url)
    Base.metadata.create_all(engine)
    
    # Add a simple API endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Welcome to Internal Admin Example",
            "admin_url": "/admin/",
            "docs_url": "/docs"
        }
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    # Create the app
    app = create_app()
    
    print("="*60)
    print("🚀 Internal Admin Example")
    print("="*60)
    print("📊 Admin Interface: http://localhost:8000/admin/")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🏠 Home: http://localhost:8000/")
    print("="*60)
    print()
    print("To create a superuser, run:")
    print("python create_superuser.py")
    print()
    
    # Run the development server
    uvicorn.run(
        "example:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        reload_dirs=["internal_admin"],
    )