#!/usr/bin/env python3
"""
Demo web server for Internal Admin Framework.

Configuration is read from a .env file or environment variables:

    DATABASE_URL=sqlite:///./demo.db
    SECRET_KEY=your-secret-key

Before starting the server for the first time, create a superuser:

    internal-admin createsuperuser
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import uvicorn

from internal_admin import AdminSite, AdminConfig, ModelAdmin
from internal_admin.auth.models import AdminUser


class AdminUserAdmin(ModelAdmin):
    list_display = ["id", "username", "email", "is_superuser", "is_active", "created_at"]
    search_fields = ["username", "email"]
    list_filter = ["is_superuser", "is_active"]
    ordering = ["username"]
    readonly_fields = ["created_at", "last_login"]
    exclude_fields = ["password_hash"]

# Demo models
Base = declarative_base()


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


def create_demo_data(session):
    """Seed demo categories and products. Never creates users."""
    if session.query(DemoCategory).count() > 0:
        return

    electronics = DemoCategory(name="Electronics", description="Electronic devices")
    books = DemoCategory(name="Books", description="Books and literature")
    session.add_all([electronics, books])
    session.commit()

    products = [
        DemoProduct(name="Laptop", description="Gaming laptop", price=99999, category=electronics),
        DemoProduct(name="Phone", description="Smartphone", price=79999, category=electronics),
        DemoProduct(name="Python Guide", description="Learn Python programming", price=2999, category=books),
        DemoProduct(name="Django Book", description="Web development with Django", price=3499, category=books),
    ]
    session.add_all(products)
    session.commit()


def create_demo_app():
    """Create demo FastAPI app with authentication."""

    app = FastAPI(
        title="Internal Admin Demo",
        description="Demo of internal-admin framework.",
        version="1.0.0",
    )

    # Read config from environment / .env file
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./demo.db")
    secret_key = os.environ.get("SECRET_KEY", "demo-secret-key-change-in-production")

    config = AdminConfig(
        database_url=database_url,
        secret_key=secret_key,
        user_model=AdminUser,
        debug=True,
    )

    admin = AdminSite(config)
    admin.register(DemoCategory, DemoCategoryAdmin)
    admin.register(DemoProduct, DemoProductAdmin)
    admin.register(AdminUser, AdminUserAdmin)
    
    # Mount admin interface
    admin.mount(app)
    
    # Create database and demo data
    from internal_admin.database.admin_tables import create_admin_tables
    engine = create_engine(config.database_url)
    
    # Create both demo tables and admin tables
    Base.metadata.create_all(engine)  # Demo tables
    create_admin_tables(engine)  # Admin tables (users, activity logs)

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
    db = os.environ.get("DATABASE_URL", "sqlite:///./demo.db")
    print("Internal Admin Demo Server")
    print("=" * 60)
    print("Admin Interface: http://localhost:8080/admin/")
    print("Database:        " + db)
    print("=" * 60)
    print("No default users are created.")
    print("Run `internal-admin createsuperuser` first if you have")
    print("not already done so.")
    print("=" * 60)
    
    app = create_demo_app()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8080,
        reload=False
    )