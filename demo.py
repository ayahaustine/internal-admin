#!/usr/bin/env python3
"""
Demo script for Internal Admin Framework.

This script demonstrates the internal-admin framework setup and usage.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from internal_admin import AdminSite, AdminConfig, ModelAdmin
from internal_admin.auth.models import AdminUser
from internal_admin.auth.security import hash_password

# Import example models from example.py
from example import User, Category, Product, CategoryAdmin, ProductAdmin


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"🎯 {title}")
    print("=" * 60)


def print_success(message: str):
    """Print a success message."""
    print(f"✅ {message}")


def print_info(message: str):
    """Print an info message."""
    print(f"ℹ️  {message}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"⚠️  {message}")


def main():
    """Run the internal-admin demo."""
    
    print_header("Internal Admin Framework Demo")
    
    print_info("This demo shows the setup and capabilities of the internal-admin framework")
    print_info("A Django-style admin interface for FastAPI applications")
    
    # 1. Configuration Demo
    print_header("1. Configuration Setup")
    
    config = AdminConfig(
        database_url="sqlite:///./demo.db",
        secret_key="demo-secret-key-change-in-production", 
        user_model=User,
        debug=True
    )
    
    print_success("AdminConfig created")
    print_info(f"Database: {config.database_url}")
    print_info(f"Database Type: {'SQLite' if config.is_sqlite else 'PostgreSQL'}")
    print_info(f"Debug Mode: {config.debug}")
    
    # 2. Admin Site Setup
    print_header("2. AdminSite Setup")
    
    admin = AdminSite(config)
    print_success("AdminSite created")
    
    # 3. Model Registration
    print_header("3. Model Registration")
    
    # Register models with their admin classes
    admin.register(Category, CategoryAdmin)
    admin.register(Product, ProductAdmin) 
    admin.register(User)  # Uses default ModelAdmin
    
    print_success("Category registered with CategoryAdmin")
    print_success("Product registered with ProductAdmin")
    print_success("User registered with default ModelAdmin")
    
    # Show registered models
    registered_models = admin.get_registered_models()
    print_info(f"Total registered models: {len(registered_models)}")
    
    for model_class, admin_class in registered_models.items():
        print_info(f"  • {model_class.__name__} → {admin_class.__name__}")
    
    # 4. ModelAdmin Configuration Examples
    print_header("4. ModelAdmin Configuration Examples")
    
    category_admin = admin.get_model_admin(Category)
    print_info("CategoryAdmin Configuration:")
    print_info(f"  • List Display: {category_admin.get_list_display()}")
    print_info(f"  • Search Fields: {category_admin.get_search_fields()}")
    print_info(f"  • List Filters: {category_admin.get_list_filter()}")
    print_info(f"  • Ordering: {category_admin.get_ordering()}")
    
    product_admin = admin.get_model_admin(Product)
    print_info("ProductAdmin Configuration:")
    print_info(f"  • List Display: {product_admin.get_list_display()}")
    print_info(f"  • Search Fields: {product_admin.get_search_fields()}")
    print_info(f"  • List Filters: {product_admin.get_list_filter()}")
    print_info(f"  • Read-only Fields: {product_admin.get_readonly_fields()}")
    
    # 5. Architecture Overview
    print_header("5. Framework Architecture")
    
    print_info("🏗️  Architecture Components:")
    print_info("  • AdminSite - Central orchestrator")
    print_info("  • ModelAdmin - Per-model configuration")
    print_info("  • AdminConfig - Configuration container")
    print_info("  • Registry - Model registration system")
    print_info("  • Query Engine - Database query pipeline")
    print_info("  • Form Engine - Form generation and validation")
    print_info("  • Router Factory - Dynamic route generation")
    print_info("  • Authentication - Session-based auth system")
    print_info("  • Permission System - Role-based access control")
    
    # 6. Generated Routes Overview
    print_header("6. Generated Admin Routes")
    
    print_info("🛣️  Auto-generated Routes per Model:")
    print_info("  • GET  /admin/{model}/           - List view")
    print_info("  • GET  /admin/{model}/create/    - Create form")
    print_info("  • POST /admin/{model}/create/    - Create submit")
    print_info("  • GET  /admin/{model}/{id}/      - Edit form")
    print_info("  • POST /admin/{model}/{id}/      - Edit submit")
    print_info("  • GET  /admin/{model}/{id}/delete/ - Delete confirmation")
    print_info("  • POST /admin/{model}/{id}/delete/ - Delete submit")
    
    print_info("🔐 Authentication Routes:")
    print_info("  • GET  /admin/login  - Login form")
    print_info("  • POST /admin/login  - Login submit")
    print_info("  • POST /admin/logout - Logout")
    
    print_info("📊 Dashboard:")
    print_info("  • GET  /admin/       - Admin dashboard")
    
    # 7. Features Summary
    print_header("7. Key Features")
    
    features = [
        "🎨 Django-style admin interface",
        "📝 Automatic CRUD generation from SQLAlchemy models", 
        "🔍 Built-in search and filtering",
        "📄 Pagination with configurable page sizes",
        "🔐 Session-based authentication",
        "🛡️  Role-based permission system",
        "📱 Responsive Bootstrap 5 UI", 
        "🗄️  SQLite & PostgreSQL support",
        "⚡ FastAPI integration",
        "🎛️  Extensible via ModelAdmin classes",
        "🔧 Form validation and type conversion",
        "🪝 Model lifecycle hooks (before_save, after_save, etc.)",
        "🎯 Zero frontend build tools required",
        "📦 Pip-installable package"
    ]
    
    for feature in features:
        print_info(f"  {feature}")
    
    # 8. Next Steps
    print_header("8. Next Steps")
    
    print_info("To try the admin interface:")
    print_info("1. Run: python create_superuser.py")
    print_info("2. Run: python example.py")
    print_info("3. Visit: http://localhost:8000/admin/")
    
    print_warning("Note: This is a demonstration - use proper secrets in production!")
    
    print_header("Demo Complete")
    print_success("The internal-admin framework is ready to use!")
    print_info("Check the example.py file for a complete FastAPI application setup")


if __name__ == "__main__":
    main()